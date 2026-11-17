#!/usr/bin/env python3
"""Full P1 analysis: CLIP-B/32 ranks 6/12/24/48 and split-2 rank 16.

Reads frozen run JSONs only. Cluster bootstrap by dataset x site.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper_b_v2/results/p1_full.json"
PROXIES = ["CG", "DG", "spec_eff_rank", "spec_top1_share"]
READOUTS = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"]
N_BOOT = 10000
SEED = 20261115


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
        rows.append(
            {
                "run_id": path.stem,
                "dataset": meta["dataset"],
                "site": meta["tower"],
                "rank": int(meta["rank"]),
                "seed": int(meta["seed"]),
                "cps": cps,
            }
        )
    return rows


def y_of(run: dict) -> np.ndarray:
    return np.asarray([c["y"] for c in run["cps"]], dtype=float)


def g_of(run: dict, pi: int) -> np.ndarray:
    return np.asarray([c["proxy"][pi] for c in run["cps"]], dtype=float)


def regret(run: dict, idx: int) -> float:
    y = y_of(run)
    return float(y.max() - y[idx])


def sign_for(cal: list[dict], pi: int) -> float:
    hs = [regret(r, int(np.argmax(g_of(r, pi)))) for r in cal]
    ls = [regret(r, int(np.argmax(-g_of(r, pi)))) for r in cal]
    return 1.0 if float(np.mean(hs)) <= float(np.mean(ls)) else -1.0


def boot(diffs: list[float], clusters: list[str], seed: int = SEED) -> dict:
    a = np.asarray(diffs, dtype=float)
    c = np.asarray(clusters)
    uniq = sorted(set(c))
    by = {u: a[c == u] for u in uniq}
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(N_BOOT):
        pick = rng.choice(len(uniq), size=len(uniq), replace=True)
        means.append(np.concatenate([by[uniq[i]] for i in pick]).mean())
    return {
        "mean": float(a.mean()),
        "ci95_cluster": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
        "n": int(len(a)),
        "n_clusters": int(len(uniq)),
    }


def analyze(name: str, directory: Path, cal_seeds: set[int], test_seeds: set[int]) -> dict:
    runs = load(directory)
    cal = [r for r in runs if r["seed"] in cal_seeds]
    test = [r for r in runs if r["seed"] in test_seeds]
    gaps = [float(y_of(r).max() - y_of(r)[-1]) for r in runs]
    last_oracle = int(sum(np.isclose(y_of(r)[-1], y_of(r).max(), atol=1e-12, rtol=0.0) for r in runs))
    proxies = {}
    for pi, pname in enumerate(PROXIES):
        s = sign_for(cal, pi)
        diffs = []
        for r in test:
            y = y_of(r)
            sel = int(np.argmax(s * g_of(r, pi)))
            diffs.append(float(y.max() - y[sel]) - float(y.max() - y[-1]))
        proxies[pname] = {
            "sign": "higher" if s > 0 else "lower",
            "test_diff": boot(diffs, [f"{r['dataset']}|{r['site']}" for r in test]),
        }
    best = min(proxies, key=lambda k: proxies[k]["test_diff"]["mean"])
    return {
        "name": name,
        "n_runs": len(runs),
        "n_cal": len(cal),
        "n_test": len(test),
        "last_oracle": last_oracle,
        "last_oracle_fraction": float(last_oracle / len(runs)),
        "mean_gap": float(np.mean(gaps)),
        "proxies": proxies,
        "best_proxy": best,
        "best_proxy_diff": proxies[best]["test_diff"]["mean"],
    }


def main() -> None:
    specs = [
        ("r6", ROOT / "outputs/paper_b/runs_b32_r6_full", {45, 46}, {47, 48}),
        ("r12", ROOT / "outputs/paper_b/runs_b32_r12_full", {45, 46}, {47, 48}),
        ("r24", ROOT / "outputs/paper_b/runs_b32_r24_full", {45, 46}, {47, 48}),
        ("r48", ROOT / "outputs/paper_b/runs_b32_r48_full", {45, 46}, {47, 48}),
        ("split2_r16", ROOT / "outputs/paper_b/runs_b32_split2_full", {49, 50}, {51, 52}),
    ]
    out = {name: analyze(name, d, cal, test) for name, d, cal, test in specs}
    out["note"] = "Full 36-run blocks; CLIP-B/32; cluster bootstrap by dataset x site."
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for name, r in out.items():
        if name == "note":
            continue
        print(name, r["n_runs"], f"last={r['last_oracle_fraction']:.3f}", f"gap={r['mean_gap']:.5f}",
              r["best_proxy"], f"{r['best_proxy_diff']:+.5f}")


if __name__ == "__main__":
    main()
