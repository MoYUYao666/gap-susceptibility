# -*- coding: utf-8 -*-
r"""Bootstrap the block allocation over the three reference batches of the paper's Gamma protocol.

Uses the per-batch Gamma values already archived in p3d_gamma_real_vs_blank.json (real condition, VIiT-B/32,
LoRA-injected protocol of tools/_p462_gamma_real_vs_blank.py).

    python tools/_p1552_gamma_bootstrap_archive.py
"""
from __future__ import annotations

import collections
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "outputs", "analysis", "p3d_gamma_real_vs_blank.json")
OUT = os.path.join(REPO, "outputs", "analysis", "p3_gamma_bootstrap.json")
BUDGET = 16
BLOCKS = ["vision", "text_shallow", "text_mid", "text_deep"]
N_BOOT = 2000


def alloc(absg):
    share = np.array([absg[b] for b in BLOCKS], dtype=float)
    share = share / share.sum()
    ranks = np.maximum(1, np.round(share * BUDGET)).astype(int)
    while ranks.sum() > BUDGET:
        i = int(np.argmax(ranks))
        if ranks[i] > 1:
            ranks[i] -= 1
        else:
            break
    while ranks.sum() < BUDGET:
        i = int(np.argmin(share * BUDGET - ranks))
        ranks[i] += 1
    return tuple(int(r) for r in ranks)


def main() -> int:
    d = json.load(io.open(SRC, encoding="utf-8"))
    pb = d["conditions"]["real"]["per_batch"]
    gammas = [{b: float(pb[i][b]["gamma"]) for b in BLOCKS} for i in range(len(pb))]
    point = alloc({b: abs(np.mean([g[b] for g in gammas])) for b in BLOCKS})
    rng = np.random.default_rng(42)
    cnt = collections.Counter()
    allr = {b: [] for b in BLOCKS}
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(gammas), len(gammas))
        mean = {b: float(np.mean([gammas[i][b] for i in idx])) for b in BLOCKS}
        cnt[alloc({b: abs(v) for b, v in mean.items()})] += 1
        for b in BLOCKS:
            allr[b].append(mean[b])
    freq = [{"ranks": list(k), "freq": v / N_BOOT} for k, v in cnt.most_common()]
    out = {"meta": {"script": "tools/_p1552_gamma_bootstrap_archive.py",
                    "task": "bootstrap of block allocation over reference batches",
                    "n_batches": len(gammas), "n_boot": N_BOOT, "source": "p3d_gamma_real_vs_blank.json"},
           "batch_gammas": gammas, "point_allocation": list(point), "frequencies": freq,
           "block_gamma": {b: {"mean": float(np.mean(allr[b])), "sd": float(np.std(allr[b], ddof=1)),
                               "ci95": [float(np.percentile(allr[b], 2.5)), float(np.percentile(allr[b], 97.5))]}
                           for b in BLOCKS}}
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("point allocation:", point)
    for f in freq:
        print("  ranks", f["ranks"], "freq", round(f["freq"], 3))
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
