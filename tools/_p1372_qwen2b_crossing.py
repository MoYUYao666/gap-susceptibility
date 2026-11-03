# -*- coding: utf-8 -*-
r"""P3: local decoder-VLM crossing check with Qwen2-VL-2B (no cloud).

Runs the Qwen training script (same blank-image protocol) at ranks 5 and 6, seed 42, three epochs, using the local
Qwen2-VL-2B-Instruct weights. The 7B model used in the paper requires a cloud GPU; this is an explicitly smaller local
replication, reported as such.

Output: outputs/analysis/p3_qwen2b_crossing.json ; log outputs/analysis/_p1372_qwen.log

    conda run -n pytorch python tools/_p1372_qwen2b_crossing.py
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
OUT = os.path.join(REPO, "outputs", "analysis", "p3_qwen2b_crossing.json")
LOG = os.path.join(REPO, "outputs", "analysis", "_p1372_qwen.log")
JOBS = [(5, 42), (6, 42)]
EPOCHS = 3


def main() -> int:
    env = dict(os.environ)
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONIOENCODING": "utf-8"})
    payload = {"protocol": "local Qwen2-VL-2B-Instruct, blank-image protocol, run_training_qwen.py defaults, seed 42, 3 epochs",
               "model": "models/Qwen2-VL-2B-Instruct", "runs": {}}
    if os.path.exists(OUT):
        payload = json.load(io.open(OUT, encoding="utf-8"))
    logf = io.open(LOG, "a", encoding="utf-8")
    for rank, seed in JOBS:
        key = f"r{rank}_s{seed}"
        if key in payload["runs"] and payload["runs"][key].get("ok"):
            print("  skip", key, flush=True)
            continue
        t0 = time.time()
        cmd = [sys.executable, SCRIPT, "--rank", str(rank), "--seed", str(seed), "--epochs", str(EPOCHS),
               "--model-path", MODEL]
        logf.write("\n==== %s\n" % " ".join(cmd))
        logf.flush()
        r = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=7200)
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        logf.write(out)
        logf.flush()
        es = [v for _, v in sorted((int(m.group(1)), float(m.group(2)))
                                    for m in re.finditer(r"E\((\d+)\)\s*=\s*([0-9.]+)", out))]
        ok = r.returncode == 0 and len(es) >= 2 and es[-1] == es[-1]
        entry = {"rank": rank, "seed": seed, "epochs": EPOCHS, "E": es, "ok": ok,
                 "delta_E": (es[-1] - es[0]) if ok else None,
                 "elapsed_min": round((time.time() - t0) / 60, 1), "returncode": r.returncode}
        payload["runs"][key] = entry
        print(f"  {key}: E={es} ΔE={entry['delta_E']} ok={ok} ({entry['elapsed_min']} min)", flush=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    logf.close()
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
