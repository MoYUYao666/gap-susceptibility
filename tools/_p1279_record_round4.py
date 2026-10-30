# -*- coding: utf-8 -*-
r"""Record the last improvements: retrieval evidence (D), k recommendation (C), monitoring intervals (E), graphical
abstract (F).

    python tools/_p1279_record_round4.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
NOVDOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"

NOVSEC = """

---

## 第 9 步（2026-10-18 19:05）：剩余提升项 C/D/E/F 全部落地

| 项 | 结果 | 归档 |
|---|---|---|
| **C τ 的 k 选择** | k=10 与 k=5 对十个模板的排序几乎一致（Spearman **≥0.95**，五骨干），且 k=10 系统性低 **0.040** ⇒ 更便宜的 **k=5 是默认** | `a1_tau_k.json` |
| **D retrieval 侧证据** | 536 图–字幕对（本地 marine_captions，冻结 CLIP）：**ΔCG=0.016** 的两配置（λ=0.5 平移 vs α=0.5 收缩）**R@1 差 61.8 点**（8.96% vs 70.71%）⇒ 分离不限于分类。但 τ 在 retrieval 上**不跟踪 R@1**（r=−0.17，CG 为 −0.23）⇒ 序统计量也有任务范围，必须按目标任务重新验证（已写入正文并如实报告为负结果）| `a1_retrieval_evidence.json` |
| **E 监控不确定性** | 对 10 条轨迹做 bootstrap：τ-max regret **0.05 [0.00, 0.14]**、CUSUM **0.14 [0.00, 0.34]**、训到末轮 **2.35 [1.65, 3.12]**、τ-max 相对末轮优势 **2.30 [1.56, 3.09]** | `a1_monitor_uncertainty.json` |
| **F graphical abstract** | 四面板整页图（匹配 gap / prompt 模板 / 阈值迁移热图 / 监控 regret）：`paper_a1/figures/graphical_abstract.{pdf,png}`，并作为可选上传项 `Graphical Abstract.pdf` 进入 PAA 包 | `paper_a1/figures/`、`SUBMISSION/A1_PatternAnalysisApplications/` |

**A1 终态**：**52 页**（正文 ~47 + 附录）、0 错误 / 0 未定义 / 0 Overfull；PAA 包 6 个文件
（Manuscript 52 页、Title Page、Cover Letter、**Graphical Abstract**、latex_source.zip 14 文件、README）；
审计 `a1_paa` **READY grade A：pass=61 fail=0 warn=0**。
"""

ENT = """> **🎨 2026-10-18 19:05 —— 剩余提升项 C/D/E/F 完成：retrieval 侧证据、k 推荐、监控区间、graphical abstract**
>
> - **D（最有价值）**：本地 536 图–字幕对，冻结 CLIP 上 **ΔCG=0.016 伴随 R@1 差 61.8 点**（8.96% vs 70.71%）
>   ⇒ gap 的失配不限于分类。但 **τ 在 retrieval 上也不跟踪 R@1**（r=−0.17，CG −0.23）⇒ 序统计量同样有任务范围，
>   正文如实写成负结果并划清推荐边界。
> - **C**：k=10 与 k=5 排序几乎一致（Spearman ≥0.95）且 k=10 系统性低 0.040 ⇒ 默认 **k=5**。
> - **E**：bootstrap over 10 轨迹：τ-max regret **0.05 [0, 0.14]**、末轮 **2.35 [1.65, 3.12]**、优势 **2.30 [1.56, 3.09]**。
> - **F**：四面板 graphical abstract（`paper_a1/figures/graphical_abstract.pdf`），已作为可选上传项进包。
>
> A1 **52 页**、0/0/0；PAA 包 6 文件；审计 **READY grade A：pass=61 fail=0 warn=0**。归档 `a1_retrieval_evidence.json`、
> `a1_tau_k.json`、`a1_monitor_uncertainty.json`；脚本 `_p1273`–`_p1279`。
>


"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    n = io.open(NOVDOC, encoding="utf-8").read()
    if "第 9 步" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "剩余提升项 C/D/E/F 完成" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("86. 🎨 **A1 剩余提升 C/D/E/F（2026-10-18 19:05）** —— retrieval 侧：ΔCG=0.016 时 **R@1 差 61.8 点**（536 图–字幕对），"
           "且 τ 在 retrieval 不跟踪 R@1（r=−0.17）→ 如实写成范围限制；τ 的 k：k=5 足够（Spearman ≥0.95）；"
           "监控 bootstrap 区间（τ-max regret 0.05 [0,0.14]、末轮 2.35 [1.65,3.12]）；四面板 graphical abstract 入包。"
           "A1 **52 页**、审计 **READY/A pass=61 fail=0 warn=0**。\n")
    if "A1 剩余提升 C/D/E/F" not in m:
        anchor = "85. 🧷 **A1 投稿前收尾"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
