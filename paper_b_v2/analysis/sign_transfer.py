#!/usr/bin/env python3
"""Frozen calibration/test sign-transfer analysis for Paper B v2."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from reanalysis import PROXIES, load_runs

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper_b_v2" / "results" / "sign_transfer.json"
CAL = {45, 46}
TEST = {47, 48}
GROUPS = {
    "site": ["both", "text", "vision"],
    "dataset": ["dtd", "inat", "nksid"],
    "rank": [8, 16, 32, 64],
}


def y_of(run: dict) -> np.ndarray:
    return np.asarray([np.mean(c["readout"]) for c in run["checkpoints"]], dtype=float)


def g_of(run: dict, pname: str) -> np.ndarray:
    pi = PROXIES.index(pname)
    return np.asarray([c["proxy"][pi] for c in run["checkpoints"]], dtype=float)


def eval_sign(runs: list[dict], pname: str, sign: float) -> dict:
    regrets = []
    diffs = []
    better = 0
    correct = 0
    for r in runs:
        y = y_of(r)
        g = g_of(r, pname)
        sel = int(np.argmax(sign * g))
        regrets.append(float(y.max() - y[sel]))
        diffs.append(float(y[sel] - y[-1]))
        better += int(y[sel] > y[-1])
        correct += int(sel == int(np.argmax(y)))
    return {
        "mean_regret": float(np.mean(regrets)),
        "mean_diff_vs_last": float(np.mean(diffs)),
        "fraction_better_than_last": float(better / len(runs)),
        "selection_accuracy": float(correct / len(runs)),
    }


def sign_table(runs: list[dict], pname: str) -> dict:
    higher = eval_sign(runs, pname, +1.0)
    lower = eval_sign(runs, pname, -1.0)
    best = min([("higher", higher), ("lower", lower)], key=lambda x: x[1]["mean_regret"])
    return {
        "higher": higher,
        "lower": lower,
        "best_sign": best[0],
        "best": best[1],
    }


def main() -> None:
    runs = load_runs()
    cal = [r for r in runs if r["seed"] in CAL]
    test = [r for r in runs if r["seed"] in TEST]
    if len(cal) != 72 or len(test) != 72:
        raise SystemExit(f"unexpected split sizes: {len(cal)} cal / {len(test)} test")

    proxies = {}
    for pname in PROXIES:
        c = sign_table(cal, pname)
        t = sign_table(test, pname)
        selected_sign = c["best_sign"]
        test_selected = t["higher"] if selected_sign == "higher" else t["lower"]
        proxies[pname] = {
            "calibration": c,
            "test": t,
            "calibration_selected_sign": selected_sign,
            "test_optimal_sign": t["best_sign"],
            "sign_transfer": selected_sign == t["best_sign"],
            "test_selected_sign": selected_sign,
            "test_selected_regret": test_selected["mean_regret"],
            "test_selected_diff_vs_last": test_selected["mean_diff_vs_last"],
            "test_selected_fraction_better": test_selected["fraction_better_than_last"],
            "test_selected_accuracy": test_selected["selection_accuracy"],
        }

    groups = {}
    for gname, levels in GROUPS.items():
        entries = []
        for level in levels:
            cg = [r for r in cal if r[gname] == level]
            tg = [r for r in test if r[gname] == level]
            if not cg or not tg:
                continue
            for pname in PROXIES:
                c = sign_table(cg, pname)
                t = sign_table(tg, pname)
                selected = c["best_sign"]
                test_selected = t["higher"] if selected == "higher" else t["lower"]
                entries.append(
                    {
                        "proxy": pname,
                        "level": str(level),
                        "calibration_sign": selected,
                        "test_optimal_sign": t["best_sign"],
                        "transferred": selected == t["best_sign"],
                        "test_regret": test_selected["mean_regret"],
                        "test_diff_vs_last": test_selected["mean_diff_vs_last"],
                        "test_fraction_better": test_selected["fraction_better_than_last"],
                    }
                )
        groups[gname] = entries

    transfer_acc = {}
    for pname in PROXIES:
        entries = [e for g in groups.values() for e in g if e["proxy"] == pname]
        transfer_acc[pname] = {
            "n_groups": len(entries),
            "n_transferred": int(sum(e["transferred"] for e in entries)),
            "fraction_transferred": float(np.mean([e["transferred"] for e in entries])),
        }

    result = {
        "source": {
            "runs_dir": "outputs/paper_b/runs",
            "n_runs": len(runs),
            "calibration_seeds": sorted(CAL),
            "test_seeds": sorted(TEST),
            "n_cal": len(cal),
            "n_test": len(test),
        },
        "proxies": proxies,
        "groups": groups,
        "transfer_accuracy": transfer_acc,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({p: {k: proxies[p][k] for k in ("calibration_selected_sign", "test_optimal_sign", "sign_transfer", "test_selected_regret", "test_selected_diff_vs_last")} for p in PROXIES}, indent=1))
    print(json.dumps(transfer_acc, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
