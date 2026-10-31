# -*- coding: utf-8 -*-
"""Inventory every gradient/Γ archive, to see what a Paper A novelty increment could be built on."""
import glob
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def show(rel, keys_of_interest=("Gamma_v", "Gamma_t", "Gamma_vision", "Gamma_text",
                                 "norm_g_vision", "norm_g_text", "cos_phi_v", "cos_phi_t")):
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
    def walk(o, prefix=""):
        if isinstance(o, dict):
            hits = {k: v for k, v in o.items() if any(x in k for x in keys_of_interest)}
            if hits:
                print(f"     {prefix}: " + ", ".join(
                    f"{k}={v:.4f}" if isinstance(v, (int, float)) else f"{k}={str(v)[:24]}" for k, v in hits.items()))
            for k, v in o.items():
                if isinstance(v, dict):
                    walk(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(o, list):
            for i, v in enumerate(o[:3]):
                if isinstance(v, dict):
                    walk(v, f"{prefix}[{i}]")
    walk(d)


for rel in ("outputs/theory/encoder_side/encoder_side.json",
            "outputs/analysis/gamma_vlm.json",
            "outputs/analysis/gamma_predictive.json",
            "outputs/theory/siglip/siglip_frozen.json",
            "outputs/theory/siglip/siglip_text_r8.json",
            "outputs/theory/siglip/siglip_both_r8.json"):
    show(rel)

print("\n  === every JSON carrying a Gamma-like field ===")
hits = []
for f in glob.glob(os.path.join(REPO, "outputs", "**", "*.json"), recursive=True):
    try:
        s = io.open(f, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    if "Gamma_v" in s or "Gamma_vision" in s or "norm_g_vision" in s:
        hits.append(os.path.relpath(f, REPO))
for h in sorted(hits):
    print("   ", h)
print("  total:", len(hits))
