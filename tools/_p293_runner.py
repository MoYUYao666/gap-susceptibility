# -*- coding: utf-8 -*-
r"""Wait for the single GPU to be free, then run one stage of the DINOv2 heterogeneous control.

This project has ONE GPU (RTX 4060 Laptop, 8 GB) and a hard rule of strictly serial GPU work.
Another teammate is running a full-fine-tuning learning-rate sweep whose python process holds
~7.2 GB of it.  This watcher blocks until no python.exe holds GPU memory, then shells out to
`tools/_p293_dinov2_hetero_strict.py all ...`, whose per-arm skip logic makes the stage
idempotent and restartable.

Usage:
    python tools/_p293_runner.py --head fitted --seeds 42 123 456 --tag fitted
    python tools/_p293_runner.py --head random --seeds 42 123 456 --tag random
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
SCRIPT = REPO / "tools" / "_p293_dinov2_hetero_strict.py"
RUNLOG = REPO / "outputs" / "analysis" / "dinov2_hetero" / "logs"
STATE = REPO / "outputs" / "analysis" / "dinov2_hetero" / "runner_state.json"


def ts():
    return datetime.now().strftime("%H:%M:%S")


def log(msg):
    print("[%s] %s" % (ts(), msg), flush=True)


def gpu_busy():
    """PIDs of python processes currently holding GPU memory.

    NOTE: under WDDM, `nvidia-smi --query-compute-apps=used_memory` reports `[N/A]`, so the
    memory column must NOT be parsed as an integer (measured: it crashed the first version of
    this watcher).  Only the PID is used, and the process name is resolved via tasklist.
    """
    try:
        p = subprocess.run(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=30,
                           encoding="utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        log("nvidia-smi failed (%s); assuming busy" % e)
        return ["unknown"]
    busy = []
    for line in (p.stdout or "").splitlines():
        pid = line.strip()
        if not pid.isdigit():
            continue
        try:
            q = subprocess.run(["tasklist", "/FI", "PID eq %s" % pid, "/FO", "CSV", "/NH"],
                               capture_output=True, text=True, timeout=30,
                               encoding="utf-8", errors="replace")
            name = (q.stdout or "").split(",")[0].strip('"').lower()
        except Exception:  # noqa: BLE001
            name = ""
        if "python" in name:
            busy.append(pid)
    return busy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", default="fitted", choices=["fitted", "random"])
    ap.add_argument("--seeds", nargs="*", type=int, default=[42, 123, 456])
    ap.add_argument("--tag", default=None)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--max-samples", type=int, default=5000)
    ap.add_argument("--max-wait-min", type=float, default=300)
    ap.add_argument("--poll-sec", type=int, default=45)
    ap.add_argument("--fit-head-first", action="store_true")
    # Scope guard: the stage must run ONLY the arms it was asked for.  Without this, a watcher
    # relaunch drove the full three-arm grid straight past an agreed two-arm scope (measured
    # 2026-10-12) -- auto-continuation has to encode the current scope, not just "keep going".
    ap.add_argument("--arms", nargs="*", default=None,
                    help="restrict the stage to these arms; unset means all three")
    a = ap.parse_args()

    tag = a.tag or a.head
    RUNLOG.mkdir(parents=True, exist_ok=True)
    STATE.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    waited = 0.0
    while True:
        busy = gpu_busy()
        if not busy:
            break
        if (time.time() - t0) / 60.0 > a.max_wait_min:
            log("waited %.0f min, still busy %s -> giving up this watcher" % (
                (time.time() - t0) / 60.0, busy))
            STATE.write_text(json.dumps(
                {"tag": tag, "status": "gave_up_waiting", "busy": busy,
                 "at": datetime.now(timezone.utc).isoformat()}, indent=2), encoding="utf-8")
            return 2
        log("GPU busy: %s  (waited %.0f min)" % (busy, (time.time() - t0) / 60.0))
        time.sleep(a.poll_sec)
    waited = time.time() - t0
    log("GPU free after %.1f min; starting head=%s" % (waited / 60.0, a.head))

    STATE.write_text(json.dumps(
        {"tag": tag, "status": "running", "waited_min": round(waited / 60, 2),
         "started_at": datetime.now(timezone.utc).isoformat()}, indent=2), encoding="utf-8")

    rc = 0
    if a.fit_head_first and a.head == "fitted":
        hp = REPO / "outputs" / "analysis" / "dinov2_hetero" / "heads" / "fitted.pt"
        if hp.exists():
            log("head already fitted -> %s" % hp)
        else:
            cmd = [PY, str(SCRIPT), "head", "--head", "fitted", "--epochs", "10",
                   "--batch", str(a.batch)]
            log("RUN " + " ".join(cmd[1:]))
            with open(RUNLOG / "head_fit.log", "w", encoding="utf-8") as fh:
                rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT,
                                    cwd=str(REPO)).returncode
            log("head fit rc=%d" % rc)
            if rc != 0:
                STATE.write_text(json.dumps(
                    {"tag": tag, "status": "head_fit_failed", "rc": rc}, indent=2),
                    encoding="utf-8")
                return rc

    cmd = [PY, str(SCRIPT), "all", "--head", a.head, "--epochs", str(a.epochs),
           "--batch", str(a.batch), "--max-samples", str(a.max_samples)]
    cmd += ["--seeds"] + [str(s) for s in a.seeds]
    if a.arms:
        cmd += ["--arms"] + list(a.arms)
    log("RUN " + " ".join(cmd[1:]))
    with open(RUNLOG / ("all_%s.log" % tag), "w", encoding="utf-8") as fh:
        rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=str(REPO)).returncode
    log("all rc=%d after %.1f min" % (rc, (time.time() - t0) / 60.0))

    STATE.write_text(json.dumps(
        {"tag": tag, "status": "done" if rc == 0 else "failed", "rc": rc,
         "waited_min": round(waited / 60, 2),
         "total_min": round((time.time() - t0) / 60, 2),
         "finished_at": datetime.now(timezone.utc).isoformat()}, indent=2), encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main())
