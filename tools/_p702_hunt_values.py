# -*- coding: utf-8 -*-
r"""Hunt the values the ledger has failed to source, across every tracked archive file.

The point of the ledger is to fail loudly rather than to assume. Six values that Paper A states
were not found where they should be, so this searches the whole tracked archive - but searches it
for exact numeric equality on a named field, not for the value's digits appearing anywhere in the
text. A file only counts as a source if it holds the number as a number.

    python tools/_p702_hunt_values.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "paperhe_hunt.json"

TARGETS = {
    "-0.71": "DG* vs retrieval correlation, n = 96 and n = 204",
    "-0.59": "centroid gap vs retrieval correlation",
    "0.943": "OpenCLIP BitFit mean R2",
    "0.946": "linear-baseline R2",
    "222": "fits archived",
    "203": "fits with negative alpha",
    "383": "experiments in the validation part",
    "221": "runs in the experiment catalogue",
    "117": "mechanism experiments",
    "95": "strict-freezing controls",
    "0.00": "constant-baseline R2",
    "0.016": "cluster-robust p for the slope",
    "-1.05": "cluster-robust slope",
    "0.29": "CR1 standard error",
}


def walk(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = subprocess.run(["git", "ls-files", "outputs"], cwd=str(PUB), capture_output=True)
    files = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines()
             if x.endswith(".json")]
    print(f"  searching {len(files)} tracked JSON files for {len(TARGETS)} values")
    print()
    found: dict[str, list[dict]] = {k: [] for k in TARGETS}
    # exact numeric match on a leaf, with a tolerance far tighter than the one that made the
    # old automatic gate meaningless
    for rel in files:
        p = PUB / rel
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for path, val in walk(d):
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                fv = float(val)
                for t in TARGETS:
                    tf = float(t)
                    tol = 0.005 if abs(tf) >= 50 else 0.0005
                    if abs(fv - tf) <= tol:
                        if len(found[t]) < 6:
                            found[t].append({"file": rel, "path": path, "value": fv})

    for t, desc in TARGETS.items():
        hits = found[t]
        # prefer files whose name suggests the right topic
        topical = [h for h in hits
                   if re.search(r"r1|retriev|corr|dg|ode|fullft|peft|freeze|catalog|lit_pool",
                                h["file"], re.I)]
        print("=" * 104)
        print(f"{t}   ({desc})")
        print("=" * 104)
        print(f"  {len(hits)} exact numeric match(es) in the archive")
        for h in (topical or hits)[:6]:
            print(f"     {h['file']}")
            print(f"        {h['path']} = {h['value']}")
        if not hits:
            print("     -> NOT PRESENT as a number anywhere in the tracked archive")
        print()

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(found, ensure_ascii=False, indent=1))
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
