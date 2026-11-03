# -*- coding: utf-8 -*-
"""Show the surgery grid and exact-predictor records for one benchmark, plus the model formula source."""
import io
import json

P = r"D:\Realdesktop\Wan\Important\New\outputs\a1_rr_e3_benchmarks.json"
d = json.load(io.open(P, encoding="utf-8"))

for bench in ("dtd", "food101"):
    bd = d["benchmarks"][bench]
    for vname, vd in bd["variants"].items():
        print(f"=== {bench} / {vname} ===")
        print("  sigma_m=%s mean_m=%s top1_frozen=%s" % (vd.get("sigma_m"), vd.get("mean_m"), vd.get("top1_frozen")))
        sur = vd.get("surgery")
        print("  surgery type:", type(sur).__name__)
        if isinstance(sur, list) and sur:
            print("   item0:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in sur[0].items()})
            print("   n points:", len(sur))
        elif isinstance(sur, dict):
            print("   keys:", list(sur)[:10])
            k0 = list(sur)[0]
            print(f"   [{k0}]:", sur[k0])
        epe = vd.get("exact_predictor_error")
        print("  exact_predictor_error:", json.dumps(epe)[:400] if not isinstance(epe, (int, float)) else epe)
        print()
