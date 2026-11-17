#!/usr/bin/env python3
"""Descriptive analysis of P1 pilots: SigLIP rank 8, CLIP-B/32 rank 24, and split-2 rank 16.

These are 6-run pilots (3 datasets x 2 seeds, both tower), not full matrices.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PROXIES = ["CG", "DG", "spec_eff_rank", "spec_top1_share"]
READOUTS = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"]
OUT = ROOT / "paper_b_v2" / "results" / "p1_pilot.json"


def norm(name: str, v: float) -> float:
    if name in ("classification_top1", "R1_i2t", "R1_t2i"):
        return float(v) / 100.0
    return float(np.clip(v, 0.0, 1.0))


def load(directory: Path) -> list[dict]:
    rows = []
    for path in sorted(directory.glob("*.json")):
        if path.name == "summary.json":
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        meta = d["run"]
        cps = []
        for rec in sorted(d["epochs"], key=lambda e: e["epoch"]):
            cond = rec["conditions"]["original"]
            cps.append(
                {
                    "loss": float(rec["train_loss"]),
                    "y": float(np.mean([norm(r, cond[r]) for r in READOUTS])),
                    "proxy": [float(cond[p]) for p in PROXIES],
                }
            )
        rows.append({"run_id": path.stem, "meta": meta, "seed": int(meta["seed"]), "cps": cps})
    return rows


def sign_for(cal: list[dict], pi: int) -> float:
    def reg(run, s):
        y = np.asarray([c["y"] for c in run["cps"]])
        g = np.asarray([c["proxy"][pi] for c in run["cps"]])
        return float(y.max() - y[int(np.argmax(s * g))])

    h = float(np.mean([reg(r, 1) for r in cal]))
    l = float(np.mean([reg(r, -1) for r in cal]))
    return 1.0 if h <= l else -1.0


def describe(name: str, rows: list[dict]) -> dict:
    cal = [r for r in rows if r["seed"] in (45, 49)]
    test = [r for r in rows if r["seed"] in (47, 51)]
    gaps = []
    oracle = 0
    for r in rows:
        y = np.asarray([c["y"] for c in r["cps"]])
        gaps.append(float(y.max() - y[-1]))
        oracle += int(np.isclose(y[-1], y.max(), atol=1e-12, rtol=0.0))
    proxies = {}
    for pi, pname in enumerate(PROXIES):
        s = sign_for(cal, pi)
        test_regs = []
        last_regs = []
        for r in test:
            y = np.asarray([c["y"] for c in r["cps"]])
            g = np.asarray([c["proxy"][pi] for c in r["cps"]])
            test_regs.append(float(y.max() - y[int(np.argmax(s * g))]))
            last_regs.append(float(y.max() - y[-1]))
        proxies[pname] = {
            "sign": "higher" if s > 0 else "lower",
            "test_mean_regret": float(np.mean(test_regs)),
            "last_mean_regret": float(np.mean(last_regs)),
            "diff": float(np.mean(np.asarray(test_regs) - np.asarray(last_regs))),
            "n_test": len(test),
        }
    best = min(proxies, key=lambda k: proxies[k]["test_mean_regret"])
    return {
        "name": name,
        "n_runs": len(rows),
        "n_cal": len(cal),
        "n_test": len(test),
        "last_oracle": oracle,
        "last_oracle_fraction": float(oracle / len(rows)),
        "mean_gap": float(np.mean(gaps)),
        "proxies": proxies,
        "best_proxy": best,
        "best_proxy_diff": proxies[best]["diff"],
    }


def main() -> None:
    dirs = {
        "siglip_b16_r8_pilot": ROOT / "outputs/paper_b/runs_siglip_pilot",
        "clip_b32_r24_pilot": ROOT / "outputs/paper_b/runs_b32_r24_pilot",
        "clip_b32_split2_r16_pilot": ROOT / "outputs/paper_b/runs_b32_split2_pilot",
    }
    out = {name: describe(name, load(d)) for name, d in dirs.items()}
    out["note"] = "6-run descriptive pilots (3 datasets x 2 seeds x both tower); no inferential claim."
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for name, r in out.items():
        if name == "note":
            continue
        print(name, "n", r["n_runs"], "last_oracle", f"{r['last_oracle_fraction']:.3f}",
              "gap", f"{r['mean_gap']:.5f}", "best", r["best_proxy"], f"{r['best_proxy_diff']:+.5f}")


if __name__ == "__main__":
    main()
