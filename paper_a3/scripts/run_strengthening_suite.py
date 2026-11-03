# -*- coding: utf-8 -*-
r"""Run the strengthening suite for A3 in the right order, waiting for the training-length ablation to finish first.

Stages (sequential, each skipped if its output already exists):
  1. epoch-ablation grid      (already running elsewhere; this script waits for its 12 JSON records)
  2. adapter export           (6 adapters at the joint site for the transfer matrix)
  3. cross-corpus transfer    (inference only)
  4. second backbone          (GeoRSCLIP ViT-B/32, 16 cells)
  5. large backbone subset    (RemoteCLIP ViT-L/14, batch 8, 4 cells)

Logs: paper_a3/runs/suite_log.txt

Usage
  python run_strengthening_suite.py [--wait-minutes 180]
"""
import argparse
import io
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
LOG = os.path.join(ROOT, "runs", "suite_log.txt")


def log(line):
    with io.open(LOG, "a", encoding="utf-8", newline="") as f:
        f.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), line))
    print(line, flush=True)


def count(d, pattern="*.json"):
    import glob
    return len(glob.glob(os.path.join(ROOT, "runs", d, pattern)))


def run_stage(name, script, args=(), expect=None, dirname=None):
    if dirname and expect and count(dirname) >= expect:
        log("skip %s (already has %d/%d)" % (name, count(dirname), expect))
        return True
    log("start %s" % name)
    started = time.time()
    proc = subprocess.run([PY, os.path.join(ROOT, "scripts", script)] + list(args),
                          cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ok = proc.returncode == 0
    with io.open(LOG, "a", encoding="utf-8", newline="") as f:
        f.write(proc.stdout.decode("utf-8", "replace")[-4000:] + "\n")
    log("%s %s in %.1f min" % ("done" if ok else "FAILED", name, (time.time() - started) / 60))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait-minutes", type=int, default=180)
    args = ap.parse_args()
    os.makedirs(os.path.join(ROOT, "runs"), exist_ok=True)
    deadline = time.time() + args.wait_minutes * 60
    log("suite started; waiting for the epoch ablation (12 cells)")
    while time.time() < deadline:
        n = count("epoch_ablation")
        if n >= 6:
            log("epoch ablation complete: %d/6" % n)
            break
        time.sleep(60)
    else:
        log("epoch ablation did not finish in %d minutes; continuing anyway with %d cells" % (
            args.wait_minutes, count("epoch_ablation")))

    stages = [
        ("adapter export", "run_adapter_export.py", ("--run",), 6, "adapter_export"),
        ("transfer matrix", "run_transfer_eval.py", (), None, None),
        ("second backbone", "run_georsclip_grid.py", ("--run",), 16, "georsclip_10k"),
        ("large backbone subset", "run_l14_subset.py", ("--run",), 4, "l14_subset"),
        ("human-rich arm", "run_humanrich_grid.py", ("--run",), 4, "humanrich_10k"),
    ]
    ok_all = True
    for name, script, sargs, expect, dirname in stages:
        ok = run_stage(name, script, sargs, expect, dirname)
        ok_all = ok_all and ok
    log("suite finished: %s" % ("all stages ok" if ok_all else "some stage failed - see log"))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
