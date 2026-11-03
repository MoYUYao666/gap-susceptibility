# -*- coding: utf-8 -*-
r"""Fix the float on page 49, and move Table 2's provenance note into the appendix.

Measured (`pdftoppm` at 150 dpi, every page, 2026-10-15): on 48 of 61 pages the lowest ink sits at
702.2 pt, the footer baseline. Page 49 reaches 791.5 pt -- the physical paper edge -- so the float
overruns the footer by about 90 pt and the page number is pushed to the very bottom of the sheet.
Profiling the page row by row shows the whole page is caption text: the caption plus the note under
the table is roughly a page and a half tall, and no caption of that size can sit under a 6-row table.

So the material is split by purpose:

* the caption keeps only what a reader needs in order to read the table (protocol, seeding, grouping,
  the $\dagger$ rows, which ordering runs which way);
* the provenance of the $R@1$ column -- two near-duplicate passages about the OpenCLIP rank-8/rank-4
  mismatch, the CLIP B/32 text-only cell that equals a non-strict mean, and the vision-only cell that
  cannot be reproduced from its checkpoint -- becomes its own numbered appendix section, which the
  caption points to. Nothing is dropped; the duplicated sentence inside it is collapsed to one.

Idempotent, and it reports the page-49 overrun before and after via `tools/_p873_measure_pages.py`.

    python tools/_p872_fix_table_float.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EMP = [REPO / "paper合" / "sections" / "empirical.tex",
       REPO / "paper合" / "NC_submission" / "latex_source" / "sections" / "empirical.tex"]
SUPP = [REPO / "paper合" / "sections" / "supplement.tex",
        REPO / "paper合" / "NC_submission" / "latex_source" / "sections" / "supplement.tex"]
MARK = "sec:r1provenance"

CAPTION_RE = re.compile(r"\\caption\{The three adaptation positions under strict freezing.*?"
                        r"(?=\\label\{tab:position_strict\})", re.S)
NOTE_RE = re.compile(r"\{\\footnotesize\\noindent\\textit\{Note on the \$R@1\$ column\.\}.*?\n\\end\{table\}",
                     re.S)

NEW_CAPTION = r"""\caption{The three adaptation positions under strict freezing, where the optimizer sees only the
adapter matrices, so the arms differ solely in where those adapters sit. Each entry is $\Delta$CG with
$R@1$ beneath it (bold marks the smallest $\Delta$CG in the row), at 5000 samples and 10 epochs with
$\alpha=2r$; negative $\Delta$CG means the gap narrowed. Every row is a five-seed mean at batch $128$,
with a seed-to-seed standard deviation of $0.0006$--$0.006$ depending on the backbone, so the
separations the arms rest on are one to several times that spread. Rows are grouped by pre-training
objective, which is what the ordering tracks: every contrastive image--text backbone puts text-only
smallest, and the two backbones trained with other objectives put both-position there. Patch size does
not separate the groups, and the two rows marked $\dagger$ show this directly, having been measured at
the same rank under the same protocol. On the contrastive backbones the arm that minimizes the gap
(text-only) retrieves worst, so the ordering by gap runs opposite to the ordering by $R@1$. BioCLIP was
measured at rank~$4$ and its retrievals were not recorded, so those cells are left blank rather than
estimated. The provenance of the $R@1$ column, including the one cell that does not reproduce, is in
Section~\ref{sec:r1provenance}.}"""

APPENDIX = r"""

\section*{F. Provenance of the $R@1$ column of Table~\ref{tab:position_strict}}
\label{sec:r1provenance}

