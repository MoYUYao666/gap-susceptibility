"""Measure the true baseline skip using the lineno line-number markers.

Each numbered line carries one number at the left margin, so the vertical
distance between consecutive line-number tokens IS the baseline skip.
Prints the median and the implied multiple of IEEEtran's 12pt unity
baselineskip (13.92pt).
"""
import re
import statistics
import subprocess
import sys

PDF = sys.argv[1]
PAGE = sys.argv[2] if len(sys.argv) > 2 else "3"
UNITY = 13.92  # IEEEtran 12pt nominal baselineskip

xml = subprocess.run(
    ["pdftotext", "-bbox", "-f", PAGE, "-l", PAGE, PDF, "-"],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
).stdout

words = re.findall(
    r'<word xMin="([0-9.]+)" yMin="([0-9.]+)" xMax="([0-9.]+)" yMax="([0-9.]+)">(\d+)</word>',
    xml,
)
if not words:
    print("no numeric words found")
    sys.exit(1)

xs = sorted(float(w[0]) for w in words)
left_edge = xs[0]
# line numbers sit at the far left; keep tokens within 12pt of the left edge
marks = [(float(w[1]), int(w[4])) for w in words if float(w[0]) < left_edge + 12]
marks.sort()

print(f"PDF={PDF} page={PAGE}")
print(f"line-number tokens found: {len(marks)}")
if len(marks) > 12:
    print(f"first few: {[m[1] for m in marks[:12]]}")

ys = [y for y, n in marks]
gaps = [round(b - a, 2) for a, b in zip(ys, ys[1:]) if 5 < (b - a) < 80]
if not gaps:
    print("no usable gaps")
    sys.exit(1)
med = statistics.median(gaps)
print(f"gaps: median={med:.2f}pt  min={min(gaps):.2f}  max={max(gaps):.2f}  n={len(gaps)}")
print(f"implied spacing multiple of unity baselineskip {UNITY}pt: {med/UNITY:.2f}x")
print("target: 2.00x for double spacing (JDE/JOE review format)")
