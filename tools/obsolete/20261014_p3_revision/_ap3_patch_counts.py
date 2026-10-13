# -*- coding: utf-8 -*-
"""ap3 sync patch 1: experiment counts (116->117, 278->279, 468->469) and the full-FT sd.

Every replacement is a literal string with an expected occurrence count; any mismatch makes the
script exit non-zero so nothing downstream runs on a half-applied patch.  No re.sub() is used for
the substitutions themselves (LaTeX backslashes must survive verbatim).

Sources:
  count 117          paper/sections/supplementary.tex:169 (printed Total) and the per-section
                     headings, re-checked with tools/_catalog_count_check.py
  full-FT sd 0.008   outputs/flickr30k_seeds/baseline_full_ft/seed{42,123,456,789,1024}/results.json
                     -> mean CG 1.0092, sd(ddof=1) 0.0084, delta vs 0.8184 = +0.1908
"""
import io
import sys

EDITS = [
    ('paper_ap3/sections/01_intro.tex',
     'a systematic 116-run characterization', 'a systematic 117-run characterization', 1),
    ('paper_ap3/sections/01_intro.tex',
     'are validated on 468 core runs plus 25 protocol-probe runs',
     'are validated on 469 core runs plus 25 protocol-probe runs', 1),
    ('paper_ap3/sections/04_mechanism.tex',
     'These experiments, spanning 116 runs,', 'These experiments, spanning 117 runs,', 1),
    ('paper_ap3/sections/04_mechanism.tex',
     'complete catalog of the 116 experiments', 'complete catalog of the 117 experiments', 1),
    ('paper_ap3/sections/04_mechanism.tex',
     r'$+0.191 \pm 0.007$', r'$+0.191 \pm 0.008$', 1),
    ('paper_ap3/sections/05_dynamics.tex',
     '278 dual-encoder experiments (116 mechanism runs plus 162 ODE fits)',
     '279 dual-encoder experiments (117 mechanism runs plus 162 ODE fits)', 1),
    ('paper_ap3/main.tex',
     '468 runs---278 dual-encoder runs', '469 runs---279 dual-encoder runs', 1),
]

failures = []
cache = {}
for path, old, new, want in EDITS:
    if path not in cache:
        cache[path] = io.open(path, encoding='utf-8').read()
    text = cache[path]
    got = text.count(old)
    if got != want:
        failures.append('%s: expected %d occurrence(s) of %r, found %d' % (path, want, old[:60], got))
        continue
    cache[path] = text.replace(old, new)
    print('OK  %-42s  %s' % (path.split('/')[-1], old[:58]))

if failures:
    print('')
    print('ABORTED - nothing written:')
    for f in failures:
        print('  - ' + f)
    sys.exit(1)

for path, text in cache.items():
    with io.open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)
    print('wrote %s' % path)

# post-conditions: the edited values are present and the stale ones are gone from the body text
import glob
import re
bodies = {}
for p in glob.glob('paper_ap3/*.tex') + glob.glob('paper_ap3/sections/*.tex'):
    bodies[p] = io.open(p, encoding='utf-8').read()
joined = '\n'.join(bodies.values())

checks = [
    ('117 occurrences (>=4)', joined.count('117') >= 4),
    ('279 dual-encoder present', '279 dual-encoder' in joined),
    ('469 runs present', '469 runs' in joined),
    ('+0.191 \\pm 0.008 present', r'$+0.191 \pm 0.008$' in joined),
    ('+0.191 \\pm 0.007 gone', r'$+0.191 \pm 0.007$' not in joined),
    ('no "116 runs" left', '116 runs' not in joined),
    ('no "116 experiments" left', '116 experiments' not in joined),
    ('no "278 dual-encoder" left', '278 dual-encoder' not in joined),
    ('no "468 runs" left', '468 runs' not in joined),
    ('no "468 core runs" left', '468 core runs' not in joined),
]
print('')
bad = 0
for name, ok in checks:
    print('  %-34s %s' % (name, 'PASS' if ok else 'FAIL'))
    if not ok:
        bad += 1
remaining = {p: len(re.findall(r'(?<![0-9.])116(?![0-9])', t)) for p, t in bodies.items()}
print('')
print('remaining standalone "116" tokens: %s' % {p.split("/")[-1]: n for p, n in remaining.items() if n})
sys.exit(1 if bad else 0)
