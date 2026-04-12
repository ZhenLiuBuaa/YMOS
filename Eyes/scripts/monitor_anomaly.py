#!/usr/bin/env python3
"""
YMOS 盘中异动监控脚本
- 每 30 分钟扫描持仓 + Watchlist 价格（Yahoo Finance，免费无限制）
- 检测异动（日内涨跌 ≥ ±5%）
- 异动时唤起 Claude 分析并发微信通知
- 不消耗 Tushare（500次/分钟）和 Finnhub（60次/分钟）配额

API 配额说明：
  Tushare:  500 calls/min — 仅用于每日雷达（1次批量调用/天）
  Finnhub:  60 calls/min  — 当前持仓全 A 股，未消耗
  Yahoo:    无限制         — 本脚本使用，盘中监控专用

用法：
  python3 Eyes/scripts/monitor_anomaly.py              # 正常运行
  python3 Eyes/scripts/monitor_anomaly.py --force       # 忽略交易时段检查
  python3 Eyes/scripts/monitor_anomaly.py --threshold 3 # 自定义阈值（%）
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, time as dtime
from pathlib import Path

# ── 配置 ──
YMOS_ROOT = Path(__file__).resolve().parent.parent.parent
ALERT_THRESHOLD_PCT = 5  # ±5% 触发异动
PRICE_CACHE = YMOS_ROOT / "Eyes" / "scripts" / ".price_cache.json"
ALERT_LOG = YMOS_ROOT / "Eyes" / "scripts" / ".alert_log.json"
CLAUDE_PATH = "/opt/homebrew/bin/claude"

STATE_FILES = {
    "持仓": YMOS_ROOT / "持仓与关注" / "持仓_状态机.md",
    "关注": YMOS_ROOT / "持仓与关注" / "Watchlist_状态机.md",
}


def is_trading_hours():
    """检查是否在 A 股交易时段（含前后 5 分钟缓冲）"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    t = now.time()
    morning = dtime(9, 25) <= t <= dtime(11, 35)
    afternoon = dtime(12, 55) <= t <= dtime(15, 5)
    return morning or afternoon


def extract_tickers_with_names(filepath):
    """从状态机 Markdown 表格提取 名称 + Ticker"""
    results = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            # 匹配: | 名称 | 603533.SS | ...
            m = re.match(
                r'\|\s*([^|]+?)\s*\|\s*(\d{6}\.\w{2})\s*\|', line
            )
            if m:
                name = m.group(1).strip()
                ticker = m.group(2).strip()
                if name not in ("名称",):  # 跳过表头
                    results.append({"name": name, "ticker": ticker})
    return results


def fetch_prices_yahoo(tickers):
    """Yahoo Finance 批量获取价格（免费无限制）"""
    try:
        import yfinance as yf
    except ImportError:
        print("❌ yfinance 未安装: pip3 install yfinance")
        sys.exit(1)

    results = {}
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="2d")
            if len(hist) >= 1:
                current = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2] if len(hist) >= 2 else current
                change = (current - prev) / prev if prev else 0
                results[t] = {
                    "price": round(float(current), 3),
                    "prev_close": round(float(prev), 3),
                    "change_pct": round(float(change), 4),
                }
            time.sleep(0.5)  # 避免请求过快
        except Exception as e:
            print(f"  ⚠️  {t}: {e}")
    return results


def detect_anomalies(prices, threshold):
    """检测日内涨跌超过阈值的标的"""
    return [
        {"ticker": t, "price": d["price"], "change_pct": d["change_pct"]}
        for t, d in prices.items()
        if abs(d["change_pct"]) >= threshold / 100
    ]


def already_alerted_today(ticker):
    """检查今日是否已对该标的发过警报（避免重复推送）"""
    if not ALERT_LOG.exists():
        return False
    try:
        log = json.loads(ALERT_LOG.read_text())
        today = datetime.now().strftime("%Y-%m-%d")
        return ticker in log.get(today, [])
    except Exception:
        return False


def record_alert(tickers):
    """记录今日已发警报的标的"""
    today = datetime.now().strftime("%Y-%m-%d")
    log = {}
    if ALERT_LOG.exists():
        try:
            log = json.loads(ALERT_LOG.read_text())
        except Exception:
            pass
    if today not in log:
        log[today] = []
    log[today].extend(tickers)
    # 只保留最近 7 天
    cutoff = (datetime.now().replace(hour=0, minute=0, second=0) -
              __import__("datetime").timedelta(days=7)).strftime("%Y-%m-%d")
    log = {k: v for k, v in log.items() if k >= cutoff}
    ALERT_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2))


