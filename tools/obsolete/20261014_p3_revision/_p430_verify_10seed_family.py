# -*- coding: utf-8 -*-
r"""核 10-seed 家族的配对结果与 E0 簇拆分（2026-10-12）。

## 已核（`paper3/scripts/outputs/experiments/verify_r{5,6}_s*.json`，n=10 each）

| | r=5 | r=6 |
|---|---|---|
| mean ΔE | **−34.70** | **+69.90** |
| 正号 | **2/10** | **10/10** |
| min / max | −80.0 / +66.0 | +22.5 / +98.5 |
| E0 取值 | {3921.0 (n=7), 3930.5 (n=3)} | 同 |

## 待核

1. **配对（同 seed）**：r6 − r5 的均值差、符号、配对 t 的 p
2. **E0 簇拆分**：3921 簇 vs 3930.5 簇 各自结论是否一致
3. **论文用的 3 个 seed 是哪三个**，与 10-seed 族是否统计等价

    python tools\_p430_verify_10seed_family.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import glob
import math
import os
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_10seed_family_verified.json"


def load(r):
    out = {}
    for f in sorted(glob.glob(str(REPO / "paper3/scripts/outputs/experiments"
                                 / f"verify_r{r}_s*.json"))):
        m = re.match(rf"verify_r{r}_s(\d+)\.json$", os.path.basename(f))
        if not m:
            continue
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        E = d.get("E") or []
        out[int(m.group(1))] = {"dE": d.get("delta_E"), "E0": E[0] if E else None,
                                "file": os.path.relpath(f, REPO)}
    return out


def boot_ci(xs, n=20000, seed=0):
    import random
    rng = random.Random(seed)
    ms = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(n))
    return ms[int(0.025 * n)], ms[int(0.975 * n)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r5, r6 = load(5), load(6)
    common = sorted(set(r5) & set(r6))
    rep = {"n_r5": len(r5), "n_r6": len(r6), "common_seeds": common}

    print("=" * 100)
    print("① 配对（同 seed）")
    print("=" * 100)
    diffs = [r6[s]["dE"] - r5[s]["dE"] for s in common]
    pos = sum(1 for d in diffs if d > 0)
    m = statistics.mean(diffs)
    sd = statistics.stdev(diffs) if len(diffs) > 1 else 0
    t = m / (sd / math.sqrt(len(diffs))) if sd else float("nan")
    lo, hi = boot_ci(diffs)
    print(f"  n={len(diffs)} ｜ 均值差 = {m:+.2f} ｜ 正号 {pos}/{len(diffs)}")
    print(f"  配对 t = {t:.3f}（df={len(diffs)-1}）｜ bootstrap 95% CI = [{lo:+.1f}, {hi:+.1f}]")
    for s in common:
        print(f"     seed={s:<6} r5={r5[s]['dE']:>8} r6={r6[s]['dE']:>8} 差={r6[s]['dE']-r5[s]['dE']:>8.1f}")
    rep["paired"] = {"n": len(diffs), "mean_diff": round(m, 4), "n_positive": pos,
                     "t": round(t, 4), "ci": [round(lo, 4), round(hi, 4)]}

    print()
    print("=" * 100)
    print("② E0 簇拆分")
    print("=" * 100)
    for e0 in (3921.0, 3930.5):
        s5 = [r5[s]["dE"] for s in r5 if abs((r5[s]["E0"] or 0) - e0) < 0.01]
        s6 = [r6[s]["dE"] for s in r6 if abs((r6[s]["E0"] or 0) - e0) < 0.01]
        com = [s for s in common if abs((r5[s]["E0"] or 0) - e0) < 0.01]
        dd = [r6[s]["dE"] - r5[s]["dE"] for s in com]
        print(f"  E0={e0}: r5 n={len(s5)} mean={statistics.mean(s5) if s5 else float('nan'):+.2f} "
              f"（正 {sum(1 for x in s5 if x>0)}/{len(s5)}）｜ r6 n={len(s6)} "
              f"mean={statistics.mean(s6) if s6 else float('nan'):+.2f}"
              f"（正 {sum(1 for x in s6 if x>0)}/{len(s6)}）")
        if dd:
            print(f"        配对：n={len(dd)} 全部为正 {all(x>0 for x in dd)} ｜ 均值差 {statistics.mean(dd):+.1f}")
        rep[f"cluster_{e0}"] = {"n_r5": len(s5), "n_r6": len(s6),
                                "r5_mean": round(statistics.mean(s5), 3) if s5 else None,
                                "r6_mean": round(statistics.mean(s6), 3) if s6 else None,
                                "paired_all_positive": all(x > 0 for x in dd) if dd else None,
                                "paired_mean": round(statistics.mean(dd), 3) if dd else None}

    print()
    print("=" * 100)
    print("③ 论文用的 3 个 seed")
    print("=" * 100)
    for s in (42, 123, 999):
        if s in r5:
            print(f"  seed={s}: r5={r5[s]['dE']:>8} r6={r6[s]['dE']:>8} ｜ E0={r5[s]['E0']}")
    sub5 = [r5[s]["dE"] for s in (42, 123, 999) if s in r5]
    print(f"  3-seed r5 均值 = {statistics.mean(sub5):+.2f}（10-seed 均值 {statistics.mean([r5[s]['dE'] for s in r5]):+.2f}）")
    rep["paper_3_seeds"] = {str(s): r5.get(s, {}).get("dE") for s in (42, 123, 999)}

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
