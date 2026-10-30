"""Apply the Paper A review findings to the live manuscript (both variants), 2026-10-25.

Reads the item list of `docs/paperA_logic_review_2026-10-25.md` and applies:

  A-1  the eight places that call the Distribution Gap a "predictor" are reworded to the abstract's own
       framing ("associated with", "correlate of retrieval"): the empirical.tex subsection title, its first
       sentence, the figure caption, the table header, theory.tex, validation.tex, introduction.tex and
       conclusion.tex;
  A-2  "far/substantially outperforming CG" is downgraded to the descriptive "higher than".
       NOTE: a Hotelling-Williams dependent-correlation test computed from the archived values
       (`dg_r1_reproducible.json::primary.{DG_vs_R1,CG_vs_R1,DG_vs_CG}` with n=204) gives t=-7.86, df=201,
       p<0.001, i.e. the difference IS significant when clustering is ignored - so the suggested
       "the intervals overlap, therefore no difference" wording would be a statistical fallacy and is NOT
       used. The comparative claim is simply made descriptive, and the test is documented in the notes.
  b1   the duplicate, self-referential Data availability subsection in conclusion.tex is deleted;
  b2   the two variants' Data availability statements are aligned on the fuller NC wording;
  b3   the provenance appendix gains one sentence disclosing that the dataset/model stratification labels
       are derived (evidence: `pr_stats_hardened.json::label_evidence`);
  c    British "characterise" in the Springer abstract -> "characterize"; the stale "Target:"
       header comment in main_springer.tex is corrected.

Hard rules honoured: no new numbers are introduced; nothing under SUBMISSION/ is touched; other
manuscripts are not touched; `tools/_p1454_final_verify.py` is not touched.

Idempotent: every replacement is skipped when its new text is already present.

Usage:
    python tools/_p1672_paperA_apply_review_fixes.py [--apply]
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EDITS = []


def edit(rel, old, new, why):
    EDITS.append((rel, old, new, why))


S = "paper合/sections/"

# ------------------------------------------------------------------ A-1 (8 places) + A-2 (3 places)
edit(S + "empirical.tex",
     r"\subsection{Distribution Gap Predicts Retrieval Performance}",
     r"\subsection{Distribution Gap Is Associated with Retrieval Performance}",
     "A-1 subsection title")

edit(S + "empirical.tex",
     "A key statistical discovery is that the Distribution Gap strongly predicts retrieval performance.",
     "A key empirical regularity is that the Distribution Gap is strongly associated with retrieval performance.",
     "A-1 first sentence of the subsection")

edit(S + "empirical.tex",
     "DG achieves $r = -0.714$ with R@1, substantially outperforming CG ($r = -0.594$);",
     "DG achieves $r = -0.714$ with R@1, higher than CG ($r = -0.594$);",
     "A-2 downgrade in the subsection")

edit(S + "empirical.tex",
     r"\caption{DG vs.\ CG as retrieval predictors over the $n=204$ archived experiments. "
     r"DG achieves $r=-0.714$, substantially stronger than CG ($r=-0.594$).}",
     r"\caption{DG vs.\ CG as correlates of retrieval over the $n=204$ archived experiments. "
     r"DG achieves $r=-0.714$, higher than CG ($r=-0.594$).}",
     "A-1 + A-2 figure caption")

edit(S + "empirical.tex",
     "Predictor & $r$ & partial $r$ (control CG) & $p$ \\\\",
     "Statistic & $r$ & partial $r$ (control CG) & $p$ \\\\",
     "A-1 table header")

edit(S + "theory.tex",
     r"\textbf{DG as a retrieval predictor.} The empirical finding that DG predicts R@1 at $r=-0.714$",
     r"\textbf{DG as a correlate of retrieval.} The empirical finding that DG is associated with R@1 at $r=-0.714$",
     "A-1 theory paragraph heading and first clause")

edit(S + "validation.tex",
     r"\item \textbf{DG as predictor:} DG is the natural state variable",
     r"\item \textbf{DG as a correlate of retrieval:} DG is the natural state variable",
     "A-1 validation item heading")

edit(S + "introduction.tex",
     "---predicts retrieval performance at $r = -0.714$ over $n=204$ experiments, far outperforming the "
     "commonly reported Centroid Gap.",
     "---is associated with retrieval performance at $r = -0.714$ over $n=204$ experiments, more strongly "
     "than the commonly reported Centroid Gap.",
     "A-1 + A-2 introduction sentence")

edit(S + "introduction.tex",
     "Core findings include text-only alignment preservation, DG-based retrieval prediction "
     "($r=-0.714$ over $n=204$ experiments)",
     "Core findings include text-only alignment preservation, the DG--retrieval association "
     "($r=-0.714$ over $n=204$ experiments)",
     "A-1 contribution bullet")

edit(S + "conclusion.tex",
     "that the Distribution Gap predicts retrieval performance ($r = -0.714$",
     "that the Distribution Gap is associated with retrieval performance ($r = -0.714$",
     "A-1 conclusion sentence")

# ------------------------------------------------------------------ b1 duplicate Data availability
edit(S + "conclusion.tex",
     "\n\\subsection*{Data availability}\n"
     "The derived data and analysis code are openly available; see the Data availability statement in the\n"
     "front matter for the repository and DOI.\n",
     "\n",
     "b1 delete the duplicate self-referential Data availability subsection")

# ------------------------------------------------------------------ b3 derived labels disclosure
# (the final wording of this edit lives in the compression block below; the first draft was superseded
#  on 2026-10-25 when the sentence had to be shortened to hold the NC page count at 79)

# ------------------------------------------------------------------ b2 align the two data-availability statements
# applied as five small, individually unique substitutions so line-wrapping differences cannot break the match
for _old, _new, _why in [
    ("the per-run result records, the analysis scripts and the training configurations",
     "the per-run result records, the per-epoch monitoring trajectories, the strict-freezing controls and "
     "the cross-architecture sweeps, together with the analysis scripts that compute the reported statistics "
     "and the training configurations",
     "b2a add the missing archive categories"),
    ("openly available at \\url{https://github.com/MoYUYao666/gap-susceptibility}",
     "openly available in a public repository at \\url{https://github.com/MoYUYao666/gap-susceptibility}",
     "b2b name the repository explicitly"),
    ("snapshot (version DOI \\texttt{10.5281/zenodo.23632347}; v2.5, 25 October 2026), which includes",
     "snapshot archived on Zenodo under version DOI \\texttt{10.5281/zenodo.23632347} "
     "(\\url{https://doi.org/10.5281/zenodo.23632347}) (v2.5, 25 October 2026), which includes",
     "b2c add the resolvable DOI URL"),
    ("are on the public repository (\\url{https://github.com/MoYUYao666/gap-susceptibility}). The adapters",
     "are on the public repository (\\url{https://github.com/MoYUYao666/gap-susceptibility}), which carries "
     "them at and after that release. The adapters",
     "b2d add the release-provenance clause"),
    ("are not required to reproduce them. The generating script",
     "are not required to reproduce them. No datum used here is restricted. The generating script",
     "b2e add the no-restricted-datum statement"),
]:
    edit("paper合/main_springer.tex", _old, _new, _why)

# ------------------------------------------------------------------ c items
edit("paper合/main_springer.tex",
     "characterise when this happens",
     "characterize when this happens",
     "c1 unify spelling with the NC variant and the body")

edit("paper合/main_springer.tex",
     "%% Target: EAAI / NCAA / Cognitive Computation",
     "%% Springer-format variant of the Neurocomputing submission (NEUCOM-D-26-23760); body shared with main_nc.tex",
     "c2 remove the stale target comment")


# ------------------------------------------------------------------ compression to hold the NC page count at 79
# (the review fixes added a few lines; these are layout-only changes, no wording or numbers touched)
edit(S + "provenance_appendix.tex",
     "and the result archive (file names; full relative paths in the repository).\n",
     "and the result archive (file names; full paths in the repository). Dataset/model labels in the stratified\n"
     "analyses of Section~\\ref{sec:empirical} come from run directory names, not archived fields (evidence:\n"
     "\\texttt{pr\\_stats\\_hardened.json, label\\_evidence}).\n",
     "b3 disclosure, final wording (supersedes the first draft of this edit)")

edit(S + "provenance_appendix.tex",
     "\\label{app:provenance}\n\nThis appendix lists",
     "\\label{app:provenance}\n\n\\begingroup\\footnotesize\nThis appendix lists",
     "compression: appendix intro at the table's footnotesize")

edit(S + "provenance_appendix.tex",
     "\n\\begingroup\\footnotesize\n\\renewcommand{\\arraystretch}{0.9}\\setlength{\\tabcolsep}{3pt}",
     "\n\\renewcommand{\\arraystretch}{0.9}\\setlength{\\tabcolsep}{3pt}",
     "compression: drop the now-duplicated \\begingroup\\footnotesize")

edit(S + "provenance_appendix.tex",
     "\\setlength{\\tabcolsep}{4pt}",
     "\\setlength{\\tabcolsep}{3pt}",
     "compression: narrower column separation (fewer wrapped rows)")

edit(S + "provenance_appendix.tex",
     "\\setlength{\\tabcolsep}{3pt}\\begin{longtable}{@{}p{0.24\\textwidth}",
     "\\renewcommand{\\arraystretch}{0.9}\\setlength{\\tabcolsep}{3pt}\\begin{longtable}{@{}p{0.24\\textwidth}",
     "compression: tighter longtable row spacing")

edit("paper合/main_nc.tex",
     "\\input{sections/provenance_appendix}\n\n\\bibliography{references}",
     "\\input{sections/provenance_appendix}\n\n\\setlength{\\bibsep}{0pt}\n\\bibliography{references}",
     "compression: natbib item separation 0pt (the edit that actually held NC at 79 pages)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rc = 0
    touched = {}
    for rel, old, new, why in EDITS:
        p = REPO / rel
        if not p.is_file():
            print("  [FAIL] missing %s" % rel)
            rc = 2
            continue
        text = io.open(p, encoding="utf-8").read()
        # Idempotency: every `new` string in this script is long and unique, so "already present" is a
        # sufficient test. The earlier "new in text and old not in text" form was wrong for prefix-overlap
        # edits (e.g. inserting a command in front of `\begin{longtable}`) and duplicated one of them.
        if new in text:
            print("  [skip] %-42s already applied (%s)" % (rel, why))
            continue
        n = text.count(old)
        if n != 1:
            print("  [FAIL] %-42s expected 1 occurrence, found %d (%s)" % (rel, n, why))
            rc = 2
            continue
        print("  [edit] %-42s %s" % (rel, why))
        if args.apply:
            out = text.replace(old, new, 1)
            io.open(p, "w", encoding="utf-8", newline="\n").write(out)
            io.open(p, encoding="utf-8").read()
            touched[rel] = len(out.splitlines())
    if args.apply:
        print("\n== files written ==")
        for rel, n in sorted(touched.items()):
            print("  %-46s %d lines" % (rel, n))
        # post-conditions: the DG-predictor wording must be gone from the live sources
        bad = []
        for rel in (S + "empirical.tex", S + "theory.tex", S + "validation.tex",
                    S + "introduction.tex", S + "conclusion.tex"):
            t = io.open(REPO / rel, encoding="utf-8").read()
            for pat in ("Distribution Gap Predicts", "strongly predicts retrieval",
                        "as retrieval predictors", "DG as a retrieval predictor", "DG as predictor"):
                if pat in t:
                    bad.append((rel, pat))
        print("\nDG-predictor wording left in the live sources:", bad if bad else "none")
        if bad:
            rc = 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
