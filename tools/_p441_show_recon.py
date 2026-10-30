#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p441_show_recon.py -- inspect the _p440 recon product (provenance check)."""
import json, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "outputs", "analysis", "p3_stats_recon.json"), encoding="utf-8") as f:
    D = json.load(f)

print("=== runs: dE by (src_file, batch, rank) ===")
grp = collections.defaultdict(list)
for r in D["runs"]:
    grp[(r["src_file"].split("/")[-1], r["batch"], r["rank"])].append(r)
for k in sorted(grp, key=lambda x: (x[0], x[1], x[2] if x[2] is not None else -1)):
    rr = sorted(grp[k], key=lambda z: (z["seed"] if z["seed"] is not None else -1))
    ds = ["%s:%s" % (z["seed"], ("NaN" if z["dE"] is None else round(z["dE"], 1))) for z in rr]
    print("  %-24s %-24s r=%-4s  %s" % (k[0], k[1], k[2], "  ".join(ds)))

print("\n=== version-record scan: key-level hits ===")
for h in D["version_record_scan"]["key_hits"]:
    print(" ", h["path"], "->", h["keys"])

print("\n=== version-record scan: text-level hits (P3-related only) ===")
for h in D["version_record_scan"]["text_hits"]:
    if h["path"].startswith("paper3") or "p3" in h["path"].lower():
        print(" ", h["path"], h["n_matches"], h["samples"][:5])

print("\ntotal text-level hits:", len(D["version_record_scan"]["text_hits"]))
print("gamma artefacts:", len(D["gamma_artefacts"]))
for g in D["gamma_artefacts"]:
    print("  ", g)
