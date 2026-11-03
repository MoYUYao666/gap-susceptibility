# -*- coding: utf-8 -*-
r"""P3: measure whether the crossing moves with the protocol - r=5 at num_samples 12 and 64.

The r=6 values at these windows already exist (+40.5 at 12, +30.0 at 64; default 20 is +115.0), so running r=5 at
the same two windows turns "the crossing belongs to the protocol" from an inference into a measured shift: if the sign
at r=5 changes with the window, the crossing has moved relative to the default.

Output: outputs/analysis/p3_protocol_shift.json ; log outputs/analysis/_p1476_protocol_shift.log

    conda run -n pytorch python tools/_p1476_p3_protocol_shift.py
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
OUT = os.path.join(REPO, "outputs", "analysis", "p3_protocol_shift.json")
LOG = os.path.join(REPO, "outputs", "analysis", "_p1476_protocol_shift.log")
RANK, SEED, EPOCHS = 5, 42, 3
NS = [12, 64]


def main() -> int:
    env = dict(os.environ)
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONIOENCODING": "utf-8"})
    payload = {"protocol": "rank 5, seed 42, three epochs; only num-samples varies (12 / 64)", "runs": {}}
    if os.path.exists(OUT):
        payload = json.load(io.open(OUT, encoding="utf-8"))
    logf = io.open(LOG, "a", encoding="utf-8")
    for n in NS:
        key = f"r5_n{n}"
        if key in payload["runs"] and payload["runs"][key].get("ok"):
            print("  skip", key, flush=True)
            continue
        t0 = time.time()
        cmd = [sys.executable, SCRIPT, "--rank", str(RANK), "--seed", str(SEED), "--epochs", str(EPOCHS),
               "--num-samples", str(n)]
        logf.write("\n==== %s\n" % " ".join(cmd))
        logf.flush()
        try:
            r = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=7200)
        except subprocess.TimeoutExpired:
            payload["runs"][key] = {"num_samples": n, "ok": False, "timeout": True}
            io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
            print(f"  {key}: TIMEOUT", flush=True)
            continue
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        logf.write(out)
        logf.flush()
        es = [v for _, v in sorted((int(m.group(1)), float(m.group(2)))
                                   for m in re.finditer(r"E\((\d+)\)\s*=\s*([0-9.]+)", out))]
        ok = r.returncode == 0 and len(es) >= 2
        entry = {"num_samples": n, "rank": RANK, "seed": SEED, "E": es, "ok": ok,
                 "delta_E": (es[-1] - es[0]) if ok else None,
                 "elapsed_min": round((time.time() - t0) / 60, 1)}
        payload["runs"][key] = entry
        print(f"  {key}: E={es} ΔE={entry['delta_E']} ok={ok} ({entry['elapsed_min']} min)", flush=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    logf.close()
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
