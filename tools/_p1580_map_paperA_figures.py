# -*- coding: utf-8 -*-
"""Map the Paper A figures that embed Type 3 fonts to their generating scripts."""
import glob
import io
import os
import re
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

STEMS = ["fig1", "fig1_ode_fits", "fig2", "fig2_v5_falsification", "fig3", "fig4",
         "fig4_effective_rank", "fig8a_rank_delta", "fig8b_budget", "fig8c_vision_untouched",
         "fig9a_noise_sweep", "fig9b_sigma0_control", "fig9c_ratio", "fig10_layered_ft",
         "fig12_zeroshot_more", "fig14_adapter_layered", "fig15_stratified_dg_r1"]


def type3(path):
    out = subprocess.run(["pdffonts", path], capture_output=True, text=True).stdout
    return sum(1 for l in out.splitlines()[2:] if "Type 3" in l)


bad = {}
for s in STEMS:
    p = os.path.join("paper合", "figures", s + ".pdf")
    if os.path.exists(p) and type3(p):
        bad[s] = p
print("figures with Type 3:", len(bad))

scripts = glob.glob("tools/*.py") + glob.glob("paper合/*.py") + glob.glob("exp/*.py")
for stem in sorted(bad):
    hits = []
    for sc in scripts:
        t = io.open(sc, encoding="utf-8", errors="ignore").read()
        if stem not in t:
            continue
        if not re.search(r"savefig|\bsave\(", t):
            continue
        line = next((l.strip() for l in t.splitlines() if stem in l), "")
        hits.append((os.path.basename(sc), line[:110]))
    print("\n== %s -> %d candidate(s)" % (stem, len(hits)))
    for n, l in hits[:6]:
        print("   ", n, "|", l)