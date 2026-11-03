# -*- coding: utf-8 -*-
"""Show the per-benchmark structure of a1_rr_e3_benchmarks.json: what each surgery point records."""
import io
import json

P = r"D:\Realdesktop\Wan\Important\New\outputs\a1_rr_e3_benchmarks.json"
d = json.load(io.open(P, encoding="utf-8"))

print("meta:", {k: (v if not isinstance(v, (list, dict)) else f"{type(v).__name__}({len(v)})")
                for k, v in d["meta"].items()})

for bench, bd in d["benchmarks"].items():
    print(f"\n=== {bench} (classes={bd.get('class_list_len')}, loaded={bd.get('loaded')}) ===")
    variants = bd.get("variants", {})
    for vname, vd in variants.items():
        print(f"  variant '{vname}' keys: {list(vd)[:10]}")
        # dig one level
        for k, v in list(vd.items())[:4]:
            if isinstance(v, list):
                n = len(v)
                print(f"    {k}: list({n})")
                if v and isinstance(v[0], dict):
                    print(f"      item0 keys: {list(v[0])}")
                    print(f"      item0: { {kk: (round(vv, 4) if isinstance(vv, float) else str(vv)[:28]) for kk, vv in list(v[0].items())[:12]} }")
            elif isinstance(v, dict):
                print(f"    {k}: dict keys {list(v)[:8]}")
            else:
                print(f"    {k} = {str(v)[:60]}")
        break  # only the first variant in detail
