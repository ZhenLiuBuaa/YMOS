# YMOS — Claude Code 上下文配置

> 本文件由 Claude Code 自动加载。每次新会话开始时，Claude 会按以下顺序初始化上下文，无需用户手动提供路径。

---

## 项目根目录

```
/Users/zhen.liu/.claude/projects/YMOS
```

---

## 会话启动：必读文件（按顺序）

每次新会话开始，Claude 必须依次读取以下文件，完成上下文初始化：

1. **`总入口暗号.md`** — 所有暗号路由表，了解可用指令
2. **`持仓与关注/当前关注方向与投资偏好.md`** — 用户投资策略（灵魂文件）
3. **`持仓与关注/持仓_状态机.md`** — 当前持仓真相源
4. **`持仓与关注/Watchlist_状态机.md`** — 当前关注真相源

> 读取完成后，主动告知用户："✅ YMOS 上下文已加载，当前持仓 N 个标的，关注 M 个标的。可直接使用暗号操作。"

---

## 日常任务序列（每日四步闭环）

```
跑一下市场洞察   →  Eyes/SOP_市场洞察.md
       ↓ 等待完成
跑一下投资雷达   →  Eyes/SOP_投资雷达.md
       ↓ 等待完成
跑一下策略分析   →  Brain/SOP_策略分析.md
       ↓ 等待完成
收口一下         →  持仓与关注/SOP_持仓收口.md
```

**依赖关系**：四步必须按顺序执行，每步依赖上一步的输出文件。

**推荐执行窗口（A股用户）**：
- A股盘中：10:30 / 10:45 / 11:00 / 11:15
- 收盘后复盘：15:30 / 15:45 / 16:00 / 16:15

---

## 脚本依赖

所有脚本位于 `Eyes/scripts/`，零第三方依赖（纯标准库 + requests）。

| 脚本 | 用途 | 依赖 Key |
|:---|:---|:---|
| `fetch_rss.py` | RSS 多源新闻抓取 | 无（Level 0） |
| `fetch_price_yahoo.py` | Yahoo Finance 价格兜底 | 无（Level 0） |
| `fetch_price_api.py` | Finnhub 美股实时报价 | `FINNHUB_API_KEY` |
| `fetch_finnhub_news.py` | 个股英文新闻 | `FINNHUB_API_KEY` |
| `fetch_price_tushare.py` | A股日线数据 | `TUSHARE_TOKEN` |
| `fetch_price_router.py` | 三源价格自动分流 | 自动降级 |
| `fetch_market_api.py` | 结构化市场事件 | `YMOS_MARKET_API_KEY` |
| `price_scan_from_state.py` | 批量价格扫描（读状态机） | 依赖路由器 |

**当前数据级别**：Level 0（.env 未配置，全部走 Yahoo Finance 兜底）

---

## P 系列提示词位置

`Brain/references/` 下共 16 个 P 模块：

| 模块 | 文件 | 功能 |
|:---|:---|:---|
| P1 | `p1-genesis.md` | 个股建档 |
| P2 | `p2-phase-check.md` | 阶段判断 |
| P3 | `p3-event-impact.md` | 事件影响评估 |
| P4 | `p4-radar.md` | 个股雷达 |
| P5 | `p5-fomo-killer.md` | FOMO 审计 |
| P6 | `p6-profit-keeper.md` | 利润守门员 |
| P7 | `p7-portfolio-check.md` | 组合再平衡 |
| P8 | `p8-macro-filter.md` | 宏观过滤 |
| P9 | `p9-valuation.md` | 估值分析 |
| P10 | `p10-options.md` | 期权策略 |
| P11 | `p11-autopsy.md` | 复盘 |
| P12 | `p12-referee.md` | 纪律审查（最终关卡） |
| P13 | `p13-market-scanner.md` | 市场扫描 |
| P14 | `p14-sector-hunter.md` | 板块猎手 |
| P15 | `p15-insight.md` | 洞察生成 |
| P16 | `p16-earnings.md` | 财报分析 |

---

## 用户画像（快速参考）

- **市场**：A股为主（全部持仓均为 A股 ETF + 个股）
- **风格**：短线 PVP，持仓周期几天到几周
- **仓位约束**：总仓位 ≤ 50%，单标的 ≤ 20%，现金底仓 ≥ 50%
- **经验**：新手，基础知识较弱，倾向挂跌 2% 价格买入
- **当前风险等级**：中（伊朗战争导致 Chaos 状态）
- **活跃持仓**：8 个（含 6 个 ETF + 2 只个股）

---

## Agent 行为规则

1. **不得静默修改** `当前关注方向与投资偏好.md`，所有修改必须用户确认
2. **不替用户做交易决策**，所有策略建议经 P12 纪律审查后仅为建议
3. **写回状态机**时（建仓/清仓/关注变更），先展示 diff，用户确认后执行
4. **执行 SOP 时**，读取对应 SOP 文件，按步骤执行，不跳步
5. **运行脚本时**，先检查 `.env` 是否存在，不存在则告知用户当前为 Level 0 模式

---

## 每日建议输出模板

每日四步闭环完成后，Claude 主动输出以下建议摘要：

```
📊 今日 YMOS 日报 [日期]

【市场洞察】（一句话）
【投资雷达】对我的持仓有影响的信号：
【策略建议】今日建议行动：
【风险提示】需要关注的风险：
【明日待办】建议明日优先处理：
```

---

## 未配置项提醒

首次使用时，Claude 应提醒用户配置以下项目：

- [ ] 复制 `.env.example` 为 `.env`，填入 API Key（提升数据质量）
- [ ] 配置 `TUSHARE_TOKEN`（A股用户必填，免费注册）
- [ ] 配置 `FINNHUB_API_KEY`（美股/Crypto 用户推荐，免费注册）
- [ ] 跑一次「收口一下」生成 `dashboard/` 目录和持仓备忘录视图
- [ ] 将自定义 RSS 源填入 `Eyes/scripts/rss_sources_custom.json`

---

*CLAUDE.md 版本：2026-04-08 · 自动生成*
