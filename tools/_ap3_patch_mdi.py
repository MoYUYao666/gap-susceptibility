# -*- coding: utf-8 -*-
"""ap3 sync patch 7: the literature MDI numbers get a checked citation and a layer qualifier.

The two values ap3 quotes were the last unexplained entries in the numeric-provenance list.  They
are not our measurements: the sentence attributes them to Wu et al., and they are indeed that
paper's Table 1 (arXiv:2508.10552, "When Language Overrules: Revealing Text Dominance in Multimodal
Large Language Models", Huyu Wu, Meng Tang, Xinhan Zheng, Haiyun Jiang):

    LLaVA-1.5-7B   image/MMMU_Pro: early 1.58   middle 10.23   late 17.37
    Qwen2.5-VL-7B  image/MMMU_Pro: early 2.26   middle 21.12   late 33.10

so 10.23 is the middle-layer value and 33.10 the late-layer one.  ap3 qualified only the Qwen value;
the patch adds the stage to the LLaVA value and replaces the placeholder author list "Wu, Y. and
others" with the verified names and an arXiv-style entry.
"""
import io
import sys

TEX = 'paper_ap3/sections/06_crossarch.tex'
BIB = 'paper_ap3/refs.bib'

EDITS = [
    (TEX,
     'report LLaVA\'s Modality\nDominance Index (MDI) of $10.23$, while Qwen2.5-VL\'s MDI is $33.10$ at\n'
     'deeper layers',
     'report LLaVA\'s Modality\nDominance Index (MDI) of $10.23$ at the middle layers, while\n'
     'Qwen2.5-VL\'s MDI reaches $33.10$ at the later layers', 1),
    (BIB,
     '@article{wu2025language,\n'
     '  title={When Language Overrules: Revealing Text Dominance in Multimodal Large Language Models},\n'
     '  author={Wu, Y. and others},\n'
     '  journal={arXiv:2508.10552},\n'
     '  year={2025}\n'
     '}',
     '@article{wu2025language,\n'
     '  title={When Language Overrules: Revealing Text Dominance in Multimodal Large Language Models},\n'
     '  author={Wu, Huyu and Tang, Meng and Zheng, Xinhan and Jiang, Haiyun},\n'
     '  journal={arXiv preprint arXiv:2508.10552},\n'
     '  year={2025},\n'
     '  doi={10.48550/arXiv.2508.10552},\n'
     '}', 1),
]

cache, failures = {}, []
for path, old, new, want in EDITS:
    if path not in cache:
        cache[path] = io.open(path, encoding='utf-8').read()
    got = cache[path].count(old)
    print('%-38s occurrences=%d' % (path.split('/')[-1], got))
    if got != want:
        failures.append('%s: expected %d, found %d for %r' % (path, want, got, old[:60]))
        continue
    cache[path] = cache[path].replace(old, new)

if failures:
    print('ABORTED - nothing written:')
    for f in failures:
        print('  - ' + f)
    sys.exit(1)

for path, text in cache.items():
    io.open(path, 'w', encoding='utf-8', newline='').write(text)
    print('wrote %s' % path)

checks = [
    ('layer qualifier added', 'at the middle layers' in cache[TEX]),
    ('real author list', 'author={Wu, Huyu and Tang, Meng and Zheng, Xinhan and Jiang, Haiyun}' in cache[BIB]),
    ('no placeholder authors left', 'Wu, Y. and others' not in cache[BIB]),
    ('doi present', '10.48550/arXiv.2508.10552' in cache[BIB]),
]
bad = 0
for name, ok in checks:
    print('  %-30s %s' % (name, 'PASS' if ok else 'FAIL'))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)
