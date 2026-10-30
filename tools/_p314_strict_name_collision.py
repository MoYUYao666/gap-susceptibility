# -*- coding: utf-8 -*-
r"""查 `strict_*` experiment 名冲突：哪些 run 属于哪个 backbone（2026-10-12）。

## 现象

`outputs/**/results.json` 里 `experiment` 字段**有重名**：
- `strict_both` 有 72 个 run，`n_trainable_params` 出现 **122,880 / 1,966,080** 两种
- `strict_text_only` 有 92 个，`n_trainable_params` 出现 **1572864 / 196608** 两种

→ 按 `experiment` 名取均值会**混池**，导致复现不出论文的单 backbone 值。

## 要做的

按 (`experiment`, `n_trainable_params`, 路径前缀) 分组，看能否**唯一区分**各 backbone，
再判断论文的 12 格分别对应哪一组。

    python tools\_p314_strict_name_collision.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "strict_name_collision.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    groups = defaultdict(list)
    for f in glob.glob(str(REPO / "outputs" / "**" / "results.json"), recursive=True):
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        exp = str(d.get("experiment", "?"))
        if not exp.startswith("strict"):
            continue
        rel = str(Path(f).relative_to(REPO))
        fin = (d.get("final_gap") or {}).get("centroid_gap")
        ini = (d.get("initial_gap") or {}).get("centroid_gap")
        groups[exp].append({
            "n_train": d.get("n_trainable_params"),
            "seed": d.get("seed"),
            "R@1": (d.get("final_task_metrics") or {}).get("R@1"),
            "dCG": (fin - ini) if (fin is not None and ini is not None) else None,
            "path": rel,
            "parent": "/".join(rel.split("/")[:-1]),
        })

    print("=" * 104)
    print("按 experiment × n_trainable 分组（判断重名是否可由参数量区分）")
    print("=" * 104)
    summary = {}
    for exp in sorted(groups):
        rs = groups[exp]
        sub = defaultdict(list)
        for r in rs:
            sub[r["n_train"]].append(r)
        print(f"\n{exp}  （共 {len(rs)} run）")
        summary[exp] = {}
        for n in sorted(sub, key=lambda x: (x is None, x)):
            g = sub[n]
            r1 = [x["R@1"] for x in g if x["R@1"] is not None]
            dcg = [x["dCG"] for x in g if x["dCG"] is not None]
            parents = sorted({x["parent"] for x in g})
            print(f"   n_train={n:>12,}  n={len(g):<3} "
                  f"R@1均值={(f'{sum(r1)/len(r1):.4f}' if r1 else '—'):<8} "
                  f"ΔCG均值={(f'{sum(dcg)/len(dcg):.4f}' if dcg else '—'):<9} "
                  f"seeds={sorted({str(x['seed']) for x in g})[:6]}")
            for p in parents[:3]:
                print(f"        └ {p}")
            if len(parents) > 3:
                print(f"        └ …另有 {len(parents)-3} 个目录")
            summary[exp][str(n)] = {
                "n_runs": len(g),
                "R1_mean": round(sum(r1) / len(r1), 6) if r1 else None,
                "dCG_mean": round(sum(dcg) / len(dcg), 6) if dcg else None,
                "seeds": sorted({str(x["seed"]) for x in g}),
                "parents": parents,
            }

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(summary, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
