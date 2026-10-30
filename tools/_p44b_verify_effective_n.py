# -*- coding: utf-8 -*-
r"""核"逐样本配对 ΔE 的 sd 恒为 0.00"这条披露（2026-10-13）。

## 为什么这条最关键

成员自披露：主实验用**空白图 + 单一重复提示**，**32 个评估样本的提示完全相同**
⇒ **逐样本配对 ΔE 的 sd 恒为 0.00** ⇒ **不确定度只能来自 seed 间**，即**每方案有效 n = 3**，
**不能当 n=32 用**。

**若属实，这影响的不只是 task-9**：
- 论文 Table 1（8/8 排序）用的 $E_2$ 数据是否也是同提示？
- task-10 的 `ΔE` 是否同提示？
- 论文报的 CI、"30×"、相变显著性**全都建立在"n 是多少"之上**

**我必须逐归档核对"有效 n"**。

    python tools\_p44b_verify_effective_n.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_effective_n_audit.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 100)
    print("① task-9 归档里逐样本 sd 是否恒为 0")
    print("=" * 100)
    for f in ("p3_alloc_results.json",):
        p = REPO / "outputs" / "analysis" / f
        if not p.exists():
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        for name, v in (d.get("per_plan") or {}).items():
            s = json.dumps(v, ensure_ascii=False)
            has = "per_sample" in s or "sample" in s.lower()
            print(f"  {name:<24} 含逐样本字段: {has}")
            for k in ("delta_E", "sd", "n"):
                if k in v:
                    print(f"        {k} = {json.dumps(v[k], ensure_ascii=False)[:180]}")

    print()
    print("=" * 100)
    print("② 论文主表（E2 数据）与 task-10 的 sd 结构")
    print("=" * 100)
    for f in ("paper3/scripts/outputs/experiments/E2_results.json",
              "outputs/analysis/p3d_clip_ranksweep.json"):
        p = REPO / f
        if not p.exists():
            print(f"  ⚠️ 缺 {f}")
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        runs = d.get("runs") if isinstance(d, dict) else d
        if not isinstance(runs, list):
            print(f"  {f}: 顶层键 {sorted(d.keys())[:10]}")
            continue
        print(f"  ── {f}（{len(runs)} run）──")
        if runs:
            print(f"     首条键：{sorted(runs[0].keys())}")
        # 找逐 run 的每样本序列
        n_with_samples = sum(1 for r in runs
                             if any('per_sample' in k or 'dE_per' in k for k in r))
        print(f"     含逐样本字段的 run：{n_with_samples}/{len(runs)}")

    print()
    print("=" * 100)
    print("③ 关键：找「同提示」的证据（评估提示是否常量）")
    print("=" * 100)
    hits = 0
    for f in glob.glob(str(REPO / "paper3/scripts/**/*.py"), recursive=True) + \
             glob.glob(str(REPO / "tools/_p43*.py")) + glob.glob(str(REPO / "tools/_p46*.py")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        if "Describe this image" in t:
            print(f"  [{os.path.relpath(f, REPO)}] 含 'Describe this image'")
            hits += 1
        if "PROMPT" in t and "=" in t:
            for line in t.splitlines():
                if line.strip().startswith("PROMPT") and "Describe" in line:
                    print(f"        {line.strip()[:120]}")
    if not hits:
        print("  （未在脚本里找到该提示字面量）")

    print()
    print("=" * 100)
    print("④ 判定")
    print("=" * 100)
    print("  ⚠️ 若逐样本 sd 恒为 0（同提示 + 同图），则每方案的**有效 n = seed 数**，")
    print("     而非评估样本数。**论文与三成员报告里的 n 全部需要复核。**")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
