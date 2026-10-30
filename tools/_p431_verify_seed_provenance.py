# -*- coding: utf-8 -*-
r"""独立核 `p3-stats` 的 seed 溯源主张（2026-10-12）。

## 它的主张

**不存在事后挑选**：mtime 最早的三个 = **{123, 999, 42}** = 论文那三个；且论文自己的 sweep driver
**硬编码** `SEEDS = [42, 123, 999]`。

## 为什么必须自己核

我先前对操作者说"论文挑的 3 个 seed 恰好全在效应最弱的簇里"，**那句隐含"挑选"**。
若它的 mtime 证据成立，**我的说法就是错的**，必须更正。
**"看起来对"不等于"有来源"。**

    python tools\_p431_verify_seed_provenance.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "seed_provenance_verified.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 100)
    print("① 20 个 verify_r{5,6}_s*.json 按 mtime 排序（逐字，非采信）")
    print("=" * 100)
    rows = []
    for f in glob.glob(str(REPO / "paper3/scripts/outputs/experiments/verify_r[56]_s*.json")):
        b = os.path.basename(f)
        m = re.match(r"verify_r(\d+)_s(\d+)\.json$", b)
        if not m:
            continue
        st = os.stat(f)
        rows.append({"rank": int(m.group(1)), "seed": int(m.group(2)),
                     "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
                     "ctime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_ctime)),
                     "_m": st.st_mtime, "_c": st.st_ctime})
    rows.sort(key=lambda r: r["_m"])
    for r in rows:
        print(f"  r={r['rank']} seed={r['seed']:<6} mtime={r['mtime']}  ctime={r['ctime']}")
    rep["by_mtime"] = [{k: v for k, v in r.items() if not k.startswith('_')} for r in rows]

    print()
    print("=" * 100)
    print("② 最早三个（按 mtime / ctime）")
    print("=" * 100)
    for key, label in (("_m", "mtime"), ("_c", "ctime")):
        first = [r["seed"] for r in sorted(rows, key=lambda x: x[key])[:3]]
        print(f"  最早三个（{label}）= {{123, 999, 42}} ? {'✅' if set(first) == {123, 999, 42} else '🔴'}  实际 = {first}")
        rep[f"first_three_{label}"] = first

    print()
    print("=" * 100)
    print("③ E0 簇是否在时间上连续（每个 rank 只切一次？）")
    print("=" * 100)
    for rank in (5, 6):
        sub = [r for r in rows if r["rank"] == rank]
        sub.sort(key=lambda r: r["_m"])
        seq = []
        for r in sub:
            d = json.loads(io.open(REPO / "paper3/scripts/outputs/experiments"
                                   / f"verify_r{rank}_s{r['seed']}.json",
                                   encoding="utf-8", errors="replace").read())
            E = d.get("E") or []
            seq.append(round(E[0], 1) if E else None)
        switches = sum(1 for i in range(1, len(seq)) if seq[i] != seq[i-1])
        print(f"  r={rank}: E0 时序 {seq} ｜ 切换次数 = {switches} "
              f"{'✅ 连续块' if switches <= 1 else '🔴 多次切换 = 非连续'}")
        rep[f"e0_sequence_r{rank}"] = seq
        rep[f"e0_switches_r{rank}"] = switches

    print()
    print("=" * 100)
    print("④ 论文的 sweep driver 是否硬编码 SEEDS = [42,123,999]")
    print("=" * 100)
    for f in glob.glob(str(REPO / "paper3/scripts/**/*.py"), recursive=True):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        if "SEEDS" in t and "42" in t:
            for m in re.finditer(r"SEEDS\s*=\s*\[[^\]]*\]", t):
                print(f"  [{os.path.relpath(f, REPO)}] {m.group(0)}")
                rep.setdefault("drivers", []).append(
                    {"file": os.path.relpath(f, REPO), "seeds": m.group(0)})

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
