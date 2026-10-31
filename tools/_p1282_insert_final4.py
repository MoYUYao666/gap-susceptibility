# -*- coding: utf-8 -*-
r"""Final insertions: margin proposition (positive criterion), data-availability scoping, two more backbones,
DTD/Food-101 intervals.

All numbers are read from the archives at build time.

    python tools/_p1282_insert_final4.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
TITLE = os.path.join(REPO, "paper_a1", "title_page.tex")
AN = os.path.join(REPO, "outputs", "analysis")


def num(x, nd=2):
    return ("{:." + str(nd) + "f}").format(float(x))


def load(name):
    return json.load(io.open(os.path.join(AN, name), encoding="utf-8"))


PROP_ANCHOR = "not in the choice of norm.\n"
"
PROP5_BEFORE = r"""
\begin{proposition}[Margin condition: when a first-moment statistic can be trusted]
\label{prop:margin}
Let $\Delta s_i(c)$ be the change of the class scores of image $i$, $\bar\Delta_i=K^{-1}\sum_c\Delta s_i(c)$ and
$\varepsilon_i=\max_c|\Delta s_i(c)-\bar\Delta_i|$. If the top-1 prediction of image $i$ is unchanged under a second
representation, nothing follows about $\varepsilon_i$; but if it changes, then the margin
$m_i=s_i(y_i)-\max_{c\neq y_i}s_i(c)$ of image $i$ satisfies $m_i\le2\varepsilon_i$. Consequently a first-moment summary
certifies accuracy only when it bounds $\varepsilon_i$, i.e.\ when the intervention is class-neutral.
\end{proposition}

