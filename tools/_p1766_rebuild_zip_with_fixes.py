# -*- coding: utf-8 -*-
r"""Apply the two hyperref fixes to the assembled LaTeX source tree and repackage the zip.

The package builder writes its own root.tex, and the earlier patch to the builder did not reach the assembled file
(the zip still carried the old root), so the fix is applied directly to the staged source here, then the tree is
recompiled twice, the log is checked for warnings, and the zip is rewritten from that same tree.
"""
import glob
import io
import os
import re
import shutil
import subprocess
import zipfile

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join("SUBMISSION", "PaperA_MachineLearning", "LaTeXSource")
BUILD = os.path.join("SUBMISSION", "PaperA_MachineLearning", "_src_build")
ZIP = os.path.join("SUBMISSION", "PaperA_MachineLearning", "LaTeXSource.zip")

root_p = os.path.join(SRC, "root.tex")
root = io.open(root_p, encoding="utf-8").read()
if "\\usepackage{bookmark}" not in root:
    i = root.index("\\documentclass")
    j = root.index("\n", i)
    root = root[: j + 1] + "\\usepackage{bookmark}\\hypersetup{bookmarksdepth=3}\n" + root[j + 1:]
    io.open(root_p, "w", encoding="utf-8", newline="\n").write(root)
    print("root.tex: bookmark loaded after documentclass")

wrapped = 0
for p in glob.glob(os.path.join(SRC, "*.tex")):
    t = io.open(p, encoding="utf-8").read()
    def one_seg(m):
        maths = m.group(1)
        plain = re.sub(r"[^0-9A-Za-z]+", " ", maths).strip() or "formula"
        return "\\texorpdfstring{$%s$}{%s}" % (maths, plain)
    def wrap(m):
        return "\\" + m.group(1) + "{" + re.sub(r"\$([^$]*)\$", one_seg, m.group(2)) + "}"
    t2 = re.sub(r"\\(section|subsection|subsubsection|paragraph)\{([^{}]*\$[^{}]*)\}", wrap, t)
    if t2 != t:
        io.open(p, "w", encoding="utf-8", newline="\n").write(t2)
        wrapped += 1
print("files with headings wrapped:", wrapped)

if os.path.isdir(BUILD):
    shutil.rmtree(BUILD)
shutil.copytree(SRC, BUILD)
for _ in range(2):
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "root.tex"],
                       cwd=BUILD, capture_output=True, text=True)
    if r.returncode != 0:
        print("compile failed:", r.stdout[-1200:])
        raise SystemExit(1)
log = io.open(os.path.join(BUILD, "root.log"), encoding="utf-8", errors="replace").read()
warns = [ln for ln in log.splitlines() if "Warning" in ln]
print("compile warnings:", len(warns))
for w in warns[:5]:
    print("  ", w[:120])

with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    for name in sorted(os.listdir(SRC)):
        full = os.path.join(SRC, name)
        if os.path.isfile(full):
            z.write(full, name)
print("zip rewritten:", ZIP, os.path.getsize(ZIP), "bytes")

z = zipfile.ZipFile(ZIP)
rootz = z.read("root.tex").decode("utf-8", "replace")
print("verify -> bookmark:", "\\usepackage{bookmark}" in rootz,
      "| depth3:", "bookmarksdepth=3" in rootz,
      "| texorpdfstring in zip:", any("\\texorpdfstring" in z.read(n).decode("utf-8", "replace")
                                     for n in z.namelist() if n.endswith(".tex")))
print("entries:", len(z.namelist()))
