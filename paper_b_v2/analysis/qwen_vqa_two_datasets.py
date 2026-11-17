#!/usr/bin/env python3
"""Two-task VQA rank sweep: TextVQA and VQAv2, Qwen2-VL-2B."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DIRS = {"textvqa": ROOT / "outputs/paper_b/qwen_textvqa", "vqav2": ROOT / "outputs/paper_b/qwen_vqav2"}
OUT = ROOT / "paper_b_v2/results/qwen_vqa_two_datasets.json"


def main():
    out = {"task": "Qwen2-VL-2B 4-bit LoRA VQA", "datasets": {}}
    for name, d in DIRS.items():
        runs = []
        for p in sorted(d.glob("*.json")):
            if p.name == "summary.json":
                continue
            x = json.loads(p.read_text(encoding="utf-8"))
            em = [float(e["em"]) for e in x["epochs"]]
            rows = x["run"]
            runs.append({"rank": int(rows["rank"]), "seed": int(rows["seed"]), "em": em,
                         "last_oracle": bool(np.isclose(em[-1], max(em))),
                         "gap": float(max(em) - em[-1])})
        ranks = {}
        for rank in sorted(set(r["rank"] for r in runs)):
            rr = [r for r in runs if r["rank"] == rank]
            ranks[str(rank)] = {"n": len(rr), "last_oracle": int(sum(r["last_oracle"] for r in rr)),
                                "last_oracle_fraction": sum(r["last_oracle"] for r in rr) / len(rr),
                                "mean_gap": float(np.mean([r["gap"] for r in rr]))}
        out["datasets"][name] = {"n_runs": len(runs), "ranks": ranks, "runs": runs}
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
