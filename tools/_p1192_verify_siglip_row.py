# -*- coding: utf-8 -*-
r"""Recompute the SigLIP strict-freezing row of Table (tab:position_strict) from its archive.

The paper's residual-risk record flagged "SigLIP CGdelta (+0.067 / +0.058) has no archive". That sentence belongs to an
earlier draft; the numbers the current manuscript quotes are +0.0664 / -0.0114 / +0.0522, and the archive
`outputs/siglip_strict/seed*/` holds five seeds of each arm. This script recomputes the row and either confirms the
published values or reports the mismatch that would require a new run.

    python tools/_p1192_verify_siglip_row.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLISHED = {"text": 0.0664, "both": -0.0114, "vision": 0.0522}
R1_PUBLISHED = {"text": 0.432, "both": 0.619, "vision": 0.341}


def cg_delta(d: dict):
    a = d.get("initial_gap") or {}
    b = d.get("final_gap") or {}
    if "centroid_gap" in a and "centroid_gap" in b:
        return b["centroid_gap"] - a["centroid_gap"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    arm_of = {"text_only": "text", "both": "both", "vision_only": "vision"}
    rows = {}
    for seed_dir in sorted(glob.glob(os.path.join(REPO, "outputs", "siglip_strict", "seed*"))):
        seed = os.path.basename(seed_dir)
        for f in glob.glob(os.path.join(seed_dir, "**", "results.json"), recursive=True):
            try:
                d = json.load(io.open(f, encoding="utf-8"))
            except Exception:
                continue
            name = (d.get("experiment") or "") + " " + os.path.basename(os.path.dirname(f))
            # only the rank-8 arms belong to the published row; the r4 variants are a separate sweep
            if "_r4_" in name:
                continue
            arm = None
            for key, label in arm_of.items():
                if key in name:
                    arm = label
                    break
            cg = cg_delta(d)
            r1 = (d.get("final_task_metrics") or {}).get("R@1")
            if arm is None or cg is None:
                continue
            rows.setdefault(arm, []).append((seed, cg, r1))

    print(f"  archive: outputs/siglip_strict/  arms found: {sorted(rows)}")
    ok = True
    for arm in ("text", "both", "vision"):
        vals = rows.get(arm, [])
        if not vals:
            print(f"  {arm:<7} NO DATA")
            ok = False
            continue
        cg = [v[1] for v in vals]
        r1 = [v[2] for v in vals if v[2] is not None]
        mean_cg = st.mean(cg)
        sds = [f"{s}:{c:+.4f}" for s, c, _ in vals]
        pub = PUBLISHED[arm]
        good = abs(mean_cg - pub) <= 0.0006
        ok &= good
        print(f"  {arm:<7} n={len(cg):2d}  mean CGd={mean_cg:+.4f} (paper {pub:+.4f}) "
              f"{'OK' if good else 'MISMATCH'}  sd={st.pstdev(cg):.4f}")
        print(f"          per seed: {', '.join(sds)}")
        if r1:
            print(f"          R@1 mean={st.mean(r1):.3f} (paper {R1_PUBLISHED[arm]:.3f}) "
                  f"{'OK' if abs(st.mean(r1)-R1_PUBLISHED[arm])<=0.0006 else 'MISMATCH'}")
    print()
    print("  RESULT:", "the published SigLIP row reproduces from the archive" if ok else
          "MISMATCH -- a new run would be needed")
    if a.apply:
        out = os.path.join(REPO, "outputs", "analysis", "siglip_row_verify.json")
        payload = {
            "source": "outputs/siglip_strict/seed*/**/results.json",
            "published_row": PUBLISHED,
            "recomputed": {k: {"n": len(v), "mean_cg_delta": st.mean([x[1] for x in v]),
                               "sd": st.pstdev([x[1] for x in v]),
                               "per_seed": [{"seed": s, "cg_delta": c} for s, c, _ in v]}
                           for k, v in rows.items()},
            "reproduces": ok,
        }
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print(f"  wrote {os.path.relpath(out, REPO)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
