# -*- coding: utf-8 -*-
"""
P1 patch H: re-base the revision cover letter on the version the reviewers actually read.

The Desktop copy the operator supplied (C:\\Users\\hongr\\Desktop\\PR-D-26-10149.pdf) is the
Editorial Manager snapshot dated 24 July 2026 --- before both 14 August correction letters
and before the remediation. Its abstract therefore says "increases the Centroid Gap by 24%
and destroys zero-shot accuracy by 53.3%, while text-only LoRA limits the gap increase to
+0.079 and zero-shot degradation to 1.7%", and its introduction lists CIFAR-100 among the
zero-shot benchmarks. None of those values survive into the current manuscript, so the
corrections table must describe the 24 July baseline, not the August one.
"""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
P = os.path.join(ROOT, "paper", "cover_letter_revision.tex")
src = io.open(P, encoding="utf-8").read()

# ---------------------------------------------------------------- H1 paragraph
anchor = "\\vspace{6pt}\n\n\\textbf{Corrections and new evidence.}"
para = ("\\vspace{6pt}\n\n"
        "\\textbf{Which version this letter concerns.} The manuscript currently in Editorial "
        "Manager is the 24 July 2026 submission snapshot. Two correction letters dated "
        "14 August followed; where the table below says ``as submitted'' it refers to the "
        "version under review, and the corrected values are those in the accompanying "
        "revision, which also incorporates a full audit of the manuscript against its own "
        "archived results.\n\n"
        "\\textbf{Corrections and new evidence.}")
if anchor not in src:
    print("H1 anchor not found")
    sys.exit(1)
src = src.replace(anchor, para, 1)
print("ok   H1 version paragraph")

# ---------------------------------------------------------------- H2 zero-shot row
row2 = ("Zero-shot claims in the abstract & ``destroys zero-shot accuracy by 53.3\\%'' and "
        "``text-only LoRA limits the gap increase to +0.079 and zero-shot degradation to "
        "1.7\\%'', with CIFAR-100 listed as the third zero-shot benchmark & The abstraction "
        "was re-derived from the archived runs: on ImageNet-1K (full 50{,}000-image validation "
        "set, single template) the frozen model scores 59.28\\%, text-only 58.66\\% "
        "($-0.62$ points), both-position 59.67\\% ($+0.39$) and full fine-tuning 2.6\\% over "
        "three retrained seeds; DTD and Food101 stay within $\\pm0.8$ points. The benchmark "
        "label is ImageNet-1K, not CIFAR-100, and the abstract, Table 7 and its footnote now "
        "state the protocol. \\\\\n"
        "\\addlinespace\n")
anchor2 = "Zero-shot protocol & The 2026-08-14 letter reported"
if anchor2 not in src:
    print("H2 anchor not found")
    sys.exit(1)
src = src.replace(anchor2, row2 + anchor2, 1)
print("ok   H2 zero-shot row")

# ---------------------------------------------------------------- H3 re-frame
old3 = "Zero-shot protocol & The 2026-08-14 letter reported the ImageNet values as"
new3 = "ImageNet protocol (second pass) & The 2026-08-14 letter reported the ImageNet values as"
if old3 not in src:
    print("H3 anchor not found")
    sys.exit(1)
src = src.replace(old3, new3, 1)
print("ok   H3 re-frame")

old4 = "Change-score correlations & The 2026-08-14 letter corrected them to"
new4 = "Change-score correlations & As submitted the change-score correlations were $r=-0.042$ ($p=0.713$) and $r=+0.012$ ($p=0.915$) per the 2026-08-14 letter; on re-derivation they are"
if old4 not in src:
    print("H4 anchor not found")
    sys.exit(1)
src = src.replace(old4, new4, 1)
print("ok   H4 change-score row")

io.open(P, "w", encoding="utf-8", newline="").write(src)
print("PATCH H APPLIED")
