# -*- coding: utf-8 -*-
r"""核 p3-stats 的两条关键发现（2026-10-12）。

## 待核

1. **"30×" 必须降级**：27 vs 808 的比较里，Random 组 **η²(rank) = 0.989**，
   即 808 的 sd 主要来自"抽到哪个 rank"；**同秩 r=4 对 r=4 的 sd 比 = 0.98**（不是 30×），Welch p=0.47。
2. **R3.18 的受控跨版本实验确实存在于归档**：
   `verify_r5/r6_s42.json`（transformers **5.16.1**）vs `_tf457.json`（**4.57.0**），同 seed 同协议；
   r=5 的 ΔE 从 **−18.0 → 0.0**（符号翻转）、r=6 从 **+93.5 → +96.5**（符号保持）。

    python tools\_p418_verify_p3_stats_findings.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_stats_findings_verify.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 100)
    print("① 找「27 vs 808」与 Random 组 15 个 run 的归档")
    print("=" * 100)
    cands = []
    for f in glob.glob(str(REPO / "**" / "*.json"), recursive=True):
        if ".worktrees" in f or "lit_pool" in f:
            continue
        try:
            t = io.open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if ("808" in t and "27" in t) or re.search(r"counterfactual|random_group|random group", t, re.I):
            cands.append(str(Path(f).relative_to(REPO)))
    print(f"  候选归档 {len(cands)} 个：")
    for c in cands[:14]:
        print(f"     {c}")
    rep["candidates"] = cands[:20]

    print()
    print("=" * 100)
    print("② 受控跨版本实验（R3.18）")
    print("=" * 100)
    for pat in ("**/verify_r5*.json", "**/*r6_s42*.json", "**/*_tf457*.json",
                "**/*tf457*.json", "**/verify_r*.json"):
        for f in glob.glob(str(REPO / pat), recursive=True):
            if ".worktrees" in f:
                continue
            rel = str(Path(f).relative_to(REPO))
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            print(f"  ── {rel} ──")
            s = json.dumps(d, ensure_ascii=False)
            for k in ("transformers", "torch", "cuda", "version"):
                for m in list(re.finditer(rf'"{k}[^"]*"\s*:\s*"[^"]*"', s))[:3]:
                    print(f"     {m.group(0)[:120]}")
            # 打印数值块
            print("     " + s[:600])
            print()
            rep.setdefault("cross_version", []).append(rel)

    print()
    print("=" * 100)
    print("③ 判定")
    print("=" * 100)
    print(f"  R3.18 受控跨版本归档：{'✅ 找到' if rep.get('cross_version') else '🔴 未找到'}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
