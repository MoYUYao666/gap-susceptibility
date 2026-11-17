#!/usr/bin/env python3
"""Descriptive TextVQA Qwen2-VL checkpoint-selection pilot."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "outputs/paper_b/qwen_vqa"
OUT = ROOT / "paper_b_v2/results/qwen_vqa_pilot.json"


def main():
    runs = []
    for p in sorted(SRC.glob("*.json")):
        if p.name == "summary.json":
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        em = [float(e["em"]) for e in d["epochs"]]
        runs.append({"run": p.stem, "rank": d["run"]["rank"], "seed": d["run"]["seed"],
                     "em": em, "last_oracle": bool(np.isclose(em[-1], max(em))),
                     "gap": float(max(em) - em[-1]), "train_loss": [e["train_loss"] for e in d["epochs"]]})
    last_oracle = int(sum(r["last_oracle"] for r in runs))
    gaps = [r["gap"] for r in runs]
    out = {
        "n_runs": len(runs), "task": "TextVQA Qwen2-VL-2B 4-bit LoRA",
        "epochs": 3, "train_samples": 80, "test_samples": 12,
        "last_oracle": last_oracle, "last_oracle_fraction": last_oracle / len(runs),
        "mean_gap": float(np.mean(gaps)), "runs": runs,
        "note": "Small second-task pilot; not a full VQA matrix.",
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
