# -*- coding: utf-8 -*-
"""Locate the exact subset definitions and check which count (43 or 49) each table metric uses."""
import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(r"D:\Realdesktop\Wan\Important\New")
led = json.loads((REPO / "outputs/analysis/ode_ledger.json").read_text(encoding="utf-8"))
runs = led["runs"]
sub = led["subsets"]

# 1) how the ledger builder defines the subsets
src = (REPO / "tools/_p1_ledger.py")
if src.is_file():
    t = src.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"lora_flickr|lora_coco|v1_trajectory|beta_pilot", t):
        line_no = t[:m.start()].count("\n") + 1
        line = t.splitlines()[line_no - 1].strip()
        print("ledger L%d: %s" % (line_no, line[:150]))
else:
    print("_p1_ledger.py missing")

# 2) R2 stats for the candidate samples
def stats(xs):
    xs = list(xs)
    if not xs:
        return None
    mean = sum(xs) / len(xs)
    sd = (sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5 if len(xs) > 1 else 0.0
    return {"n": len(xs), "mean": round(mean, 4), "sd": round(sd, 4)}

lora = [r for r in runs if r["family"] == "lora"]
print("\n=== R2 samples ===")
print("all lora (55):", stats(r["R2"] for r in lora))
for top in sorted(set(r["top"] for r in lora)):
    print("lora top=%-14s" % top, stats(r["R2"] for r in lora if r["top"] == top))
flickr_v1 = [r for r in lora if r["top"] == "v1_trajectory"]
flickr_all = [r for r in lora if r["top"] in ("v1_trajectory", "beta_pilot")]
print("lora flickr (43) :", stats(r["R2"] for r in flickr_v1))
print("lora flickr (49) :", stats(r["R2"] for r in flickr_all))
print("ledger subset lora_flickr:", sub["lora_flickr"])
print("ledger subset lora_coco  :", sub["lora_coco"])
print("\n=== alpha/beta means ===")
for name, sel in (("v1 43", flickr_v1), ("v1+beta 49", flickr_all)):
    a = sum(r["alpha"] for r in sel) / len(sel)
    b = sum(r["beta"] for r in sel) / len(sel)
    print("%-12s alpha=%.4f beta=%.4f n=%d" % (name, a, b, len(sel)))

# 3) dg_r1_reproducible.json: count Flickr30k LoRA entries with usable R1
for rel in ("outputs/analysis/dg_r1_reproducible.json", "outputs/analysis/flickr_rank.json"):
    p = REPO / rel
    if not p.is_file():
        print(rel, "MISSING")
        continue
    d = json.loads(p.read_text(encoding="utf-8"))
    print("\n==", rel, "| type:", type(d).__name__)
    if isinstance(d, dict):
        print("  keys:", list(d.keys())[:15])
        for k in list(d.keys())[:4]:
            print("   ", k, "->", json.dumps(d[k], ensure_ascii=False)[:220])
    elif isinstance(d, list):
        print("  len:", len(d), "| sample:", json.dumps(d[0], ensure_ascii=False)[:300])
