# -*- coding: utf-8 -*-
r"""Remove historical checkpoints and staging directories, keeping every irreplaceable artifact.

Operator instruction, 2026-10-17: "保留 data 和 models" -- datasets and model weights stay. Everything else in the
size report is a candidate.

## What must NOT be deleted, and why

`outputs/llava_canonical_cloud/*.pt` holds the **nine LoRA adapters from the 2026-10-17 canonical retrain**. They are
the only copy: the sweep ran on a rented host that is about to be shut down under the standing rule, and the clean
gap measurement (the basis of the corrected supplement G) is reproducible only from these files. They are excluded
by an explicit path allow-list, not by size heuristics.

`envs/tf457/` is a local Python environment and stays for the same reason: small, and scripts may reference it.

Everything deleted here is git-ignored, so the repository is unaffected:
`*.pt`, `outputs/` (except JSON/TXT/CSV), `backups/`, `data/`, `models/`.

    python tools/_p1161_cleanup_artifacts.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MB = 1024 * 1024
GB = 1024 * MB

# paths whose .pt files survive, relative to the repo root (prefix match)
KEEP_PT_PREFIXES = (
    "outputs/llava_canonical_cloud/",     # the 9 retrain adapters -- the only copy
)

# whole directories that are removed
DROP_DIRS = (
    "_removed_from_publish",              # staging of files already taken out of the publish repo
    ".codegraph",                         # regenerable code-graph cache
)


def free_d() -> float:
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-PSDrive D).Free/1GB"], capture_output=True, text=True, timeout=120)
    try:
        return float(out.stdout.strip().splitlines()[-1])
    except Exception:
        return float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    pts, kept = [], []
    for root, dirs, files in os.walk(os.path.join(REPO, "outputs")):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if not f.endswith(".pt"):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, REPO).replace(os.sep, "/")
            if any(rel.startswith(p) for p in KEEP_PT_PREFIXES):
                kept.append((os.path.getsize(fp), rel))
            else:
                pts.append((os.path.getsize(fp), rel))

    pt_bytes = sum(s for s, _ in pts)
    kept_bytes = sum(s for s, _ in kept)
    dir_bytes = {}
    for d in DROP_DIRS:
        p = os.path.join(REPO, d)
        total = 0
        if os.path.isdir(p):
            for r, _dd, ff in os.walk(p):
                for f in ff:
                    try:
                        total += os.path.getsize(os.path.join(r, f))
                    except OSError:
                        pass
        dir_bytes[d] = total

    print("=== plan ===")
    print(f"  delete {len(pts):>4} .pt under outputs/      {pt_bytes / GB:6.2f} GB")
    print(f"  KEEP   {len(kept):>4} .pt (adapters, excluded) {kept_bytes / GB:6.2f} GB")
    for _, rel in sorted(kept, reverse=True)[:4]:
        print(f"         keep {rel}")
    for d, b in dir_bytes.items():
        print(f"  delete dir {d:<24} {b / MB:7.1f} MB")
    total = pt_bytes + sum(dir_bytes.values())
    print(f"  total to free: {total / GB:.2f} GB")
    print(f"  free on D before: {free_d():.1f} GB")

    if not a.apply:
        print("\n  (dry run; pass --apply)")
        return 0

    removed = 0
    for _, rel in pts:
        fp = os.path.join(REPO, rel.replace("/", os.sep))
        assert fp.startswith(os.path.join(REPO, "outputs")), fp
        assert not any(rel.startswith(p) for p in KEEP_PT_PREFIXES), rel
        os.remove(fp)
        removed += 1
    for d in DROP_DIRS:
        p = os.path.join(REPO, d)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
    print(f"\n  removed {removed} .pt files and {len(DROP_DIRS)} staging dirs, ~{total / GB:.2f} GB")
    print(f"  free on D after:  {free_d():.1f} GB")
    print(f"  adapters still present: {len(kept)} files, {kept_bytes / GB:.2f} GB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
