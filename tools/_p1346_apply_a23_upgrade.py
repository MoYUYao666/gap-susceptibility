# -*- coding: utf-8 -*-
r"""A23 upgrade edits: threshold transfer + symmetric-surgery paragraph, dead-label references, PDF metadata, citation.

    python tools/_p1346_apply_a23_upgrade.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAINS = os.path.join(REPO, "paper_a2", "ext_partII_domains.tex")
THEORY = os.path.join(REPO, "paper_a2", "ext_partI_theory.tex")
MAIN = os.path.join(REPO, "paper_a2", "main_ieee.tex")

PARA = r"""

\textbf{Thresholds transfer within a domain, not across domains or models.} A gap threshold fitted on one
domain---separating checkpoints whose accuracy is above the domain median from those below---reaches a
balanced accuracy of $0.83$ in domain, but the same threshold scores $0.25$--$0.67$ on the other archived
domain--model arms (chance $0.50$). The pattern holds in both directions and is consistent with the
task-sensitivity argument of Section~\ref{sec:spectrum}: the gap is a within-geometry diagnostic, and its
absolute scale is set by the domain's own embedding space. The archive also contains both surgery directions
(image-side translations and a text-side translation, $\lambda{=}1.0$), so the asymmetry reported here is not
a one-sided artefact. A margin-mass variant of the diagnostic was tested on a generic CLIP control on the same
marine and sonar data and saturated ($M\approx1$ at every configuration, because the frozen model's accuracy
is too low for small margins to separate rows); we report it as a negative control in
\texttt{outputs/\allowbreak analysis/\allowbreak a23\_certificate\_control.json} and do not read it into the main
claim. Cross-modal distillation between acoustic and visual streams has been used to transfer supervision
under such gaps~\cite{kim2026acoustic}; the present diagnostic differs in that it reads the frozen geometry
rather than distilling a student.
"""

REF_SENTENCE = r""" The section closes with Corollary~\ref{cor:nocg} (what the bounds do not contain) and
Corollary~\ref{cor:orth} (orthogonal families), and Corollary~\ref{cor:twofield} states the two-field
decomposition used for the measured self-field.
"""

META = r"""\usepackage[hidelinks]{hyperref}
\hypersetup{hidelinks,%
  pdftitle={Alignment health across perception modalities: a gap-surgery diagnostic for marine vision and acoustic sonar models},%
  pdfauthor={Hongrui Wan}}""" 

BIBITEM = r"""
\bibitem{kim2026acoustic}
Y. Kim, C. Han, S. Gatungay, S. Guhathakurta, A. Lerch, ``Cross-modal knowledge distillation for acoustic pedestrian detection,'' arXiv:2609.31785, 2026.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ops = []

    d = io.open(DOMAINS, encoding="utf-8").read()
    if "Thresholds transfer within a domain" not in d:
        d = d.rstrip("\n") + PARA
        ops.append(("domains paragraph", DOMAINS, d))
    t = io.open(THEORY, encoding="utf-8").read()
    if "The section closes with Corollary~\\ref{cor:nocg}" not in t:
        anchor = "\\subsection{Theory stack summary}"
        assert t.count(anchor) == 1, t.count(anchor)
        t = t.replace(anchor, REF_SENTENCE.strip() + "\n\n" + anchor, 1)
        ops.append(("theory references", THEORY, t))
    m = io.open(MAIN, encoding="utf-8").read()
    if "pdftitle={Alignment health across perception modalities" not in m:
        old = "\\usepackage[hidelinks]{hyperref}"
        assert m.count(old) == 1, m.count(old)
        m = m.replace(old, META, 1)
        if "kim2026acoustic" not in m:
            anchor = "\\begin{thebibliography}{99}"
            assert m.count(anchor) == 1
            m = m.replace(anchor, anchor + BIBITEM, 1)
        ops.append(("metadata + bibliography", MAIN, m))
    print(f"  edits pending: {len(ops)}")
    for name, path, _ in ops:
        print("   -", name, "->", os.path.relpath(path, REPO))
    if not a.apply:
        print("  (dry run)")
        return 0
    for _, path, content in ops:
        io.open(path, "w", encoding="utf-8", newline="").write(content)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
