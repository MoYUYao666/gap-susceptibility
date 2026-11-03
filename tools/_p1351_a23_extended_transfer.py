# -*- coding: utf-8 -*-
r"""A23 extension: threshold transfer across all archived gap-surgery domain arms, including the spectrum sweeps.

Adds the `ocean_spectrum.json` arms (bioclip / oceanclip) to the eight arms already used, and recomputes the
fit-in-domain / test-cross-domain balanced accuracies over the enlarged domain set.

Output: outputs/analysis/a23_threshold_transfer_extended.json

    python tools/_p1351_a23_extended_transfer.py [--apply]
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os

import numpy as np
from scipy import stats as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a23_threshold_transfer_extended.json")


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
        domains[f"gapsurgery|{r['model']}|{r['side']}"].append({"CG": r["CG"], "top1": r["top1"]})
    sp = json.load(io.open(os.path.join(REPO, "outputs", "sonar_protocol.json"), encoding="utf-8"))
    for key in ("clip_frozen", "sonar_ft"):
        for r in sp[key]["rows"]:
            if "top1" in r and isinstance(r["lambda"], (int, float)):
                domains[f"sonar|{key}"].append({"CG": r["CG"], "top1": r["top1"]})
    spec = json.load(io.open(os.path.join(REPO, "outputs", "ocean_spectrum.json"), encoding="utf-8"))
    for model, v in spec.items():
        for r in v["rows"]:
            domains[f"spectrum|{model}"].append({"CG": r["CG"], "top1": r["top1"]})

    summary, labels, masses = [], {}, {}
    for name, rows in domains.items():
        top = np.array([r["top1"] for r in rows], dtype=float)
        cg = np.array([r["CG"] for r in rows], dtype=float)
        summary.append({"domain": name, "n": len(rows), "top1_range": [float(top.min()), float(top.max())],
                        "cg_range": [float(cg.min()), float(cg.max())],
                        "r_CG_top1": float(st.pearsonr(cg, top)[0]) if len(rows) > 2 and np.std(cg) > 0 else None})
        labels[name] = top <= float(np.median(top))
        masses[name] = cg
    transfer = {}
    for fit_name in domains:
        best = None
        for thr in np.linspace(masses[fit_name].min(), masses[fit_name].max(), 201):
            sc = ba(masses[fit_name] >= thr, labels[fit_name])
            if best is None or sc > best[1]:
                best = (float(thr), float(sc))
        thr = best[0]
        for test_name in domains:
            if test_name == fit_name:
                continue
            transfer[f"{fit_name}->{test_name}"] = {"threshold": thr, "fit_BA": best[1],
                                                    "test_BA": ba(masses[test_name] >= thr, labels[test_name])}
    test_vals = [v["test_BA"] for v in transfer.values()]
    fit_vals = [v["fit_BA"] for k, v in transfer.items() if k.split("->")[0] == k.split("->")[0]][:len(domains)]
    payload = {"n_domains": len(domains), "n_transfers": len(transfer), "domains": summary,
               "fit_BA": {"min": float(np.min(fit_vals)), "max": float(np.max(fit_vals))},
               "test_BA": {"min": float(np.min(test_vals)), "max": float(np.max(test_vals)),
                           "median": float(np.median(test_vals))},
               "transfer": transfer}
    print(f"  domains={len(domains)} transfers={len(transfer)}")
    print(f"  fit BA range {payload['fit_BA']} | test BA min {payload['test_BA']['min']:.2f} "
          f"median {payload['test_BA']['median']:.2f} max {payload['test_BA']['max']:.2f}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
