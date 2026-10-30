# -*- coding: utf-8 -*-
r"""列出所有 OpenCLIP 相关 strict 目录 × 臂 的 ΔCG，找论文 +0.0802 的出处（2026-10-12）。

    python tools\_p321_openclip_search.py
"""
from __future__ import annotations

import glob
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = {"text_only": 0.0802, "both": 0.0864, "vision_only": 0.0996}


def main() -> int:
    g = defaultdict(list)
    pats = ["strict_freeze*openclip*", "strict_freeze*oclip*", "openclip*"]
    for pat in pats:
        for f in glob.glob(str(REPO / "outputs" / pat / "**" / "results.json"),
                           recursive=True):
            try:
                d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            except Exception:
                continue
            fin = (d.get("final_gap") or {}).get("centroid_gap")
            ini = (d.get("initial_gap") or {}).get("centroid_gap")
            if fin is None or ini is None:
                continue
            parts = Path(f).parts[1:-1]
            arm = next((p for p in reversed(parts)
                        if p in ("text_only", "both", "vision_only")), None)
            if not arm:
                continue
            key = "/".join(parts[:parts.index(arm)])
            g[(key, arm)].append({
                "dcg": fin - ini,
                "r1": (d.get("final_task_metrics") or {}).get("R@1"),
                "n": d.get("n_trainable_params"),
                "file": str(Path(f).relative_to(REPO)),
            })
    print("=" * 104)
    print("OpenCLIP 相关 目录 × 臂 的 ΔCG")
    print("=" * 104)
    for k in sorted(g):
        v = g[k]
        dc = [x["dcg"] for x in v]
        m = sum(dc) / len(dc)
        tgt = TARGET.get(k[1])
        hit = "🎯 命中发表值" if tgt is not None and abs(m - tgt) < 5e-4 else ""
        print(f"  {k[0]:<34} {k[1]:<12} n={len(dc):<3} ΔCG均值={m:+.4f} "
              f"各seed={[round(x, 4) for x in dc]} {hit}")
        print(f"        n_train={sorted({str(x['n']) for x in v})}")

    print()
    print("=" * 104)
    print("论文发表值 vs 最接近的目录")
    print("=" * 104)
    for arm, tgt in TARGET.items():
        cands = [(k[0], sum(x["dcg"] for x in v) / len(v))
                 for k, v in g.items() if k[1] == arm]
        if not cands:
            continue
        best = min(cands, key=lambda c: abs(c[1] - tgt))
        print(f"  {arm:<12} 发表 {tgt:+.4f} ｜ 最接近 {best[0]:<34} 均值 {best[1]:+.4f} "
              f"差 {best[1]-tgt:+.4f} {'🎯' if abs(best[1]-tgt) < 5e-4 else '🔴'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
