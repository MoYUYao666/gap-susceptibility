# -*- coding: utf-8 -*-
r"""Fix Table S4's overflow and make all five supplement tables column-safe by construction.

The first attempt gave Table S3, S4 and S5 fixed-width p{} columns. Table S3 (a table*, full text width)
came out right, but Table S4 (a single column, 3.5 in) was wider than the column and its last column ran
into the right-hand column and over the text below.

Fix: give each table an explicit width budget and wrap the whole tabular in
`\resizebox{\columnwidth}{!}{...}` (or `\textwidth` for the table*), so a table can never exceed its
column no matter how the numbers grow. Column specs are reduced to proportions.

    python tools/_p918_rebalance_supp_tables.py [--apply]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
B = chr(92)

# Table S4: 8 pt face, six columns; measured natural width was about 1.19x the column, so the widths are
# reduced and the result is scaled to the column as a guarantee.
S4_OLD = (B + "fontsize{8}{9.5}" + B + "selectfont\n"
          + B + "setlength{" + B + "tabcolsep}{3pt}\n"
          + B + "begin{tabular}{@{}>{"
          + B + "raggedright" + B + "arraybackslash}p{1.7cm}"
          + (">{"
             + B + "centering" + B + "arraybackslash}p{1.45cm}") * 5 + "@{}}")
S4_NEW = (B + "fontsize{8}{9.5}" + B + "selectfont\n"
          + B + "setlength{" + B + "tabcolsep}{2pt}\n"
          + B + "resizebox{" + B + "columnwidth}{!}{%\n"
          + B + "begin{tabular}{@{}>{"
          + B + "raggedright" + B + "arraybackslash}p{1.35cm}"
          + (">{"
             + B + "centering" + B + "arraybackslash}p{1.15cm}") * 5 + "@{}}}")

S4_END = B + "end{tabular}\n" + B + "end{table}"

# Tables S1 and S2 are numeric with short first columns; scale them too, so the guarantee is uniform.
S12 = [("tab:gamma_detail", "lrrrr", "3.2cm"),
       ("tab:gamma_rank", "lrrrrr", "3.2cm")]
S12_OLD = [(B + "fontsize{8}{9.5}" + B + "selectfont\n"
            + B + "setlength{" + B + "tabcolsep}{5pt}\n"
            + B + "begin{tabular}{@{}l" + "r" * (len(spec) - 1) + "@{}}")
           for _lab, spec, _w in S12]
S12_NEW = [(B + "fontsize{8}{9.5}" + B + "selectfont\n"
            + B + "setlength{" + B + "tabcolsep}{3pt}\n"
            + B + "resizebox{" + B + "columnwidth}{!}{%\n"
            + B + "begin{tabular}{@{}l" + "r" * (len(spec) - 1) + "@{}}}")
           for _lab, spec, _w in S12]

# Table S5 has 15 rows in a single column; scale it as well.
S5_OLD = (B + "fontsize{8}{9.5}" + B + "selectfont\n"
          + B + "setlength{" + B + "tabcolsep}{5pt}\n"
          + B + "begin{tabular}{@{}>{"
          + B + "centering" + B + "arraybackslash}p{0.9cm}")
S5_NEW = (B + "fontsize{8}{9.5}" + B + "selectfont\n"
          + B + "setlength{" + B + "tabcolsep}{3pt}\n"
          + B + "resizebox{" + B + "columnwidth}{!}{%\n"
          + B + "begin{tabular}{@{}>{"
          + B + "centering" + B + "arraybackslash}p{0.9cm}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SUPP.read_text(encoding="utf-8")
    # Idempotence guard. Re-running after a successful pass would look for `end{tabular}` inside a
    # resized table, find only the already-closed `end{tabular}}`, and mis-patch: the first attempt did
    # exactly that. If the file is already in the target state, stop here.
    if (t.count(B + "resizebox{" + B + "columnwidth") == 4
            and not any(line.rstrip().endswith("@{}}}") for line in t.splitlines())):
        print("  already rebalanced: 4 resized tables, no excess brace")
        return 0
    out = t
    print(f"  resizebox already present: {out.count(B + 'resizebox')}")

    for name, old, new in (("Table S4 widths and scale", S4_OLD, S4_NEW),
                           ("Table S1 scale", S12_OLD[0], S12_NEW[0]),
                           ("Table S2 scale", S12_OLD[1], S12_NEW[1]),
                           ("Table S5 scale", S5_OLD, S5_NEW)):
        c = out.count(old)
        if c == 0 and new in out:
            print(f"  {name}: already applied")
            continue
        assert c == 1, f"{name}: anchor found {c} times, expected 1"
        out = out.replace(old, new, 1)
        print(f"  {name}: applied")

    # close the four resizeboxes. Each region runs from its own `\resizebox` to the first `end{table}`
    # after it; the opening is renamed to `\resizeboxtmp` once handled, because patching the closing line
    # alone would leave the loop finding the same opening again.
    n = 0
    while B + "resizebox{" + B + "columnwidth" in out:
        start = out.find(B + "resizebox{" + B + "columnwidth")
        tab_end = out.find(B + "end{tabular}\n", start)
        table_end = out.find(B + "end{table}", start)
        assert 0 <= tab_end < table_end, "an end{tabular} is missing inside a resized table"
        out = (out[:tab_end] + B + "end{tabular}}\n" + out[tab_end + len(B + "end{tabular}\n"):])
        out = (out[:start] + B + "resizeboxtmp{" + B + "columnwidth}"
               + out[start + len(B + "resizebox{" + B + "columnwidth}"):])
        n += 1
        print(f"  table {n}: tabular scaled to the column")
    out = out.replace(B + "resizeboxtmp{", B + "resizebox{")
    if n > 4:
        raise SystemExit(f"  ERROR: {n} resizebox openings, expected 4")

    # each of the four single-column tables now has to close its resizebox
    n_open = out.count(B + "resizebox{" + B + "columnwidth}")
    n_close = out.count(B + "end{tabular}}")
    print(f"  resizebox opens: {n_open}, closes: {n_close}")
    assert n_open == n_close == 4, f"{n_open} opens vs {n_close} closes"

    # `\resizebox{\columnwidth}{!}{%` opens a group that the closing `\end{tabular}}` shuts, so each
    # tabular line must end with exactly `@{}}`: one brace for `@{}` and one for the group. Three braces
    # leave the alignment unterminated, which LaTeX reports as "Missing \cr inserted".
    over = [ln for ln, line in enumerate(out.splitlines(), 1)
            if line.rstrip().endswith("@{}}}")]
    for ln in over:
        bad = out.splitlines()[ln - 1]
        out = out.replace(bad, bad[:-1], 1)
        print(f"  line {ln}: removed one excess brace from the tabular spec")
    assert not [ln for ln, line in enumerate(out.splitlines(), 1)
                if line.rstrip().endswith("@{}}}")], "an excess brace remains"

    if not a.apply:
        print("  (dry run)")
        return 0
    SUPP.write_text(out, encoding="utf-8", newline="")
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
