# -*- coding: utf-8 -*-
"""Compare the seeded noise runs with the original single draw, and locate the 2.6x claim."""
import glob
import io
import json
import os
import re

ROOT = r"D:\Realdesktop\Wan\Important\New"


def load(rel):
    with io.open(os.path.join(ROOT, rel.replace("/", os.sep)), encoding="utf-8-sig") as fh:
        return json.load(fh)


agg = load("outputs/noise_sensitivity_seeds.json")
print("seeded runs: %d seeds %s" % (len(agg["runs"]), agg["seeds"]))
print("baseline R@1 per seed: %s" % [round(r["baseline_R1"], 4) for r in agg["runs"]])
print("\n%-8s %-20s %-20s %-10s %s" % ("sigma", "vision drop %", "text drop %", "ratio", "vision>text"))
for k, v in agg["per_sigma"].items():
    print("%-8s %-20s %-20s %-10s %d/%d" % (
        k, "%.2f +/- %.2f" % (v["vision_drop_mean"], v["vision_drop_sd"]),
        "%.2f +/- %.2f" % (v["text_drop_mean"], v["text_drop_sd"]),
        v["ratio"] if v["ratio"] is not None else "-",
        v["n_seeds_vision_gt_text"], len(agg["runs"])))

pre = load("outputs/noise_sensitivity_pre_seed.json")
print("\noriginal single draw (unseeded):")
print("  baseline R@1 = %.4f" % pre["baseline_R1"])
for name in ("vision", "text"):
    print("  %-7s %s" % (name, [(s, round(r, 4), round(p, 2)) for s, r, p in pre[name]]))

print("\nfiles:")
for p in sorted(glob.glob(os.path.join(ROOT, "outputs", "noise_seeds", "*.json"))):
    print("  " + os.path.basename(p))

print("\n'2.6' occurrences in the manuscript sources:")
for base, _d, files in os.walk(os.path.join(ROOT, "paper", "sections")):
    for f in sorted(files):
        if not f.endswith(".tex"):
            continue
        for i, line in enumerate(io.open(os.path.join(base, f), encoding="utf-8"), 1):
            if re.search(r"2\.6", line):
                print("  %s:%d  %s" % (f, i, line.strip()[:150]))
