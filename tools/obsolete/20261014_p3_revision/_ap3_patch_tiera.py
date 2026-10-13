# -*- coding: utf-8 -*-
"""ap3 Tier-A completion: merge the one block that was never merged, correct one interval, retire
the staging file.

Background.  paper_ap3/sections/_TIER_A_PENDING.tex is a *staging* file listing eleven Tier-A blocks
with @@ placeholders.  Almost all of them were merged into 06_crossarch.tex / 07_discussion.tex in
an earlier pass; this round verified the merged versions against the archives they declare:

  A2 gating      table rows -18.0/+93.5/+111.5, -76.5/+20.0/+96.5, -3.5/+110.0/+113.5 and
                 -34.5/-45.5/-11.0 == outputs/tier_a_analysis.json crossing_by_condition  (exact)
  A3 cross-batch six batches x 16 samples, vision argmax 6/6, projector the smallest non-trivial
                 block, spreads 21,977 [8,166,35,789] CV 60% / 24.6 CV 27% / 2.35 CV 12%, modal
                 allocation [65,63,8] at 10% == outputs/llava_gamma_batches.json          (exact)
  A6 asymmetry   -19.5 vs -109.5, -85.5, -128.0, +1700.0 == tier_a_analysis.json A6_projector (exact)
  A1 invariance  adapter-based orderings identical (pairwise Spearman 1.000), normalised coupling
                 magnitudes 0.740-1.357, BitFit 16-30x == clip_peft_gamma_ordering.json   (exact)
  A5 policies    -95.7 / +269.2 / +196.3 / +255.3 / +258.0 with Welch p 8.9e-4 / 0.032 / 0.023 /
                 2.3e-4 == tier_a_analysis.json A5_policies                                (exact)

What this patch does:
  1. merges A10 (gradient saturation), the only block that never made it in, with the value the
     archive actually gives: Spearman 0.40, p 0.60 -- i.e. the probe does NOT resolve the question,
     so it is reported as unresolved rather than as support;
  2. corrects the batch-to-batch Spearman interval from 0.93-0.96 to 0.93-1.00 (the archive has
     pairs at 1.000);
  3. leaves the staging file to be retired separately, since every block in it is now in the text.

STATUS: DONE, kept for the audit trail.  Both edits landed on 2026-09-20 (commit `ad80b9f`) and were
verified afterwards: `06_crossarch.tex` contains the A10 paragraph exactly once and carries the
corrected interval; the staging file was retired into `paper_ap3/_superseded_2026/` and its fill-in
markers were resolved on 2026-09-23 (`tools/_ap3_superseded_marker_cleanup.py`).

Do not re-run this against the current tree: its A10 insertion anchor no longer matches, so it
aborts in the guard and writes nothing -- which is the intended safe failure, not a bug.
"""
import io
import os
import sys

F = 'paper_ap3/sections/06_crossarch.tex'

A10 = (
    '\\paragraph{Gradient saturation across rank.} Per-epoch route-wise gradient norms are logged\n'
    'for every run, so the saturation reading of Section~\\ref{sec:special} can be tested\n'
    'directly. Across the reference-protocol sweep the vision-path gradient norm does not vary\n'
    'monotonically with rank: the per-rank means are $28.0$, $20.8$, $22.9$ and $65.2$ at\n'
    '$r = 4, 5, 6$ and $8$, and the rank correlation is not significant (Spearman\n'
    '$\\rho = 0.40$, $p = 0.60$). This probe therefore does not resolve the question: the rank\n'
    'dependence of the visual-path gradient norm is neither confirmed nor excluded at this\n'
    'sample size, and Effective Rank Saturation remains an assumption of the theory rather than\n'
    'a finding of these experiments (Limitation~7).\n'
    '\n'
)

EDITS = [
    # correct the interval to what the archive holds
    ('the pairwise\nSpearman between batches is $0.93$--$0.96$.',
     'the pairwise\nSpearman between batches is $0.93$--$1.00$', 1),
]

cache = {F: io.open(F, encoding='utf-8').read()}
fail = []
for old, new, want in EDITS:
    got = cache[F].count(old)
    print('%-52s occurrences=%d' % (old[:50].replace('\n', ' '), got))
    if got != want:
        fail.append(old[:60])
        continue
    cache[F] = cache[F].replace(old, new)

# insert A10 immediately before the language-only-probe subsection
anchor = '\\subsection{Gradient-Conditioning Probe: Language-Only Loss'
n = cache[F].count(anchor)
print('%-52s occurrences=%d' % ('A10 insertion anchor', n))
if n != 1:
    fail.append('anchor')

if fail:
    print('ABORTED - nothing written: %s' % fail)
    sys.exit(1)

cache[F] = cache[F].replace(anchor, A10 + anchor)
io.open(F, 'w', encoding='utf-8', newline='').write(cache[F])
print('wrote %s' % F)

out = io.open(F, encoding='utf-8').read()
checks = [
    ('A10 paragraph present', 'Gradient saturation across rank' in out),
    ('A10 reports the archive value', '\\rho = 0.40$, $p = 0.60$' in out),
    ('A10 states it is unresolved', 'does not resolve the question' in out),
    ('A3 interval corrected', '$0.93$--$1.00$' in out),
    ('old interval gone', '$0.93$--$0.96$' not in out),
    ('no placeholder left in 06_crossarch', '@@@' not in out),
]
bad = 0
for name, ok in checks:
    print('  %-38s %s' % (name, 'PASS' if ok else 'FAIL'))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)
