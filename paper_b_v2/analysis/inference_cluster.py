#!/usr/bin/env python3
"""Cluster-aware inference and selection baselines for Paper B v2.

Frozen B32 matrix only. Reads outputs/paper_b/runs/*.json; no training.
Primary clustering: dataset x adaptation site (9 clusters). Sensitivity: dataset, site.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "outputs" / "paper_b" / "runs"
OUT = ROOT / "paper_b_v2" / "results" / "cluster_inference.json"
PROXIES = ["CG", "DG", "spec_eff_rank", "spec_top1_share"]
READOUTS = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"]
CAL = {45, 46}
TEST = {47, 48}
N_BOOT = 10000
SEED = 20261115


def norm(name: str, v: float) -> float:
    if name in ("classification_top1", "R1_i2t", "R1_t2i"):
        return float(v) / 100.0
    if name == "ARI":
        return float(np.clip(v, 0.0, 1.0))
    raise KeyError(name)


def load() -> list[dict]:
    rows = []
    for path in sorted(RUNS.glob("*.json")):
        if path.name == "summary.json":
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        meta = d["run"]
        cps = []
        for rec in sorted(d["epochs"], key=lambda e: e["epoch"]):
            cond = rec["conditions"]["original"]
            cps.append(
                {
                    "epoch": int(rec["epoch"]),
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


def regret(y: np.ndarray, idx: int) -> float:
    return float(y.max() - y[idx])


def sign_for(cal: list[dict], pname: str) -> float:
    pi = PROXIES.index(pname)
    hs = [regret(np.asarray([c["y"] for c in r["cps"]]), int(np.argmax([c["proxy"][pi] for c in r["cps"]]))) for r in cal]
    ls = [regret(np.asarray([c["y"] for c in r["cps"]]), int(np.argmax([-c["proxy"][pi] for c in r["cps"]]))) for r in cal]
    return 1.0 if float(np.mean(hs)) <= float(np.mean(ls)) else -1.0


def selector_indices(run: dict, name: str, sign: float | None = None) -> int:
    cps = run["cps"]
    y = np.asarray([c["y"] for c in cps])
    if name == "last":
        return len(cps) - 1
    if name == "first":
        return 0
    if name == "middle":
        return 1
    if name == "train_loss":
        return int(np.argmin([c["loss"] for c in cps]))
    if name == "random":
        return -1
    if name == "oracle":
        return int(np.argmax(y))
    pi = PROXIES.index(name)
    return int(np.argmax((sign or 1.0) * np.asarray([c["proxy"][pi] for c in cps])))


def selector_regret(run: dict, name: str, sign: float | None = None) -> float:
    cps = run["cps"]
    y = np.asarray([c["y"] for c in cps])
    idx = selector_indices(run, name, sign)
    if idx == -1:  # random expected regret
        return float(y.max() - y.mean())
    return float(y.max() - y[idx])


def cluster_bootstrap(diffs: list[float], clusters: list[str], n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    d = np.asarray(diffs, dtype=float)
    c = np.asarray(clusters)
    uniq = sorted(set(c))
    by = {u: d[c == u] for u in uniq}
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for b in range(n_boot):
        picked = rng.choice(len(uniq), size=len(uniq), replace=True)
        vals = np.concatenate([by[uniq[i]] for i in picked])
        means[b] = vals.mean()
    # cluster-robust variance of the mean
    k = len(uniq)
    n = len(d)
    cluster_means = np.asarray([by[u].mean() for u in uniq])
    cluster_ns = np.asarray([len(by[u]) for u in uniq])
    var_cluster = float(((cluster_ns / n) ** 2 * (cluster_means - d.mean()) ** 2).sum() * k / (k - 1))
    var_iid = float(d.var(ddof=1) / n)
    return {
        "n": int(n),
        "n_clusters": int(k),
        "mean": float(d.mean()),
        "ci95_cluster": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
        "se_cluster": float(math.sqrt(max(var_cluster, 0.0))),
        "se_iid": float(math.sqrt(max(var_iid, 0.0))),
        "design_effect": float(var_cluster / var_iid) if var_iid > 0 else None,
        "cluster_sizes": {u: int(len(by[u])) for u in uniq},
    }


def main() -> None:
    runs = load()
    cal = [r for r in runs if r["seed"] in CAL]
    test = [r for r in runs if r["seed"] in TEST]
    if len(cal) != 72 or len(test) != 72:
        raise SystemExit(f"unexpected split sizes {len(cal)}/{len(test)}")
    signs = {p: sign_for(cal, p) for p in PROXIES}
    names = ["last", "first", "middle", "train_loss", "random", "oracle"] + PROXIES
    out = {"n_runs": len(runs), "n_cal": len(cal), "n_test": len(test),
           "signs": {k: ("higher" if v > 0 else "lower") for k, v in signs.items()},
           "selectors": {}}
    for name in names:
        sign = signs.get(name)
        diffs = []
        for r in test:
            last = selector_regret(r, "last")
            sel = selector_regret(r, name, sign)
            diffs.append(sel - last)
        clusters_ds = [f"{r['dataset']}|{r['site']}" for r in test]
        clusters_d = [r["dataset"] for r in test]
        clusters_s = [r["site"] for r in test]
        out["selectors"][name] = {
            "mean_regret_minus_last": cluster_bootstrap(diffs, clusters_ds),
            "sensitivity_dataset": cluster_bootstrap(diffs, clusters_d),
            "sensitivity_site": cluster_bootstrap(diffs, clusters_s),
        }
    # last-oracle and gaps
    y_gaps = []
    last_oracle = 0
    for r in test:
        y = np.asarray([c["y"] for c in r["cps"]])
        y_gaps.append(float(y.max() - y[-1]))
        last_oracle += int(np.isclose(y[-1], y.max(), atol=1e-12, rtol=0.0))
    out["coverage"] = {
        "last_oracle": int(last_oracle), "n": len(test),
        "last_oracle_fraction": float(last_oracle / len(test)),
        "mean_gap": float(np.mean(y_gaps)),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(out["coverage"], indent=2))
    for name in names:
        b = out["selectors"][name]["mean_regret_minus_last"]
        deff = "NA" if b["design_effect"] is None else f"{b['design_effect']:.2f}"
        print(f"{name:16s} diff={b['mean']:+.5f} cluster_ci=[{b['ci95_cluster'][0]:+.5f},{b['ci95_cluster'][1]:+.5f}] "
              f"k={b['n_clusters']} deff={deff}")


if __name__ == "__main__":
    main()
