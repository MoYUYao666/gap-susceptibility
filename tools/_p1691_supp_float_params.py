# -*- coding: utf-8 -*-
r"""Try the standard float-density parameters so multiple floats can share a page, and measure the tail whitespace."""
import glob
import io
import os
import re
import subprocess

os.chdir(r"D:\Realdesktop\Wan\Important\New")
SUP = "paper3/paper_ieee/supplementary"
TEX = os.path.join(SUP, "supplementary.tex")
PDF = os.path.join(SUP, "supplementary.pdf")

PARAMS = r"""% float-density fix (2026-10-25): let several floats share a page instead of leaving half-empty pages
\renewcommand{\topfraction}{0.92}
\renewcommand{\bottomfraction}{0.85}
\renewcommand{\textfraction}{0.08}
\renewcommand{\floatpagefraction}{0.72}
\renewcommand{\dbltopfraction}{0.92}
\renewcommand{\dblfloatpagefraction}{0.72}
\setcounter{topnumber}{3}
\setcounter{bottomnumber}{2}
\setcounter{totalnumber}{4}
\setcounter{dbltopnumber}{3}
"""


def ink_profile(pdf):
    out = os.path.join(os.environ.get("TEMP", "."), "ink_fix3")
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
    m = re.search(r"Output written on supplementary\.pdf \((\d+) pages", log)
    return dict(pages=int(m.group(1)) if m else -1,
                errors=len(re.findall(r"^! ", log, re.M)),
                overfull=len(re.findall(r"Overfull \\hbox", log)),
                float_too_large=len(re.findall(r"Float too large", log)))


def tailwaste(prof, k=5):
    return round(sum(100 - v for v in prof[-k:]) / k, 1)


orig = io.open(TEX, encoding="utf-8").read()
assert "float-density fix" not in orig, "already applied"
t = orig
marker = "\\begin{document}"
t = t.replace(marker, PARAMS + marker, 1)
io.open(TEX, "w", encoding="utf-8", newline="").write(t)

before_p = ink_profile(PDF)   # current build's profile (previous state, already compiled)
after = build()
after_p = ink_profile(PDF)
print("AFTER:", after)
print("pages:", len(after_p), "| mean ink %.1f%%" % (sum(after_p) / len(after_p)), "| tail:", after_p[-5:])
print("tail waste (100-ink): %.1f  (5 pages)" % tailwaste(after_p))
keep = after["errors"] == 0 and after["overfull"] == 0 and after["float_too_large"] == 0 and len(after_p) <= 24
print("verdict:", "KEEP" if keep else "ROLL BACK")
if not keep:
    io.open(TEX, "w", encoding="utf-8", newline="").write(orig)
    build()
    print("rolled back")