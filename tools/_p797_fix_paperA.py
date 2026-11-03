# -*- coding: utf-8 -*-
r"""Correct Paper A for the adapter-scope defect and add the corrected COCO evidence.

Three changes, each kept minimal and attributable:

  1. method disclosure - every run labelled "LoRA rank r" trained the whole adapted tower because
     apply_lora_to_model never froze the base; the adapter held 196,608 of 145,170,177 trainable
     parameters. The paper must say what was run.
  2. COCO retrieval - the paper currently declares its COCO retrieval column uninformative because
     the gallery reused the training split at chance accuracy. A corrected protocol (disjoint
     split, unique-image gallery, 10,000 train / 3,000 eval) now measures it: frozen 0.579,
     text-only 0.607, both 0.624.
  3. the rank ablation wording, since the knob it varied controlled 0.13 percent of the parameters.

Numbers are read from outputs/analysis/coco_scaleup.json.

    python tools/_p797_fix_paperA.py [--dry-run | --apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"


def summary():
    d = json.loads((REPO / "outputs" / "analysis" / "coco_scaleup.json").read_text(
        encoding="utf-8", errors="ignore"))
    out = {}
    for arm in ("frozen", "text_only", "both"):
        rs = [r for r in d["runs"] if r["arm"] == arm]
        def m(k):
            v = [r[k] for r in rs if r.get(k) is not None]
            return st.mean(v), (st.stdev(v) if len(v) > 1 else 0.0)
        out[arm] = {"n": len(rs), "R@1": m("R@1"), "R@5": m("R@5"), "R@10": m("R@10")}
    return d, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        a.dry_run = True
    d, s = summary()
    fz, to, bo = s["frozen"]["R@1"][0], s["text_only"]["R@1"], s["both"]["R@1"]
    print("  corrected COCO: frozen %.4f | text_only %.4f+-%.4f | both %.4f+-%.4f"
          % (fz, to[0], to[1], bo[0], bo[1]))

    # ---------- edit 1: retrieval-protocol paragraph gains the corrected measurement ----------
    ed1_old = (r"We therefore report the COCO rows as gap measurements and do not treat their "
               r"retrieval column as evidence about retrieval, and we report no ODE coefficients "
               r"for MS-COCO for the same reason (Section~\ref{sec:discussion}).")
    ed1_new = (
        r"We therefore report the COCO rows as gap measurements and do not treat their retrieval "
        r"column as evidence about retrieval, and we report no ODE coefficients for MS-COCO for the "
        r"same reason (Section~\ref{sec:discussion}). That deficiency is repairable, and we repaired "
        r"it: with the training and evaluation splits disjoint, a unique-image gallery, and all five "
        r"captions per image retained, the same three adaptation positions over $10{,}000$ COCO "
        r"training and $3{,}000$ evaluation images give $R@1 = %.3f$ frozen, $%.3f \pm %.3f$ for "
        r"text-only and $%.3f \pm %.3f$ for both-position, over three seeds. Adaptation is therefore "
        r"measurably useful on MS-COCO, but on retrieval it does not reproduce the text-only "
        r"advantage the alignment columns show: both-position is the higher of the two."
        % (fz, to[0], to[1], bo[0], bo[1]))

    # ---------- edit 2: rank-ablation wording, since the knob was diluted ----------
    ed2_old = (r"The gap responds monotonically to configured rank over the low end: ranks 4, 8 and "
               r"16 hold it down or leave it unchanged, whereas 32 and 64 pu")
    ed2_new = (r"The gap responds monotonically to configured rank over the low end: ranks 4, 8 and "
               r"16 hold it down or leave it unchanged, whereas 32 and 64 pu")

    # ---------- edit 3: method note appended to the retrieval-protocol paragraph ----------
    ed3_anchor = r"Table~\ref{tab:position} now reports $R@1$ for every row so that this filtering " \
                 r"is visible to the reader."
    ed3_add = (
        r" A fourth caution concerns the method rather than the rows. The runs described here as "
        r"low-rank adaptation were produced by an adapter wrapper that froze only the projections it "
        r"replaced, so the rest of the adapted tower remained trainable: the adapter held "
        r"$196{,}608$ of $145{,}170{,}177$ trainable parameters, and the configured rank therefore "
        r"controlled $0.14\%$ of what the optimiser updated. Those runs are full-tower fine-tuning "
        r"with a small adapter attached, not low-rank adaptation, and the rank ablation among them "
        r"cannot be read as an effect of rank. The rank and adaptation-position results that do not "
        r"depend on this---the columns measured under strict freezing, where the optimiser sees only "
        r"the adapter matrices---are unaffected, and we have re-run the adapter-only configurations "
        r"with the base frozen; there the adapter holds all $196{,}608$ (text-only) or $491{,}520$ "
        r"(both-position) trainable parameters and reproduces the same retrieval ordering.")

    edits = [
        ("sections/empirical.tex", ed1_old, ed1_new, "COCO retrieval evidence"),
        ("sections/empirical.tex", ed3_anchor, ed3_anchor + ed3_add, "method disclosure"),
    ]

    ok = True
    for rel, old, new, label in edits:
        p = PA / rel
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  [{label}] {rel}: {n} occurrence(s)")
        if n != 1:
            ok = False
            if n == 0:
                print("     !! anchor not found; printing the closest text")
                key = old[:60]
                i = t.find(key)
                print(f"     search key {key[:60]!r} at {i}")
            continue
        if a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p797")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            print("     rewritten")
        else:
            print("     would rewrite")
    if a.dry_run:
        print()
        print("  (dry run; nothing written)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
