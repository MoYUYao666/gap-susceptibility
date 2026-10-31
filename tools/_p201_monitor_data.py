# -*- coding: utf-8 -*-
r"""查 A1 现有归档里**能支撑「监控器做过决策」演示**的数据（2026-10-12）。

## 我的发现（`tools/_p199_monitor_claim.py`）

新标题主打 *"Zero-Overhead Monitor"*，正文已给出：
- ✅ **可算性**（τ 来自验证时已有的 top-k 类集合）
- ✅ **灵敏度**（τ 比 top-1 **更早**指示秩序侵蚀）
- 🔴 **缺**：**实际用它做过决策的演示**（如"τ 触发早停／选检查点，结果更好"）

**本脚本**：查归档里有哪些 (检查点, τ, top-1) 的数据，判能否补一个"决策演示"。

    python tools\_p201_monitor_data.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "a1_monitor_data.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 86)
    print("① 含 (tau, top-1) 的归档文件")
    print("=" * 86)
    hits = []
    for f in sorted(glob.glob(str(REPO / "outputs" / "**" / "*.json"), recursive=True)):
        try:
            t = io.open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        low = t.lower()
        if ("tau" in low or "kendall" in low) and ("top1" in low or "top-1" in low
                                                   or "accuracy" in low):
            sz = Path(f).stat().st_size
            hits.append((str(Path(f).relative_to(REPO)), sz))
    for h, sz in hits[:22]:
        print(f"  {h:<62} {sz:>9,} B")
    print(f"  → 共 {len(hits)} 个")

    print()
    print("=" * 86)
    print("② 检查点级 (tau, top-1) 数据（用于「选检查点」演示）")
    print("=" * 86)
    for pat, tag in (("outputs/a1_*.json", "a1_*"),
                     ("outputs/**/ckpt*.json", "ckpt*"),
                     ("outputs/**/*seed*.json", "*seed*")):
        fs = sorted(glob.glob(str(REPO / pat), recursive=True))
        print(f"  {tag:<14} {len(fs)} 个")
        for f in fs[:6]:
            try:
                d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            except Exception:
                continue
            keys = list(d.keys())[:12] if isinstance(d, dict) else f"list[{len(d)}]"
            print(f"     {Path(f).name:<40} {str(keys)[:110]}")

    print()
    print("=" * 86)
    print("③ 训练期逐 epoch 的 tau 轨迹（用于「早停」演示）")
    print("=" * 86)
    for f in sorted(glob.glob(str(REPO / "outputs" / "**" / "*traj*.json"), recursive=True))[:10]:
        print("  " + str(Path(f).relative_to(REPO)))
    for f in sorted(glob.glob(str(REPO / "outputs" / "**" / "*epoch*.json"), recursive=True))[:10]:
        print("  " + str(Path(f).relative_to(REPO)))

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"tau_top1_files": [{"file": h, "bytes": sz} for h, sz in hits]},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