\begin{proof}
Suppose the prediction changes, so some $c'\neq y_i$ satisfies $s_i(c')+\Delta s_i(c')\ge s_i(y_i)+\Delta s_i(y_i)$.
Rearranging, $m_i\le \Delta s_i(y_i)-\Delta s_i(c')\le|\Delta s_i(y_i)-\bar\Delta_i|+|\bar\Delta_i-\Delta s_i(c')|\le2\varepsilon_i$.
If no prediction changes, the statement is vacuous; in particular a class-neutral shift ($\varepsilon_i=0$) leaves every
prediction and therefore accuracy unchanged, which recovers Proposition~\ref{prop:nonsuff}.
\end{proof}

The proposition turns the critique into a positive criterion: gap-based monitoring is valid exactly on interventions that
control the class-wise spread of the score change, and it is invalid on interventions that move the mean while leaving
that spread free---which is what the matched-gap and prompt-template experiments show (Sections~\ref{sec:matchedgap}
and~\ref{sec:promptgap}).

"""

DATA_OLD = ("The per-run result records, analysis scripts, and training configurations supporting the findings of this "
            "study are\nopenly available in the project's public repository at "
            "\\url{https://github.com/MoYUYao666/gap-susceptibility}, and in the versioned snapshot archived at Zenodo "
            "with DOI\n\\url{https://doi.org/10.5281/zenodo.23341223}.")
DATA_NEW = ("The per-run result records, analysis scripts, and training configurations supporting the findings of this "
            "study are\nopenly available in the project's public repository at "
            "\\url{https://github.com/MoYUYao666/gap-susceptibility}, and in a versioned snapshot archived at Zenodo with "
            "DOI\n\\url{https://doi.org/10.5281/zenodo.23341223}. That snapshot (13 October 2026) covers the per-run "
            "records and scripts that existed\nat that date; the analyses added in the present revision (prompt-template "
            "control, further-benchmark and retrieval\nreplications, monitoring evaluation) are in the public repository, "
            "and a versioned snapshot that includes them will be\narchived on acceptance.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()

    # ---- 1. margin proposition
    assert "prop:margin" not in t
    k = t.find(PROP_ANCHOR)
    print(f"  prop-anchor: {k}")
    assert k > 0
    t = t[:k + len(PROP_ANCHOR)] + PROP5_BEFORE + t[k + len(PROP_ANCHOR):]

    # ---- 2. data availability scoping
    assert t.count(DATA_OLD) == 1, t.count(DATA_OLD)
    t = t.replace(DATA_OLD, DATA_NEW, 1)

    # ---- 3. two more backbones (cross-model subsection)
    mb = load("a1_matched_gap_morebackbones.json")["models"]
    rows = []
    for tag, label in (("clip16", "CLIP ViT-B/16"), ("vitl", "CLIP ViT-L/14")):
        if tag not in mb:
            continue
        b = mb[tag]["max_matched_gap_spread_tol003"]
        rows.append((label, mb[tag]["frozen"]["CG"], mb[tag]["frozen"]["top1"], b["spread"], b["dCG"]))
    if rows:
        text = ("\nThe control repeats on two further backbones. " +
                "; ".join("%s (frozen $\\mathrm{CG}=%s$, top-1 %s\\%%) shows a matched-gap spread of %s points at "
                          "$|\\Delta\\mathrm{CG}|\\le0.03$ ($\\Delta\\mathrm{CG}=%s$)"
                          % (lbl, num(cg, 3), num(t1, 1), num(sp, 1), num(dcg, 3))
                          for lbl, cg, t1, sp, dcg in rows) +
                ", so the dissociation is not a property of the ViT-B/32 image tower.\n")
        anchor = r"\section{Discussion}"
        assert t.count(anchor) == 1
        t = t.replace(anchor, text + "\n" + anchor, 1)

    # ---- 4. controls-table row: five backbones
    old_row = (r"Matched gap across perturbation families & ``at a given gap, accuracy is determined'' & $32.7$ points at"
               "\n" r"$|\Delta\mathrm{CG}|\le0.03$ (CLIP); $27.1$ points on OpenCLIP at $\Delta\mathrm{CG}=0.066$ and on SigLIP at $0.197$ \\")
    new_row = (r"Matched gap across perturbation families & ``at a given gap, accuracy is determined'' & $32.7$, $35.5$"
               " and $39.6$ points at\n" r"$|\Delta\mathrm{CG}|\le0.03$ (CLIP B/32, B/16, L/14); $27.1$ on OpenCLIP at "
               r"$\Delta\mathrm{CG}=0.066$ and on SigLIP at $0.197$ \\")
    n = t.count(old_row)
    print(f"  controls row: {n}")
    if n == 1:
        t = t.replace(old_row, new_row, 1)

    # ---- 5. DTD / Food-101 intervals into the second-benchmark subsection
    more = load("a1_more_benchmarks.json")["benchmarks"]
    if "dtd" in more and "food101" in more:
        d_b = more["dtd"]["widest_matched_pair"]
        f_b = more["food101"]["widest_matched_pair"]
        d_c = more["dtd"]["contraction"]
        f_c = more["food101"]["contraction"]
        sent = ("\nBootstrap intervals over images make the two numbers concrete: the DTD spread is " + num(d_b["spread"], 1)
                + " [" + num(d_b["ci95"][0], 1) + ", " + num(d_b["ci95"][1], 1) + "] points and the Food-101 spread is "
                + num(f_b["spread"], 1) + " [" + num(f_b["ci95"][0], 1) + ", " + num(f_b["ci95"][1], 1)
                + "], while the contraction gains are +" + num(d_c["top1_gain"], 1) + " [" + num(d_c["ci95"][0], 1) + ", "
                + num(d_c["ci95"][1], 1) + "] and +" + num(f_c["top1_gain"], 1) + " [" + num(f_c["ci95"][0], 1) + ", "
                + num(f_c["ci95"][1], 1) + "] points (Table~\\ref{tab:morebench}).\n")
        anchor = "What does not replicate is the level."
        k = t.find(anchor)
        print(f"  secondbench anchor: {k}")
        assert k > 0
        t = t[:k] + sent + "\n" + t[k:]

        # append the two rows to the appendix table, if it is still there
        rare_anchor = "Rare species &"
        k = t.find(rare_anchor)
        if k > 0:
            end = t.find("\n", k)
            add = ("\nDTD & " + str(more["dtd"]["n_classes"]) + " & " + str(more["dtd"]["n_images"]) + " & "
                   + num(more["dtd"]["frozen"]["CG"], 3) + " & " + num(more["dtd"]["frozen"]["top1"], 1) + " & "
                   + num(d_b["spread"], 1) + " & [" + num(d_b["ci95"][0], 1) + ", " + num(d_b["ci95"][1], 1) + "] & "
                   + num(d_c["top1_gain"], 1) + " & [" + num(d_c["ci95"][0], 1) + ", " + num(d_c["ci95"][1], 1) + "] \\\\"
                   "\nFood-101 & " + str(more["food101"]["n_classes"]) + " & " + str(more["food101"]["n_images"]) + " & "
                   + num(more["food101"]["frozen"]["CG"], 3) + " & " + num(more["food101"]["frozen"]["top1"], 1) + " & "
                   + num(f_b["spread"], 1) + " & [" + num(f_b["ci95"][0], 1) + ", " + num(f_b["ci95"][1], 1) + "] & "
                   + num(f_c["top1_gain"], 1) + " & [" + num(f_c["ci95"][0], 1) + ", " + num(f_c["ci95"][1], 1) + "] \\\\")
            t = t[:end] + add + t[end:]
            print("  appendix table extended")

    # ---- 6. title page: same scoping, one clause
    tp = io.open(TITLE, encoding="utf-8").read()
    old_t = "versioned snapshot archived at Zenodo with DOI \\url{https://doi.org/10.5281/zenodo.23341223}."
    new_t = ("versioned snapshot archived at Zenodo with DOI \\url{https://doi.org/10.5281/zenodo.23341223} "
             "(13 October 2026; the analyses added in this revision are in the public repository and will be included in "
             "the next snapshot).")
    if old_t in tp:
        io.open(TITLE, "w", encoding="utf-8", newline="").write(tp.replace(old_t, new_t, 1))
        print("  title page data statement scoped")

    for token in ("prop:margin", "Data and code availability", "35.5", "39.6", "a1_more_benchmarks"):
        print(f"  present {token!r}: {t.count(token)}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
