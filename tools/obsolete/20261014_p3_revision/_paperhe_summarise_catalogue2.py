# -*- coding: utf-8 -*-
"""paper合 overlap fix, part 1b: replace the reprinted catalogue with a corrected summary.

What the parse found.  paper合/sections/supplement.tex reproduces P1's tab:full_experiments row for
row, and it is the *pre-remediation* version: it totals 116 experiments (P1's is 117 after the
section that declared seven while listing eight was corrected), its section XII is still headed
"Causal Evidence" (P1 renamed it "Mechanism Probes"), its section XIII declares 7 while listing 9
rows (P1 is 8 and 8), and its Adapter rows still carry the withdrawn own-baseline convention.

What this does.  Replaces the whole longtable with a section-level summary carrying P1's verified
counts -- re-checked this session with tools/_catalog_count_check.py, whose thirteen headings sum to
117 -- and names the released catalogue as the place to find the rows.  No per-run value from the
stale table survives, so the old-convention Adapter figures cannot leak through it.

Counts (paper/sections/supplementary.tex, verified): I 30, II 7, III 8, IV 7, V 3, VI 16, VII 20,
VIII 4, IX 5, X 4, XI 2, XII 3, XIII 8 = 117.
"""
import io
import re
import sys

F = 'paper合/sections/supplement.tex'

SECTIONS = [
    ('I. LoRA Core (Flickr30k)', 30),
    ('II. Adapter (Flickr30k)', 7),
    ('III. COCO Cross-Dataset', 8),
    ('IV. BLIP-1 Cross-Architecture', 7),
    ('V. ViT-L Cross-Model', 3),
    ('VI. Route C/D/E Enhanced Strategies', 16),
    ('VII. 5-Seed Statistical Validation', 20),
    ('VIII. ImageNet Zero-Shot', 4),
    ('IX. ViT-B Layered Fine-Tuning', 5),
    ('X. ViT-L Layered Fine-Tuning', 4),
    ('XI. Adapter Layered Fine-Tuning', 2),
    ('XII. Mechanism Probes', 3),
    ('XIII. Zero-Shot Generalization and SigLIP', 8),
]
assert sum(n for _, n in SECTIONS) == 117, 'section counts must sum to 117'

src = io.open(F, encoding='utf-8').read()
lines = src.splitlines()
start = next(i for i, l in enumerate(lines) if '\\begin{longtable}' in l)
end = next(i for i, l in enumerate(lines) if i > start and '\\end{longtable}' in l)
print('replacing longtable at lines %d-%d' % (start + 1, end + 1))

body = ['\\toprule',
        'Catalogue section & Experiments \\\\',
        '\\midrule']
for name, n in SECTIONS:
    body.append('%s & %d \\\\' % (name, n))
body += ['\\midrule',
         '\\textbf{Total} & \\textbf{117} \\\\',
         '\\bottomrule']

new_table = ['\\begin{longtable}{lc}',
             '\\caption{Experiment catalogue by section. The per-run rows, configurations and '
             'metrics of all 117 experiments are released with the analysis code; this table gives '
             'the distribution over the thirteen sections.} \\\\']
new_table += ['\\endfirsthead', '\\endhead'] + body + ['\\label{tab:catalogue_summary}',
                                                       '\\end{longtable}']

out = lines[:start] + new_table + lines[end + 1:]
new_src = '\n'.join(out)
# the sentence that introduced the reprinted catalogue must now point at the release
new_src = re.sub(r'(?i)(Table~\\ref\{tab:catalogue_summary\}[^.]*\.)',
                 r'\\1', new_src)
io.open(F, 'w', encoding='utf-8', newline='').write(new_src)
print('wrote %s' % F)

check = io.open(F, encoding='utf-8').read()
problems = []
if '\\begin{longtable}{lc}' not in check:
    problems.append('summary table missing')
if '\\textbf{117}' not in check:
    problems.append('total not 117')
if 'Causal Evidence' in check:
    problems.append('old section XII name still present')
for token in ('adapter\\_d64\\_text', 'rq1\\_rank4'):
    if token in check:
        problems.append('per-run row still present: %s' % token)
print('checks: %s' % ('; '.join(problems) if problems else 'all pass'))
sys.exit(1 if problems else 0)
