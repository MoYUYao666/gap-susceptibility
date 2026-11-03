# -*- coding: utf-8 -*-
r"""补最后 3 处（2026-10-12）。

| # | 位置 | 改动 | 依据 |
|---|---|---|---|
| A | `main.tex` `sec:epoch_sweep` | 补**逐数据集组内相关**与 **n=30** 说明 | E-A：`tools/_p219` |
| B | `highlights.tex:13` | "governs zero-shot robustness" → "tracks" | E-A/E-B：论文自曝决策无效 |
| C | `docs/A1_VENUE_DECISION.md` | 加 10-10 拒稿更正标注 | 邮件事实 |

    python tools\_p228_last_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"

A_OLD = "\\label{sec:epoch_sweep}\n"
A_NEW = (r"\label{sec:epoch_sweep}"
         "\n\n"
         r"Every comparison above pools runs drawn from different datasets, which makes the "
         r"coefficient hard to interpret: $\tau$ differs between datasets for reasons that have "
         r"nothing to do with the relation we test. To measure it where it is used---inside one "
         r"training trajectory---we evaluated all $100$ archived per-epoch checkpoints of ten "
         r"runs (four datasets; $30$ checkpoints each for three of them and $10$ for the fourth; "
         r"no retraining, only evaluation). Within each dataset the Kendall coefficient tracks "
         r"zero-shot top-1 at Spearman $+0.670$ (MS-COCO, $t=4.8$), $+0.970$ (DTD, $t=21.2$), "
         r"$+0.915$ (Flickr30k) and $+0.397$ (Food-101, $t=2.3$): positive in all four, Fisher "
         r"mean $+0.840$. The cleanest contrast is a single run, where nothing but the training "
         r"step varies: across epoch $1\to10$ of one MS-COCO trajectory $\tau_5$ falls "
         r"$0.688\to0.575$ while top-1 falls $60.14\%\to58.14\%$, and the same monotone "
         r"co-movement appears in all ten runs (mean Pearson $0.90$, $10/10$ positive; "
         r"\texttt{outputs/\allowbreak a1\_epoch\_sweep.json}).")

B_OLD = r"\item Order preservation (Kendall tau) governs zero-shot robustness"
B_NEW = (r"\item Order preservation (Kendall tau) tracks zero-shot accuracy within a dataset, "
         r"but does not improve the stopping decision")

C_STAMP = (
    "\n\n---\n\n"
    "## ⚠️ 2026-10-12 更正（本节状态已过期）\n\n"
    "上文关于 A1 的陈述（**Submitted to Journal**，`NEUCOM-D-26-20952`，2026-09-16 提交）"
    "**已于 2026-10-10 失效**：\n\n"
    "| 字段 | 事实 |\n|---|---|\n"
    "| 决定 | **拒稿**（desk reject，*\"after an initial evaluation\"*）|\n"
    "| 理由 | *\"falls within the aim and scope of our journal, it did not meet the "
    "significance level required\"* |\n"
    "| 审稿意见 | **无**（`Comments to Authors:` 与 `Editor's comments` 均空）|\n"
    "| 转投 | 有（Elsevier ATS），须在 **`Nov 08 2026 11:59PM`** 前确认 |\n\n"
    "**由此连带**：`paper_a2`（A23）里「修订版已投 Neurocomputing"
    "（`NEUCOM-D-26-20952`）」这类表述**仍然属实**（那是历史事实），"
    "但**不应再暗示该稿仍在审**。\n"
    "A1 的当前目标刊见 `paper_a1/main.tex` 的 `\\journal{}`；投稿件见 `paper_a1/`。\n"
)


def patch(path: Path, pairs, required=True) -> int:
    t = io.open(path, encoding="utf-8", errors="replace").read()
    n = 0
    for i, (old, new) in enumerate(pairs):
        c = t.count(old)
        if c == 0:
            print(f"  {'🔴' if required else '⚠️ '} {path.name}#{i + 1}: 未命中")
            if required:
                return -1
            continue
        print(f"  ✅ {path.name}#{i + 1}: 命中 {c}")
        t = t.replace(old, new)
        n += c
    if not APPLY:
        return n
    bak = path.with_suffix(path.suffix + ".bak_p228")
    if not bak.exists():
        shutil.copy2(path, bak)
    io.open(path, "w", encoding="utf-8", newline="").write(t)
    return n


APPLY = False


def main() -> int:
    global APPLY
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    APPLY = args.apply

    print("=== A: main.tex 补组内证据 ===")
    r = patch(A1 / "main.tex", [(A_OLD, A_NEW)])
    if r < 0 and not APPLY:
        print("  （预演：锚点缺失）")
    print("=== B: highlights.tex ===")
    patch(A1 / "highlights.tex", [(B_OLD, B_NEW)])

    print("=== C: docs/A1_VENUE_DECISION.md ===")
    vd = REPO / "docs" / "A1_VENUE_DECISION.md"
    if vd.exists():
        v = io.open(vd, encoding="utf-8", errors="replace").read()
        if "2026-10-12 更正" not in v:
            if APPLY:
                bak = vd.with_suffix(".md.bak_p228")
                if not bak.exists():
                    shutil.copy2(vd, bak)
                io.open(vd, "w", encoding="utf-8", newline="").write(v + C_STAMP)
                print("  ✅ 已加更正标注")
            else:
                print("  （预演）")
        else:
            print("  ⚠️ 已有")

    if not APPLY:
        print("\n  （预演结束）")
        return 0

    # 核对
    print()
    print("=== 核对 ===")
    mt = io.open(A1 / "main.tex", encoding="utf-8", errors="replace").read()
    hl = io.open(A1 / "highlights.tex", encoding="utf-8", errors="replace").read()
    v = io.open(vd, encoding="utf-8", errors="replace").read()
    checks = [
        ("A 组内证据写入", "+0.840" in mt and "0.670" in mt and "100" in mt),
        ("B highlights 已改", "tracks zero-shot accuracy within a dataset" in hl),
        ("C docs 更正", "2026-10-12 更正" in v),
        ("标题仍是新版", "Tracks Zero-Shot Accuracy" in mt),
        ("无 Zero-Overhead Monitor", "Zero-Overhead Monitor" not in mt),
    ]
    ok = True
    for n_, x in checks:
        print(f"  {'✅' if x else '🔴'} {n_}")
        ok = ok and x
    print(f"\n  {'✅ 全部完成' if ok else '🔴 有未完成'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
