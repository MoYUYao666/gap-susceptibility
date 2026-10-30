# -*- coding: utf-8 -*-
r"""Time a few LLaVA configurations for a few steps each, to find what makes each step cost 72 s.

Measured 2026-10-15 16:21 on the run started at 16:08: `text_only_s42` holds **72.5 s per step** with
batch 2 and max-len 2048, and the new breakdown attributes **0.1 s to batch preparation and 345.8 s to
compute over five steps** -- so the cost is inside the forward/backward. At 600 steps per run that is
about 12 hours per run and 4.5 days for the queue.

This runs three short configurations (40 steps each, well under three minutes apiece) and reports the
seconds per step and the actual padded token counts, so the choice of what to change is made on
measurements rather than on guesses about padding or quantisation.

The current sweep must be stopped first: the device has 8.6 GB and no room for a second 7B model.

    python tools/_p942_llava_step_bench.py [--steps 40]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
LOGDIR = REPO / "outputs" / "analysis"

BASE = ["--samples", "400", "--eval-pairs", "8", "--epochs", "1", "--seeds", "1",
        "--lr", "1e-4", "--rank", "8", "--arms", "text_only"]

CONFIGS = [
    ("current: batch 2, max-len 2048", BASE + ["--batch", "2", "--max-len", "2048"]),
    ("batch 4, max-len 1024", BASE + ["--batch", "4", "--max-len", "1024"]),
    ("batch 8, max-len 1024", BASE + ["--batch", "8", "--max-len", "1024"]),
]


def read_log(p: Path) -> str:
    raw = p.read_bytes()
    t = raw.decode("utf-16-le", "replace") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else \
        raw.decode("utf-8", "replace")
    return t.replace("\x00", "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=40, help="steps to time per configuration")
    ap.add_argument("--configs", type=int, default=3)
    a = ap.parse_args()

    env = {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "HF_HUB_OFFLINE": "1",
           "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_PROGRESS_BARS": "1",
           "PYTORCH_ALLOC_CONF": "expandable_segments:True"}
    import os
    run_env = dict(os.environ)
    run_env.update(env)

    results = []
    for label, args in CONFIGS[: a.configs]:
        log = LOGDIR / f"_p942_bench_{len(results)}.log"
        if log.exists():
            log.unlink()
        cmd = [PY, "-u", "-X", "utf8", str(SCRIPT)] + args + [
            "--apply", "--report-every", "5", "--bench-steps", str(a.steps),
            "--out-dir", str(LOGDIR / "_p942_bench_records")]
        print(f"=== {label}")
        with open(log, "wb") as fh:
            t0 = time.time()
            proc = subprocess.run(cmd, cwd=REPO, env=run_env, stdout=fh, stderr=subprocess.STDOUT)
            wall = time.time() - t0
        txt = read_log(log)
        beats = re.findall(r"step (\d+)/\d+\s+loss ([\d.]+)\s+([\d.]+) s/step", txt)
        tok = re.findall(r"batch tokens:\s+(\d+)\s+mean\s+([\d.]+)", txt)
        shape = re.findall(r"sequence length in this batch:\s+(\d+)", txt)
        per = float(beats[-1][2]) if beats else None
        print(f"    wall {wall:.0f} s, heartbeats {len(beats)}, "
              f"per step {per if per else 'n/a'} s, tokens {tok if tok else 'n/a'}"
              f"{', seq len ' + shape[-1] if shape else ''}")
        results.append({"config": label, "wall_s": round(wall, 1), "sec_per_step": per,
                        "tokens": tok[-1] if tok else None})
        if proc.returncode not in (0, 1):
            print(f"    exit {proc.returncode} (may be the step cap)")

    print()
    print("=== summary")
    base = next((r for r in results if r["sec_per_step"]), None)
    for r in results:
        line = f"  {r['config']:<34} {r['sec_per_step'] if r['sec_per_step'] else 'n/a':>7} s/step"
        if base and r["sec_per_step"]:
            line += f"   speedup x{base['sec_per_step'] / r['sec_per_step']:.2f}"
        print(line)
    out = LOGDIR / "_p942_bench.json"
    out.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"  written {out.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
