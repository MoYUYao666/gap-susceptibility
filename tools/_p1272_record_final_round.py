# -*- coding: utf-8 -*-
r"""Record the final pre-submission round for A1: cover letter, automation handover, Proposition 4, appendix.

    python tools/_p1272_record_final_round.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
WHICH = REPO / "哪篇是哪篇.md"
NOVDOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"

NOVSEC = """

---

## 第 8 步（2026-10-18 18:40）：投稿前收尾四项，A1 **52 页**

| 项 | 内容 |
|---|---|
| **揭示函** | companion 表述由"being handled separately"改为 **"under consideration at Neurocomputing (submitted October 2026)"**（Paper A 已于 2026-10-18 投出，状态 Submitted）。注意：包构建脚本 `_p1236` 内置模板会覆盖该文件，模板本身已同步修改 |
| **自动化交接文档** | `AUTOMATION_HANDOVER.md`：Paper A 改为"已投，状态 Submitted，稿号待补"；A1 改为"已改投 PAA（SCIE），包就绪待投"；新增 2026-10-18 18:40 状态块；每周检索 prompt 的 A1 段落同步更新 |
| **Proposition 4（一阶矩统计量均不充分）** | 把非充分性从 centroid gap 推广到任意只依赖两个经验均值的统计量 $F(\\bar x,\\bar t)$：文本侧平移移动均值、保持行序 ⇒ 除非 $F$ 不依赖 $\\bar t$，否则不可能是充分统计量；CG、归一化 gap、角 gap 及其单调变换都是实例 | 
| **附录化** | `tab:protocol`（监控规则）、`tab:morebench`（新基准+区间）、`tab:standard`（报告标准）与 Proposition 3 的证明移入附录；正文因此更短，表格与证明仍在同一 PDF 内 |

**编译**：52 页、**0 错误 / 0 未定义 / 0 Overfull**；包重建（Manuscript 52 页、latex_source 14 文件）；
审计 `a1_paa` **READY grade A：pass=61 fail=0 warn=0**。
"""

ENT = """> **🧷 2026-10-18 18:40 —— A1 投稿前收尾：揭示函更新、自动化文档刷新、Proposition 4、附录化（**52 页**，审计 READY/A）**
>
> 1. **揭示函**：companion 改为 **"under consideration at Neurocomputing (submitted October 2026)"**（Paper A 今天已投）；
>    `_p1236` 的内置模板同步修改（否则会被覆盖）。
> 2. **AUTOMATION_HANDOVER.md**：Paper A → 已投（Submitted，稿号待补）；A1 → PAA（SCIE）待投；每周检索 prompt 同步。
> 3. **Proposition 4**：非充分性推广到**任意一阶矩统计量** $F(\\bar x,\\bar t)$（含证明）。
> 4. **附录化**：`tab:protocol`、`tab:morebench`、`tab:standard` + Prop 3 证明移入附录，正文更紧凑。
>
> **A1 终态**：**52 页**、0/0/0；包 `SUBMISSION/A1_PatternAnalysisApplications/` 重建；审计 **READY grade A：pass=61 fail=0 warn=0**。
> 仍待投（Springer EM）。
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
    if "第 8 步" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 投稿前收尾" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")
    w = io.open(WHICH, encoding="utf-8").read()
    old = "5 基准复现** | 51 + 1 title page |"
    new = "5 基准复现 + 附录化** | 52 + 1 title page |"
    print(f"  which row: {w.count(old)}")
    if w.count(old) == 1:
        io.open(WHICH, "w", encoding="utf-8", newline="").write(w.replace(old, new, 1))
    m = io.open(MAP, encoding="utf-8").read()
    row = ("85. 🧷 **A1 投稿前收尾（2026-10-18 18:40）** —— 揭示函 companion 改为 **under consideration at Neurocomputing**"
           "（Paper A 已投；构建模板同步）；`AUTOMATION_HANDOVER.md` 状态刷新；新增 **Proposition 4（任意一阶矩统计量不充分）**；"
           "`tab:protocol`/`tab:morebench`/`tab:standard` 与 Prop 3 证明移入附录。A1 **52 页**、审计 **READY/A pass=61 fail=0 warn=0**。\n")
    if "A1 投稿前收尾" not in m:
        anchor = "84. 🧪 **A1 第 1–7 项"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
