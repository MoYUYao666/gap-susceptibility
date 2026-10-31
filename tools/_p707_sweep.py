# -*- coding: utf-8 -*-
r"""Final sweep for the Paper A values that still have no home.

Searches every tracked JSON for the exact numbers, listing the file and the full path of each
match, so the last few claims can be either sourced or declared unsourced.

    python tools/_p707_sweep.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "paperhe_sweep.json"

TARGETS = ["0.29", "0.943", "117", "95", "221", "383", "222", "203", "0.016", "-0.59"]


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
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                fv = float(v)
                for t in TARGETS:
                    tf = float(t)
                    tol = 0.005 if abs(tf) >= 50 else 0.0005
                    if abs(fv - tf) <= tol and len(hits[t]) < 40:
                        hits[t].append((rel, path, fv))
    result = {}
    for t in TARGETS:
        rows = hits[t]
        # rank by how topical the file name is
        topical = [r_ for r_ in rows
                   if re.search(r"stat|ode|freeze|catalog|pool|sweep|r1|retriev", r_[0], re.I)]
        print("=" * 110)
        print(f"{t}: {len(rows)} exact numeric match(es), {len(topical)} in topical files")
        print("=" * 110)
        for rel, path, fv in (topical or rows)[:10]:
            print(f"   {fv:<14} {rel}")
            print(f"                  {path}")
        if not rows:
            print("   NOT PRESENT as a number in any tracked JSON")
        result[t] = [{"file": f, "path": pa, "value": v} for f, pa, v in (topical or rows)[:12]]
        print()
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(result, ensure_ascii=False, indent=1))
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
