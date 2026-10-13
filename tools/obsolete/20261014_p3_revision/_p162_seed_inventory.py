# -*- coding: utf-8 -*-
r"""清点全项目的 seed 覆盖（找出 1–3 seed 的实验）（2026-10-10）。

## 规则（操作者）

> **"所有 1-3 seed 你都可以视成本来提升为 5 seed"**

**故需先列出**：哪些实验目录的 seed 数 < 5，及其 run 数与估算成本。

    python tools\_p162_seed_inventory.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "seed_inventory.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # 所有 results.json：按"上两级目录模式"分组
    files = glob.glob(str(REPO / "outputs" / "**" / "results.json"), recursive=True)
    groups = defaultdict(set)
    for f in files:
        p = Path(f)
        seed = p.parent.name                       # seedXX
        parent = p.parent.parent.name              # 臂或配置
        gp = p.parent.parent.parent.name           # 组（实验名）
        if re.fullmatch(r"seed\d+", seed):
            groups[f"{gp}/{parent}"].add(seed)
        else:
            # 无 seed 层：用文件所在目录当组
            groups[f"{gp}/{parent}"].add("(single)")

    print("=" * 78)
    print(f"共 {len(files)} 个 results.json ｜ {len(groups)} 个 (组/配置)")
    print("=" * 78)

    rows = []
    for k in sorted(groups):
        n = len(groups[k])
        rows.append({"group": k, "n_seeds": n, "seeds": sorted(groups[k]),
                     "files": len(glob.glob(str(REPO / "outputs" / k.split("/")[0]
                                                   / k.split("/")[1] / "**" / "results.json"),
                                            recursive=True))})

    need = [r for r in rows if r["n_seeds"] < 5]
    ok = [r for r in rows if r["n_seeds"] >= 5]
    print(f"\n=== seed < 5 的组：{len(need)} 个 ===")
    for r in need:
        print(f"  {r['group']:<44} {r['n_seeds']} seed  {r['seeds'][:6]}")
    print(f"\n=== seed >= 5 的组：{len(ok)} 个 ===")
    for r in ok:
        print(f"  {r['group']:<44} {r['n_seeds']} seed")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"total_results": len(files), "groups": rows,
             "need_upgrade": need, "already_ok": ok},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
