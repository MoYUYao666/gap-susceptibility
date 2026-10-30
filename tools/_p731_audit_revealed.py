# -*- coding: utf-8 -*-
r"""Audit the 113 files the anchoring revealed, and add the ones that are result data.

Anchoring the dataset rules exposed files that were previously hidden by the bare "coco/" and
"flickr30k/" patterns. They are results, not datasets, but "results" is a claim to verify, not an
assumption - the publication boundary forbids weights, archives and dataset directories, and
allows outputs/.

This lists them by directory and extension, sizes them, and reports which are needed to make the
paper's own counts reproducible.

    python tools/_p731_audit_revealed.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=str(PUB), capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    out = git("status", "--porcelain", "--untracked-files=all")
    untracked = [l[3:].strip().strip('"') for l in out.splitlines() if l.startswith("?? ")]
    print(f"  {len(untracked)} untracked entries")
    print()

    ext = Counter()
    top = Counter()
    total = 0
    big = []
    for f in untracked:
        p = PUB / f
        if p.is_dir():
            continue
        e = p.suffix.lower() or "(none)"
        ext[e] += 1
        top["/".join(f.split("/")[:2])] += 1
        if p.exists():
            total += p.stat().st_size
            if p.stat().st_size > 2_000_000:
                big.append((f, p.stat().st_size))
    print("  by extension:")
    for k, v in ext.most_common():
        print(f"     {v:>4}  {k}")
    print()
    print("  by top-level pair:")
    for k, v in top.most_common():
        print(f"     {v:>4}  {k}")
    print()
    print(f"  total size: {total/1024/1024:.2f} MB")
    print(f"  files over 2 MB: {len(big)}")
    for f, s in big[:10]:
        print(f"     {s/1024/1024:>6.2f} MB  {f}")

    print()
    print("=" * 104)
    print("verdict on admissible content")
    print("=" * 104)
    bad = [f for f in untracked if Path(f).suffix.lower() in
           (".pt", ".pth", ".bin", ".safetensors", ".ckpt", ".onnx", ".h5", ".zip",
            ".tar", ".gz", ".7z", ".log", ".png", ".pdf", ".jpg")]
    print(f"  files that the publication boundary forbids (weights/archives/logs/images): {len(bad)}")
    for f in bad[:10]:
        print(f"     {f}")
    json_only = [f for f in untracked if Path(f).suffix.lower() == ".json"]
    print(f"  result JSON files (admissible, and what the paper counts): {len(json_only)}")
    if a.apply:
        r = subprocess.run(["git", "add", "-A", "outputs"], cwd=str(PUB), capture_output=True)
        print()
        print(f"  git add -A outputs: rc={r.returncode} "
              f"{r.stderr.decode('utf-8', 'replace')[:120]}")
        out = git("status", "--porcelain")
        staged = [l for l in out.splitlines() if l.startswith("A ")]
        print(f"  staged additions: {len(staged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
