#!/usr/bin/env python3
"""Supervised validation selector reference using paired seed-47/48 runs."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "outputs/paper_b/runs"
OUT = ROOT / "paper_b_v2/results/validation_selector.json"
READOUTS = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"]


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
            cps.append({"y": float(np.mean([norm(r, c[r]) for r in READOUTS])), "loss": float(rec["train_loss"])})
        rows.append({"key": (m["dataset"], m["tower"], int(m["rank"])), "seed": int(m["seed"]), "cps": cps})
    return {(r["key"], r["seed"]): r for r in rows}


def cluster_ci(vals, clusters):
    a = np.asarray(vals); c = np.asarray(clusters); us = sorted(set(c)); by = {u: a[c == u] for u in us}
    rng = np.random.default_rng(20261116); means = []
    for _ in range(10000):
        pick = rng.choice(len(us), size=len(us), replace=True)
        means.append(np.concatenate([by[us[i]] for i in pick]).mean())
    return {"mean": float(a.mean()), "ci95_cluster": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
            "n": len(a), "n_clusters": len(us)}


def main():
    runs = load()
    diffs, clusters, selected, last = [], [], [], []
    for (key, seed), r47 in runs.items():
        if seed != 47:
            continue
        r48 = runs.get((key, 48))
        if r48 is None:
            continue
        y47 = np.asarray([c["y"] for c in r47["cps"]])
        y48 = np.asarray([c["y"] for c in r48["cps"]])
        idx = int(np.argmax(y47))
        diffs.append(float(y48.max() - y48[idx]) - float(y48.max() - y48[-1]))
        clusters.append(f"{key[0]}|{key[1]}")
        selected.append(idx + 1)
        last.append(int(np.isclose(y48[-1], y48.max(), atol=1e-12, rtol=0.0)))
    out = {"selector": "validation-label readout on seed 47; evaluate selected epoch on seed 48",
           "n_pairs": len(diffs), "diff": cluster_ci(diffs, clusters),
           "selected_epoch_hist": {str(k): selected.count(k) for k in sorted(set(selected))},
           "last_oracle_seed48": int(sum(last)), "note": "Supervised upper reference, not a label-free method."}
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
