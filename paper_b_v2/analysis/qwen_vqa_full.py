#!/usr/bin/env python3
"""TextVQA/Qwen2-VL full rank-sweep analysis (4 ranks x 4 seeds)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "outputs/paper_b/qwen_vqa"
OUT = ROOT / "paper_b_v2/results/qwen_vqa_full.json"


def main():
    runs = []
    for p in sorted(SRC.glob("*.json")):
        if p.name == "summary.json":
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        em = [float(e["em"]) for e in d["epochs"]]
        runs.append({"run": p.stem, "rank": int(d["run"]["rank"]), "seed": int(d["run"]["seed"]),
                     "em": em, "last_oracle": bool(np.isclose(em[-1], max(em))),
                     "gap": float(max(em) - em[-1])})
    ranks = {}
    for rank in sorted(set(r["rank"] for r in runs)):
        rr = [r for r in runs if r["rank"] == rank]
        ranks[str(rank)] = {
            "n": len(rr),
            "last_oracle": int(sum(r["last_oracle"] for r in rr)),
            "last_oracle_fraction": sum(r["last_oracle"] for r in rr) / len(rr),
            "mean_gap": float(np.mean([r["gap"] for r in rr])),
        }
    out = {"n_runs": len(runs), "task": "TextVQA Qwen2-VL-2B 4-bit LoRA",
           "ranks": ranks, "runs": runs, "note": "16-run rank sweep, 80 train / 12 test, 3 epochs."}
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
