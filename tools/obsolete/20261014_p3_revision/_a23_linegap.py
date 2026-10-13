"""Measure the actual baseline skip in a PDF, to verify double spacing.
Uses pdftotext -bbox-layout and the y-coordinates of consecutive text lines."""
import re
import subprocess
import sys
from collections import Counter

PDF = sys.argv[1] if len(sys.argv) > 1 else "main_ieee.pdf"
PAGE = sys.argv[2] if len(sys.argv) > 2 else "3"

xml = subprocess.run(
    ["pdftotext", "-bbox-layout", "-f", PAGE, "-l", PAGE, PDF, "-"],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
).stdout

# <line ... yMin="..." yMax="..."> ... </line>
lines = re.findall(r'<line[^>]*yMin="([0-9.]+)"[^>]*yMax="([0-9.]+)"[^>]*>', xml)
if not lines:
    print("no <line> elements found; dumping first 400 chars of xml")
    print(xml[:400])
    sys.exit(1)

tops = sorted(float(a) for a, b in lines)
gaps = []
for p, q in zip(tops, tops[1:]):
    d = round(q - p, 1)
    if 0 < d < 60:          # ignore paragraph/page jumps
        gaps.append(d)

cnt = Counter(gaps)
print(f"PDF={PDF} page={PAGE}")
print(f"text lines on page: {len(lines)}")
print("most common vertical gaps between consecutive text lines (points):")
for gap, n in cnt.most_common(6):
    print(f"   {gap:6.1f} pt   x{n}")
print()
print("Interpretation: 12pt single spacing ~ 14-15pt; double spacing ~ 24-29pt.")
