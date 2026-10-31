# -*- coding: utf-8 -*-
r"""Strict search: a field whose NAME says experiment/run/fit and whose VALUE is the number.

The looser searches returned array indices. This requires both, which is the criterion the ledger
uses, and it covers every tracked JSON. If nothing qualifies, the conclusion is that Paper A's
counts have no named source in the archive and must be re-derived or removed.

    python tools/_p717_strict_counts.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "paperhe_strict_counts.json"

TARGETS = {117: "mechanism experiments", 95: "strict-freezing controls",
           221: "catalogue runs", 383: "validation experiments", 222: "fits archived",
           203: "negative alpha"}
NAME = re.compile(r"experiment|run|fit|control|mechanism|catalog|count|total|^n$|_n$", re.I)


def walk(o, p="$"):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f"{p}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, f"{p}[{i}]")
    else:
        yield p, o


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = subprocess.run(["git", "ls-files", "outputs"], cwd=str(PUB), capture_output=True)
    files = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines()
             if x.endswith(".json")]
    hits = {t: [] for t in TARGETS}
    for rel in files:
        p = PUB / rel
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for path, v in walk(d):
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                continue
            key = path.split(".")[-1]
            # the key must be a NAME, not an index
            if "[" in key:
                continue
            if not NAME.search(key):
                continue
            iv = int(v)
            if iv in TARGETS and abs(float(v) - iv) < 1e-9:
                hits[iv].append(f"{rel}::{path}")
    for t, desc in TARGETS.items():
        print(f"  {t:<5} {desc:<26} {len(hits[t])} name-qualified match(es)")
        for h in hits[t][:5]:
            print(f"          {h}")
    print()
    print("  interpretation: a match here means a field whose own name says what it counts.")
    print("  No match means the number has no named source in the tracked archive.")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({str(k): v for k, v in hits.items()}, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
