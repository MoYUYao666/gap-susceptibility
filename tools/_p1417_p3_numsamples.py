# -*- coding: utf-8 -*-
r"""P3: protocol ablation at the crossing - vary only the number of training samples.

Runs rank 6, seed 42, three epochs with --num-samples 12, 32 and 64. Only the sample-window size changes, so any shift of the
crossing is a controlled protocol effect rather than a script-version artefact.

Output: outputs/analysis/p3_numsamples_ablation.json ; log outputs/analysis/_p1417_numsamples.log

    conda run -n pytorch python tools/_p1417_p3_numsamples.py
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
SCRIPT = os.path.join(REPO, "paper3", "scripts", "run_training.py")
OUT = os.path.join(REPO, "outputs", "analysis", "p3_numsamples_ablation.json")
LOG = os.path.join(REPO, "outputs", "analysis", "_p1417_numsamples.log")
RANK, SEED, EPOCHS = 6, 42, 3
NS = [12, 32, 64]  # full protocol ablation; the default 20 is the existing seed-42 r=6 baseline (+115.0)


def main() -> int:
    env = dict(os.environ)
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONIOENCODING": "utf-8"})
    payload = {"protocol": "rank 6, seed 42, three epochs; only --num-samples varies (16 train / 4 eval by design)",
               "runs": {}}
    if os.path.exists(OUT):
        payload = json.load(io.open(OUT, encoding="utf-8"))
    logf = io.open(LOG, "a", encoding="utf-8")
    for n in NS:
        key = f"n{n}"
        if key in payload["runs"] and payload["runs"][key].get("ok"):
            print("  skip", key, flush=True)
            continue
        t0 = time.time()
        cmd = [sys.executable, SCRIPT, "--rank", str(RANK), "--seed", str(SEED), "--epochs", str(EPOCHS),
               "--num-samples", str(n)]
        logf.write("\n==== %s\n" % " ".join(cmd))
        logf.flush()
        r = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=5400)
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        logf.write(out)
        logf.flush()
        es = [v for _, v in sorted((int(m.group(1)), float(m.group(2)))
                                    for m in re.finditer(r"E\((\d+)\)\s*=\s*([0-9.]+)", out))]
        ok = r.returncode == 0 and len(es) >= 2 and es[-1] == es[-1]
        entry = {"num_samples": n, "rank": RANK, "seed": SEED, "E": es, "ok": ok,
                 "delta_E": (es[-1] - es[0]) if ok else None,
                 "elapsed_min": round((time.time() - t0) / 60, 1)}
        payload["runs"][key] = entry
        print(f"  num-samples={n}: E={es} ΔE={entry['delta_E']} ok={ok} ({entry['elapsed_min']} min)", flush=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    logf.close()
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
