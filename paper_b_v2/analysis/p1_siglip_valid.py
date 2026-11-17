#!/usr/bin/env python3
"""SigLIP-B/16 rank-8 descriptive analysis on complete 3-epoch runs only."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "cloud/p1_retrieved/outputs/paper_b"
OUT = ROOT / "paper_b_v2/results/p1_siglip_valid.json"
PROXIES = ["CG", "DG", "spec_eff_rank", "spec_top1_share"]
READOUTS = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"]
CAL, TEST = {45, 46}, {47, 48}


def norm(name, v):
    if name in ("classification_top1", "R1_i2t", "R1_t2i"):
        return float(v) / 100.0
    return float(np.clip(v, 0.0, 1.0))


def load():
    rows = []
    for sub in ["runs_siglip_r8_dtd", "runs_siglip_r8_other"]:
        for p in (SRC / sub).glob("*.json"):
            if p.name == "summary.json":
                continue
            d = json.loads(p.read_text(encoding="utf-8"))
            if len(d.get("epochs", [])) < 3:
                continue
            meta = d["run"]
            cps = []
            for rec in sorted(d["epochs"], key=lambda e: e["epoch"]):
                c = rec["conditions"]["original"]
                cps.append({"y": float(np.mean([norm(r, c[r]) for r in READOUTS])),
                            "proxy": [float(c[k]) for k in PROXIES]})
            rows.append({"id": p.stem, "dataset": meta["dataset"], "site": meta["tower"],
                         "seed": int(meta["seed"]), "cps": cps})
    return rows


def y(r): return np.asarray([c["y"] for c in r["cps"]])
def g(r, i): return np.asarray([c["proxy"][i] for c in r["cps"]])


def sign(cal, pi):
    def reg(run, s):
        yy = y(run)
        return float(yy.max() - yy[int(np.argmax(s * g(run, pi)))])
    return 1.0 if np.mean([reg(r, 1) for r in cal]) <= np.mean([reg(r, -1) for r in cal]) else -1.0


def boot(diffs, clusters):
    a = np.asarray(diffs); c = np.asarray(clusters)
    us = sorted(set(c)); by = {u: a[c == u] for u in us}
    rng = np.random.default_rng(20261115); means = []
    for _ in range(10000):
        pick = rng.choice(len(us), size=len(us), replace=True)
        means.append(np.concatenate([by[us[i]] for i in pick]).mean())
    return {"mean": float(a.mean()), "ci95_cluster": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
            "n": len(a), "n_clusters": len(us)}


def main():
    runs = load(); cal = [r for r in runs if r["seed"] in CAL]; test = [r for r in runs if r["seed"] in TEST]
    gaps = [float(y(r).max() - y(r)[-1]) for r in runs]
    last = int(sum(np.isclose(y(r)[-1], y(r).max(), atol=1e-12, rtol=0.0) for r in runs))
    proxies = {}
    for pi, name in enumerate(PROXIES):
        s = sign(cal, pi); diffs = []
        for r in test:
            yy = y(r); sel = int(np.argmax(s * g(r, pi)))
            diffs.append(float(yy.max() - yy[sel]) - float(yy.max() - yy[-1]))
        proxies[name] = {"sign": "higher" if s > 0 else "lower",
                         "test_diff": boot(diffs, [f"{r['dataset']}|{r['site']}" for r in test])}
    best = min(proxies, key=lambda k: proxies[k]["test_diff"]["mean"])
    out = {"n_runs": len(runs), "n_cal": len(cal), "n_test": len(test), "last_oracle": last,
           "last_oracle_fraction": last / len(runs), "mean_gap": float(np.mean(gaps)),
           "proxies": proxies, "best_proxy": best, "best_proxy_diff": proxies[best]["test_diff"]["mean"],
           "note": "SigLIP-B/16 rank-8; only 33/36 runs complete; 3 incomplete dropped."}
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n_runs", "n_cal", "n_test", "last_oracle", "last_oracle_fraction", "mean_gap", "best_proxy", "best_proxy_diff")}, indent=2))


if __name__ == "__main__":
    main()
