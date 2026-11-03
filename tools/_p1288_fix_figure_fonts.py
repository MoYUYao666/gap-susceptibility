# -*- coding: utf-8 -*-
"""Force Times New Roman (text) and STIX (math) in every figure-producing script, and regenerate.

The operator's standing rule: all text inside generated figures must be Times New Roman. The two figures still set in
DejaVu Sans are fig5_matched_gap (tools/_p1210_figure_matched_gap.py) and the graphical abstract
(tools/_p1276_graphical_abstract.py). This patch inserts a shared style block into both scripts; they are then re-run and
re-cropped.

    python tools/_p1288_fix_figure_fonts.py [--apply] [--regenerate]
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = r"D:\Anaconda\envs\pytorch\python.exe"

STYLE = '''
# --- figure style: Times New Roman text, STIX math (project standing rule, 2026-10-18) ---
import matplotlib as _mpl
_mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
})
'''

TARGETS = [
    "tools/_p1210_figure_matched_gap.py",
    "tools/_p1276_graphical_abstract.py",
]


def patch(path: str) -> bool:
    p = os.path.join(REPO, path)
    t = io.open(p, encoding="utf-8").read()
    if "project standing rule, 2026-10-18" in t:
        print(f"  {path}: style already present")
        return False
    anchor = "import matplotlib"
    i = t.find(anchor)
    assert i > 0, path
    j = t.find("\n", i)
    t = t[:j + 1] + STYLE + t[j + 1:]
    io.open(p, "w", encoding="utf-8", newline="").write(t)
    print(f"  {path}: style inserted")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--regenerate", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    for path in TARGETS:
        patch(path)

    if a.regenerate:
        for cmd in (["tools/_p1210_figure_matched_gap.py", "--apply"],
                    ["tools/_p1276_graphical_abstract.py", "--apply"]):
            r = subprocess.run([PY] + cmd, cwd=REPO, capture_output=True, text=True, timeout=1200)
            print(f"  ran {cmd[0]}: rc={r.returncode}")
            print("   ", (r.stdout or "").strip().splitlines()[-1] if r.stdout.strip() else "")
            if r.returncode != 0:
                print("   !! stderr:", (r.stderr or "")[-400:])
                return 1
        # re-crop the two regenerated figures
        fig = os.path.join(REPO, "paper_a1", "figures")
        for name in ("fig5_matched_gap", "graphical_abstract"):
            src = os.path.join(fig, name + ".pdf")
            dst = os.path.join(fig, name + "_crop.pdf")
            r = subprocess.run(["pdfcrop", src, dst], cwd=fig, capture_output=True, text=True, timeout=600)
            print(f"  recrop {name}: rc={r.returncode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
