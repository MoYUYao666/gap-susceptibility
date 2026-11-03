# -*- coding: utf-8 -*-
r"""核实：`master_results.json` 里 params=145170177 / cg_delta=0.079171 的那条记录是什么配置（2026-10-12）。

## 已发现

`paper合/sections/empirical.tex` 写：
> *"text-only LoRA **limits** CG increase to $+0.079$ and zero-shot degradation to 0.6 points"*

但 `outputs/master_results.json` 里 `cg_delta = 0.079171` 的那条**`params = 145,170,177`**
（= CLIP B/32 **全部**参数）→ 疑似**全量微调**，不是 LoRA。

**若证实，则 `+0.079` 被张冠李戴：全量微调的 CG∆ 被写成了 text-only LoRA 的值。**

    python tools\_p254_master_record.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "outputs" / "master_results.json"
OUT = REPO / "outputs" / "analysis" / "master_record.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(SRC, encoding="utf-8", errors="replace").read())

    print("=" * 96)
    print(f"① master_results.json 顶层结构：{type(d).__name__}")
    print("=" * 96)
    if isinstance(d, dict):
        for k in list(d.keys())[:20]:
            v = d[k]
            print(f"  {k:<30} {type(v).__name__}"
                  + (f"({len(v)})" if isinstance(v, (list, dict)) else f" = {v}"))
    elif isinstance(d, list):
        print(f"  list[{len(d)}]")

    # 找含 params=145170177 或 cg_delta≈0.079171 的记录
    recs = []

    def walk(o, path=""):
        if isinstance(o, dict):
            keys = {k.lower() for k in o}
            if ("cg_delta" in keys) or ("params" in keys and "cg_final" in keys):
                recs.append((path, o))
            for k, v in o.items():
                walk(v, path + "/" + k)
        elif isinstance(o, list):
            for i, v in enumerate(o[:400]):
                walk(v, path + f"[{i}]")

    walk(d)
    print()
    print("=" * 96)
    print(f"② 含 cg_delta/params 的记录：{len(recs)} 条")
    print("=" * 96)
    target = None
    for path, r in recs:
        cd = r.get("cg_delta")
        if isinstance(cd, (int, float)) and abs(cd - 0.079171) < 1e-5:
            target = (path, r)
            print(f"\n  🔴 命中 {path}")
            print("  " + json.dumps(r, ensure_ascii=False, indent=1)[:1100])
        elif isinstance(cd, (int, float)) and r.get("params"):
            print(f"     {path[:58]:<60} params={r.get('params'):<12} cg_delta={cd:+.4f} "
                  f"R@1={r.get('r1') or r.get('R@1')}")

    print()
    print("=" * 96)
    print("③ 该记录的全部字段（判断配置）")
    print("=" * 96)
    if target:
        path, r = target
        for k in sorted(r):
            v = r[k]
            print(f"  {k:<26} {str(v)[:110]}")
    else:
        print("  🔴 未命中 0.079171")

    print()
    print("=" * 96)
    print("④ 判定")
    print("=" * 96)
    if target:
        r = target[1]
        p = r.get("params")
        cfg = {k: r[k] for k in r if k.lower() in
               ("arm", "config", "name", "position", "method", "target", "mode", "kind")}
        print(f"  params = {p}")
        print(f"  配置线索: {cfg}")
        if p and p > 140_000_000:
            print(f"  → params ≈ 1.45e8 = CLIP B/32 全参数量 → **这是全量微调，不是 LoRA**")
            print(f"  → 论文把全量微调的 CG∆ 写成 'text-only LoRA' 的值 → **必须改**")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"target_path": target[0] if target else None,
             "record": target[1] if target else None,
             "n_records": len(recs)}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
