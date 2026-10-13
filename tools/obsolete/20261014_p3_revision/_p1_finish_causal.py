# -*- coding: utf-8 -*-
"""Finish removing the causal-evidence framing, and record the noise finding."""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    ("paper/sections/discussion.tex",
     "converging evidence from retrieval performance, zero-shot preservation, gap dynamics, and causal analysis.",
     "converging evidence from retrieval performance, zero-shot preservation, gap dynamics, and the strict control of Section~\\ref{sec:strictcontrol}."),
    ("paper/sections/supplementary.tex",
     "\\multicolumn{5}{c}{\\textbf{XII. Causal Evidence --- 3 experiments}} \\\\",
     "\\multicolumn{5}{c}{\\textbf{XII. Mechanism Probes --- 3 experiments}} \\\\"),
    ("paper/sections/supplementary.tex",
     "Superscript letters in Causal Evidence and Zero-Shot rows refer to footnotes at the end of the table.",
     "Superscript letters in Mechanism Probes and Zero-Shot rows refer to footnotes at the end of the table."),
]
fails = []
for rel, old, new in EDITS:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    s = io.open(p, encoding="utf-8").read()
    n = s.count(old)
    if n != 1:
        fails.append("%s: found %d" % (rel, n))
        print("FAIL %s (%d)" % (rel, n))
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new, 1))
    print("ok   %s" % rel)

# ---- log -------------------------------------------------------------------
LOG = os.path.join(ROOT, "docs", "P1_REMEDIATION_LOG.md")
ADD = """
## 十二、轻量实验：参数噪声主张不可复现（2026-09-20）

操作者要求"跑轻量的"，于是只跑了 `noise_sensitivity.py` 的 **[A] 噪声敏感性**（纯前向，2000 样本、batch 64，3 seeds 共约 4 分钟；**[B] 有效秩跟踪会重训并覆盖已归档的 `effective_rank_tracking.json`，故刻意未跑**）。脚本 `tools/p1_noise_seeds.py`，原始单次抽样先存档为 `outputs/noise_sensitivity_pre_seed.json`，逐种子原始值在 `outputs/noise_seeds/`，聚合在 `outputs/noise_sensitivity_seeds.json`。

| σ=0.1 | 视觉编码器注噪 | 文本编码器注噪 | 比值 |
|---|---|---|---|
| 原始单次抽样（论文所引） | R@1 0.705→0.640，降 **9.22%** | 0.705→0.680，降 **3.55%** | **2.6×** ← 论文该数字的来源 |
| **3 seeds（新跑）** | **2.15% ± 4.41** | **−0.01% ± 1.93** | 分母≈0，**无意义** |

- 视觉优于文本的种子数：**2/3**（σ=0.1）；σ=0.01 时 3/3，σ=0.03 时 0/3 —— 排序**不稳定**。
- 另有一个设计弱点：每次运行都重建验证子集（baseline R@1 在 0.685–0.695 间波动），本身放大方差。

**结论：删去"视觉噪声危害 2.6× 于文本"这一主张。** 改动：图 9 图注改为如实描述"这是单次评估 + 三种子复跑不稳定、故不据此下结论"；supplementary 脚注 a 同步；`experiments.tex:6` 的 "causal evidence" → "mechanism probes"；catalog 的 "XII. Causal Evidence" → "XII. Mechanism Probes" 及其脚注引用；`discussion.tex:44` 的 "causal analysis" → "the strict control of Section 5"。

**这条与 §八的机理降级同向**：论文现在的证据基础是"经验规律 + 严格对照"，而不是"因果证据"。图 9 的面板 (B)(C) 来自早期训练跑（未重训），其有效秩结论已在 §八按同一逻辑处理。
"""
s = io.open(LOG, encoding="utf-8").read()
if "## 十二、轻量实验" in s:
    print("log already has section 十二")
else:
    io.open(LOG, "w", encoding="utf-8", newline="").write(s.rstrip() + ADD)
    print("log appended")

# ---- HANDOFF ---------------------------------------------------------------
H = os.path.join(ROOT, "HANDOFF.md")
HO = "① **Adapter 行**"
HN = ('① **参数噪声主张已删**（轻量实验核实，见日志 §十二）：原“视觉噪声危害 2.6× 于文本”来自**单次不可复现抽样**'
      '（9.22% vs 3.55%）；3 seeds 复跑为 2.15%±4.41 vs −0.01%±1.93、且仅 2/3 种子视觉更差 → 图 9 图注、'
      'supplementary 脚注、`experiments.tex:6`、catalog 小节名、`discussion.tex:44` 全部改为不依赖该实验；'
      '原始单次值存档 `outputs/noise_sensitivity_pre_seed.json`，聚合 `outputs/noise_sensitivity_seeds.json`。\n'
      '>   ① **Adapter 行**')
h = io.open(H, encoding="utf-8").read()
if HO in h and "参数噪声主张已删" not in h:
    io.open(H, "w", encoding="utf-8", newline="").write(h.replace(HO, HN, 1))
    print("handoff updated")
else:
    print("handoff anchor not found or already updated")
if fails:
    sys.exit(1)
