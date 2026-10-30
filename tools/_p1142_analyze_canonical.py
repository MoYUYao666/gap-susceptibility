# -*- coding: utf-8 -*-
r"""Summarise the canonical retrain: per-arm mean +/- sd under both metric definitions, and the arm contrasts.

The twelve records each carry both definitions, so the same script reports:
  * the canonical DG* / CG / DG_emp of `src/dg_star_tracker.py`, which is what the paper and the ODE use;
  * the legacy definition the archived 2026-10-16 sweep used, so the two runs can be compared without confusing
    which definition each number belongs to.

The point of the run is the contrast between arms. The frozen arm trains nothing, so its "change" is the
sampling difference between the 100-pair `before` slice and the 500-pair `after` measurement; it is reported as
the noise floor against which the trained arms are read.

    python tools/_p1142_analyze_canonical.py [--dir outputs/llava_canonical_cloud] [--json out.json]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics as st
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = ("frozen", "text_only", "vision_only", "both")
FIELDS = ("dg_star_before", "dg_star_after", "dg_star_rel_change",
          "cg_canonical_after", "dg_empirical_after",
          "dg_before", "dg_after", "dg_rel_change")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(REPO, "outputs", "llava_canonical_cloud"))
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    recs = {}
    for f in sorted(glob.glob(os.path.join(a.dir, "*.json"))):
        base = os.path.basename(f)
        if "progress" in base or base.endswith("sites.json"):
            continue
        d = json.load(open(f, encoding="utf-8"))
        if "arm" in d and "seed" in d:
            recs[(d["arm"], d["seed"])] = d
    print(f"  records: {len(recs)} from {os.path.relpath(a.dir, REPO)}")
    missing = [(arm, s) for arm in ARMS for s in (42, 123, 456) if (arm, s) not in recs]
    print(f"  missing: {missing if missing else 'none'}")
    if missing:
        print("\n  the sweep is not complete; the table below covers what exists")

    out = {}
    print("\n=== canonical definition (src/dg_star_tracker.py) ===")
    print(f"  {'arm':<12} {'n':>2} {'DG*before':>10} {'DG*after':>9} {'rel mean':>10} {'rel sd':>8} "
          f"{'CG':>7} {'DG_emp':>8}")
    for arm in ARMS:
        rows = [recs[(arm, s)] for s in (42, 123, 456) if (arm, s) in recs]
        if not rows:
            continue
        rel = [r["dg_star_rel_change"] for r in rows if r.get("dg_star_rel_change") is not None]
        rec = {
            "n": len(rows),
            "dg_star_before": st.mean(r["dg_star_before"] for r in rows),
            "dg_star_after": st.mean(r["dg_star_after"] for r in rows),
            "rel_mean": st.mean(rel) if rel else None,
            "rel_sd": st.pstdev(rel) if len(rel) > 1 else 0.0,
            "rel_values": rel,
            "cg": st.mean(r["cg_canonical_after"] for r in rows if r.get("cg_canonical_after") is not None),
            "dg_emp": st.mean(r["dg_empirical_after"] for r in rows if r.get("dg_empirical_after") is not None),
        }
        out[arm] = {"canonical": rec}
        fm = (lambda v, spec: format(v, spec) if v is not None else "n/a")
        print(f"  {arm:<12} {rec['n']:>2} {fm(rec['dg_star_before'], '.4f'):>10} "
              f"{fm(rec['dg_star_after'], '.4f'):>9} {fm(rec['rel_mean'] * 100, '+.3f') + '%':>10} "
              f"{fm(rec['rel_sd'] * 100, '.3f') + '%':>8} {fm(rec['cg'], '.4f'):>7} {fm(rec['dg_emp'], '.4f'):>8}")

    print("\n=== legacy definition (the archived 2026-10-16 metric) ===")
    print("  same sides as the canonical one now, so these are NOT the archived numbers either;")
    print("  they are the legacy formula applied to the corrected sides, for continuity only.")
    print(f"  {'arm':<12} {'n':>2} {'DG_before':>10} {'DG_after':>9} {'rel mean':>10} {'rel sd':>8}")
    for arm in ARMS:
        rows = [recs[(arm, s)] for s in (42, 123, 456) if (arm, s) in recs]
        if not rows:
            continue
        rel = [r["dg_rel_change"] for r in rows if r.get("dg_rel_change") is not None]
        rec = {
            "dg_before": st.mean(r["dg_before"] for r in rows),
            "dg_after": st.mean(r["dg_after"] for r in rows),
            "rel_mean": st.mean(rel) if rel else None,
            "rel_sd": st.pstdev(rel) if len(rel) > 1 else 0.0,
            "rel_values": rel,
        }
        out[arm]["legacy"] = rec
        fm = (lambda v, spec: format(v, spec) if v is not None else "n/a")
        print(f"  {arm:<12} {len(rows):>2} {fm(rec['dg_before'], '.4f'):>10} "
              f"{fm(rec['dg_after'], '.4f'):>9} {fm(rec['rel_mean'] * 100, '+.3f') + '%':>10} "
              f"{fm(rec['rel_sd'] * 100, '.3f') + '%':>8}")

    # the contrast the run exists to answer
    print("\n=== arm contrasts (canonical) ===")
    if "frozen" in out:
        floor = out["frozen"]["canonical"]["rel_mean"]
        print(f"  frozen noise floor (100-pair before vs 500-pair after): {floor * 100:+.3f}%")
        for arm in ARMS[1:]:
            if arm not in out:
                continue
            m = out[arm]["canonical"]["rel_mean"]
            sd = out[arm]["canonical"]["rel_sd"]
            diff = m - floor
            separation = abs(diff) / sd if sd else float("inf")
            print(f"  {arm:<12} {m * 100:+.3f}% +/- {sd * 100:.3f}%  | delta vs frozen {diff * 100:+.3f}%  "
                  f"| delta/sd {separation:.2f}")
            out[arm]["canonical"]["delta_vs_frozen"] = diff
            out[arm]["canonical"]["delta_over_sd"] = separation

    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)
        print(f"\n  wrote {os.path.relpath(a.json, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
