#!/usr/bin/env python3
"""Certified abstention selector: select proxy-best only when its margin exceeds 2*epsilon."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "outputs/paper_b/runs"
OUT = ROOT / "paper_b_v2/results/certified_selector.json"
PROXIES = ["CG", "DG", "spec_eff_rank", "spec_top1_share"]
READOUTS = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"]
CAL, TEST = {45, 46}, {47, 48}


def norm(name, v):
    if name in ("classification_top1", "R1_i2t", "R1_t2i"):
        return float(v) / 100.0
    return float(np.clip(v, 0.0, 1.0))


def load():
    rows = []
    for p in sorted(RUNS.glob("*.json")):
        if p.name == "summary.json":
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        m = d["run"]
        cps = []
        for rec in sorted(d["epochs"], key=lambda e: e["epoch"]):
            c = rec["conditions"]["original"]
            cps.append({"y": float(np.mean([norm(r, c[r]) for r in READOUTS])),
                        "proxy": [float(c[k]) for k in PROXIES]})
        rows.append({"dataset": m["dataset"], "site": m["tower"], "seed": int(m["seed"]), "cps": cps})
    return rows


def sign_for(cal, pi):
    def reg(run, s):
        y = np.asarray([c["y"] for c in run["cps"]])
        g = s * np.asarray([c["proxy"][pi] for c in run["cps"]])
        return float(y.max() - y[int(np.argmax(g))])
    h = np.mean([reg(r, 1) for r in cal]); l = np.mean([reg(r, -1) for r in cal])
    return 1.0 if h <= l else -1.0


def main():
    runs = load(); cal = [r for r in runs if r["seed"] in CAL]; test = [r for r in runs if r["seed"] in TEST]
    out = {"epsilon_definition": "linear calibration on calibration seeds; max |calibrated_proxy-readout|", "proxies": {}}
    for pi, name in enumerate(PROXIES):
        xs = np.asarray([c["proxy"][pi] for r in cal for c in r["cps"]], dtype=float)
        ys = np.asarray([c["y"] for r in cal for c in r["cps"]], dtype=float)
        a, b = np.polyfit(xs, ys, 1)
        eps = float(np.max(np.abs(a * xs + b - ys)))
        selected = 0; last_y = []; sel_y = []
        for r in test:
            y = np.asarray([c["y"] for c in r["cps"]])
            g = a * np.asarray([c["proxy"][pi] for c in r["cps"]]) + b
            gap = float(g.max() - g[-1])
            if gap > 2.0 * eps:
                idx = int(np.argmax(g)); selected += 1
            else:
                idx = len(y) - 1
            last_y.append(float(y[-1])); sel_y.append(float(y[idx]))
        risks = [a1 < b1 - 1e-12 for a1, b1 in zip(sel_y, last_y)]
        diffs = [a1 - b1 for a1, b1 in zip(sel_y, last_y)]
        out["proxies"][name] = {
            "slope": float(a), "intercept": float(b), "epsilon": eps,
            "n_test": len(test), "coverage": selected / len(test),
            "risk_worse_than_last": float(np.mean(risks)),
            "mean_diff": float(np.mean(diffs)),
            "mean_last": float(np.mean(last_y)),
        }
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
