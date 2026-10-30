# -*- coding: utf-8 -*-
"""Settle the 49 vs 43 question from the archives: count Flickr30k LoRA runs by every plausible
filter in ode_ledger.json and look for 43 in the other candidate archives."""
import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(r"D:\Realdesktop\Wan\Important\New")
led = json.loads((REPO / "outputs/analysis/ode_ledger.json").read_text(encoding="utf-8"))
runs = led["runs"]
print("ledger runs:", len(runs), "| top-level n_runs_total:", led.get("n_runs_total"))
print("run field names:", sorted(runs[0].keys()))
print("\nfirst run:", json.dumps(runs[0], ensure_ascii=False)[:400])

print("\n=== subsets ===")
for k, v in led.get("subsets", {}).items():
    print("  %-14s n=%-4s keys=%s" % (k, v.get("n"), sorted(v.keys())[:10]))

print("\n=== run families/datasets ===")
print(Counter((r.get("family"), r.get("dataset")) for r in runs))
print("\n=== LoRA Flickr30k breakdown ===")
lora = [r for r in runs if r.get("family") == "lora" and "flickr" in str(r.get("dataset", "")).lower()]
print("lora+flickr runs:", len(lora))
for field in ("top", "arm", "position", "mode", "seed", "rank", "has_r1", "r1", "usable", "status"):
    vals = Counter(str(r.get(field)) for r in lora)
    if len(vals) <= 12:
        print("  %-10s %s" % (field, dict(vals)))
non_none_r2 = [r for r in lora if r.get("r_squared") is not None]
print("  r_squared non-null:", len(non_none_r2))
print("  sample lora run:", json.dumps(lora[0], ensure_ascii=False)[:400])

print("\n=== candidate archives ===")
for rel in ("outputs/analysis/dg_r1_reproducible.json",
            "outputs/analysis/flickr_rank.json",
            "outputs/analysis/paperA_lora_vs_fullft.json"):
    p = REPO / rel
    if not p.is_file():
        print(rel, "MISSING")
        continue
    d = json.loads(p.read_text(encoding="utf-8"))
    txt = json.dumps(d, ensure_ascii=False)
    print("\n--", rel, "| top keys:", list(d.keys())[:12] if isinstance(d, dict) else type(d).__name__,
          "| len:", len(d) if hasattr(d, "__len__") else "")
    for pat in ("49", "43"):
        hits = len(re.findall(r"\b" + pat + r"\b", txt))
        print("   occurrences of %s: %d" % (pat, hits))
    if isinstance(d, dict):
        for k, v in list(d.items())[:8]:
            print("   ", k, "->", (json.dumps(v, ensure_ascii=False)[:160] if not isinstance(v, (int, float, str)) else v))
