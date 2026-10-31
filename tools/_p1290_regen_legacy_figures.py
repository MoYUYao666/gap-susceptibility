# -*- coding: utf-8 -*-
"""Patch the two legacy A1 figure generators with the Times New Roman style block and regenerate.

fig1-fig4 were embedded as Type 3 fonts (the scripts set the family but not the PDF font type). Inserting the shared
style block (fonttype 42 = TrueType) makes them CID-TrueType, which is what publishers expect.

    python tools/_p1290_regen_legacy_figures.py [--apply] [--regenerate]
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = r"D:\Anaconda\envs\pytorch\python.exe"
TEX = r"D:\texlive\2025\bin\windows"

STYLE = '''
# --- figure style: Times New Roman text, STIX math, TrueType embedding (project standing rule) ---
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

TARGETS = ["tools/clip_a1_figures.py", "tools/clip_a1_fig4.py"]


def patch(path: str) -> None:
    p = os.path.join(REPO, path)
    t = io.open(p, encoding="utf-8").read()
    if "TrueType embedding (project standing rule)" in t:
        print(f"  {path}: already patched")
        return
    i = t.find("import matplotlib")
    assert i > 0, path
    j = t.find("\n", i)
    io.open(p, "w", encoding="utf-8", newline="").write(t[:j + 1] + STYLE + t[j + 1:])
    print(f"  {path}: style inserted")


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
        for script in TARGETS:
            r = subprocess.run([PY, script], cwd=REPO, capture_output=True, text=True, timeout=900)
            print(f"  ran {script}: rc={r.returncode}")
            out = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
            for line in out[-3:]:
                print("    ", line[:120])
        env = dict(os.environ)
        env["PATH"] = TEX + os.pathsep + env.get("PATH", "")
        for name in ("fig1_lambda", "fig2_tau_top1", "fig3_trajectory", "fig4_spectrum"):
            src = os.path.join(REPO, "paper_a1", "figures", name + ".pdf")
            dst = os.path.join(REPO, "paper_a1", "figures", name + "_crop.pdf")
            r = subprocess.run([os.path.join(TEX, "pdfcrop.exe"), src, dst], capture_output=True, text=True, timeout=600, env=env)
            print(f"  crop {name}: rc={r.returncode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
