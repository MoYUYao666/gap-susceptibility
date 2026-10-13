# -*- coding: utf-8 -*-
r"""判定 R3.1：`+0.079` 与 `−0.064` 是**同一配置**还是**两个实验**（2026-10-12）。

## 审稿人 R3.1 原话

> *"the abstract and conclusion cite a text-only CG change of +0.079, whereas the main
> tables report −0.064 or −0.066 for the standard text-only setting"*

**若两者是同一配置 → 真矛盾（必须改）；若是两个不同实验 → 需在稿里写清区分。**

## 判据

1. `paper合` 的 `tab:position`（PEFT 约定）里 Flickr30k text-only = ?
2. `paper合` 里 `+0.079` 出现在哪个语境（哪个实验）？
3. 归档 `outputs/analysis/dg_r1_reproducible.json:rows` 里 Flickr30k text-only 的 cg 变化 = ?
4. 严格冻结（strict freeze）的 text-only 值来自哪个归档？

    python tools\_p252_r31_verdict.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "r31_verdict.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 96)
    print("① paper合 里 +0.079 的语境")
    print("=" * 96)
    for f in sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"\+0\.079", t):
            s = " ".join(t[max(0, m.start() - 420):m.start() + 220].split())
            print(f"\n  [{Path(f).name}] …{s[:560]}…")

    print()
    print("=" * 96)
    print("② tab:position 里 Flickr30k / COCO 的 text-only 值")
    print("=" * 96)
    t = io.open(REPO / "paper合" / "sections" / "empirical.tex",
                encoding="utf-8", errors="replace").read()
    m = re.search(r"Flickr30k & .*?\\\\", t)
    if m:
        print("  " + m.group(0)[:120])
    for m in re.finditer(r"(Flickr30k|COCO|BLIP-1|ViT-L) & \$?\\?mathbf?\{?([-+0-9.]+)", t):
        print(f"    {m.group(1):<10} text-only = {m.group(2)}")

    print()
    print("=" * 96)
    print("③ 归档里 Flickr30k 的 text-only 行（`dg_r1_reproducible.json:rows`）")
    print("=" * 96)
    p = REPO / "outputs" / "analysis" / "dg_r1_reproducible.json"
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        rows = d.get("rows", [])
        print(f"  共 {len(rows)} 行")
        hit = [r for r in rows if "flickr" in str(r.get("path", "")).lower()
               and "text" in str(r.get("path", "")).lower()]
        print(f"  路径含 flickr+text 的行: {len(hit)}")
        for r in hit[:8]:
            dg = r.get("dg_final"); dgi = r.get("dg_init")
            cg = r.get("cg_final"); cgi = r.get("cg_init")
            print(f"    {r.get('path')}")
            print(f"      CG {cgi} → {cg}  (Δ={None if None in (cg,cgi) else round(cg-cgi,4)})  "
                  f"DG {dgi} → {dg}  R@1={r.get('r1')}")
        # 全体里 CG 变化 ≈ +0.079 的行
        print()
        print("  全表中 |CGΔ − 0.079| < 0.002 的行（找 +0.079 的出处）:")
        n = 0
        for r in rows:
            cg, cgi = r.get("cg_final"), r.get("cg_init")
            if isinstance(cg, (int, float)) and isinstance(cgi, (int, float)):
                dd = cg - cgi
                if abs(dd - 0.079) < 0.002:
                    n += 1
                    if n <= 8:
                        print(f"    {r.get('path'):<44} CGΔ={dd:+.4f}  R@1={r.get('r1')}")
        print(f"    → 共 {n} 行")
    else:
        print("  🔴 无该归档")

    print()
    print("=" * 96)
    print("④ 严格冻结（strict freeze）的 text-only 值出处")
    print("=" * 96)
    for f in sorted(glob.glob(str(REPO / "outputs" / "**" / "*strict*"), recursive=True)):
        pp = Path(f)
        if pp.is_file() and pp.suffix == ".json":
            print(f"  {pp.relative_to(REPO)}")
    for f in ("outputs/analysis/recomputed_tables.json",
              "outputs/analysis/statistics_audit.json"):
        pp = REPO / f
        if pp.exists():
            d = json.loads(io.open(pp, encoding="utf-8", errors="replace").read())
            txt = json.dumps(d, ensure_ascii=False)
            print(f"  {f}: 含 '+0.079' {'✅' if '+0.079' in txt else '❌'} ｜ "
                  f"含 '0.079' {'✅' if '0.079' in txt else '❌'}")

    print()
    print("=" * 96)
    print("⑤ 判定")
    print("=" * 96)
    print("  （人工判定：见上文证据——若 +0.079 出自严格冻结实验、−0.064 出自 PEFT 约定，")
    print("    则两者**不是同一配置**，需在稿里显式区分）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"note": "see stdout for evidence"}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
