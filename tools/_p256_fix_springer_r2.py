# -*- coding: utf-8 -*-
r"""修 `main_springer.tex` 摘要的 ODE R²（0.986 → 0.949 + 分数据集），对齐 `main_nc.tex`（2026-10-12）。

## 为什么

| 文件 | 现值 | 判定 |
|---|---|---|
| `main_nc.tex` | *"mean $R^2 = 0.949$ over LoRA ($0.953$ on Flickr30k, $0.903$ on MS-COCO)"* | ✅ 与归档一致 |
| `main_springer.tex` | *"mean $R^2 = 0.986$ over the LoRA configurations across all tested LoRA configurations"* | 🔴 两处错 |

**归档**：`outputs/analysis/ode_ledger.json::subsets`
- `lora`: n=55, **mean = 0.9486153770**, max = 0.9773493815
- `lora_flickr`: n=49, mean = 0.95418
- `lora_coco`: n=6, mean = 0.90317

**→ `0.986` 超过该集合最大值 0.9773，不可能是均值**；且原文有笨拙重复（"over the LoRA
configurations across all tested LoRA configurations"）。

**注**：`0.986` 在 `outputs/a1_tau_holdout.json`（皮尔逊 r）、`master_results.json`（R@10）里
确实存在，但**都不是 LoRA 的 ODE R²** → **不是来源**。

    python tools\_p256_fix_springer_r2.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

OLD = ("The ODE\npredicts the full gap trajectory at mean $R^2 = 0.986$ over the LoRA "
       "configurations across all tested LoRA configurations, against\n"
       "$0.00$ for a constant baseline and $0.946$ for a linear one.")
NEW = ("Fitted per run, the ODE reproduces the full gap trajectory at mean $R^2 = 0.949$ "
       "over LoRA ($0.953$ on Flickr30k, $0.903$ on MS-COCO), against $0.00$ for a constant "
       "baseline and $0.946$ linear.")

TARGETS = ["paper合/main_springer.tex",
           "paper合/NC_submission/latex_source/main_nc.tex"]


def sha(p: Path) -> str:
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # 先确认 main_nc 的镜像关系
    nc = REPO / "paper合" / "main_nc.tex"
    mirror = REPO / "paper合" / "NC_submission" / "latex_source" / "main_nc.tex"
    if nc.exists() and mirror.exists():
        print(f"  main_nc.tex 与投稿包镜像: "
              f"{'✅ 相同' if sha(nc) == sha(mirror) else '🔴 不同'} "
              f"({sha(nc)} vs {sha(mirror)})")

    hits = 0
    for rel in TARGETS:
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(OLD)
        print(f"  {rel}: 命中 {n}")
        if n == 0:
            continue
        if not a.apply:
            continue
        t2 = t.replace(OLD, NEW)
        bak = p.with_suffix(p.suffix + ".bak_p256")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t2)
        hits += n

    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {hits} 处")
    for rel in TARGETS:
        p = REPO / rel
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        print(f"  复核 {rel}: 0.986 剩 {t.count('0.986')} ｜ 0.949 有 {t.count('0.949')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
