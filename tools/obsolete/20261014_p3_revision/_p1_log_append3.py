# -*- coding: utf-8 -*-
"""Append the round-3 entry to docs/P1_REMEDIATION_LOG.md (idempotent)."""
import io
import os

P = os.path.join(r"D:\Realdesktop\Wan\Important\New", "docs", "P1_REMEDIATION_LOG.md")
MARK = "## 七、第三轮补充"
ADD = """
## 七、第三轮补充（补丁 A8/A9 + highlights + 图-产物核验）

- **补丁 A8**：supplementary 脚注 c 的秩定义（"threshold 0.99 explained variance"）与跟踪代码/图 8 用的定义不同（第三套定义）→ 改为与代码一致的 `exp(-Σ p_i log p_i)`，并写明"legacy 跑会降低它、严格对照完全不变"。
- **补丁 A9**：Connector-S 改引 **IJCAI 2025 正式版**（DOI 10.24963/ijcai.2025/1202，已核）；GTMA 加"IEEE Xplore doc 11463397"注（期刊名未核，**不猜**）；`related_work.tex:20` 与 `visual_fragility.tex:12` 的 `zhu2026fi`（LLM 脆弱性论文）改为显式说明"该结论出自 LLM 场景，我们推测可迁移到视觉编码器"；`visual_fragility.tex:8` 的 "proved" → "attributes"。
- **`paper/highlights.tex` 重写**：原 5 条**全部**含过期主张（first / 116 / r=-0.827 / partial -0.807 / causal evidence）。新 5 条渲染长度 78–85 字符（含项目符号），符合 Elsevier ≤85 限制；已编译 `highlights.pdf`。
- **图-产物核验**：`pdfimages -list` 与源 PNG 尺寸逐一比对 → fig1/fig2/fig3/fig5/fig7 **五张重画图全部确实嵌入**重编译后的 PDF（2051×1151 / 2370×1019 / 2844×1348 / 1841×941 / 1691×1027）。
- **编译状态**：40 页，0 error、0 undefined citation；唯一待办 = Patch B 的 `sec:strictcontrol` 标签。
- **新工具**：`tools/p1_strict_control_summary.py`（严格对照汇总：逐配置 CGΔ/R@1/可训参数/视觉非零张量数/逐层秩变化 + 与 legacy 对比 + LaTeX 表行），幂等，实验结束直接重跑即可。
"""

s = io.open(P, encoding="utf-8").read()
if MARK in s:
    print("already present, skipping")
else:
    io.open(P, "w", encoding="utf-8", newline="").write(s.rstrip() + ADD)
    print("appended")
