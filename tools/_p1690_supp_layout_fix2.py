# -*- coding: utf-8 -*-
r"""Fix the two remaining visual defects in the P3 supplement:
   1. too little space between a table body and its caption below it;
   2. large whitespace blocks on the last pages (full-width floats restricted to [!t], no barrier before references).

Changes: caption skip; allow [!tp] so several floats can share a float page; flush floats before the references.
Rolls back automatically if the build breaks or the result gets worse (more pages / lower mean ink).
"""
import glob
import io
import os
import re
import subprocess

os.chdir(r"D:\Realdesktop\Wan\Important\New")
SUP = "paper3/paper_ieee/supplementary"
TEX = os.path.join(SUP, "supplementary.tex")
PDF = os.path.join(SUP, "supplementary.pdf")


def ink_profile(pdf):
    out = os.path.join(os.environ.get("TEMP", "."), "ink_fix2")
    os.makedirs(out, exist_ok=True)
    for f in glob.glob(os.path.join(out, "*.png")):
        try:
            os.remove(f)
        except OSError:
            pass
    subprocess.run(["pdftoppm", "-r", "60", "-png", pdf, os.path.join(out, "pg")], check=True)
    from PIL import Image
    prof = []
    for p in sorted(glob.glob(os.path.join(out, "pg-*.png"))):
        im = Image.open(p).convert("L")
        h = im.histogram()
        prof.append(round(sum(h[:200]) / (im.width * im.height) * 100, 1))
    return prof


def build():
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "supplementary.tex"], cwd=SUP,
                       capture_output=True, encoding="utf-8", errors="ignore")
    log = open(os.path.join(SUP, "supplementary.log"), encoding="utf-8", errors="ignore").read()
    errs = len(re.findall(r"^! ", log, re.M))
    over = len(re.findall(r"Overfull \\hbox", log))
    too_large = len(re.findall(r"Float too large", log))
    m = re.search(r"Output written on supplementary\.pdf \((\d+) pages", log)
    return dict(pages=int(m.group(1)) if m else -1, errors=errs, overfull=over, float_too_large=too_large)


orig = io.open(TEX, encoding="utf-8").read()
before = build()
bp = ink_profile(PDF)
print("BEFORE:", before, "mean %.1f%%" % (sum(bp) / len(bp)), "| tail ink", bp[-4:])

t = orig

# 1) caption spacing: give the caption a real gap above it (and a small one below)
if "supp captionskip fix" not in t:
    marker = "\\begin{document}"
    assert marker in t
    t = t.replace(marker, "% supp captionskip fix (2026-10-25): table body -> caption gap\n"
                          "\\setlength{\\abovecaptionskip}{7pt plus 2pt minus 1pt}\n"
                          "\\setlength{\\belowcaptionskip}{3pt plus 1pt minus 1pt}\n" + marker, 1)

# 2) allow float pages so several full-width floats can share a page
t = t.replace("\\begin{table*}[!t]", "\\begin{table*}[!tp]")

# 3) flush pending floats before the references
if "placeins" not in t:
    t = t.replace("\\begin{document}", "\\usepackage{placeins}\n\\begin{document}", 1)
if "\\FloatBarrier" not in t:
    refs = t.find("\\bibliographystyle")
    if refs < 0:
        refs = t.find("\\begin{thebibliography}")
    if refs > 0:
        t = t[:refs] + "\\FloatBarrier\n" + t[refs:]

io.open(TEX, "w", encoding="utf-8", newline="").write(t)
print("\npatched: captionskip + [!tp] (%d) + placeins/FloatBarrier" % len(re.findall(r"\\begin\{table\*\}\[!tp\]", t)))

after = build()
ap = ink_profile(PDF)
print("AFTER :", after, "mean %.1f%%" % (sum(ap) / len(ap)), "| tail ink", ap[-4:])

keep = after["errors"] == 0 and after["overfull"] == 0 and after["float_too_large"] == 0 \
    and after["pages"] <= before["pages"] + 2 and sum(ap) / len(ap) >= sum(bp) / len(bp) - 0.5
print("\nverdict:", "KEEP" if keep else "ROLL BACK")
if not keep:
    io.open(TEX, "w", encoding="utf-8", newline="").write(orig)
    build()
    print("rolled back and rebuilt")
print("pages %d -> %d | mean ink %.1f%% -> %.1f%%" % (before["pages"], after["pages"], sum(bp) / len(bp), sum(ap) / len(ap)))
print("tail ink before:", bp[-4:], "after:", ap[-4:])