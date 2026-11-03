# -*- coding: utf-8 -*-
r"""Integrate the A23 margin-certificate negative control (evidence: docs/a23_margin_negative_control_paragraph.md).

The negative control is already in the working manuscript (`paper_a2/ext_partII_domains.tex:94-99`); this
replaces that sentence block with the stronger, fully-provenanced version: the validated operating point
(ImageNet-5k, eps=0.01, r=-0.996), the generic-CLIP saturation with its degenerate threshold, the adapted
encoders' weak correlations and the honest boundary statement.

    python tools/_p1587_integrate_a23_margin_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
TEX = "paper_a2/ext_partII_domains.tex"

OLD = """A margin-mass variant of the diagnostic was also tested as a potential scalar certificate, and it does
not replace the within-domain diagnostic: on a generic CLIP control the mass saturates ($M\\approx1$ at every
configuration, because the frozen accuracy is too low for small margins to separate rows), and on the two
adapted encoders (BioCLIP base and OceanCLIP) it correlates only weakly with accuracy across the same surgery
family ($r=-0.35$ and $-0.56$ at $\\varepsilon=0.05$) while a threshold fitted on one encoder fails on the other
(balanced accuracy $0.13$--$0.50$, chance $0.50$)."""

NEW = """The margin mass $M(\\varepsilon)$---the fraction of images whose true-class score exceeds its best
competitor by at most $2\\varepsilon$---was also tested as a potential scalar certificate, and it does not replace
the within-domain diagnostic. It is informative only at the resolution at which it was validated: on the
ImageNet-5k reference ($5{,}000$ images, CLIP ViT-B/32) the frozen top-1 margin has median $0.0063$, so
$M(0.01)=0.681$ still varies across configurations and tracks top-1 at $r=-0.996$, whereas at
$\\varepsilon=0.10$ it is identically $1.0$ in every archived configuration. On a generic-CLIP control over two
marine corpora (FathomNet-derived optical, $343$ images, $7$ classes; NKSID sonar, $1{,}783$ images, $7$ classes)
the mass is $1.0$ in all $14$ surgery configurations at $\\varepsilon\\in\\{0.05,0.10\\}$, so its correlation with
top-1 is undefined and a fitted threshold degenerates to chance (balanced accuracy $0.50$ in both directions); on
the two adapted encoders (BioCLIP base and OceanCLIP) the statistic is defined but weak ($r=-0.35$ and $-0.56$ at
$\\varepsilon=0.05$), and a threshold fitted on one encoder reaches balanced accuracy $0.125$ on the other against
a chance level of $0.50$. We therefore report the certificate as a negative control at this operating point and
claim no advantage from it; making it usable would require a domain-relative resolution evaluated at
$\\varepsilon\\approx0.01$ on the marine and sonar domains, which we have not performed."""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(TEX, encoding="utf-8").read()
    assert OLD in t, "A23 block not found"
    t2 = t.replace(OLD, NEW, 1)
    print("block replaced: %d -> %d chars" % (len(OLD), len(NEW)))
    if a.apply:
        io.open(TEX, "w", encoding="utf-8", newline="").write(t2)
        print("written", TEX)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())