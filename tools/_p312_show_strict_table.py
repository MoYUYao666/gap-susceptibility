# -*- coding: utf-8 -*-
r"""打印 `tab:position_strict` 表体，并把每格与归档 run 对上（2026-10-12）。

    python tools\_p312_show_strict_table.py
"""
from __future__ import annotations

import glob
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    t = io.open(REPO / "paper合" / "sections" / "empirical.tex",
                encoding="utf-8", errors="replace").read()
    k = t.find("tab:position_strict")
    i = t.rfind("\\begin{table}", 0, k)
    j = t.find("\\end{table}", k)
    print("=" * 100)
    print("tab:position_strict 表体")
    print("=" * 100)
    print(t[i:j + 12])

    print()
    print("=" * 100)
    print("归档 strict_freeze 的 run（按 experiment 分组，列出全部 seed 与 R@1）")
    print("=" * 100)
    from collections import defaultdict
    by = defaultdict(list)
    for f in glob.glob(str(REPO / "outputs" / "strict_freeze" / "**" / "results.json"),
                       recursive=True):
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        exp = d.get("experiment", "?")
        r1 = (d.get("final_task_metrics") or {}).get("R@1")
        fin = (d.get("final_gap") or {}).get("centroid_gap")
        ini = (d.get("initial_gap") or {}).get("centroid_gap")
        dcg = (fin - ini) if (fin is not None and ini is not None) else None
        by[exp].append({
            "seed": d.get("seed"),
            "R@1": r1,
            "dCG": dcg,
            "batch": d.get("batch_size"),
            "path": str(Path(f).relative_to(REPO)),
        })
    for exp in sorted(by):
        rs = by[exp]
        r1s = [r["R@1"] for r in rs if r["R@1"] is not None]
        dcgs = [r["dCG"] for r in rs if r["dCG"] is not None]
        print(f"\n  {exp}  n={len(rs)}")
        print(f"    seeds   = {sorted(str(r['seed']) for r in rs)}")
        print(f"    batch   = {sorted({str(r['batch']) for r in rs})}")
        if r1s:
            print(f"    R@1     = {[round(v,4) for v in r1s]}  → 均值 {sum(r1s)/len(r1s):.4f}")
        if dcgs:
            print(f"    ΔCG     = {[round(v,4) for v in dcgs]}  → 均值 {sum(dcgs)/len(dcgs):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
