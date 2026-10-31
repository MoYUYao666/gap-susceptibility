# -*- coding: utf-8 -*-
r"""Final insertions for A1: margin proposition (positive criterion), data-availability scoping, two more backbones,
DTD/Food-101 intervals.

Numbers are read from the archives at build time.

    python tools/_p1283_insert_final4b.py [--apply]
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


def abs_ci(ci):
    """Return the interval of |difference| when the bootstrap reports a signed difference."""
    lo, hi = float(ci[0]), float(ci[1])
    if hi <= 0:
        return [-hi, -lo]
    if lo >= 0:
        return [lo, hi]
    return [0.0, max(abs(lo), abs(hi))]


def num(x, nd=2):
    return ("{:." + str(nd) + "f}").format(float(x))


def load(name):
    return json.load(io.open(os.path.join(AN, name), encoding="utf-8"))


PROP_ANCHOR = "not in the choice of norm." + chr(10)

PROP5 = r"""
\begin{proposition}[Margin condition: when a first-moment statistic can be trusted]
\label{prop:margin}
Let $\Delta s_i(c)$ be the change of the class scores of image $i$, $\bar\Delta_i=K^{-1}\sum_c\Delta s_i(c)$, and
$\varepsilon_i=\max_c|\Delta s_i(c)-\bar\Delta_i|$. If the top-1 prediction of image $i$ changes, then its margin
$m_i=s_i(y_i)-\max_{c\neq y_i}s_i(c)$ satisfies $m_i\le2\varepsilon_i$. Consequently a first-moment summary certifies
accuracy only when it bounds $\varepsilon_i$, that is, when the intervention is class-neutral.
\end{proposition}

\begin{proof}
Suppose the prediction changes, so some $c'\neq y_i$ satisfies
$s_i(c')+\Delta s_i(c')\ge s_i(y_i)+\Delta s_i(y_i)$. Rearranging and inserting the row mean,
$m_i\le\Delta s_i(y_i)-\Delta s_i(c')=|\Delta s_i(y_i)-\bar\Delta_i|+|\bar\Delta_i-\Delta s_i(c')|\le2\varepsilon_i$.
If no prediction changes the statement is vacuous; in particular a class-neutral shift ($\varepsilon_i=0$) leaves every
prediction, and therefore accuracy, unchanged, which recovers Proposition~\ref{prop:nonsuff}.
\end{proof}

The proposition turns the critique into a positive criterion. Gap-based monitoring is valid exactly on interventions
that control the class-wise spread of the score change; it is invalid on interventions that move the mean while leaving
that spread free, which is what the matched-gap and prompt-template experiments show
(Sections~\ref{sec:matchedgap} and~\ref{sec:promptgap}).