def trigger_claude_analysis(anomalies, ticker_names):
    """唤起 Claude 分析异动 + 微信推送"""
    details = []
    for a in anomalies:
        name = ticker_names.get(a["ticker"], a["ticker"])
        details.append(f"  {name}({a['ticker']}): ¥{a['price']} ({a['change_pct']:+.1%})")
    details_str = "\n".join(details)

    prompt = f"""[YMOS 盘中异动警报] {datetime.now().strftime('%Y-%m-%d %H:%M')}

以下标的触发 ±5% 异动阈值：
{details_str}

请执行：
1. 读取 持仓与关注/持仓_状态机.md 和 Watchlist_状态机.md
2. 对每个异动标的，根据已有 P4 关注点简要分析可能原因
3. 给出操作建议（持有/观察/建议跑策略分析）
4. 生成小于 100 字的中文摘要，通过微信发送给用户（chat_id 从 wechat status 获取）
5. 摘要格式：[异动] 日期时间 + 标的 + 涨跌幅 + 建议动作"""

    print(f"🤖 唤起 Claude 分析...")
    try:
        subprocess.Popen(
            [CLAUDE_PATH, "-p", prompt,
             "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep,mcp__*"],
            cwd=str(YMOS_ROOT),
            stdout=open("/tmp/ymos_alert.log", "a"),
            stderr=subprocess.STDOUT,
        )
        print(f"✅ Claude 已启动，分析结果将通过微信推送")
    except Exception as e:
        print(f"❌ 启动 Claude 失败: {e}")


def save_cache(prices):
    """保存价格缓存"""
    data = {"timestamp": datetime.now().isoformat(), "prices": prices}
    PRICE_CACHE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    # 解析参数
    force = "--force" in sys.argv
    threshold = ALERT_THRESHOLD_PCT
    for i, arg in enumerate(sys.argv):
        if arg == "--threshold" and i + 1 < len(sys.argv):
            threshold = float(sys.argv[i + 1])

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{'=' * 55}")
    print(f"YMOS 盘中异动监控 — {now_str}")
    print(f"阈值: ±{threshold}% | Yahoo Finance（免费无限制）")
    print(f"{'=' * 55}")

    # 交易时段检查
    if not force and not is_trading_hours():
        print("⏸️  非交易时段，跳过。（用 --force 强制运行）")
        return

    # 提取标的
    all_items = []
    ticker_names = {}
    for label, path in STATE_FILES.items():
        items = extract_tickers_with_names(path)
        print(f"📋 {label}: {len(items)} 个标的")
        all_items.extend(items)

    # 去重
    seen = set()
    unique_tickers = []
    for item in all_items:
        if item["ticker"] not in seen:
            seen.add(item["ticker"])
            unique_tickers.append(item["ticker"])
            ticker_names[item["ticker"]] = item["name"]
    print(f"📊 去重后共 {len(unique_tickers)} 个标的\n")

    # 拉取价格
    print("📡 拉取实时价格...")
    prices = fetch_prices_yahoo(unique_tickers)
    print(f"✅ 获取 {len(prices)}/{len(unique_tickers)} 个\n")

    # 展示
    for t in sorted(prices.keys()):
        d = prices[t]
        flag = "🔴" if abs(d["change_pct"]) >= threshold / 100 else "  "
        name = ticker_names.get(t, t)
        print(f"  {flag} {name:12s} {t:12s} ¥{d['price']:>10.3f}  {d['change_pct']:+.2%}")

    # 检测异动
    anomalies = detect_anomalies(prices, threshold)

    # 过滤已通知过的
    new_anomalies = [a for a in anomalies if not already_alerted_today(a["ticker"])]

    if new_anomalies:
        print(f"\n🚨 新异动 {len(new_anomalies)} 个！")
        trigger_claude_analysis(new_anomalies, ticker_names)
        record_alert([a["ticker"] for a in new_anomalies])
    elif anomalies:
        print(f"\n⚠️  {len(anomalies)} 个异动已在今日通知过，不重复推送")
    else:
        print(f"\n✅ 无异动（阈值 ±{threshold}%）")

    save_cache(prices)
    print(f"\n💾 缓存已更新: {PRICE_CACHE}")


if __name__ == "__main__":
    main()
