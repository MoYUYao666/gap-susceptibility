# -*- coding: utf-8 -*-
r"""Chase the remaining unsourced numbers: 117, 95, 221, 383 and the CR1 SE of 0.29.

The 222/203 pair was reproduced exactly by summing the alpha_sign_audit entries, which means the
same trick may work for the counts. This searches for audit-style files that already count things,
and for the standard error.

    python tools/_p714_rest.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 112)
    print("1. audit-style files (names containing audit / summary / inventory / manifest)")
    print("=" * 112)
    r = subprocess.run(["git", "ls-files", "outputs"], cwd=str(PUB), capture_output=True)
    files = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
    for f in files:
        if re.search(r"audit|summary|inventory|manifest|catalog|count|index", f, re.I):
            p = PUB / f
            print(f"  {p.stat().st_size:>10,}  {f}")

    print()
    print("=" * 112)
    print("2. every tracked JSON that sums to 117, 95, 221 or 383 in an 'n' field")
    print("=" * 112)
    targets = {117, 95, 221, 383}
    for f in files:
        p = PUB / f
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue

        def walk(o, path="$"):
            if isinstance(o, dict):
                for k, v in o.items():
                    yield from walk(v, f"{path}.{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    yield from walk(v, f"{path}[{i}]")
            else:
                yield path, o

        hits = []
        for path, v in walk(d):
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if int(v) in targets and abs(float(v) - int(v)) < 1e-9:
                    key = path.split(".")[-1].split("[")[0]
                    if re.search(r"^n$|_n$|n_|count|total|size|len", key, re.I):
                        hits.append((v, path))
        if hits:
            print(f"  {f}")
            for v, path in hits[:6]:
                print(f"     {int(v):>5}  {path}")

    print()
    print("=" * 112)
    print("3. the CR1 standard error: candidate fields near 0.29")
    print("=" * 112)
    e = json.loads((PUB / "outputs/analysis/pr_stats_hardened.json").read_text(
        encoding="utf-8", errors="ignore"))

    def walk2(o, path="$"):
        if isinstance(o, dict):
            for k, v in o.items():
                yield from walk2(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from walk2(v, f"{path}[{i}]")
        else:
            yield path, o

    for path, v in walk2(e):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if abs(float(v) - 0.29) <= 0.03:
                print(f"  {v:<12} {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
