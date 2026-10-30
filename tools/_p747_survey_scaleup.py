# -*- coding: utf-8 -*-
r"""Survey what is needed to add a larger-dataset validation run.

Reviewer R2-3 asks for "broader validation on larger datasets and modern VLMs". Before running
anything, establish:
  - what the existing experiment pipeline looks like (scripts, datasets, model loading)
  - which datasets are already present locally
  - whether an experiment server is reachable (the project rule is to download weights on the
    server, never locally)
  - what the current largest dataset is, so "larger" has a definition

    python tools/_p747_survey_scaleup.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 108)
    print("1. experiment scripts")
    print("=" * 108)
    for d in ("exp", "experiments", "src"):
        p = REPO / d
        if not p.exists():
            print(f"  {d}/: absent")
            continue
        files = sorted(x for x in p.rglob("*") if x.is_file())
        print(f"  {d}/: {len(files)} files")
        for f in files[:18]:
            print(f"     {f.relative_to(REPO)}")

    print()
    print("=" * 108)
    print("2. what datasets the scripts reference")
    print("=" * 108)
    pat = re.compile(r"flickr30k|coco|mscoco|imagenet|dtd|food101|cc3m|laion|vg|visual genome",
                     re.I)
    counts = {}
    for d in ("exp", "experiments", "src", "tools"):
        p = REPO / d
        if not p.exists():
            continue
        for f in p.rglob("*.py"):
            try:
                t = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in pat.findall(t):
                counts[m.lower()] = counts.get(m.lower(), 0) + 1
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {v:>6}  {k}")

    print()
    print("=" * 108)
    print("3. local dataset directories")
    print("=" * 108)
    for d in ("data", "datasets", "coco", "flickr30k"):
        p = REPO / d
        if p.exists():
            n = sum(1 for _ in p.rglob("*") if _.is_file())
            print(f"  {d}/: exists, {n} files")

    print()
    print("=" * 108)
    print("4. experiment server configuration")
    print("=" * 108)
    for name in ("exp/README.md", "exp/README.txt", ".env"):
        p = REPO / name
        if p.exists():
            t = p.read_text(encoding="utf-8", errors="ignore")
            print(f"  {name} ({len(t)} chars)")
            for line in t.splitlines()[:40]:
                if re.search(r"ssh|host|autodl|port|server|root@|scp|rsync|ip\b", line, re.I):
                    print(f"     {line.strip()[:150]}")
    # ssh config
    ssh_cfg = Path(os.path.expanduser("~/.ssh/config"))
    print()
    print(f"  ~/.ssh/config: {'exists' if ssh_cfg.exists() else 'absent'}")
    if ssh_cfg.exists():
        t = ssh_cfg.read_text(encoding="utf-8", errors="ignore")
        for line in t.splitlines():
            if re.search(r"Host|HostName|User|Port|IdentityFile", line, re.I):
                print(f"     {line.strip()[:140]}")

    print()
    print("=" * 108)
    print("5. GPU availability locally")
    print("=" * 108)
    r = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                       capture_output=True)
    out = r.stdout.decode("utf-8", errors="replace").strip()
    print(f"  {out if out else 'no nvidia-smi / no GPU'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
