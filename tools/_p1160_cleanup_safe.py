# -*- coding: utf-8 -*-
r"""Remove only the regenerable scratch in the workspace, with guards.

Scope is deliberately tiny: `__pycache__` directories and two stray log files at the repo root. Everything else
(datasets, model weights, checkpoints, the backup snapshot) is left alone pending the operator's choice, because
each of those has a real cost to rebuild and the disks currently have 90 GB / 113 GB free.

Guards, so a rerun cannot go wide:
  * only directories literally named `__pycache__`, and only under this repo;
  * only the two named root-level log files, checked by name;
  * refuses to touch anything under `data/`, `models/`, `outputs/`, `backups/`, `paper*`, `.git`, `publish_clean`;
  * reports bytes freed and the resulting free space.

    python tools/_p1160_cleanup_safe.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MB = 1024 * 1024

PROTECTED = {"data", "models", "outputs", "backups", ".git", "publish_clean", "SUBMISSION",
             "paper", "paper2", "paper3", "paper合", "paper_a1", "paper_a2", "paper_review",
             "paper_review_prl", "备选", "docs", "tools", "src", "exp", "experiments"}
STRAY_LOGS = ["coco_mt.log"]


def free_gb(path: str) -> float:
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          f"$d=Get-Item '{path}'; (Get-PSDrive $d.PSDrive.Name).Free/1GB"],
                         capture_output=True, text=True, timeout=120)
    try:
        return float(out.stdout.strip().splitlines()[-1])
    except Exception:
        return float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    targets = []
    for root, dirs, _files in os.walk(REPO):
        rel = os.path.relpath(root, REPO)
        parts = set(rel.split(os.sep))
        if parts & PROTECTED:
            dirs[:] = []
            continue
        for d in list(dirs):
            if d == "__pycache__":
                targets.append(os.path.join(root, d))
                dirs.remove(d)

    strays = [os.path.join(REPO, n) for n in STRAY_LOGS if os.path.exists(os.path.join(REPO, n))]

    size = 0
    for t in targets:
        for r, _dd, ff in os.walk(t):
            for f in ff:
                try:
                    size += os.path.getsize(os.path.join(r, f))
                except OSError:
                    pass
    for s in strays:
        size += os.path.getsize(s)

    print(f"  __pycache__ directories: {len(targets)}")
    for t in targets[:12]:
        print("   ", os.path.relpath(t, REPO))
    print(f"  stray logs: {[os.path.basename(s) for s in strays]}")
    print(f"  total to remove: {size / MB:.1f} MB")
    print(f"  free before: C {free_gb('C:\\\\'):.1f} GB | D {free_gb('D:\\\\'):.1f} GB")

    if not a.apply:
        print("\n  (dry run; pass --apply to remove)")
        return 0

    removed = 0
    for t in targets:
        assert os.path.basename(t) == "__pycache__", t
        assert not (set(os.path.relpath(t, REPO).split(os.sep)) & PROTECTED), t
        shutil.rmtree(t, ignore_errors=True)
        removed += 1
    for s in strays:
        os.remove(s)
    print(f"\n  removed {removed} __pycache__ dirs and {len(strays)} stray logs, ~{size / MB:.1f} MB")
    print(f"  free after:  C {free_gb('C:\\\\'):.1f} GB | D {free_gb('D:\\\\'):.1f} GB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
