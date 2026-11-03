# -*- coding: utf-8 -*-
r"""A1 写作修正 6 项（全部有实验依据，2026-10-12）。

| # | 修正 | 依据 |
|---|---|---|
| 1 | 标题去掉 "Zero-Overhead Monitor" → "Tracks Zero-Shot Accuracy" | **E-B**：τ 达峰与"固定停 ep1"逐位相同（59.44/+0.05/8-of-10） |
| 2 | `highlights.tex` r=1.000 加限定 | `_p204`：`tau_pred_exact` ≡ `tau`（12/12 逐位相同）= 同义反复 |
| 3 | "four decimals" → "three decimals" | `_p204`：最大残差 0.0019 |
| 4 | `main.tex:308` "zero-overhead monitor" → "erosion signal" + 决策局限 | **E-B** |
| 5 | 补写组内证据（n=30）+ "决策价值未证明" | **E-A**：组内 Fisher +0.840；单 seed +0.945 |
| 6 | 修 `abstract.tex` / `main_zh.tex` / `docs/A1_VENUE_DECISION.md` | `_p203` |

    python tools\_p222_a1_writing_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"

TITLE_OLD = (r"\title{Order Preservation as a Zero-Overhead Monitor for Classification "
             r"Fine-Tuning:  Why the Modality Gap Is Not a Universal Health Metric}")
TITLE_NEW = (r"\title{Order Preservation Tracks Zero-Shot Accuracy under Classification "
             r"Fine-Tuning: Why the Modality Gap Is Not a Universal Health Metric}")

HL_OLD = (r"\item First-order bias-field theory matches measurements with r = 1.000")
HL_NEW = (r"\item The bias-field closed form is an identity: it reproduces the measured "
          r"shift to three decimals as a self-consistency check, not as independent validation")

FOUR_OLD = "matches measurement to four decimals"
FOUR_NEW = "matches measurement to three decimals"

# L308 的"zero-overhead monitor"句 → 改为只承诺"跟踪 + 可零成本算出"，并写入决策局限
MON_OLD = ("Two practical points follow: $\\tau$ is an earlier and more sensitive indicator of "
           "order erosion than top-1 itself, and it is computable from the top-$k$ class sets "
           "already available during validation---making it a zero-overhead training-time "
           "monitor for classification-oriented fine-tuning.")
MON_NEW = ("Two practical points follow. First, $\\tau$ is computable from the top-$k$ class "
           "sets a validation pass already produces, so it costs no additional forward pass. "
           "Second, within a single training trajectory it tracks zero-shot accuracy closely: "
           "over the ten runs we evaluated epoch by epoch, $\\tau$ rises and falls with top-1 "
           "at a mean Pearson correlation of $0.90$ ($10/10$ runs positive; "
           "Section~\\ref{sec:epoch_sweep}). What this does \\emph{not} license is a stopping "
           "rule. Evaluating four stopping criteria on the same ten runs, halting where $\\tau$ "
           "peaks selects checkpoints whose mean top-1 is $59.44\\%$---identical to the "
           "$59.44\\%$ obtained by ignoring every signal and halting after the first epoch, and "
           "below the $59.49\\%$ of an oracle that sees the ImageNet labels. $\\tau$ is "
           "therefore a \\emph{diagnostic} of order erosion rather than a decision rule, and we "
           "report it as such.")

# "Only the second governs" 与 Table 1 冲突 → 改为与正文一致的"必要不充分"
GOVERNS_OLD = ("Only the second governs zero-shot accuracy, and it is free to monitor: "
              "the Kendall order-preservation coefficient $\\tau$ follows from the top-$k$ "
              "class sets a validation pass already produces.")
GOVERNS_NEW = ("Only the second tracks zero-shot accuracy, and it is free to compute: "
              "the Kendall order-preservation coefficient $\\tau$ co-moves with it inside a "
              "single training trajectory (mean Pearson $0.90$ over ten runs, $10/10$ positive) "
              "and follows from the top-$k$ class sets a validation pass already produces.")


def patch(path: Path, pairs, required: bool = True) -> int:
    t = io.open(path, encoding="utf-8", errors="replace").read()
    n = 0
    for i, (old, new) in enumerate(pairs):
        c = t.count(old)
        tag = f"{path.name}#{i + 1}"
        if c == 0:
            print(f"  {'🔴' if required else '⚠️ '} {tag}: 未命中")
            if required:
                return -1
            continue
        print(f"  ✅ {tag}: 命中 {c} 处")
        t = t.replace(old, new)
        n += c
    bak = path.with_suffix(path.suffix + ".bak_p222")
    if not bak.exists():
        shutil.copy2(path, bak)
    io.open(path, "w", encoding="utf-8", newline="").write(t)
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0

    main_tex = A1 / "main.tex"
    print("=== 1/2/3/4/5: main.tex ===")
    r = patch(main_tex, [
        (TITLE_OLD, TITLE_NEW),
        (FOUR_OLD, FOUR_NEW),
        (MON_OLD, MON_NEW),
        (GOVERNS_OLD, GOVERNS_NEW),
    ])
    if r < 0:
        print("  ❌ main.tex 有未命中项，未写入")
        return 1

    print("=== 1: highlights.tex（r=1.000 加限定）===")
    patch(A1 / "highlights.tex", [(HL_OLD, HL_NEW)])

    print("=== 5: 新小节（组内 n=30 证据）===")
    t = io.open(main_tex, encoding="utf-8", errors="replace").read()
    anchor = r"\section{Discussion}"
    if "sec:epoch_sweep" not in t:
        sec = (
            r"\subsection{Within-dataset evidence: ten runs evaluated epoch by epoch}"
            "\n"
            r"\label{sec:epoch_sweep}" "\n\n"
            r"Every confusion above mixes runs drawn from different datasets. To test the "
            r"relation where it is actually used---inside one training trajectory---we "
            r"evaluated the archived per-epoch checkpoints of ten runs (four datasets; "
            r"$30$ checkpoints for each of three datasets and $10$ for the fourth; $100$ in "
            r"total, all already on disk, no retraining). Within each dataset the Kendall "
            r"coefficient tracks zero-shot $50{,}000$-image top-1 at Spearman $+0.670$ (MS-COCO, "
            r"$t=4.8$), $+0.970$ (DTD, $t=21.2$), $+0.915$ (Flickr30k) and $+0.397$ "
            r"(Food-101, $t=2.3$)---positive in all four, Fisher mean $+0.840$. The cleanest "
            r"contrast uses a single run: across $\\mathrm{epoch}\\ 1\\to 10$ of one MS-COCO "
            r"trajectory, $\\tau_5$ falls $0.688\\to0.575$ while top-1 falls $60.14\\%\\to58.14\\%$; "
            r"the same monotone co-movement appears in all ten runs (mean Pearson $0.90$, "
            r"$10/10$ positive). "
            r"\emph{The decision value of the signal is a separate question, and on this "
            r"evidence it is negative.} We compared four stopping criteria on the same ten "
            r"runs. Halting where $\\tau$ peaks gives a mean top-1 of $59.44\\%$; halting after "
            r"the first epoch without consulting any signal gives $59.44\\%$; the oracle that "
            r"reads the ImageNet labels gives $59.49\\%$. Training to epoch $10$ gives "
            r"$57.14\\%$. $\\tau$'s peak therefore identifies the same stopping point as a "
            r"constant rule, and $\\tau$ does not flag the first decline earlier than top-1 "
            r"does (it does so in $2$ of the ten runs). We report this because it bounds the "
            r"claim: $\\tau$ is a diagnostic that co-moves with classification health, not a "
            r"monitor that improves a training decision."
            "\n\n")
        t = t.replace(anchor, sec + anchor, 1)
        io.open(main_tex, "w", encoding="utf-8", newline="").write(t)
        print(f"  ✅ 已插入 sec:epoch_sweep（{len(sec)} 字符）")
    else:
        print("  ⚠️ sec:epoch_sweep 已存在，跳过")

    print("=== 6: abstract.tex（半成品：新标题+旧摘要）===")
    ab = A1 / "abstract.tex"
    at = io.open(ab, encoding="utf-8", errors="replace").read()
    # 用 main.tex 的摘要替换 abstract.tex 的摘要体
    mt = io.open(main_tex, encoding="utf-8", errors="replace").read()
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", mt, re.S)
    if m:
        new_body = m.group(1).strip()
        at2 = re.sub(r"\\begin\{abstract\}.*?\\end\{abstract\}",
                     "\\\\begin{abstract}\n" + new_body + "\n\\\\end{abstract}",
                     at, flags=re.S)
        # 同步标题
        mt_title = re.search(r"\\title\{(.*?)\}", mt, re.S).group(1)
        at2 = re.sub(r"\\title\{.*?\}", "\\\\title{" + mt_title + "}", at2,
                     count=1, flags=re.S)
        bak = ab.with_suffix(".tex.bak_p222")
        if not bak.exists():
            shutil.copy2(ab, bak)
        io.open(ab, "w", encoding="utf-8", newline="").write(at2)
        print("  ✅ abstract.tex 摘要体与标题已同步 main.tex")
    else:
        print("  🔴 main.tex 里找不到 abstract")

    print("=== 6: docs/A1_VENUE_DECISION.md（过期状态）===")
    vd = REPO / "docs" / "A1_VENUE_DECISION.md"
    if vd.exists():
        vt = io.open(vd, encoding="utf-8", errors="replace").read()
        stamp = ("\n> **⚠️ 2026-10-12 更正**：本节状态**已过期**。"
                 "A1 已于 **2026-10-10 被 Neurocomputing 拒稿**（`NEUCOM-D-26-20952`，"
                 "编辑初筛，`significance level` 不足，**无审稿意见**），"
                 "并收到 ATS 转投邀请（截止 `Nov 08 2026 11:59PM`）。"
                 "当前目标刊见 `paper_a1/main.tex` 的 `\\journal{}`。\n")
        if "2026-10-12 更正" not in vt:
            io.open(vd, "w", encoding="utf-8", newline="").write(vt + stamp)
            print("  ✅ 已加过期更正标注")
        else:
            print("  ⚠️ 已有更正标注")

    print()
    print("=== 核对 ===")
    mt2 = io.open(main_tex, encoding="utf-8", errors="replace").read()
    checks = [
        ("标题已改", "Zero-Overhead Monitor" not in mt2 and "Tracks Zero-Shot Accuracy" in mt2),
        ("four decimals 已改", "four decimals" not in mt2),
        ("zero-overhead monitor 已改", "zero-overhead training-time monitor" not in mt2),
        ("sec:epoch_sweep 已插入", "sec:epoch_sweep" in mt2),
        ("组内证据已写入", "+0.840" in mt2 and "59.44" in mt2),
    ]
    hl2 = io.open(A1 / "highlights.tex", encoding="utf-8", errors="replace").read()
    checks.append(("highlights 已加限定", "self-consistency check" in hl2))
    ab2 = io.open(ab, encoding="utf-8", errors="replace").read()
    checks.append(("abstract.tex 已同步", "Tracks Zero-Shot Accuracy" in ab2))
    ok = True
    for name, v in checks:
        print(f"  {'✅' if v else '🔴'} {name}")
        ok = ok and v
    print(f"\n  {'✅ 6 项全部完成' if ok else '🔴 有未完成项'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