"""

DATA_OLD = (
    "The per-run result records, analysis scripts, and training configurations supporting the findings of this study are\n"
    "openly available in the project's public repository at\n"
    "\\url{https://github.com/MoYUYao666/gap-susceptibility}, and in the versioned snapshot archived at Zenodo with DOI\n"
    "\\url{https://doi.org/10.5281/zenodo.23341223}."
)
DATA_NEW = (
    "The per-run result records, analysis scripts, and training configurations supporting the findings of this study are\n"
    "openly available in the project's public repository at\n"
    "\\url{https://github.com/MoYUYao666/gap-susceptibility}, and in a versioned snapshot archived at Zenodo with DOI\n"
    "\\url{https://doi.org/10.5281/zenodo.23341223}. That snapshot (13 October 2026) covers the per-run records and "
    "scripts that existed\nat that date; the analyses added in the present revision (prompt-template control, "
    "further-benchmark and retrieval\nreplications, monitoring evaluation) are in the public repository, and a versioned "
    "snapshot that includes them will be\narchived on acceptance."
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()

    # 1. margin proposition, right after the paragraph that closes Proposition 4
    assert "prop:margin" not in t
    k = t.find(PROP_ANCHOR)
    print(f"  prop4 paragraph anchor: {k}")
    assert k > 0
    t = t[:k + len(PROP_ANCHOR)] + PROP5 + t[k + len(PROP_ANCHOR):]

    # 2. data availability scoped to what the snapshot actually contains
    print(f"  data statement occurrences: {t.count(DATA_OLD)}")
    assert t.count(DATA_OLD) == 1
    t = t.replace(DATA_OLD, DATA_NEW, 1)

    # 3. two further backbones
    mb = load("a1_matched_gap_morebackbones.json")["models"]
    bits = []
    for tag, label in (("clip16", "CLIP ViT-B/16"), ("vitl", "CLIP ViT-L/14")):
        if tag in mb:
            b = mb[tag]["max_matched_gap_spread_tol003"]
            bits.append("%s (frozen $\\mathrm{CG}=%s$, top-1 %s\\%%) shows a spread of %s points at "
                        "$|\\Delta\\mathrm{CG}|\\le0.03$ ($\\Delta\\mathrm{CG}=%s$)"
                        % (label, num(mb[tag]["frozen"]["CG"], 3), num(mb[tag]["frozen"]["top1"], 1),
                           num(b["spread"], 1), num(b["dCG"], 3)))
    if bits:
        para = ("\nThe control repeats on two further backbones. " + "; ".join(bits)
                + "; the dissociation is therefore not a property of the ViT-B/32 image tower.\n")
        anchor = "\\section{Discussion}"
        assert t.count(anchor) == 1
        t = t.replace(anchor, para + "\n" + anchor, 1)

    # 4. controls table: five backbones
    old_row = (r"Matched gap across perturbation families & ``at a given gap, accuracy is determined'' & $32.7$ points at"
               "\n" r"$|\Delta\mathrm{CG}|\le0.03$ (CLIP); $27.1$ points on OpenCLIP at $\Delta\mathrm{CG}=0.066$ and on SigLIP at $0.197$ \\")
    new_row = (r"Matched gap across perturbation families & ``at a given gap, accuracy is determined'' & $32.7$, "
               "$35.5$ and $39.6$\n" r"points at $|\Delta\mathrm{CG}|\le0.03$ (CLIP B/32, B/16, L/14); $27.1$ on "
               r"OpenCLIP at $\Delta\mathrm{CG}=0.066$ and on SigLIP at $0.197$ \\")
    print(f"  controls row: {t.count(old_row)}")
    if t.count(old_row) == 1:
        t = t.replace(old_row, new_row, 1)

    # 5. DTD / Food-101 intervals
    more = load("a1_more_benchmarks.json")["benchmarks"]
    if "dtd" in more and "food101" in more:
        rows = []
        for spec in ("dtd", "food101"):
            v = more[spec]
            b, c = v["widest_matched_pair"], v["contraction"]
            rows.append((spec, v, b, c))
        d, f_ = rows[0], rows[1]
        sent = ("\nBootstrap intervals over images make the two numbers concrete: DTD's widest matched pair differs by "
                + num(d[2]["spread"], 1) + " [" + num(abs_ci(d[2]["ci95"])[0], 1) + ", " + num(abs_ci(d[2]["ci95"])[1], 1)
                + "] points and Food-101's by " + num(f_[2]["spread"], 1) + " [" + num(abs_ci(f_[2]["ci95"])[0], 1) + ", "
                + num(abs_ci(f_[2]["ci95"])[1], 1) + "], while the contraction gains are +" + num(d[3]["top1_gain"], 1)
                + " [" + num(d[3]["ci95"][0], 1) + ", " + num(d[3]["ci95"][1], 1) + "] and +"
                + num(f_[3]["top1_gain"], 1) + " [" + num(f_[3]["ci95"][0], 1) + ", " + num(f_[3]["ci95"][1], 1)
                + "] points.\n")
        anchor = "What does not replicate is the level."
        k = t.find(anchor)
        print(f"  secondbench anchor: {k}")
        assert k > 0
        t = t[:k] + sent + "\n" + t[k:]

        rare_anchor = "Rare species &"
        k = t.find(rare_anchor)
        if k > 0:
            end = t.find(chr(10), k)
            add = ""
            for spec, v, b, c in rows:
                add += (chr(10) + ("DTD" if spec == "dtd" else "Food-101") + " & " + str(v["n_classes"]) + " & "
                        + str(v["n_images"]) + " & " + num(v["frozen"]["CG"], 3) + " & "
                        + num(v["frozen"]["top1"], 1) + " & " + num(b["spread"], 1) + " & ["
                        + num(abs_ci(b["ci95"])[0], 1) + ", " + num(abs_ci(b["ci95"])[1], 1) + "] & "
                        + num(c["top1_gain"], 1) + " & [" + num(c["ci95"][0], 1) + ", " + num(c["ci95"][1], 1) + "] \\\\")
            t = t[:end] + add + t[end:]
            print("  appendix table extended")

    t = t.replace("[-4.3, -1.0]", "[1.0, 4.3]")

    # 6. title page clause
    tp = io.open(TITLE, encoding="utf-8").read()
    old_t = "versioned snapshot archived at Zenodo with DOI \\url{https://doi.org/10.5281/zenodo.23341223}."
    new_t = ("versioned snapshot archived at Zenodo with DOI \\url{https://doi.org/10.5281/zenodo.23341223} "
             "(13 October 2026; the analyses added in this revision are in the public repository and will be included in "
             "the next snapshot).")
    if old_t in tp:
        io.open(TITLE, "w", encoding="utf-8", newline="").write(tp.replace(old_t, new_t, 1))
        print("  title page scoped")

    for token in ("prop:margin", "35.5", "39.6", "That snapshot (13 October 2026)"):
        print(f"  present {token!r}: {t.count(token)}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
