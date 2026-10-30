# -*- coding: utf-8 -*-
r"""Update the A23 evaluation-size numbers after the stratified rerun (67/134/268/536/full)."""
import io
import json

tex = "paper_a2/main_ieee.tex"
d = json.load(io.open("outputs/analysis/a23_neval_sensitivity.json", encoding="utf-8"))
b, o = d["models"]["bioclip"], d["models"]["oceanclip"]
order = ["67", "134", "268", "536", "None"]
bv = [b[k]["r_tau"] for k in order]
ov = [o[k]["r_tau"] for k in order]


def f(x):
    return ("%.2f" % x) if x >= 0 else ("$%.2f$" % x)


t = io.open(tex, encoding="utf-8").read()

old1 = ("Calibration also has a sample-size floor: subsampling the 67-class marine evaluation set, the "
        "$\\tau$--accuracy correlation is unstable at 32--64 images (Pearson $r$ between $-0.64$ and $0.48$ across the two "
        "encoders) and only stabilises with the full split ($0.61$--$0.83$; "
        "\\texttt{outputs/\\allowbreak analysis/\\allowbreak a23\\_neval\\_sensitivity.json}), so tripwire levels fitted on "
        "fewer than a hundred evaluation images are indicative only.")
new1 = ("Calibration also has a sample-size floor: subsampling the 67-class marine evaluation set, the "
        "$\\tau$--accuracy correlation is unstable at 67--134 images (Pearson $r$ from $-0.64$ to $0.52$ across the two "
        "encoders) and only becomes reliable at 268 images and above ($0.27$--$0.91$; the full split gives "
        "$0.61$--$0.83$; \\texttt{outputs/\\allowbreak analysis/\\allowbreak a23\\_neval\\_sensitivity.json}), so tripwire "
        "levels fitted on fewer than about 270 evaluation images are indicative only.")
assert t.count(old1) == 1
t = t.replace(old1, new1, 1)

old2 = ("The $\\tau$--accuracy correlation is unstable below roughly a hundred images and stabilises at the full\n"
        "split, so tripwire levels fitted on fewer than a hundred evaluation images are indicative only "
        "(Table~\\ref{tab:neval}).")
new2 = ("The $\\tau$--accuracy correlation is unstable at 67--134 images and becomes reliable from 268 images on, so "
        "tripwire levels fitted on fewer than about 270 evaluation images are indicative only "
        "(Table~\\ref{tab:neval}).")
assert t.count(old2) == 1
t = t.replace(old2, new2, 1)

old3 = ("encoder & $n{=}32$ & $n{=}64$ & $n{=}128$ & $n{=}256$ & full \\\\\n"
        "\\midrule\n"
        "BioCLIP & 0.48 & 0.21 & 0.91 & 0.89 & 0.83 \\\\\n"
        "OceanCLIP & $-0.64$ & 0.79 & $-0.26$ & 0.06 & 0.61 \\\\")
new3 = ("encoder & $n{=}67$ & $n{=}134$ & $n{=}268$ & $n{=}536$ & full \\\\\n"
        "\\midrule\n"
        "BioCLIP & %s & %s & %s & %s & %s \\\\\n"
        "OceanCLIP & %s & %s & %s & %s & %s \\\\"
        % (f(bv[0]), f(bv[1]), f(bv[2]), f(bv[3]), f(bv[4]),
           f(ov[0]), f(ov[1]), f(ov[2]), f(ov[3]), f(ov[4])))
assert t.count(old3) == 1
t = t.replace(old3, new3, 1)

io.open(tex, "w", encoding="utf-8", newline="").write(t)
print("A23 neval text/table updated:", [round(x, 2) for x in bv], [round(x, 2) for x in ov])
