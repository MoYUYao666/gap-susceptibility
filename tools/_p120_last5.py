# -*- coding: utf-8 -*-
r"""看清 5 条 UNVERIFIED 并修复（2026-10-10）。

`yang2020alignment` 的 bib 姓解析成 "Wang,Isola"（两个词），
说明该条作者区格式与其它不同 → 需看清。

    python tools\_p120_last5.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"
FIXED = REPO / "outputs" / "analysis" / "a1_apa_fixed.json"

BAD = ["yi2025", "mistretta2025", "fang2022data", "yuksekgonul2023when",
       "wang2020alignment"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    src = ""
    for f in (A1 / "main.tex", A1 / "related_work_bibitems.tex"):
        if f.exists():
            src += io.open(f, encoding="utf-8", errors="replace").read()
    bodies = {}
    for m in re.finditer(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}\s*(.*?)(?=\\bibitem|$)",
                         src, re.S):
        bodies[m.group(1)] = " ".join(m.group(2).split())

    rows = json.loads(io.open(FIXED, encoding="utf-8").read())
    rmap = {r["key"]: r for r in rows}

    print("=== 5 条 UNVERIFIED 的原文与解析 ===")
    for k in BAD:
        r = rmap.get(k, {})
        print(f"\n── [{k}]")
        print(f"   bibitem: {bodies.get(k, '?')[:190]}")
        print(f"   解析出的 bib 姓: {r.get('bibitem_families')}")
        au = r.get("authors") or []
        print(f"   OpenAlex 作者({len(au)}): "
              f"{'; '.join(x['display'] for x in au[:6])}")

    # 人工核对后的映射（姓, 依据= bibitem 里写明的姓）
    MANUAL = {
        "yi2025": "Yi",
        "mistretta2025": "Mistretta",
        "fang2022data": "Fang",
        "yuksekgonul2023when": "Yuksekgonul",
        "wang2020alignment": "Wang",
    }
    print("\n=== 应用修正（姓以 bibitem 为准）===")
    for k, fam in MANUAL.items():
        r = rmap.get(k)
        if not r:
            continue
        au = r.get("authors") or []
        target = fam.lower()
        hit = next((i for i, x in enumerate(au)
                    if target in (x["family"].lower(), x["given"].lower(),
                                  x["display"].lower())), None)
        if hit is None:
            print(f"  ⚠ [{k}] 作者列表中找不到 '{fam}'："
                  f"{[x['display'] for x in au]}")
            continue
        x = au[hit]
        if x["family"].lower() != target:
            x["family"], x["given"] = fam, x["family"]
        if hit != 0:
            au.insert(0, au.pop(hit))
        r["name_status"] = "OK_MANUAL"
        r["bibitem_families"] = [fam] + [f for f in (r.get("bibitem_families") or [])
                                         if f.lower() != target]
        print(f"  ✅ [{k}] 首位 → {x['display']}（family={x['family']}）")

    ok = sum(1 for r in rows if r.get("name_status", "").startswith("OK"))
    print(f"\n=== 汇总：{ok}/{len(rows)} 条作者已核 ===")

    if a.apply:
        io.open(FIXED, "w", encoding="utf-8", newline="").write(
            json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {FIXED.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
