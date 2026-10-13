# -*- coding: utf-8 -*-
"""Regression gate for the P1 -> ap3 synchronisation: assert against the COMPILED PDF text.

Source-level assertions do not survive a rebuild (P1's earlier lesson: 11 stale values lived on in
the PDF after the sources were fixed), so this reads paper_ap3/_ap3pdf.txt, which is produced by
pdftotext from the built PDF, and checks both directions:

  MUST-BE-PRESENT : the corrected values the P1 remediation established
  MUST-BE-ABSENT  : the stale forms that remediation removed, plus the withdrawn claims

Run it after every recompile:  python tools/_ap3_sync_check.py

Note on wrapping: pdftotext breaks lines, so phrases are matched on short fragments; numbers are
matched with an optional surrounding space to survive line breaks inside a number.
"""
import io
import re
import sys

TXT = 'paper_ap3/_ap3pdf.txt'

MUST_PRESENT = [
    ('117 experiment count', r'117'),
    ('279 dual-encoder', r'279 dual-encoder'),
    ('469 core runs', r'469 core runs'),
    ('full-FT sd = 0.008', r'0\.191 \u00b1 0\.008'),
    ('full-FT CG increase 23.3%', r'23\.3%'),
    ('DG/R@1 r = -0.714', r'0\.714'),
    ('CG/R@1 r = -0.594', r'0\.594'),
    ('partial r = -0.581', r'0\.581'),
    ('DG<->CG +0.945', r'\+0\.945'),
    ('CG-delta +0.190', r'\+0\.190'),
    ('cluster bootstrap 12 clusters', r'12\s+clusters'),
    ('noise claim withdrawn', r'withdrawn'),
    ('GSNR 1.4x', r'1\.4'),
    ('Adapter d=16 +0.237', r'\+0\.237'),
    ('Adapter d=32 +0.103', r'\+0\.103'),
    ('Adapter d=64 +0.064', r'\+0\.064'),
    ('ImageNet protocol 50,000', r'50,000-image'),
    ('zero-shot within 0.8 points', r'within 0\.8 percentage points'),
    # the sentence spans a page boundary in the built PDF (the page number lands inside the phrase),
    # so the assertion uses the fragment that survives extraction
    ('batch-size convention', r'128 for the five-seed runs'),
    ('g_v = 0 in the adapter subspace', r'adapter subspace'),
]

MUST_BE_ABSENT = [
    ('old experiment count 116 runs', r'116 runs'),
    ('old catalogue count', r'116 experiments'),
    ('old dual-encoder total 278', r'278 dual-encoder'),
    ('old grand total 468', r'468 runs'),
    ('withdrawn DG r = -0.827', r'0\.827'),
    ('withdrawn partial r = -0.807', r'0\.807'),
    ('withdrawn CG r = -0.683', r'0\.683'),
    ('unreproducible n=81 subset', r'n\s*=\s*81'),
    ('withdrawn "outperforming CG"', r'outperforming CG'),
    ('superseded H1 24%', r'by 24%'),
    ('zero-shot 0.9 points claim', r'within 0\.9 percentage points'),
    ('weight-matrix effective rank', r'weight update matrix'),
    ('blanket batch-128 claim', r'All experiments use batch size 128'),
    ('old Adapter claim', r'reduces gap more effectively'),
]

def main():
    try:
        text = io.open(TXT, encoding='utf-8', errors='replace').read()
    except FileNotFoundError:
        print('ABORT: %s missing - run pdftotext on the built PDF first' % TXT)
        return 2
    flat = re.sub(r'\s+', ' ', text)
    bad = 0
    print('MUST BE PRESENT')
    for name, pat in MUST_PRESENT:
        ok = re.search(pat, flat) is not None
        print('  %-34s %s' % (name, 'ok' if ok else 'MISSING'))
        bad += 0 if ok else 1
    print('')
    print('MUST BE ABSENT')
    for name, pat in MUST_BE_ABSENT:
        hit = re.search(pat, flat) is not None
        print('  %-34s %s' % (name, 'STALE VALUE STILL PRESENT' if hit else 'ok'))
        bad += 1 if hit else 0
    print('')
    print('RESULT: %d problem(s)' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
