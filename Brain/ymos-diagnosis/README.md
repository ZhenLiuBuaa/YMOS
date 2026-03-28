# ymos-diagnosis — 投资策略诊断模块

> **Agent 入口**：读取 `SKILL.md` 即可启动诊断。SKILL.md 是完全自包含的。

---

## 定位

ymos-diagnosis 是 YMOS 的**诊断模块**——不做策略制定，不做交易执行，只做一件事：**审视投资者的投资逻辑和系统健康度**。

它和 Brain 中其他模块的关系：

```
Brain/references/（P1-P16）→ 制定策略、执行分析、纪律审查
Brain/ymos-diagnosis/      → 审视整体投资逻辑、诊断系统漏洞
```

**适用场景**：
- 用户不确定自己的投资策略是否合理 → 先用诊断梳理，再进入 YMOS 主流程
- 用户想定期审视自己的投资逻辑 → 体检模式，7 项检验
- 用户带着具体投资问题 → 问诊模式，5 层消解漏斗

---

## 文件结构

```
Brain/ymos-diagnosis/
├── SKILL.md                                # 诊断入口（Agent 读这个文件）
├── README.md                               # 本文件（模块说明）
└── knowledge/
    ├── investment_axioms_and_framework.md   # 投资公理与诊断框架（深度参考）
    └── diagnosis_case_library.md           # 按失败模式分类的案例库（15 个案例）
```

---

## 两种模式

| 模式 | 触发 | 过程 | 产出 |
|:---|:---|:---|:---|
| **问诊** | 用户带着具体投资问题 | 5 层消解漏斗（语言陷阱→假设错误→逻辑错误→事实前提→信息充分） | 问题消解或正面解答 |
| **体检** | 用户想全面审视 | 7 项检验逐项进行 | 诊断报告 |

---

## Agent 使用指南

1. 读取 `Brain/ymos-diagnosis/SKILL.md`
2. 按 SKILL.md 中的 Phase 0 引导用户选择模式
3. 如需更深入的参考，读取 `knowledge/` 目录下的文件补充上下文
4. 诊断过程中如发现用户需要系统化策略，可建议使用 YMOS 的 P 系列模块（如 P2 阶段判断、P5 FOMO 审计等）

---

## 独立项目

ymos-diagnosis 同时作为独立开源项目发布：[github.com/Evan-XYZ/ymos-diagnosis](https://github.com/Evan-XYZ/ymos-diagnosis)

不需要安装 YMOS 也能单独使用。
