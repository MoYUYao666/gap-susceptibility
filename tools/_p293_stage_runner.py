# -*- coding: utf-8 -*-
r"""Watch the three seed-42 DINOv2 arms, then stop the queue and run the random-head control.

The Lead's decision (2026-10-12) is to answer the one core question -- does the adaptation-site
ordering reproduce or reverse on a heterogeneous pairing whose vision tower is not contrastively
pretrained -- with n=1 seed per arm, because a full 3-seed grid would occupy the single GPU for
~7.4 h while another teammate waits for it.

That means three configurations are needed and the rest of the queued grid is surplus:

    text_only/seed42    both/seed42    vision_only/seed42

Two timing facts drive this watcher:

* the running `all ... --seeds 42 123 456` driver processes arms in the order
  text_only -> both -> vision_only, and WITHIN each arm the seeds in order, so text_only/seed42
  finishes first and then a whole hour would be spent on text_only/seed123;
* the `all` driver's per-arm skip logic makes any restart cheap and idempotent: a run whose
  results.json exists is skipped, so killing the driver and relaunching never redoes work.

So this watcher
  1. waits until `both/seed42/results.json` exists (by then text_only/seed42 is already done);
  2. terminates the running `all` driver, which at that moment is on its first surplus run;
  3. relaunches the driver so that both/seed42 is skipped and vision_only/seed42 runs next;
  4. once all three seed-42 arms are archived, runs the random-head control stage.

USAGE
    python tools/_p293_stage_runner.py --mode fitted-seed42
    python tools/_p293_stage_runner.py --mode random
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.chdir(REPO)
PY = sys.executable
STAGE = REPO / "tools" / "_p293_dinov2_hetero_strict.py"
RUNNER = REPO / "tools" / "_p293_runner.py"
LOGS = REPO / "outputs" / "analysis" / "dinov2_hetero" / "logs"

SEED42 = ["text_only", "both", "vision_only"]


def ts():
    return datetime.now().strftime("%H:%M:%S")


def log(m):
    print("[%s] %s" % (ts(), m), flush=True)


def res(head, arm, seed=42):
    return (REPO / "outputs" / "analysis" / "dinov2_hetero" / head / arm
            / ("seed%d" % seed) / "results.json")


def python_procs():
    """(pid, cmdline) of python processes whose command line mentions our script."""
    out = subprocess.run(["wmic", "process", "where", "name='python.exe'", "get",
                          "ProcessId,CommandLine", "/format:csv"],
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    rows = []
    for line in (out.stdout or "").splitlines():
        if "_p293_dinov2_hetero_strict.py" in line and "all" in line:
            parts = line.rsplit(",", 2)
            pid = parts[-1].strip()
            if pid.isdigit():
                rows.append(pid)
    return rows


def kill(pids, why):
    for pid in pids:
        log("taskkill /PID %s /F  (%s)" % (pid, why))
        subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")


def launch_stage(args, tag):
    cmd = [PY, str(RUNNER), "--head", args.head, "--tag", tag, "--fit-head-first"]
    cmd += ["--seeds"] + [str(s) for s in args.seeds]
    cmd += ["--epochs", str(args.epochs), "--batch", str(args.batch),
            "--max-samples", str(args.max_samples), "--max-wait-min", "120"]
    logf = LOGS / ("stage_%s.log" % tag)
    log("LAUNCH " + " ".join(cmd[1:]))
    with open(logf, "w", encoding="utf-8") as fh:
        return subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=str(REPO))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["fitted-seed42", "random"])
    ap.add_argument("--head", default="fitted")
    ap.add_argument("--seeds", nargs="*", type=int, default=[42])
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--max-samples", type=int, default=5000)
    ap.add_argument("--poll", type=int, default=60)
    a = ap.parse_args()

    if a.mode == "fitted-seed42":
        log("waiting for both/seed42 (text_only/seed42 completes before it)...")
        while not res("fitted", "both").exists():
            time.sleep(a.poll)
        done = [arm for arm in SEED42 if res("fitted", arm).exists()]
        log("both/seed42 appeared; completed seed42 arms so far: %s" % done)
        pids = python_procs()
        if pids:
            kill(pids, "surplus seeds 123/456 no longer needed (Lead decision: n=1/arm)")
        else:
            log("no running 'all' driver found (already finished or none)")
        time.sleep(5)
        # relaunch so that completed arms are skipped and vision_only/seed42 runs
        launch_stage(a, "fitted_seed42_finish")
        log("relaunched; waiting for all three seed42 arms...")
        while not all(res("fitted", arm).exists() for arm in SEED42):
            time.sleep(a.poll)
        log("ALL THREE seed42 arms archived:")
        for arm in SEED42:
            log("  %s" % res("fitted", arm))
        log("now starting the random-head control stage")
        launch_stage(argparse.Namespace(head="random", seeds=[42], epochs=a.epochs,
                                       batch=a.batch, max_samples=a.max_samples),
                     "random")
        log("random-head stage launched; this watcher exits")
        return 0

    # mode == random: just drive the random-head control to completion
    log("driving random-head control for seeds %s" % a.seeds)
    launch_stage(a, "random")
    while not all(res("random", arm).exists() for arm in SEED42):
        time.sleep(a.poll)
    log("random-head control complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
