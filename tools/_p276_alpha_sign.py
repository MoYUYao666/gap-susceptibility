# -*- coding: utf-8 -*-
r"""统计归档里 α 的正负分布（用于修正"α is universally/consistently negative"）（2026-10-12）。

## 为什么

`paper合` 有三处写"α 对 PEFT 普适/一致为负"：
- `conclusion.tex:9` *"$\alpha$ is universally negative for PEFT"*
- `validation.tex:73` *"$\alpha$ is consistently negative for all PEFT configurations"*
- `validation.tex:109` *"$\alpha$ is consistently negative for all PEFT configurations on both
  Flickr30k and COCO"*

**写作面报告称**：Adapter 50 个拟合里 **40 负 10 非负**（最大 +0.0608）；CLIP BitFit α = **+0.0002**。
**必须自己核过再改。**

    python tools\_p276_alpha_sign.py [--apply]
"""
from __future__ import annotations

import argparse
import collections
import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "alpha_sign_audit.json"


def walk_alpha(o, path=""):
    """收集所有形如 {..., 'alpha': x, ...} 的记录。"""
    out = []
    if isinstance(o, dict):
        if "alpha" in o and isinstance(o["alpha"], (int, float)):
            out.append((path, o["alpha"], o.get("beta"), o.get("R2") or o.get("r2")))
        for k, v in o.items():
            out += walk_alpha(v, path + "/" + k)
    elif isinstance(o, list):
        for i, v in enumerate(o[:400]):
            out += walk_alpha(v, path + f"[{i}]")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    res = {}
    for f in ("outputs/analysis/ode_ledger.json",
              "outputs/analysis/ode_loco.json",
              "outputs/analysis/ode_loco2.json",
              "outputs/theory/adapter/adapter_all_results.json",
              "outputs/theory/bitfit/bitfit_results.json"):
        p = REPO / f
        if not p.exists():
            print(f"  ❌ 缺 {f}")
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        recs = walk_alpha(d)
        if not recs:
            print(f"  ⚠️ {f}: 无 alpha 字段")
            continue
        vals = [r[1] for r in recs]
        neg = sum(1 for v in vals if v < 0)
        nonneg = len(vals) - neg
        print(f"  {f}")
        print(f"     n={len(vals)}  负={neg}  非负={nonneg}  "
              f"min={min(vals):+.6f}  max={max(vals):+.6f}")
        if nonneg:
            ex = [(r[0][-60:], round(r[1], 6)) for r in recs if r[1] >= 0][:5]
            print(f"     非负示例: {ex}")
        res[f] = {"n": len(vals), "neg": neg, "nonneg": nonneg,
                  "min": round(min(vals), 6), "max": round(max(vals), 6),
                  "nonneg_examples": [(r[0][-70:], round(r[1], 6))
                                      for r in recs if r[1] >= 0][:8]}
        print()

    # 按族汇总
    print("=" * 88)
    print("按归档文件汇总")
    print("=" * 88)
    tot_n = sum(v["n"] for v in res.values())
    tot_nn = sum(v["nonneg"] for v in res.values())
    print(f"  合计 n={tot_n}  非负={tot_nn}")
    print(f"  → {'🔴 存在非负 α，不能写 universally/consistently negative' if tot_nn else '✅ 全为负'}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
