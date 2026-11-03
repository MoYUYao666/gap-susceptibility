# -*- coding: utf-8 -*-
r"""Publish the decoder-run records to the public repository, then show exactly what would be pushed.

Scope: only JSON result records. The LoRA adapters (1.58 GB) stay out -- `*.pt` is git-ignored in the mirror, and the
data statement says the adapters are not required to reproduce the archived statistics.

Each copied file is compared by SHA-256 against its source so a truncated copy cannot be committed.

    python tools/_p1173_publish_decoder_records.py [--apply] [--push]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"

SOURCES = [
    ("outputs/vlm_clean_cloud", "outputs/vlm_clean_cloud"),          # 53 JSON (39 runs + summaries + frozen)
    ("outputs/vlm_clean_summary.json", "outputs/vlm_clean_summary.json"),
    ("outputs/llava_canonical_cloud", "outputs/llava_canonical_cloud"),  # 12 records (+ adapters skipped)
    ("outputs/canonical_caption_metric.json", "outputs/canonical_caption_metric.json"),
    ("outputs/canonical_summary.json", "outputs/canonical_summary.json"),
]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()

    plan = []
    for src_rel, dst_rel in SOURCES:
        src, dst = REPO / src_rel, PUB / dst_rel
        if not src.exists():
            print(f"  !! missing source {src_rel}")
            return 2
        if src.is_dir():
            for f in sorted(src.iterdir()):
                if f.is_file() and f.suffix == ".json":
                    plan.append((f, dst / f.name))
        else:
            plan.append((src, dst))
    total = sum(f.stat().st_size for f, _ in plan)
    print(f"  {len(plan)} JSON files, {total/1024:.1f} KB")

    if not a.apply:
        print("  (dry run)")
        return 0

    bad = 0
    for src, dst in plan:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if sha(src) != sha(dst):
            bad += 1
            print(f"  MISMATCH {src.relative_to(REPO)}")
    print(f"  copied {len(plan)} files, {bad} mismatched")

    print("\n  === git status in publish_clean (JSON only) ===")
    r = subprocess.run(["git", "-C", str(PUB), "status", "--porcelain"], capture_output=True, text=True, timeout=300)
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    for l in lines[:20]:
        print("   ", l)
    print(f"  total changed entries: {len(lines)}")

    print("\n  === tracked size check (must stay small) ===")
    r2 = subprocess.run(["git", "-C", str(PUB), "add", "-A"], capture_output=True, text=True, timeout=600)
    r3 = subprocess.run(["git", "-C", str(PUB), "diff", "--cached", "--stat"], capture_output=True, text=True,
                        timeout=300)
    print("  " + (r3.stdout.strip().splitlines()[-1] if r3.stdout.strip() else "(nothing staged)"))
    r4 = subprocess.run(["git", "-C", str(PUB), "ls-files", "-s"], capture_output=True, text=True, timeout=300)
    big = []
    for line in r4.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            p = PUB / parts[1]
            if p.exists() and p.stat().st_size > 20 * 1024 * 1024:
                big.append((p.stat().st_size, parts[1]))
    print(f"  tracked files > 20 MB: {len(big)}")
    for s, p in sorted(big, reverse=True)[:5]:
        print(f"    {s/1024/1024:.0f} MB {p}")

    if a.push:
        print("\n  === committing and pushing ===")
        msg = "Add decoder-VLM per-run records for supplementary Sections E and G"
        r5 = subprocess.run(["git", "-C", str(PUB), "commit", "-q", "-m", msg], capture_output=True, text=True,
                            timeout=900)
        print("  commit:", "ok" if r5.returncode == 0 else r5.stderr.strip()[:200])
        r6 = subprocess.run(["git", "-C", str(PUB), "push", "ssh-origin", "main"], capture_output=True, text=True,
                            timeout=900)
        print("  push rc:", r6.returncode)
        print("  " + (r6.stdout or r6.stderr).strip()[:400])
        if r6.returncode == 0:
            head = subprocess.run(["git", "-C", str(PUB), "log", "--oneline", "-1"], capture_output=True,
                                  text=True, timeout=120)
            print("  HEAD:", head.stdout.strip())
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