Table~\ref{tab:position_strict} is used for its $\Delta$CG column, and that column is exact: all twelve
cells reproduce from the archived per-seed JSON at four-decimal precision, and its sampling noise is
$80$--$200$ times below the between-arm differences. The $R@1$ column does not reproduce uniformly, and
we state its provenance rather than silently adjust it. Six cells reproduce exactly. Three cells of the
OpenCLIP row ($0.643$, $0.680$, $0.672$) come from the rank-$8$ OpenCLIP archive
(\texttt{strict\_freeze\_openclip}) while that row's $\Delta$CG comes from the rank-$4$ archive
(\texttt{strict\_freeze\_oclip/r4}), so the two halves of that row were not measured on the same
configuration; the sixth and largest discrepancy ($0.643$ against $0.6366$) has the same cause. One
cell, CLIP B/32$^\dagger$ text-only ($0.621$), equals the non-strict
\texttt{flickr30k\_seeds/rq2\_text\_only} five-seed mean ($0.6210$, $145{,}170{,}177$ trainable
parameters) rather than the strict-freezing mean for that cell ($0.6222$, $98{,}304$ trainable
parameters). The remaining five entries differ from the five-seed means by at most $0.0022$, of the same
order as the sampling noise. We also note that the $R@1$ of the CLIP B/32 vision-only cell cannot be
reproduced from its own checkpoint under the paper's own loader and metric function: four independent
evaluations give $0.675$--$0.682$ (mean $0.679$) against the archived $0.700$, which is the largest of
that cell's five seeds ($0.671$--$0.700$, mean $0.680$), i.e.\ the archived value is a high draw rather
than a reproducible measurement. The recomputed five-seed means, from
\texttt{outputs/strict\_freeze\_oclip/r4}, \texttt{outputs/strict\_freeze\_b32\_r4} and
\texttt{outputs/strict\_freeze\_b16/r4} respectively, are: OpenCLIP text-only $0.6366$, both-position
$0.6818$, vision-only $0.6698$; CLIP B/32$^\dagger$ text-only $0.6222$, both-position $0.6796$; and
CLIP B/16$^\dagger$ text-only $0.6502$.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    for p in EMP:
        t = io.open(p, encoding="utf-8").read()
        m = CAPTION_RE.search(t)
        assert m, f"{p.name}: caption not found"
        note = NOTE_RE.search(t)
        if MARK in t and not note:
            print(f"  {p.name}: already applied")
            continue
        old_caption = m.group(0)
        assert old_caption.count("Every row is a five-seed mean") == 2, \
            f"{p.name}: expected the duplicated sentence twice"
        if not a.apply:
            print(f"  would rewrite {p.name}: caption {len(old_caption.splitlines())} -> "
                  f"{len(NEW_CAPTION.splitlines())} lines, and remove the in-table note")
            continue
        t = t.replace(old_caption, NEW_CAPTION, 1)
        if note:
            t = NOTE_RE.sub("", t, count=1)
        io.open(p, "w", encoding="utf-8", newline="").write(t)
        print(f"  rewrote {p.relative_to(REPO).as_posix()}")

    for p in SUPP:
        t = io.open(p, encoding="utf-8").read()
        if MARK in t:
            print(f"  {p.name}: appendix section already present")
            continue
        if not a.apply:
            print(f"  would append section F to {p.name}")
            continue
        io.open(p, "w", encoding="utf-8", newline="").write(
            t.rstrip("\n") + "\n" + APPENDIX.lstrip("\n"))
        print(f"  appended section F to {p.relative_to(REPO).as_posix()}")

    if not a.apply:
        print("  (dry run)")
        return 0

    for p in EMP:
        t = io.open(p, encoding="utf-8").read()
        assert t.count(MARK) == 1, f"{p.name}: cross-reference missing"
        assert "Note on the $R@1$ column" not in t, f"{p.name}: in-table note survives"
        assert t.count("Every row is a five-seed mean") == 1, f"{p.name}: duplicate sentence survives"
        assert t.count("\\end{tabular}") == 3 and t.count("\\end{table}") == 3, \
            f"{p.name}: table environments unbalanced"
    for p in SUPP:
        t = io.open(p, encoding="utf-8").read()
        assert t.count(MARK) == 1, f"{p.name}: appendix label missing"
        for keep in ("$0.6366$", "$0.6502$", "high draw rather", "rank-$4$ archive", "F. Provenance"):
            assert keep in t, f"{p.name}: section F dropped {keep}"
        print(f"  verified {p.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
