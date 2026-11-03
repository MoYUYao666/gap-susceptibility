# -*- coding: utf-8 -*-
r"""Report how long the LLaVA run is really taking, from its own log, and project the finish time.

The run prints one line per epoch, so the log's modification time is the only progress signal. This reads
the raw bytes (the file is UTF-16 on this machine), pairs the startup parameters with the epoch lines, and
computes the per-step cost and the projected completion.

    python tools/_p939_llava_eta.py
"""
from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOG = REPO / "outputs" / "analysis" / "_p838_llava.out"
OUT = REPO / "outputs" / "llava_sites"


def read_log(p: Path) -> str:
    raw = p.read_bytes()
    for enc in ("utf-16-le", "utf-8"):
        try:
            t = raw.decode(enc)
            if t.count("\x00") < len(t) // 10:
                return t.replace("\x00", "")
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def main() -> int:
    txt = read_log(LOG)
    pairs = re.search(r"(\d+)\s+training pairs and (\d+)\s+held-out", txt)
    eps = re.findall(r"epoch (\d+)/(\d+)\s+loss ([\d.]+)", txt)
    mtime = os.path.getmtime(LOG)
    started = None
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-CimInstance Win32_Process -Filter \"ProcessId=40300\").CreationDate"],
        capture_output=True)
    # the epoch count is what matters here, and the process start is known from the session log
    print(f"  log: {LOG.name}, last write {time.strftime('%H:%M:%S', time.localtime(mtime))}")
    if pairs:
        n_train, n_eval = int(pairs.group(1)), int(pairs.group(2))
        print(f"  training pairs {n_train}, held-out {n_eval}")
    print(f"  epoch lines in the log: {eps if eps else 'none'}")

    args = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-CimInstance Win32_Process -Filter \"ProcessId=40300\").CommandLine"],
        capture_output=True).stdout.decode("utf-8", "replace")
    m = re.search(r"--batch (\d+)", args)
    batch = int(m.group(1)) if m else None
    m = re.search(r"--max-len (\d+)", args)
    maxlen = int(m.group(1)) if m else None
    m = re.search(r"--epochs (\d+)", args)
    epochs = int(m.group(1)) if m else None
    m = re.search(r"--arms ([\w,]+)", args)
    arms = m.group(1).split(",") if m else []
    m = re.search(r"--seeds (\d+)", args)
    seeds = int(m.group(1)) if m else None
    print(f"  batch {batch}, max-len {maxlen}, epochs {epochs}, arms {arms}, seeds {seeds}")

    if pairs and batch and epochs and eps:
        steps = -(-n_train // batch)
        # the log line for epoch 1 was written when the epoch finished
        start = time.mktime(time.strptime("2026-10-15 13:02:42", "%Y-%m-%d %H:%M:%S"))
        ep1_done = mtime
        sec_per_epoch = ep1_done - start
        per_step = sec_per_epoch / steps
        run_total = sec_per_epoch * epochs
        done = len([e for e in eps if e[0] == "1"])
        print()
        print(f"  steps per epoch      : {steps} (batch {batch})")
        print(f"  epoch 1 wall time    : {sec_per_epoch / 60:.0f} min "
              f"({sec_per_epoch:.0f} s), {per_step:.1f} s per step")
        print(f"  one run (3 epochs)   : {run_total / 3600:.1f} h")
        n_runs = len(arms) * (seeds or 1)
        print(f"  runs in the queue    : {n_runs} ({len(arms)} arms x {seeds} seeds)")
        finished = len(list(OUT.glob('*.json'))) if OUT.exists() else 0
        remaining_runs = n_runs - finished
        print(f"  finished runs on disk: {finished}")
        eta = time.time() + remaining_runs * run_total
        print(f"  projected finish     : {time.strftime('%Y-%m-%d %H:%M', time.localtime(eta))} "
              f"({remaining_runs * run_total / 3600:.1f} h from now)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
