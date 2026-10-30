# -*- coding: utf-8 -*-
r"""查论文各评测路径是否都经 `create_dataloaders`（受随机画廊影响）（2026-10-12）。

## 为什么

已确认 `src/dataset.py::create_dataloaders` 的 val/test 子集**继承 train transform**
（`RandomHorizontalFlip(0.5)` + `ColorJitter`）→ **每次评测是不同抽样**。

**但这只影响走该函数的路径。** 论文里的数字可能来自：
1. `create_dataloaders`（**受影响**）
2. 自己写 DataLoader / 直接用 processor（**可能不受影响**）

**必须逐路径查明**，才能知道**论文哪些数字受影响**。

    python tools\_p380_eval_paths.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "eval_paths_audit.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    files = sorted(glob.glob(str(REPO / "tools" / "*.py"))) + \
        sorted(glob.glob(str(REPO / "src" / "*.py"))) + \
        sorted(glob.glob(str(REPO / "paper" / "scripts" / "*.py"))) + \
        sorted(glob.glob(str(REPO / "experiments" / "*.py")))
    rows = []
    for f in files:
        try:
            t = io.open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        uses_cdl = "create_dataloaders" in t
        # 是否自建评测集（绕开 create_dataloaders）
        own_eval = bool(re.search(r"class\s+\w*(Eval|Retrieval|Gallery)\w*|"
                                  r"get_clip_transform\s*\(|"
                                  r"CLIPProcessor\.from_pretrained", t))
        # 是否显式关掉 transform（eval 模式）
        explicit_eval_tf = bool(re.search(r"is_train\s*=\s*False|"
                                          r"get_clip_transform\([^)]*is_train\s*=\s*False", t))
        if uses_cdl or own_eval:
            rows.append({
                "file": str(Path(f).relative_to(REPO)),
                "uses_create_dataloaders": uses_cdl,
                "has_own_eval_or_transform": own_eval,
                "explicit_is_train_False": explicit_eval_tf,
                "affected": uses_cdl and not explicit_eval_tf,
            })

    print("=" * 104)
    print("评测路径审计")
    print("=" * 104)
    n_cdl = sum(1 for r in rows if r["uses_create_dataloaders"])
    n_aff = sum(1 for r in rows if r["affected"])
    for r in sorted(rows, key=lambda x: (not x["affected"], x["file"])):
        tag = "🔴 受影响" if r["affected"] else ("  " if r["uses_create_dataloaders"] else "  ")
        print(f"  {tag} {r['file']:<56} cdl={int(r['uses_create_dataloaders'])} "
              f"own={int(r['has_own_eval_or_transform'])} evalTF={int(r['explicit_is_train_False'])}")
    print()
    print(f"  用到 create_dataloaders 的文件 {n_cdl} 个；其中**未显式关随机变换**的 {n_aff} 个")

    print()
    print("=" * 104)
    print("关键路径专项：论文主表的产出脚本")
    print("=" * 104)
    KEY = ["train_class_aligned", "strict_freeze_control", "noise_sensitivity",
           "lora_experiments", "rq2", "blip2_experiments"]
    for k in KEY:
        hits = [r for r in rows if k in r["file"]]
        if not hits:
            print(f"  ⚠️  {k}: 未在扫描范围内找到")
            continue
        for r in hits[:2]:
            print(f"  {'🔴' if r['affected'] else '✅'} {r['file']:<56} "
                  f"受影响={r['affected']}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"n_files_using_create_dataloaders": n_cdl, "n_affected": n_aff,
             "rows": rows}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
