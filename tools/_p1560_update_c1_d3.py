# -*- coding: utf-8 -*-
r"""Update S33 (r=3/8 ten-seed extension) and S35 (multi-seed real-image sweep) with the cloud round-3 data."""
import glob
import io
import json
import os
import statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
bs = chr(92)


def delta(f):
    try:
        d = json.load(io.open(f, encoding="utf-8"))
        return d.get("delta_E")
    except Exception:
        return None


def blank_runs(rank):
    vals = []
    for f in glob.glob(os.path.join(EXP, "cloud_verify_r%d_s*.json" % rank)):
        n = os.path.basename(f)
        if "imgs" in n or "partial" in n or "_e1_" in n:
            continue
        v = delta(f)
        if v is not None:
            vals.append(v)
    return vals


rows = []
for r in range(3, 9):
    v = blank_runs(r)
    if not v:
        continue
    rows.append("%d & %d & %+.1f & %.1f & %+.1f & %+.1f %s" % (
        r, len(v), st.mean(v), st.stdev(v) if len(v) > 1 else 0.0, min(v), max(v), bs * 2))
print("crossing rows:", rows)

real = {}
for r in (4, 5, 6, 7, 8):
    for f in glob.glob(os.path.join(EXP, "cloud_verify_r%d_s*imgs_cap*.json" % r)):
        d = json.load(io.open(f, encoding="utf-8"))
        real[(r, d.get("seed", 42))] = d.get("delta_E")
real_rows = "\n".join("%d & %s & %+.1f %s" % (r, s, v, bs * 2) for (r, s), v in sorted(real.items()))
print("real rows:", real_rows.replace("\n", " | "))

t = io.open(SUPP, encoding="utf-8").read()
bsr = bs
# S33 table body
i = t.find("\\label{app:crossing10}")
m = t.rfind("\\begin{tabular}", 0, i)
e = t.find("\\end{tabular}", m)
table = ("\\begin{tabular}{@{}lrrrrr@{}}\n\\toprule\nrank & $n$ & mean & sd & min & max \\\\\n\\midrule\n"
         + "\n".join(rows) + "\n\\bottomrule\n")
t = t[:m] + table + t[e + len("\\end{tabular}"):]
old_cap = ("Every $r=4$/$r=5$ run is negative and every $r=6$/$r=7$ run is positive")
new_cap = ("Every run at $r=3,4,5$ is negative and every run at $r=6,7,8$ is positive")
if old_cap in t:
    t = t.replace(old_cap, new_cap, 1)
else:
    print("S33 caption phrase not found")
# S35 table body
j = t.find("\\label{app:realimage}")
m2 = t.rfind("\\begin{tabular}", 0, j)
e2 = t.find("\\end{tabular}", m2)
table2 = ("\\begin{tabular}{@{}lrr@{}}\n\\toprule\nrank & seed & $\\Delta E$ \\\\\n\\midrule\n"
          + real_rows + "\n\\bottomrule\n")
t = t[:m2] + table2 + t[e2 + len("\\end{tabular}"):]
old_cap2 = "Ranks 4--8 on the caption protocol with real image--caption pairs (20 samples, three epochs, seed 42)."
new_cap2 = ("Ranks 4--8 on the caption protocol with real image--caption pairs (20 samples, three epochs); "
            "$r=5$/$r=6$ are repeated across three seeds.")
if old_cap2 in t:
    t = t.replace(old_cap2, new_cap2, 1)
io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
print("S33/S35 updated")
