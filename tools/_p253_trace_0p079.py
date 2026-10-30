# -*- coding: utf-8 -*-
r"""追 `paper合` 里 `+0.079` 的**出处**（项目铁律：每个数字必须能指名来源）（2026-10-12）。

## 背景

`paper合/sections/empirical.tex` 写：
> *"text-only LoRA limits CG increase to $+0.079$"*（与 full-FT 对比的语境）

但已核：
- `tab:position`（PEFT 约定）Flickr30k text-only = **−0.064**
- `strict_control_summary.json` text-only CGD = **−0.0465**
- `dg_r1_reproducible.json` 里 `+0.0792` 的行是 `route_d/d1_alpha64_text_r8`（α=64，R@1=0.389）

**→ `+0.079` 到底指哪个实验？若无法指名来源，按项目规矩该数字必须删或改。**

    python tools\_p253_trace_0p079.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "trace_0p079.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 96)
    print("① 全库找 0.079 / +0.079 的字符串出现（JSON/CSV/TXT）")
    print("=" * 96)
    hits = []
    for pat in ("outputs/**/*.json", "outputs/**/*.csv", "outputs/**/*.txt",
                "outputs/**/*.log"):
        for f in glob.glob(str(REPO / pat), recursive=True):
            if "lit_pool" in f or "analysis/lit_" in f:
                continue
            try:
                t = io.open(f, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            for m in re.finditer(r"0\.079\d*", t):
                hits.append((str(Path(f).relative_to(REPO)), m.group(0),
                             t[max(0, m.start() - 90):m.start() + 60].replace("\n", " ")))
                break
    print(f"  命中 {len(hits)} 个文件")
    for rel, val, ctx in hits[:26]:
        print(f"    {rel:<52} {val}")
        print(f"        …{' '.join(ctx.split())[:110]}…")

    print()
    print("=" * 96)
    print("② 数值层面：找 CG 变化 ≈ +0.079 的记录（任何 json）")
    print("=" * 96)
    found = []
    for f in glob.glob(str(REPO / "outputs" / "**" / "*.json"), recursive=True):
        if "lit_pool" in f:
            continue
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue

        def walk(o, path=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, (int, float)) and abs(v - 0.079) < 0.0015:
                        found.append((str(Path(f).relative_to(REPO)), path + "/" + k, v))
                    else:
                        walk(v, path + "/" + k)
            elif isinstance(o, list):
                for i, v in enumerate(o[:200]):
                    walk(v, path + f"[{i}]")
        walk(d)
    seen = set()
    for rel, path, v in found:
        key = (rel, path.split("[")[0])
        if key in seen:
            continue
        seen.add(key)
        print(f"  {rel:<46} {path[:44]:<46} = {v:.6f}")
    print(f"  → 共 {len(seen)} 条唯一位置")

    print()
    print("=" * 96)
    print("③ 判定")
    print("=" * 96)
    print("  若 ③ 里没有与 empirical.tex 语境（'text-only LoRA 相对 full-FT 的 CG 增幅'）")
    print("  匹配的记录，则 `+0.079` **缺少可指名的来源** → 按项目铁律应删除或替换为有源数字。")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"string_hits": [{"file": r, "value": v} for r, v, _ in hits],
             "numeric_hits": [{"file": r, "path": p, "value": v} for r, p, v in found]},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
