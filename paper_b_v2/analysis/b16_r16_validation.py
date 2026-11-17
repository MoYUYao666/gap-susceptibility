#!/usr/bin/env python3
"""Validate the B16 rank-8 second-backbone matrix against the pre-registered criteria."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "outputs" / "paper_b" / "runs_b16_r16"
OUT = ROOT / "paper_b_v2" / "results" / "b16_r16_validation.json"
PROXIES = ["CG", "DG", "spec_eff_rank", "spec_top1_share"]
READOUTS = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"]
CAL = {45, 46}
TEST = {47, 48}
N_BOOT = 10000
SEED = 20261115


def norm(name: str, v: float) -> float:
    if name in ("classification_top1", "R1_i2t", "R1_t2i"):
        return float(v) / 100.0
    return float(np.clip(v, 0.0, 1.0))


def load():
    rows = []
    for p in sorted(RUNS.glob("*.json")):
        if p.name == "summary.json":
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        eps = d.get("epochs", [])
        if len(eps) != 3:
            continue
        cps = []
        for rec in eps:
            c = rec["conditions"]["original"]
            cps.append(
                {
                    "epoch": int(rec["epoch"]),
                    "proxy": [float(c[x]) for x in PROXIES],
                    "readout": [norm(x, c[x]) for x in READOUTS],
                }
            )
        cps.sort(key=lambda x: x["epoch"])
        rows.append({"run_id": p.stem, "meta": d.get("run", {}), "checkpoints": cps})
    return rows


def y_of(r):
    return np.asarray([np.mean(c["readout"]) for c in r["checkpoints"]], dtype=float)


def g_of(r, pname):
    i = PROXIES.index(pname)
    return np.asarray([c["proxy"][i] for c in r["checkpoints"]], dtype=float)


def regret(r, pname, sign):
    y = y_of(r)
    s = int(np.argmax(sign * g_of(r, pname)))
    return float(y.max() - y[s])


def choose_sign(cal, pname):
    h = float(np.mean([regret(r, pname, +1) for r in cal]))
    l = float(np.mean([regret(r, pname, -1) for r in cal]))
    return "higher" if h <= l else "lower"


def boot(diffs):
    a = np.asarray(diffs, dtype=float)
    rng = np.random.default_rng(SEED)
    means = np.empty(N_BOOT)
    for i in range(N_BOOT):
        means[i] = a[rng.integers(0, len(a), len(a))].mean()
    return {"mean": float(a.mean()), "ci95": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]}


def wilson(p, n, z=1.959963984540054):
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return [float(max(0, c - h)), float(min(1, c + h))]


def main():
    runs = load()
    cal = [r for r in runs if r["meta"].get("seed") in CAL]
    test = [r for r in runs if r["meta"].get("seed") in TEST]
    all_gaps = [float(y_of(r).max() - y_of(r)[-1]) for r in runs]
    last_oracle = [bool(np.isclose(y_of(r)[-1], y_of(r).max(), atol=1e-12, rtol=0)) for r in runs]
    nonmono = [bool(not np.all(np.diff(y_of(r)) >= 0)) for r in runs]

    proxies = {}
    for p in PROXIES:
        sign = choose_sign(cal, p)
        s = +1.0 if sign == "higher" else -1.0
        test_reg = [regret(r, p, s) for r in test]
        last_reg = [float(y_of(r).max() - y_of(r)[-1]) for r in test]
        diffs = [a - b for a, b in zip(test_reg, last_reg)]
        test_optimal = min([("higher", np.mean([regret(r, p, +1) for r in test])),
                            ("lower", np.mean([regret(r, p, -1) for r in test]))], key=lambda x: x[1])[0]
        proxies[p] = {
            "cal_sign": sign,
            "test_optimal_sign": test_optimal,
            "sign_transfer": sign == test_optimal,
            "test_mean_regret": float(np.mean(test_reg)),
            "last_mean_regret": float(np.mean(last_reg)),
            "paired_diff": boot(diffs),
            "fraction_better": float(np.mean(np.asarray(test_reg) < np.asarray(last_reg))),
        }

    v1 = float(np.mean(last_oracle))
    v4 = float(np.mean(nonmono))
    best = min(proxies, key=lambda x: proxies[x]["test_mean_regret"])
    v2 = proxies[best]["paired_diff"]["mean"] > 0
    v3 = sum(proxies[x]["sign_transfer"] for x in PROXIES)
    criteria = {
        "coverage_36_of_36": len([r for r in runs if len(r["checkpoints"]) == 3]) == 36,
        "X1_last_oracle_ge_50pct": {"value": v1, "pass": bool(v1 >= 0.50)},
        "X2_best_proxy_paired_diff_positive": {"best_proxy": best, "diff": proxies[best]["paired_diff"]["mean"], "pass": bool(v2)},
        "X3_sign_transfer_ge_3_of_4": {"count": int(v3), "pass": bool(v3 >= 3)},
        "X4_nonmonotone_ge_20pct": {"value": v4, "pass": bool(v4 >= 0.20)},
    }
    numeric = [criteria[k]["pass"] for k in ("X1_last_oracle_ge_50pct", "X2_best_proxy_paired_diff_positive", "X3_sign_transfer_ge_3_of_4", "X4_nonmonotone_ge_20pct")]
    overall = bool(criteria["coverage_36_of_36"] and sum(numeric) >= 3)

    result = {
        "source": {"runs_dir": "outputs/paper_b/runs_b16_r16", "n_runs": len(runs), "cal": len(cal), "test": len(test), "rank": 16},
        "coverage": {"n_runs": len(runs), "cal": len(cal), "test": len(test), "last_oracle": int(sum(last_oracle)),
                     "last_oracle_wilson95": wilson(float(np.mean(last_oracle)), len(runs)),
                     "mean_oracle_gap": float(np.mean(all_gaps)),
                     "nonmonotone_fraction": v4},
        "proxies": proxies,
        "criteria": criteria,
        "overall_pass": overall,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
