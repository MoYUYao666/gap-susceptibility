# -*- coding: utf-8 -*-
r"""Check whether P3's rank experiments are among the affected runs.

P3's central empirical claim is a critical rank at which the sign of the alignment-energy change
flips, plus monotonic growth across fifteen ranks. If those LLaVA and Qwen runs trained the whole
adapted tower, the rank was not what varied.

This reads the parameter counts recorded for P3's rank experiments and classifies them.

    python tools/_p799_p3_affected.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "p3_affected.json"

# trees P3's rank experiments could live in
CANDIDATE = ["outputs/analysis/p3_", "outputs/p3_", "outputs/llava", "outputs/qwen",
             "outputs/route_c", "outputs/route_d", "outputs/route_e"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = subprocess.run(["git", "ls-files", "outputs"], cwd=str(PUB), capture_output=True)
    files = [x for x in r.stdout.decode("utf-8", "replace").splitlines() if x.endswith(".json")]
    print(f"  {len(files)} tracked JSON files")

    hits = defaultdict(list)
    for f in files:
        p = PUB / f
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        n = d.get("n_trainable_params")
        if not isinstance(n, int):
            continue
        if n > 1_000_000:
            tree = "/".join(f.split("/")[:2])
            hits[tree].append((f, d.get("experiment") or Path(f).parent.name, n))

    print()
    print("=" * 104)
    print("trees holding runs with more than 1M trainable parameters")
    print("=" * 104)
    for tree in sorted(hits):
        rows = hits[tree]
        print(f"  {tree:<38} {len(rows):>4} runs   e.g. n_trainable = {rows[0][2]:,}")

    print()
    print("=" * 104)
    print("P3-specific trees")
    print("=" * 104)
    for c in CANDIDATE:
        n = sum(len(v) for k, v in hits.items() if k.startswith(c.rstrip("_")))
        print(f"  {c:<34} {n} affected run(s)")

    print()
    print("=" * 104)
    print("files that record LoRA-style names with a huge trainable count")
    print("=" * 104)
    cnt = 0
    for tree in sorted(hits):
        for f, exp, n in hits[tree]:
            if any(k in exp.lower() for k in ("r1", "r2", "r4", "r5", "r6", "r8", "r16", "r20",
                                               "r24", "r32", "r64", "rank")):
                cnt += 1
                if cnt <= 14:
                    print(f"     {f:<64} {n:>12,}")
    print(f"  ... {cnt} run(s) with a rank-like name and a tower-sized trainable count")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({k: [{"file": f, "exp": e, "n": n} for f, e, n in v]
                                   for k, v in hits.items()}, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
