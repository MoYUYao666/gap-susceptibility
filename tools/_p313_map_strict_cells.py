# -*- coding: utf-8 -*-
r"""提取 `tab:position_strict` 的表体，并找出承载它的归档 run（2026-10-12）。

表的每格是「ΔCG / R@1」上下两行。**要把每格对上具体归档文件**。

    python tools\_p313_map_strict_cells.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "strict_table_provenance.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(REPO / "paper合" / "sections" / "empirical.tex",
                encoding="utf-8", errors="replace").read()
    k = t.find("\\label{tab:position_strict}")
    i = t.rfind("\\begin{table}", 0, k)
    j = t.find("\\end{table}", k)
    body = t[i:j + 12]
    print("=" * 100)
    print("① 表体（tabular 部分）")
    print("=" * 100)
    tb = body[body.find("\\begin{tabular}"):]
    print(tb[:2200])

    print()
    print("=" * 100)
    print("② 全库找 strict 相关 run（不限 outputs/strict_freeze）")
    print("=" * 100)
    from collections import defaultdict
    by = defaultdict(list)
    for f in glob.glob(str(REPO / "outputs" / "**" / "results.json"), recursive=True):
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        r1 = (d.get("final_task_metrics") or {}).get("R@1")
        fin = (d.get("final_gap") or {}).get("centroid_gap")
        ini = (d.get("initial_gap") or {}).get("centroid_gap")
        if r1 is None and fin is None:
            continue
        exp = str(d.get("experiment", "?"))
        if not re.search(r"strict|s\d+_|openclip|siglip|bioclip", exp, re.I):
            continue
        dcg = (fin - ini) if (fin is not None and ini is not None) else None
        by[exp].append({"seed": d.get("seed"), "R@1": r1, "dCG": dcg,
                        "batch": d.get("batch_size"), "n": d.get("n_trainable_params"),
                        "file": str(Path(f).relative_to(REPO))})
    for exp in sorted(by):
        rs = by[exp]
        r1s = [r["R@1"] for r in rs if r["R@1"] is not None]
        dcg = [r["dCG"] for r in rs if r["dCG"] is not None]
        print(f"  {exp:<32} n={len(rs):<3} seeds={len({str(r['seed']) for r in rs})}  "
              f"R@1均值={(f'{sum(r1s)/len(r1s):.4f}' if r1s else '—'):<8} "
              f"ΔCG均值={(f'{sum(dcg)/len(dcg):.4f}' if dcg else '—'):<9} "
              f"batch={sorted({str(r['batch']) for r in rs})}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"experiments": {k: v for k, v in by.items()}}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
