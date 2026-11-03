# -*- coding: utf-8 -*-
r"""PR R1.6 / task-7 -- driver for the three full-FT extensions.

A. lower learning rates  : lr in {1e-7, 3e-7} x seeds {42, 123}
B. high-lr seeds        : lr in {3e-5, 1e-4, 3e-4} x seeds {123, 999}  (each cell -> 3 seeds)
C. 1e-4 reproduction    : lr = 1e-4, seed 42, trained a second time into a separate output and
                          checkpoint directory, to test whether that run is reproducible at all
                          (the 2026-08 archive diverged from the first reproduction at epoch 4)

Each stage runs `tools/_p263_fullft_lr_sweep.py` as a subprocess with `--resume`, so the stages
are idempotent and can be re-run after an interruption.  The merged answer file
`outputs/analysis/pr_fullft_lr_sweep_full.json` is produced separately by
`tools/_p265_fullft_reeval.py` (it merges the extension file with checkpoint re-evaluations and
never drops earlier runs).

    python tools\_p295_fullft_extend.py                 # print the plan
    python tools\_p295_fullft_extend.py --apply         # A + B (C only with --include-c)
    python tools\_p295_fullft_extend.py --apply --include-c --only-c
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P263 = REPO / "tools" / "_p263_fullft_lr_sweep.py"
EXT = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep_ext.json"
FULL = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep_full.json"
REPRO = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep_repro.json"
REPRO_CKPT = REPO / "outputs" / "analysis" / "pr_fullft_repro_ckpt"
T0 = time.time()


def log(m):
    print("  [%7.1fs] %s" % (time.time() - T0, m), flush=True)


def run(args, tag):
    log("%s: %s" % (tag, " ".join(args)))
    p = subprocess.run([sys.executable, str(P263)] + args, cwd=str(REPO))
    if p.returncode != 0:
        raise SystemExit("%s failed with exit code %d" % (tag, p.returncode))
    return p.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--include-c", action="store_true", help="also run the 1e-4 reproduction")
    ap.add_argument("--only-c", action="store_true")
    args = ap.parse_args()

    stages = {
        "A": ["--apply", "--lrs", "1e-7,3e-7", "--seeds", "42,123", "--resume",
              "--out", str(EXT)],
        "B": ["--apply", "--lrs", "3e-5,1e-4,3e-4", "--seeds", "123,999", "--resume",
              "--out", str(EXT)],
        "C": ["--apply", "--lrs", "1e-4", "--seeds", "42", "--resume",
              "--out", str(REPRO), "--ckpt-dir", str(REPRO_CKPT)],
    }
    print("plan:")
    for k, v in stages.items():
        print("  %s: %s" % (k, " ".join(v)))
    print("\nresume base for A/B: %s (%s)"
          % (EXT.relative_to(REPO),
             "exists, %d runs" % len(json.load(open(EXT, encoding="utf-8"))["runs"])
             if EXT.exists() else "MISSING -- copy %s first" % FULL.relative_to(REPO)))
    if not args.apply:
        print("(dry run; add --apply)")
        return 0
    if not EXT.exists():
        assert FULL.exists(), "neither the extension base nor the merged file exists"
        shutil.copyfile(FULL, EXT)
        log("created resume base %s from %s" % (EXT.name, FULL.name))

    if not args.only_c:
        run(stages["A"], "A (low lr)")
        run(stages["B"], "B (high-lr seeds)")
    if args.include_c or args.only_c:
        run(stages["C"], "C (1e-4 reproduction)")
    log("done; now run: python tools\\_p265_fullft_reeval.py --apply --reuse-raw --sweep %s"
        % EXT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
