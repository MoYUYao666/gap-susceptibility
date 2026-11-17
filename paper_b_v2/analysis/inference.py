#!/usr/bin/env python3
"""Paired inference and margin analysis for Paper B v2 (frozen data only)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from reanalysis import PROXIES, load_runs

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper_b_v2" / "results" / "inference.json"
CAL = {45, 46}
TEST = {47, 48}
N_BOOT = 10000
SEED = 20261115


def y_of(run: dict) -> np.ndarray:
    return np.asarray([np.mean(c["readout"]) for c in run["checkpoints"]], dtype=float)


def g_of(run: dict, pname: str) -> np.ndarray:
    pi = PROXIES.index(pname)
    return np.asarray([c["proxy"][pi] for c in run["checkpoints"]], dtype=float)


def sign_regret(runs: list[dict], pname: str, sign: float) -> list[float]:
    out = []
    for r in runs:
        y = y_of(r)
        g = g_of(r, pname)
        sel = int(np.argmax(sign * g))
        out.append(float(y.max() - y[sel]))
    return out


def choose_sign(cal: list[dict], pname: str) -> str:
    h = float(np.mean(sign_regret(cal, pname, +1.0)))
    l = float(np.mean(sign_regret(cal, pname, -1.0)))
    return "higher" if h <= l else "lower"


def bootstrap_mean_ci(values: list[float], n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    a = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        means[b] = a[rng.integers(0, len(a), len(a))].mean()
    return {
        "mean": float(a.mean()),
        "ci95": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
        "n": int(len(a)),
        "n_boot": int(n_boot),
    }


def wilson(p: float, n: int, z: float = 1.959963984540054) -> list[float]:
    den = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return [float(max(0.0, centre - half)), float(min(1.0, centre + half))]


def main() -> None:
    runs = load_runs()
    cal = [r for r in runs if r["seed"] in CAL]
    test = [r for r in runs if r["seed"] in TEST]
    if len(cal) != 72 or len(test) != 72:
        raise SystemExit(f"unexpected split sizes: {len(cal)} / {len(test)}")

    gaps_all = [float(y_of(r).max() - y_of(r)[-1]) for r in runs]
    gaps_test = [float(y_of(r).max() - y_of(r)[-1]) for r in test]
    last_oracle = [bool(np.isclose(y_of(r)[-1], y_of(r).max(), atol=1e-12, rtol=0.0)) for r in runs]

    proxies = {}
    for pname in PROXIES:
        sign = choose_sign(cal, pname)
        s = +1.0 if sign == "higher" else -1.0
        proxy_regrets = sign_regret(test, pname, s)
        last_regrets = [float(y_of(r).max() - y_of(r)[-1]) for r in test]
        diffs = [a - b for a, b in zip(proxy_regrets, last_regrets)]
        boot = bootstrap_mean_ci(diffs)

        margins_correct = []
        margins_wrong = []
        for r in test:
            y = y_of(r)
            second = float(np.sort(y)[-2])
            margin = float(y.max() - second)
            selected = int(np.argmax(s * g_of(r, pname)))
            if selected == int(np.argmax(y)):
                margins_correct.append(margin)
            else:
                margins_wrong.append(margin)

        # success by margin quartile (proxy-specific, test)
        margins = []
        successes = []
        for r in test:
            y = y_of(r)
            second = float(np.sort(y)[-2])
            margin = float(y.max() - second)
            selected = int(np.argmax(s * g_of(r, pname)))
            margins.append(margin)
            successes.append(selected == int(np.argmax(y)))
        order = np.argsort(margins)
        quartiles = np.array_split(order, 4)
        by_quartile = []
        for qi, idx in enumerate(quartiles):
            by_quartile.append(
                {
                    "quartile": qi + 1,
                    "n": int(len(idx)),
                    "margin_range": [float(np.min(np.asarray(margins)[idx])), float(np.max(np.asarray(margins)[idx]))],
                    "success_rate": float(np.mean(np.asarray(successes)[idx])),
                }
            )

        proxies[pname] = {
            "selected_sign": sign,
            "mean_regret": float(np.mean(proxy_regrets)),
            "last_mean_regret": float(np.mean(last_regrets)),
            "paired_diff": boot,
            "fraction_better_than_last": float(np.mean(np.asarray(proxy_regrets) < np.asarray(last_regrets))),
            "selection_accuracy": float(np.mean([x == 0.0 for x in proxy_regrets])),
            "margin_correct_median": float(np.median(margins_correct)) if margins_correct else None,
            "margin_wrong_median": float(np.median(margins_wrong)) if margins_wrong else None,
            "n_correct": len(margins_correct),
            "n_wrong": len(margins_wrong),
            "success_by_margin_quartile": by_quartile,
        }

    result = {
        "source": {
            "runs": "outputs/paper_b/runs",
            "n_runs": len(runs),
            "calibration_seeds": sorted(CAL),
            "test_seeds": sorted(TEST),
            "n_cal": len(cal),
            "n_test": len(test),
            "bootstrap": {"n_boot": N_BOOT, "seed": SEED, "unit": "run"},
        },
        "coverage": {
            "n_runs": len(runs),
            "n_test": len(test),
            "n_last_oracle": int(sum(last_oracle)),
            "last_oracle_fraction": float(np.mean(last_oracle)),
            "last_oracle_fraction_wilson95": wilson(float(np.mean(last_oracle)), len(runs)),
            "mean_oracle_gap_all": bootstrap_mean_ci(gaps_all),
            "mean_oracle_gap_test": bootstrap_mean_ci(gaps_test),
        },
        "proxies": proxies,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"coverage": result["coverage"], "proxies": proxies}, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
