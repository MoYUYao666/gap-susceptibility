# -*- coding: utf-8 -*-
r"""核 `p3-downstream` 的分辨率稳健性检验（证伪）（2026-10-13）。

## 待核

| `max_pixels` | token | real ΔE_train | blank ΔE_train | 配对 |
|---|---|---|---|---|
| 16384 | 15 | 21/21 **正** | 21/21 **负** | 21/21 负（−699.0） |
| **50176** | **54** | **2/2 负** | 2/2 负 | **0/2 负**（+393.9） |

**初始能量 E0**：

| token | real | blank | 差 |
|---|---|---|---|
| 15 | 21751.8 | 22373.3 | **+2.9%** |
| **54** | **14718.0** | 22207.0 | **+50.9%** |

⇒ **把预算从 54 压到 15，"真实 vs 空白"的差别从 50.9% 塌到 2.9%**

    python tools\_p450_verify_resolution_check.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_resolution_verified.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    for f in ("p3d_qwen_ranksweep.json", "p3d_qwen_ranksweep_mp50176.json"):
        p = REPO / "outputs" / "analysis" / f
        print("=" * 100)
        print(f"{f}  ｜ 存在 {p.exists()}"
              + (f" ｜ {os.path.getsize(p):,} B" if p.exists() else ""))
        print("=" * 100)
        if not p.exists():
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        runs = [r for r in (d.get("runs") or []) if r.get("condition")]
        print(f"  runs = {len(runs)}")
        proto = d.get("protocol") or {}
        print(f"  max_pixels = {proto.get('max_pixels')} ｜ min_pixels = {proto.get('min_pixels')}")
        # ΔE_train 逐条件
        for cond in ("real", "blank"):
            v = [(r.get("rank"), r.get("seed"), r.get("dE_train")) for r in runs
                 if r.get("condition") == cond and isinstance(r.get("dE_train"), (int, float))]
            if v:
                xs = [x for _, _, x in v]
                print(f"  {cond:<6} n={len(xs)} ｜ 正 {sum(1 for x in xs if x>0)}/{len(xs)} "
                      f"｜ 范围 {min(xs):+.1f} … {max(xs):+.1f}")
        # E0 对比
        for cond in ("real", "blank"):
            e0 = [r.get("E_train_epochs", [None])[0] for r in runs
                  if r.get("condition") == cond]
            e0 = [x for x in e0 if isinstance(x, (int, float))]
            if e0:
                print(f"  {cond:<6} E0 均值 = {statistics.mean(e0):,.1f}")
        rep[f] = {"runs": len(runs), "max_pixels": proto.get("max_pixels")}
        print()

    # 配对
    print("=" * 100)
    print("配对（同 rank / 同 seed，blank − real）")
    print("=" * 100)
    for f in ("p3d_qwen_ranksweep.json", "p3d_qwen_ranksweep_mp50176.json"):
        p = REPO / "outputs" / "analysis" / f
        if not p.exists():
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        runs = [r for r in (d.get("runs") or []) if r.get("condition")]
        g = {}
        for r in runs:
            g.setdefault((r.get("rank"), r.get("seed")), {})[r.get("condition")] = r.get("dE_train")
        pairs = [(b - a) for k, v in g.items()
                 if isinstance(v.get("real"), (int, float)) and isinstance(v.get("blank"), (int, float))
                 for a, b in [(v["real"], v["blank"])]]
        if pairs:
            print(f"  {f}: 配对 {len(pairs)} ｜ 负 {sum(1 for x in pairs if x<0)}/{len(pairs)} "
                  f"｜ 均值 {statistics.mean(pairs):+.1f}")
            rep[f"{f}_pairs"] = {"n": len(pairs),
                                 "n_negative": sum(1 for x in pairs if x < 0),
                                 "mean": round(statistics.mean(pairs), 2)}

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
