# -*- coding: utf-8 -*-
"""Inventory A1's archives: which families, perturbations and checkpoints exist, and what the bias-field model needs."""
import glob
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def peek(rel):
    p = os.path.join(REPO, rel)
    if not os.path.exists(p):
        print(f"  {rel}: MISSING")
        return
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception as e:
        print(f"  {rel}: unreadable ({type(e).__name__})")
        return
    print(f"  {rel}")
    if isinstance(d, dict):
        for k, v in list(d.items())[:8]:
            if isinstance(v, (list, dict)):
                print(f"     {k:<26} {type(v).__name__}({len(v)})")
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    print(f"       item keys: {list(v[0])[:10]}")
                elif isinstance(v, dict):
                    print(f"       child keys: {list(v)[:8]}")
            else:
                print(f"     {k:<26} {str(v)[:70]}")


for rel in ("outputs/a1_full_results.json", "outputs/a1_crossmodel_results.json",
            "outputs/a1_baseline_metrics.json", "outputs/a1_h_bootstrap.json",
            "outputs/a1_dinov2_surgery.json"):
    peek(rel)
    print()

print("=== scripts mentioning a bias field / class-dependent bias ===")
hits = []
for f in glob.glob(os.path.join(REPO, "tools", "*.py")):
    s = io.open(f, encoding="utf-8", errors="ignore").read()
    low = s.lower()
    if ("bias" in low and ("field" in low or "class-dependent" in low or "class_dependent" in low)) or "a1_bias" in low:
        hits.append(os.path.basename(f))
print("  candidates:", len(hits))
for h in hits[:12]:
    print("   ", h)

print("\n=== A1 outputs whose name suggests the bias-field fit ===")
for f in sorted(glob.glob(os.path.join(REPO, "outputs", "a1*.json"))):
    print("   ", os.path.basename(f), os.path.getsize(f), "B")
