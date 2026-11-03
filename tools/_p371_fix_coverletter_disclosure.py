# -*- coding: utf-8 -*-
r"""修正 `paper合` 封面信的 3 处过期披露 + 补入 A1（2026-10-12）。

## 触发

A1 已于 2026-10-12 投出 **Neural Networks**（`NEUNET-D-26-09426`）。
核查 `paper合/cover_letter.tex:73-92` 的披露清单，发现 **3 处与事实不符**：

| # | 现文 | 事实 |
|---|---|---|
| 1 | *"A predecessor manuscript **under review at** Pattern Recognition …"*（L77-82） | P1 **已被拒**（操作者 2026-10-12 确认）。且本稿"supersedes it"的说法在 P1 被拒后**需重述** |
| 2 | *"A critical review under review at PRL …, now at manuscript number **`PRLETTERS-D-26-02378`**"*（L83-88） | **稿号张冠李戴**：`-02378` = **P3**（PRL）；**综述**的稿号是 **`PRLETTERS-D-26-02402`** |
| 3 | **A1 完全未披露** | A1 是最相关的一篇（同做 PEFT 下的 modality gap），**必须披露**其**已投 Neural Networks `NEUNET-D-26-09426`** |

**注**：`paper合` **尚未投稿**，所以这些是"投出前必须修"的问题（现已修）。

    python tools\_p371_fix_coverletter_disclosure.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILES = ["paper合/cover_letter.tex", "paper合/cover_letter_nc.tex"]

OLD_HEAD = (
    "\\noindent\\textbf{Related manuscripts by the same author, disclosed.}\n"
    "Three related items by the same author are in the editorial process or in preparation, and I disclose\n"
    "them so that the editor can judge overlap directly rather than infer it:")
NEW_HEAD = (
    "\\noindent\\textbf{Related manuscripts by the same author, disclosed.}\n"
    "Four related items by the same author are under review or were previously submitted, and I disclose\n"
    "them so that the editor can judge overlap directly rather than infer it:")

OLD_ITEM1 = (
    "\\item \\textbf{A predecessor manuscript} under review at \\emph{Pattern Recognition} (``Protect, Don't\n"
    "Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models''). That manuscript covers the\n"
    "empirical characterisation only. The present submission \\emph{supersedes} it: it adds the dynamical\n"
    "theory, the cross-architecture validation and the strict-freezing controls, and it is the fuller\n"
    "treatment of the same programme of work. The predecessor's empirical material appears here in merged\n"
    "and extended form, and readers should treat this manuscript as the current version.")
NEW_ITEM1 = (
    "\\item \\textbf{A predecessor manuscript} that was submitted to \\emph{Pattern Recognition}\n"
    "(``Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models'',\n"
    "\\texttt{PR-D-26-10149}) and was \\emph{rejected without a revision invitation}. That manuscript\n"
    "covered the empirical characterisation only. The present submission \\emph{supersedes} it: it adds\n"
    "the dynamical theory, the cross-architecture validation and the strict-freezing controls, and it is\n"
    "the fuller treatment of the same programme of work. The predecessor's empirical material appears\n"
    "here in merged, extended and corrected form, and readers should treat this manuscript as the current\n"
    "version of that work.")

OLD_ITEM2 = (
    "\\item \\textbf{A critical review} under review at \\emph{Pattern Recognition Letters} (``Allocation, not\n"
    "selection: comparability in parameter-efficient multimodal adaptation''), now at manuscript number\n"
    "\\texttt{PRLETTERS-D-26-02378}.")
NEW_ITEM2 = (
    "\\item \\textbf{A critical review} under review at \\emph{Pattern Recognition Letters} (``Allocation, not\n"
    "selection: comparability in parameter-efficient multimodal adaptation''), manuscript number\n"
    "\\texttt{PRLETTERS-D-26-02402}.")

OLD_ITEM3 = (
    "\\item A manuscript on an unrelated topic (underwater acoustics) under review at \\emph{IEEE Journal of\n"
    "Oceanic Engineering} (\\texttt{26-0663}).")
NEW_ITEM3 = (
    "\\item \\textbf{A companion study on cross-modal alignment diagnostics} under review at \\emph{Neural\n"
    "Networks} (``Order Preservation Tracks Zero-Shot Accuracy under Classification Fine-Tuning: Why the\n"
    "Modality Gap Is Not a Universal Health Metric'', \\texttt{NEUNET-D-26-09426}). It shares the subject\n"
    "matter of modality-gap behaviour under fine-tuning but asks a different question --- which of the two\n"
    "quantities, the gap or the rank-order statistic $\\tau$, tracks zero-shot accuracy --- and reports no\n"
    "overlap of results with the present manuscript.\n"
    "\\item A manuscript on an unrelated topic (underwater acoustics) under review at \\emph{IEEE Journal of\n"
    "Oceanic Engineering} (\\texttt{26-0663}).")

PAIRS = [("head", OLD_HEAD, NEW_HEAD), ("item1", OLD_ITEM1, NEW_ITEM1),
         ("item2", OLD_ITEM2, NEW_ITEM2), ("item3", OLD_ITEM3, NEW_ITEM3)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for rel in FILES:
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n_file = 0
        for tag, old, new in PAIRS:
            c = t.count(old)
            print(f"  {p.name:<24} {tag:<6} 命中 {c}")
            if c:
                t = t.replace(old, new)
                n_file += c
        if n_file and a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p371")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t)
            total += n_file
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    ok = True
    for rel in FILES:
        p = REPO / rel
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        checks = {
            f"{p.name}: 含 NEUNET-D-26-09426": "NEUNET-D-26-09426" in t,
            f"{p.name}: 综述稿号已改为 -02402": "PRLETTERS-D-26-02402" in t,
            f"{p.name}: 不再说 '-02378' 是综述": "multimodal adaptation''), now at manuscript number\n\\texttt{PRLETTERS-D-26-02378}" not in t,
            f"{p.name}: P1 已标为 rejected": "rejected without a revision invitation" in t,
            f"{p.name}: 四项计数已更新": "Four related items" in t,
        }
        for k, v in checks.items():
            print(f"  {'✅' if v else '🔴'} {k}")
            ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
