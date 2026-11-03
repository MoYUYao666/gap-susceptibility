# -*- coding: utf-8 -*-
r"""Repoint the four citations that led a reviewer to files they cannot open.

The three response boxes cite documentation by path:
    docs/P3_DOWNSTREAM.md      (Reviewer 1, and referenced from Reviewer 3)
    docs/P3_EXPERIMENTS.md     (Reviewer 2)
    docs/P3_STATS.md           (Reviewer 3)
    tools/_p434_alloc_train.py (Reviewer 3)

None of those is in the published archive. Worse, the three markdown files cannot simply be
published: they are internal working documents that quote the reviewer comments verbatim
("R2.2", "R3.21"), name internal tasks, and in places recommend wording to the author. That
is not material to hand a reviewer.

So each citation is replaced by the public artefact that carries the same evidence: the
archived result JSONs and their fields, which is what the responses already cite elsewhere
and what the Data statement points at.

The same three files are inside the LaTeX source package, under evidence/, so they are
removed there too - a source package that ships review commentary invites the same problem.

    python tools/_p657_fix_cited_docs.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESP = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"
SRC = REPO / "SUBMISSION" / "P3_PRL_revision" / "manuscript" / "latex_source"

FIXES = [
    # (old, new)
    ("Sources: outputs/analysis/p3d_clip_ranksweep.json :: runs[*] (per-run, append-only); "
     "analysis in docs/P3_DOWNSTREAM.md.",
     "Sources: outputs/analysis/p3d_clip_ranksweep.json :: runs[*] (per-run, append-only), "
     "and the downstream tables in the supplementary material."),
    ("Analysis in docs/P3_EXPERIMENTS.md.",
     "The per-run records carry their own protocol blocks, so the arm, seed and learning rate "
     "of each value can be read off directly."),
    ("Sources: outputs/analysis/p3_seed_provenance.json; "
     "p3d_e0_vs_token_budget_*.json :: rows[*].device; docs/P3_STATS.md.",
     "Sources: outputs/analysis/p3_seed_provenance.json; "
     "p3d_e0_vs_token_budget_*.json :: rows[*].device."),
    ("Source: outputs/analysis/p3_alloc_results.json :: measured_n_trainable_params and the "
     "per-run protocol blocks; assertion in tools/_p434_alloc_train.py.",
     "Source: outputs/analysis/p3_alloc_results.json :: measured_n_trainable_params, and the "
     "assertion recorded in each per-run protocol block under "
     "outputs/analysis/p3_alloc_runs/."),
]

# evidence documents that must not ship in the source package
EVIDENCE_IN_SRC = ["evidence/P3_EXPERIMENTS.md", "evidence/P3_STATS.md",
                   "evidence/P3_DOWNSTREAM.md", "evidence/P3_COMPRESSION.md"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print("  1) repoint the citations in every copy of the response material")
    n = 0
    for p in sorted(list(RESP.glob("*")) + [REPO / "docs" / "P3_RESPONSE_LETTER.md"]):
        if not p.is_file() or p.suffix.lower() not in (".txt", ".md"):
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        t2, hits = t, 0
        for old, new in FIXES:
            c = t2.count(old)
            if c:
                t2 = t2.replace(old, new)
                hits += c
        if hits:
            n += hits
            print(f"     {p.name:<44} {hits} replacement(s)")
            if a.apply:
                bak = p.with_suffix(p.suffix + ".bak_p657")
                if not bak.exists():
                    shutil.copy2(p, bak)
                io.open(p, "w", encoding="utf-8", newline="").write(t2)
    print(f"     total {n}")

    print()
    print("  2) remove the internal evidence documents from the source package")
    for rel in EVIDENCE_IN_SRC:
        p = SRC / rel
        if p.exists():
            print(f"     removing {rel}  ({p.stat().st_size:,} bytes)")
            if a.apply:
                p.unlink()
        else:
            print(f"     absent   {rel}")

    print()
    print("  3) re-check: does any response still point at docs/ or a removed tool?")
    bad = 0
    for p in sorted(RESP.glob("*_plain.txt")):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        for k in ("docs/P3_", "tools/_p434"):
            if k in t:
                print(f"     BAD {p.name}: still cites {k}")
                bad += 1
    print(f"     {bad} remaining")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
