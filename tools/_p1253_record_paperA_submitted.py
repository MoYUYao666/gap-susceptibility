# -*- coding: utf-8 -*-
r"""Record that Paper A has been submitted to Neurocomputing (status seen on the submission portal, 2026-10-18).

Evidence: submit.elsevier.com/NEUCOM/submissions, "Your Neurocomputing submissions (3)" row 1:
  "Adaptation Site and the Modality Gap ..." | Neurocomputing | Submitted October 18, 2026 | Status: Submitted.
The manuscript number is not displayed on that page yet, so it is recorded as 待补 (to be taken from the
confirmation e-mail or the Editorial Manager author menu).

    python tools/_p1253_record_paperA_submitted.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
WHICH = REPO / "哪篇是哪篇.md"

ENT = """> **📮 2026-10-18 17:40 —— Paper A 已投出 Neurocomputing（状态 `Submitted`，稿号待补）**
>
> 证据：`submit.elsevier.com/NEUCOM/submissions` → "Your Neurocomputing submissions (3)" 第 1 行：
> *Adaptation Site and the Modality Gap: Empirical Regularities and a Gradient-Flow Theory for PEFT of Contrastive
> Dual-Encoders* ｜ Neurocomputing ｜ **Submitted October 18, 2026** ｜ 状态 **Submitted**。
>
> | 项 | 值 |
> |---|---|
> | 稿件 | Paper A（`paper合/`，P1+P2 合并）|
> | 期刊 | Neurocomputing（SCIE）|
> | 提交日期 | **2026-10-18** |
> | 状态 | **Submitted**（已进入编辑部流程）|
> | 稿号 | **待补** —— 该页面暂不显示，需从确认邮件或 EM 作者主菜单取 |
> | 投递文件 | Manuscript（70 页）· Abstract（1 页）· Highlights（5 条）· Cover Letter（3 页）· LaTeX source（45 文件）；包在 `SUBMISSION/PaperA_Neurocomputing/` |
>
> 同一列表另有两条：① 早前 A1 的 Neurocomputing 投稿 `NEUCOM-D-26-20952` 显示 **Submission Transferred**（已转 Neural Networks 并被桌面拒）；② 一条 **Incomplete submission** 残留草稿，建议在门户里删除。
>
> **待办**：取稿号后回填本文件与 `哪篇是哪篇.md`；此后每周文献检索的状态文本按"Paper A 在审"更新。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "Paper A 已投出 Neurocomputing（状态" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")

    w = io.open(WHICH, encoding="utf-8").read()
    old = ("**Neurocomputing**（elsarticle）｜**待投**（包就绪：`SUBMISSION/PaperA_Neurocomputing/`；**稿号待补**）")
    new = ("**Neurocomputing**（elsarticle）｜**2026-10-18 已投出，状态 Submitted**（包 `SUBMISSION/PaperA_Neurocomputing/`；"
           "**稿号待补**）")
    n = w.count(old)
    print(f"  which-table Paper A row: {n}")
    if n == 1:
        w = w.replace(old, new, 1)
    old2 = "若操作者已实际投出，请把稿号补到本行与 `HANDOFF.md`。"
    new2 = "**2026-10-18 17:40 更新：已确认投出（门户状态 Submitted），稿号仍需从确认邮件补录。**"
    if old2 in w:
        w = w.replace(old2, new2, 1)
    io.open(WHICH, "w", encoding="utf-8", newline="").write(w)

    m = io.open(MAP, encoding="utf-8").read()
    row = ("82. 📮 **Paper A 已投出 Neurocomputing（2026-10-18 17:40）** —— 门户状态 **Submitted**（提交日期 Oct 18, 2026）；"
           "投递：Manuscript 70 页 + Abstract 1 页 + Highlights 5 条 + Cover Letter 3 页 + 源码 45 文件；"
           "**稿号待补**（确认邮件/EM 取）。同列表另有 A1 旧投（Submission Transferred）与一条 Incomplete 草稿待清理。\n")
    if "Paper A 已投出 Neurocomputing" not in m:
        anchor = "81. 📋 **Paper A 可复制摘要"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
