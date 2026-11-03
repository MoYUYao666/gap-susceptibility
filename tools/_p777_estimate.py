# -*- coding: utf-8 -*-
r"""Estimate the scale-up wall time from the observed step rate, before committing hours to it.

Observed: 437 of 782 steps in 4 minutes 43 seconds, so about 1.5 steps per second. This turns that
into a per-run and total estimate for the configured grid, so the scope can be cut deliberately
rather than discovered half way through.

    python tools/_p777_estimate.py
"""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps-per-epoch", type=int, default=782)
    ap.add_argument("--steps-per-second", type=float, default=1.5)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--arms", type=int, default=2)
    ap.add_argument("--eval-captions", type=int, default=15010)
    ap.add_argument("--eval-rate", type=float, default=350.0,
                    help="caption rows embedded per second (measured: 50032 rows in 146 s)")
    ap.add_argument("--eval-matrix-seconds", type=float, default=90.0)
    a = ap.parse_args()

    train_s = a.steps_per_epoch / a.steps_per_second * a.epochs
    eval_s = a.eval_captions / a.eval_rate + a.eval_matrix_seconds
    per_run = train_s + eval_s
    runs = a.arms * a.seeds
    total = per_run * runs

    print(f"  steps/epoch {a.steps_per_epoch} at {a.steps_per_second} it/s -> "
          f"{a.steps_per_epoch / a.steps_per_second / 60:.1f} min/epoch")
    print(f"  training one run: {train_s / 60:.1f} min ({a.epochs} epochs)")
    print(f"  evaluating one run ({a.eval_captions} captions): {eval_s / 60:.1f} min")
    print(f"  per run total: {per_run / 60:.1f} min")
    print()
    print(f"  configured grid: {a.arms} arms x {a.seeds} seeds = {runs} runs")
    print(f"  TOTAL: {total / 60:.1f} min = {total / 3600:.2f} h")
    print()

    print("  alternative scopes:")
    for label, arms, seeds in (
        ("1 arm x 1 seed  (a single large-scale point)", 1, 1),
        ("1 arm x 2 seeds", 1, 2),
        ("2 arms x 1 seed", 2, 1),
        ("2 arms x 2 seeds", 2, 2),
        ("2 arms x 3 seeds (current)", 2, 3),
    ):
        t = per_run * arms * seeds
        print(f"    {label:<44} {t / 60:>6.1f} min = {t / 3600:.2f} h")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
