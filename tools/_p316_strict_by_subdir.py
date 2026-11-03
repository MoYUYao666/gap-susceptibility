# -*- coding: utf-8 -*-
r"""按**子目录**分组 strict run，定位 `tab:position_strict` 每格出处（2026-10-12）。

    python tools\_p316_strict_by_subdir.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "strict_by_subdir.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    bydir = defaultdict(list)
    for f in glob.glob(str(REPO / "outputs" / "**" / "results.json"), recursive=True):
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        exp = str(d.get("experiment", "?"))
        if not exp.startswith("strict"):
            continue
        rel = Path(f).relative_to(REPO)
        # 去掉末尾的 results.json，再取倒数第 2 段（run 目录）与倒数第 3 段（实验目录）
        parts = rel.parts
        run_dir = "/".join(parts[:-1])                     # …/strict_both
        exp_dir = "/".join(parts[:-2]) if len(parts) > 2 else ""
        fin = (d.get("final_gap") or {}).get("centroid_gap")
        ini = (d.get("initial_gap") or {}).get("centroid_gap")
        bydir[run_dir].append({
            "experiment": exp, "exp_dir": exp_dir,
            "n_train": d.get("n_trainable_params"),
            "seed": d.get("seed"),
            "R@1": (d.get("final_task_metrics") or {}).get("R@1"),
            "dCG": (fin - ini) if (fin is not None and ini is not None) else None,
        })

    print("=" * 108)
    print("按 run 目录分组（每个目录 = 一种配置 × 一组 seed）")
    print("=" * 108)
    rows = []
    for run_dir in sorted(bydir):
        rs = bydir[run_dir]
        r1 = [x["R@1"] for x in rs if x["R@1"] is not None]
        dcg = [x["dCG"] for x in rs if x["dCG"] is not None]
        if not r1:
            continue
        m = sum(r1) / len(r1)
        rows.append({"dir": run_dir, "exp": rs[0]["experiment"],
                     "n": len(r1), "R1_mean": m,
                     "dCG_mean": (sum(dcg) / len(dcg)) if dcg else None,
                     "n_train": sorted({str(x["n_train"]) for x in rs})})
    rows.sort(key=lambda r: -r["R1_mean"])
    for r in rows:
        dcg_s = f"{r['dCG_mean']:+.4f}" if r["dCG_mean"] is not None else "—"
        print(f"  {r['R1_mean']:.4f}  n={r['n']:<3} ΔCG={dcg_s:<9} "
              f"{r['exp']:<20} n_train={r['n_train']}")
        print(f"          └ {r['dir']}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
