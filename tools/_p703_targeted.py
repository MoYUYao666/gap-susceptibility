# -*- coding: utf-8 -*-
r"""Targeted search for the Paper A values that still lack a named source.

The broad numeric hunt returned false positives (array indices, unrelated fields), which is the
reason the project retired automatic matching. This narrows the search by requiring the value to
sit under a key whose name describes the same thing, and by looking in the topic-specific files.

    python tools/_p703_targeted.py [--apply]
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

# value -> regex the KEY must match
WANTED = {
    "383": r"n_(?:total|runs|experiments|obs)|total|count|n$",
    "221": r"n_(?:total|runs|experiments)|catalog|total|count",
    "117": r"mechanism|n_(?:total|runs)|total|count",
    "95": r"freeze|control|n_(?:total|runs)|total|count",
    "0.943": r"r2|r\^2|fit|mean",
    "0.00": r"const|baseline|r2",
    "-1.05": r"slope|beta|coef",
    "0.29": r"se|stderr|standard_error|sd",
    "0.016": r"p_|pval|p_value|sig",
    "-0.59": r"cg|centroid|corr|r$|slope",
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
    # keep only files whose name is about statistics or the relevant experiments
    files = [f for f in files if re.search(
        r"stat|corr|r1|retriev|ode|pool|freeze|catalog|lit|gap|multiseed|sweep", f, re.I)]
    print(f"  {len(files)} topic-relevant JSON files")

    for val, keypat in WANTED.items():
        tf = float(val)
        tol = 0.005 if abs(tf) >= 50 else 0.0005
        hits = []
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
                if abs(float(v) - tf) > tol:
                    continue
                key = path.split(".")[-1].split("[")[0]
                if re.search(keypat, key, re.I):
                    hits.append((rel, path, v))
        print()
        print("=" * 104)
        print(f"  {val}  (key must match /{keypat}/)")
        print("=" * 104)
        if hits:
            for rel, path, v in hits[:8]:
                print(f"     {rel}")
                print(f"        {path} = {v}")
        else:
            print("     no key-qualified match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
