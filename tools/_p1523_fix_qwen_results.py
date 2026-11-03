# -*- coding: utf-8 -*-
"""Restore the good supplement from git and apply the corrected Qwen tables cleanly."""
import io
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
GAP = os.path.join(REPO, "docs", "P3_GAPFILL_2026-10-21.md")
GOOD = "b5b22c7"
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")


def rows():
    out = []
    import glob
    for f in sorted(glob.glob(os.path.join(EXP, "qwen_cf_uniform_rank*_q25_r*.json"))):
        d = json.load(io.open(f, encoding="utf-8"))
        out.append((d["rank"], d["seed"], d["delta_E"], d["E"]))
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def replace_rows(tex: str, start_marker: str, end_marker: str, new_rows: str) -> str:
    i = tex.find(start_marker)
    assert i >= 0, start_marker
    m = tex.find("\\midrule", i)
    b = tex.find("\\bottomrule", m)
    return tex[: m + len("\\midrule")] + "\n" + new_rows + "\n" + tex[b:]


def main() -> int:
    subprocess.run(["git", "-C", REPO, "checkout", GOOD, "--", "paper3/paper_ieee/supplementary/supplementary.tex",
                    "docs/P3_GAPFILL_2026-10-21.md"], check=True)
    print("restored supplement and gapfill doc from", GOOD)
    rs = rows()
    table = "\n".join("%d & %d & %+.1f & %s \\\\" % (r, s, dE, E) for r, s, dE, E in rs)
    t = io.open(SUPP, encoding="utf-8").read()
    # S20: widen the 3-column table to 4 columns and replace its rows
    i = t.find("\\section{Newer model family}")
    j = t.find("\\label{tab:newer}")
    assert i > 0 and j > i
    seg = t[i:j]
    seg = seg.replace("\\begin{tabular}{@{}rl l@{}}", "\\begin{tabular}{@{}lrr l@{}}", 1)
    seg = seg.replace("rank & $\\Delta E$ & trajectory \\\\", "rank & seed & $\\Delta E$ & trajectory \\\\", 1)
    t = t[:i] + seg + t[j:]
    t = replace_rows(t, "\\section{Newer model family}", "\\label{tab:newer}", table)
    # S26
    t = replace_rows(t, "\\section{Newer-family seed replication}", "\\label{tab:newerseeds}", table)
    # reading text in S20
    old_read = ("The sign pattern is the opposite of LLaVA's (positive at $r=5$, near zero at $r=6$), so\n"
                "the crossing does not replicate; this bounds the cross-architecture claim rather than extending it.")
    new_read = ("LLaVA's crossing does not replicate on this family: the two ranks are positive or near zero depending on\n"
                "the seed, and even the sign at $r=5$ varies across seeds ($+448$, $+384$, $-64$), so no sign change is\n"
                "established between $r=5$ and $r=6$. This bounds the cross-architecture claim rather than extending it.")
    if old_read in t:
        t = t.replace(old_read, new_read, 1)
    old_cap = ("The sign pattern is stable (all $r=5$ positive, all $r=6$ negative),\n"
               "opposite to LLaVA's; the crossing does not replicate.")
    new_cap = ("No sign change is established between $r=5$ and $r=6$; the sign at $r=5$ varies across seeds, so the\n"
               "LLaVA crossing does not replicate on this family.")
    if old_cap in t:
        t = t.replace(old_cap, new_cap, 1)
    old_row = "crossing transfers to a newer model family & \\emph{not} supported & Qwen2.5-VL-3B: $r=5$ $+608$, $r=6$ $-48$ (S20) \\\\"
    new_row = ("crossing transfers to a newer model family & \\emph{not} supported & Qwen2.5-VL-3B: no sign change; "
               "$r=5$ sign varies across seeds (S20) \\\\")
    if old_row in t:
        t = t.replace(old_row, new_row, 1)
    io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
    print("qwen tables patched cleanly")
    g = io.open(GAP, encoding="utf-8").read()
    note = ("""
## rank-bug correction (2026-10-22 17:20)

The first Qwen2.5-VL run set was invalid: `run_training_qwen25.py` ignored `--rank` (every record had
`trainable_params=1,843,200`, the default rank 4). The runner is fixed, the invalid records are archived under
`outputs/analysis/_invalid_qwen25_rank_bug/`, and the corrected rank-controlled results are:
r5 = +448 / +384 / −64, r6 = +432 / −32 / −80 (seeds 42/123/789). No sign change between r5 and r6; the sign at r5
varies across seeds. The earlier "stable reversed sign pattern" wording is withdrawn.
""")
    if "rank-bug correction" not in g:
        io.open(GAP, "w", encoding="utf-8", newline="").write(g.rstrip() + note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
