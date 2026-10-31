# -*- coding: utf-8 -*-
"""Append the Patch-B / strict-control entry to docs/P1_REMEDIATION_LOG.md (idempotent)."""
import io
import os

P = os.path.join(r"D:\Realdesktop\Wan\Important\New", "docs", "P1_REMEDIATION_LOG.md")
MARK = "## 八、Patch B"
ADD = """
## 八、Patch B：严格冻结对照与机理重写（2026-09-20）

### 结果（5 seeds，全部完成）

| | 严格冻结（可训 **196,608** = 0.13%） | 旧"text-only"（可训 145,170,177） |
|---|---|---|
| CGΔ | **−0.0465 ± 0.0027** | −0.0458 ± 0.0021（5-seed） |
| R@1 | **0.6238 ± 0.0049** | 0.6210 |
| 视觉侧改动 | **0/199 张量**；逐层有效秩 Δ = **+0.0000** | 全模型 96% 参数在训 |
| 文本侧秩变化 | +0.4612 | — |

**结论**：用 0.13% 的参数、视觉编码器可证明零更新，效果与旧跑几乎一致 → 历史跑多训的 1.45 亿参数对本效应**无贡献**；"protect the visual encoder" 由推断变为实证。

### ⚠️ 未完成的 joint 行（如实记录，勿再重跑）

`both` / `vision_only` 的严格跑**慢约 10 倍**（实测 312–326 s/epoch，text-only 仅 ~30 s/epoch）：视觉塔一旦含可训参数即必须做完整反向传播；text-only 严格跑则整棵视觉塔的反向被跳过（这正是它 6 分钟/跑的原因）。按此速度 10 个跑需 8+ 小时，**本轮放弃**，并在新章节中明写"对照覆盖承载机理主张的 text-only 配置；joint 行留作未来工作，而不是以低种子数硬报"。

### 本轮改动的文件

- 新增 `paper/sections/strict_control.tex`（`\\label{sec:strictcontrol}`，Table 8），由 `paper/main_nn.tex` 在 visual_fragility 之前 `\\input`；
- 机理表述重写：摘要（"direct causal evidence" → 严格对照）、`introduction.tex` 贡献 7 与第 8 行、`conclusion.tex` 贡献 3 与 5、`visual_fragility.tex` 两处；
- 生成器 `tools/_p1_patch_b.py`（运行时读 `outputs/analysis/strict_control_summary.json` 填数，缺数据则断言失败且**不写盘**）。

### 我自己犯并修掉的两个错（教训）

1. `\\begin{tabular}{lcccc}` 声明 5 列而行内 6 个字段 → LaTeX "Extra alignment tab"（已改 `lccccc`，并把生成器同步）。
2. 摘要替换用了**错误的换行位置**导致 0 命中；因为 `_p1_patch_b2.py` 是"全部成功才写盘"，文件**没被改坏**——这种"先断言、后写盘"的写法本次避免了一次半成品编辑。**今后所有补丁脚本都按此模式写。**
"""

s = io.open(P, encoding="utf-8").read()
if MARK in s:
    print("already present, skipping")
else:
    io.open(P, "w", encoding="utf-8", newline="").write(s.rstrip() + ADD)
    print("appended")
