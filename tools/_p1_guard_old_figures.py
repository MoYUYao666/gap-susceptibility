# -*- coding: utf-8 -*-
"""
Guard the superseded figure generators.

paper/generate_figures.py and paper/scripts/generate_figures.py contain the selectors that
produced the defective figures found in the audit: fig1 took the first *alphabetical*
gap_history match (so COCO curves landed under a Flickr30k seed band), fig2 hard-coded
"n = 81" over a 17-30 point scatter and drew r from a correlations.json whose subset is
unreconstructible, fig3 plotted the Adapter bars against each run's own post-injection
baseline, fig5 labelled a text-only run as "Both-LoRA", and fig7 showed the superseded
correlations.  All five are now produced by dedicated scripts.  Re-running the old
generators would silently restore the defects, so each file gets a header naming the
replacements.  Idempotent: the marker header is only inserted once.
"""
import io
import os

ROOT = r"D:\Realdesktop\Wan\Important\New"
MARK = "% SUPERSEDED FIGURE GENERATORS"
HEADER = """% SUPERSEDED FIGURE GENERATORS -- do not re-run this file for the figures listed below.
% The audit (docs/P1_ADVERSARIAL_REVIEW.md, docs/P1_REMEDIATION_LOG.md) found defects in
% what this script produced, and each replacement now lives in its own script:
%   fig1  -> paper/scripts/plot_fig1_single_dataset.py   (was: alphabetical first match,
%            so COCO curves were drawn under a Flickr30k five-seed band)
%   fig2  -> paper/scripts/plot_fig2_reproducible.py     (was: title "n = 81" over a
%            17-30 point scatter, r read from an unreconstructible n=81 subset)
%   fig3  -> paper/scripts/plot_fig3_crossval.py         (was: Adapter bars measured from
%            each run's own post-injection baseline, not from the frozen model)
%   fig5  -> paper/scripts/plot_fig5_dges.py             (was: a text-only run labelled
%            "Both-LoRA"; the experiment script defines it as text-only, alpha=4)
%   fig7  -> paper/scripts/plot_fig7_correlations.py     (was: the superseded n=81 values)
% Running this file would overwrite the corrected figures.
"""

for rel in ["paper/generate_figures.py", "paper/scripts/generate_figures.py"]:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    src = io.open(p, encoding="utf-8").read()
    if MARK in src:
        print("already guarded: %s" % rel)
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(HEADER + src)
    print("guarded: %s" % rel)
