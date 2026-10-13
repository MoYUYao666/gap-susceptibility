# -*- coding: utf-8 -*-
"""Patch the two figure scripts so each figure is also written as a vector PDF.

The manuscripts now include figures/figN_*.pdf instead of the 300-dpi PNGs, because
Elsevier's artwork table judges bitmapped line art at a much higher pixel count than
our PNGs carry.  Re-rendering the same matplotlib figure straight to PDF gives a
vector figure with no resolution ceiling.

The PNG call is left untouched so the two outputs stay in step; the PDF call is
appended immediately after it."""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = [('tools/clip_a1_figures.py', 3), ('tools/clip_a1_fig4.py', 1)]

PAT = re.compile(r"(fig\.savefig\(\s*'paper_a1/figures/(fig\d_[A-Za-z0-9_]+)\.png'(?:\s*,\s*dpi=\d+)?\s*\))")

failed = False
for rel, expected in TARGETS:
    path = os.path.join(ROOT, rel)
    with io.open(path, encoding='utf-8') as f:
        src = f.read()
    found = PAT.findall(src)
    names = [m[1] for m in found]
    if len(found) != expected:
        print('ABORT %s: expected %d savefig call(s), found %d %s' % (rel, expected, len(found), names))
        failed = True
        continue
    if 'savefig' in src and '.pdf' in src and 'figures/' + names[0] + '.pdf' in src:
        print('SKIP %s: already patched (%s)' % (rel, ', '.join(names)))
        continue
    out = PAT.sub(lambda m: "%s; fig.savefig('paper_a1/figures/%s.pdf')" % (m.group(1), m.group(2)), src)
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(out)
    print('PATCHED %s -> PDF also emitted for: %s' % (rel, ', '.join(names)))

sys.exit(1 if failed else 0)
