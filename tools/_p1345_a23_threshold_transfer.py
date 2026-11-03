# -*- coding: utf-8 -*-
r"""A23 upgrade analyses from archives (no new runs).

  P0-3  symmetric-surgery check: does the archive contain both image-side and text-side surgery on every model/domain?
  P0-2  threshold transfer: fit a gap threshold on one domain that separates better-than-median from worse, then evaluate
        the balanced accuracy of that threshold on the other domains.

Domains come from outputs/ocean_gap_surgery.json (model x side x lambda) and outputs/sonar_protocol.json
(clip_frozen, sonar_ft x lambda).

Output: outputs/analysis/a23_threshold_transfer.json

    python tools/_p1345_a23_threshold_transfer.py [--apply]
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a23_threshold_transfer.json")


def ba(pred, truth):
    tp = np.sum(pred & truth)
    tn = np.sum(~pred & ~truth)
    fp = np.sum(pred & ~truth)
    fn = np.sum(~pred & truth)
    return float(0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    domains = collections.defaultdict(list)
    gs = json.load(io.open(os.path.join(REPO, "outputs", "ocean_gap_surgery.json"), encoding="utf-8"))
    for r in gs:
        domains[f"{r['model']}|{r['side']}"].append({"lam": r["lam"], "CG": r["CG"], "top1": r["top1"],
                                                     "tau": r.get("tau")})
    sp = json.load(io.open(os.path.join(REPO, "outputs", "sonar_protocol.json"), encoding="utf-8"))
    text_side = []
    for key in ("clip_frozen", "sonar_ft"):
        for r in sp[key]["rows"]:
            if "top1" not in r or not isinstance(r["lambda"], (int, float)):
                text_side.append({"domain": key, **r})
                continue
            domains[f"NKSID|{key}"].append({"lam": r["lambda"], "CG": r["CG"], "top1": r["top1"],
                                             "tau": r.get("tau_meas")})

    summary = []
    for name, rows in domains.items():
        top = np.array([r["top1"] for r in rows], dtype=float)
        cg = np.array([r["CG"] for r in rows], dtype=float)
        tau = np.array([r["tau"] if r["tau"] is not None else np.nan for r in rows], dtype=float)
        ok = np.isfinite(tau)
        from scipy import stats as st
        summary.append({"domain": name, "n": len(rows),
                        "cg_range": [float(cg.min()), float(cg.max())],
                        "top1_range": [float(top.min()), float(top.max())],
                        "r_CG_top1": float(st.pearsonr(cg, top)[0]),
                        "r_tau_top1": float(st.pearsonr(tau[ok], top[ok])[0]) if ok.sum() > 2 else None})
        print(f"  {name}: n={len(rows)} tree r(CG,top1)={summary[-1]['r_CG_top1']:+.2f} "
              f"r(tau,top1)={summary[-1]['r_tau_top1']}")

    # threshold transfer: label "degraded" = top1 below the domain median; fit a CG threshold on one domain
    labels, masses = {}, {}
    for name, rows in domains.items():
        top = np.array([r["top1"] for r in rows], dtype=float)
        cg = np.array([r["CG"] for r in rows], dtype=float)
        labels[name] = top <= float(np.median(top))
        masses[name] = cg
    transfer = {}
    for fit_name in domains:
        best = None
        for thr in np.linspace(masses[fit_name].min(), masses[fit_name].max(), 201):
            # a larger gap is expected to mark degradation, so "degraded" = CG >= thr
            pred = masses[fit_name] >= thr
            score = ba(pred, labels[fit_name])
            if best is None or score > best[1]:
                best = (float(thr), float(score))
        thr = best[0]
        for test_name in domains:
            if test_name == fit_name:
                continue
            pred = masses[test_name] >= thr
            transfer[f"{fit_name}->{test_name}"] = {"threshold": thr, "fit_BA": best[1],
                                                    "test_BA": ba(pred, labels[test_name])}
    print("  threshold transfer:")
    for k, v in transfer.items():
        print(f"   {k}: thr={v['threshold']:.3f} fitBA={v['fit_BA']:.2f} testBA={v['test_BA']:.2f}")

    payload = {"domains": summary, "threshold_transfer": transfer, "text_side_surgery": text_side,
               "note": "degraded = top-1 below the domain median; larger centroid gap marks degradation"}
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
