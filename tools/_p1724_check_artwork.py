# -*- coding: utf-8 -*-
r"""Programmatic pre-check of Paper A's 18 artwork files: text bounding boxes versus the page box,
fonts (Times/STIX CID TrueType, no Type 3), page count and page size. Flags text that touches or
crosses the page edge, which is what "the figure looks broken" usually means.
"""
import glob
import os
import re
import subprocess

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ART = sorted(glob.glob("SUBMISSION/PaperA_MachineLearning/Artwork/*.pdf"))
print("artwork files:", len(ART))

from pypdf import PdfReader


def bbox_stats(path):
    r = PdfReader(path)
    pg = r.pages[0]
    mb = pg.mediabox
    x0, y0, x1, y1 = float(mb.left), float(mb.bottom), float(mb.right), float(mb.top)
    xs, ys = [], []
    flags = {"out": 0, "edge": 0}

    def visitor(text, cm, tm, font_dict, font_size):
        if not text.strip():
            return
        # approximate glyph box: text matrix translation plus a nominal advance
        tx = tm[4]
        ty = tm[5]
        size = abs(font_size or 10)
        w = 0.5 * size * len(text.strip())
        bx0, bx1 = tx, tx + w
        by0, by1 = ty - 0.25 * size, ty + 0.75 * size
        xs.extend([bx0, bx1])
        ys.extend([by0, by1])
        if bx1 > x1 + 2 or by1 > y1 + 2 or bx0 < x0 - 2 or by0 < y0 - 2:
            flags["out"] += 1
        elif bx1 > x1 - 3 or by1 > y1 - 3 or bx0 < x0 + 3 or by0 < y0 + 3:
            flags["edge"] += 1

    try:
        pg.extract_text(visitor_text=visitor)
    except Exception as e:
        return (x0, y0, x1, y1), None, flags, str(e)
    if not xs:
        return (x0, y0, x1, y1), None, flags, "no text"
    return (x0, y0, x1, y1), (min(xs), min(ys), max(xs), max(ys)), flags, ""


def fonts(path):
    out = subprocess.run(["pdffonts", path], capture_output=True, encoding="utf-8", errors="ignore").stdout
    names = []
    for line in out.splitlines()[2:]:
        if line.strip():
            names.append(line.split()[0])
    banned = [n for n in names if re.search(r"CMR|CMBX|CMTI|CMSY|CMMI|DejaVu|Arial|Helvetica", n)]
    type3 = "Type 3" in out
    return names, banned, type3


problems = []
for p in ART:
    (mb, tb, flags, err) = bbox_stats(p)
    w, h = mb[2] - mb[0], mb[3] - mb[1]
    names, banned, type3 = fonts(p)
    n = len(PdfReader(p).pages)
    status = "OK"
    if flags["out"]:
        status = "TEXT CROSSES EDGE (%d runs)" % flags["out"]
        problems.append((os.path.basename(p), status))
    elif flags["edge"]:
        status = "text within 3pt of edge (%d)" % flags["edge"]
    if type3:
        status += " | TYPE3"
        problems.append((os.path.basename(p), "Type 3 font"))
    if banned:
        status += " | NON-TIMES: " + ",".join(sorted(set(banned))[:2])
        problems.append((os.path.basename(p), "non-Times font"))
    print("%-26s p=%d box=%dx%d %s" % (os.path.basename(p), n, round(w), round(h), status))

print()
print("PROBLEMS:", problems if problems else "none")
