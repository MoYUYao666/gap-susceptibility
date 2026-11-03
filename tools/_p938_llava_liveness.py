# -*- coding: utf-8 -*-
r"""Decide whether the running LLaVA job is stuck or merely slow, and say why.

Signals available without attaching a debugger:

* **GPU utilisation** -- 99-100% means the device is busy, not idle-waiting;
* **GPU memory, sampled** -- a training step oscillates by a few MiB (activations, allocator), a hung
  kernel stays flat to the byte;
* **process CPU and write bytes** -- near zero for both is normal while CUDA works, but a host-side
  block (disk, lock, print) would show up as no GPU progress either;
* **step arithmetic** -- the job prints one line per epoch, and the startup log records the sample
  count, batch size and epoch count, so the expected wall time per epoch can be computed and compared
  with the time actually elapsed.

    python tools/_p938_llava_liveness.py [--seconds 60]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def gpu_sample() -> tuple[int, int]:
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu",
                          "--format=csv,noheader,nounits"], capture_output=True)
    txt = out.stdout.decode("utf-8", "ignore").strip().splitlines()[0]
    used, util = [int(x.strip()) for x in txt.split(",")]
    return used, util


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=60)
    ap.add_argument("--interval", type=float, default=2.0)
    a = ap.parse_args()

    print(f"  sampling the GPU every {a.interval:g}s for {a.seconds}s")
    mems, utils = [], []
    t_end = time.time() + a.seconds
    while time.time() < t_end:
        m, u = gpu_sample()
        mems.append(m)
        utils.append(u)
        time.sleep(a.interval)
    print(f"  GPU memory used: min {min(mems)} MiB, max {max(mems)} MiB, spread {max(mems) - min(mems)} MiB")
    print(f"  GPU utilisation: min {min(utils)}%, max {max(utils)}%, mean {sum(utils) / len(utils):.0f}%")

    spread = max(mems) - min(mems)
    busy = sum(1 for u in utils if u >= 50) / len(utils)
    print()
    if spread <= 2 and busy > 0.9:
        print("  READING: the device is busy but its memory footprint is frozen to the byte.")
        print("           That is the signature of a single kernel running far longer than it should,")
        print("           not of steady training (which reallocates a few MiB every step).")
    elif spread > 2 and busy > 0.9:
        print("  READING: the device is busy and its memory wobbles, so steps are completing.")
        print("           The job is slow rather than stuck.")
    else:
        print("  READING: the device is not consistently busy; the job may be waiting on the host.")

    # expected vs actual time
    log = REPO / "outputs" / "analysis" / "_p838_llava.out"
    if log.exists():
        raw = log.read_bytes()
        txt = raw.decode("utf-16-le", "replace") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else \
            raw.decode("utf-8", "replace")
        txt = txt.replace("\x00", "")
        pairs = re.search(r"(\d+)\s+training pairs", txt)
        ep = re.findall(r"epoch (\d+)/(\d+)\s+loss", txt)
        mtime = time.strftime("%H:%M:%S", time.localtime(log.stat().st_mtime))
        print()
        print(f"  run log: last write {mtime}, {len(ep)} epoch line(s) seen {ep}")
        if pairs:
            n = int(pairs.group(1))
            print(f"           training pairs in the log: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
