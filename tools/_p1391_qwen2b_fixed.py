# -*- coding: utf-8 -*-
r"""P3: corrected local Qwen2-VL-2B crossing check.

The first attempt passed only --rank, but the Qwen training script uses --llm-rank for the actual adapter rank (uniform
config keeps a base rank of 4 unless overridden), so both runs trained the same adapter and produced identical
trajectories. This rerun passes --llm-rank explicitly.

Output: outputs/analysis/p3_qwen2b_crossing_fixed.json ; log outputs/analysis/_p1391_qwen.log

    conda run -n pytorch python tools/_p1391_qwen2b_fixed.py
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "paper3", "scripts", "run_training_qwen.py")
MODEL = os.path.join(REPO, "models", "Qwen2-VL-2B-Instruct")
OUT = os.path.join(REPO, "outputs", "analysis", "p3_qwen2b_crossing_fixed.json")
LOG = os.path.join(REPO, "outputs", "analysis", "_p1391_qwen.log")
JOBS = [(5, 42), (6, 42)]
EPOCHS = 3


def main() -> int:
    env = dict(os.environ)
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONIOENCODING": "utf-8"})
    payload = {"protocol": "local Qwen2-VL-2B-Instruct, blank-image protocol, seed 42, 3 epochs; --llm-rank set to the "
                          "same value as --rank so the adapter rank actually varies",
               "model": "models/Qwen2-VL-2B-Instruct", "runs": {}}
    logf = io.open(LOG, "a", encoding="utf-8")
    for rank, seed in JOBS:
        key = f"r{rank}_s{seed}"
        t0 = time.time()
        cmd = [sys.executable, SCRIPT, "--rank", str(rank), "--llm-rank", str(rank), "--seed", str(seed),
               "--epochs", str(EPOCHS), "--model-path", MODEL]
        logf.write("\n==== %s\n" % " ".join(cmd))
        logf.flush()
        r = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=7200)
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        logf.write(out)
        logf.flush()
        es = [v for _, v in sorted((int(m.group(1)), float(m.group(2)))
                                    for m in re.finditer(r"E\((\d+)\)\s*=\s*([0-9.]+)", out))]
        trainable = re.findall(r"Trainable:\s*([0-9.]+)M", out)
        ok = r.returncode == 0 and len(es) >= 2 and es[-1] == es[-1]
        entry = {"rank": rank, "seed": seed, "epochs": EPOCHS, "E": es, "ok": ok,
                 "delta_E": (es[-1] - es[0]) if ok else None,
                 "trainable_M": float(trainable[0]) if trainable else None,
                 "elapsed_min": round((time.time() - t0) / 60, 1), "returncode": r.returncode}
        payload["runs"][key] = entry
        print(f"  {key}: E={es} ΔE={entry['delta_E']} trainable={entry['trainable_M']}M ok={ok}", flush=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    logf.close()
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
