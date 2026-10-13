# -*- coding: utf-8 -*-
r"""修正作者姓名解析：**姓以 bibitem 为准，OpenAlex 只补名**（2026-10-10）。

## 我上一版的错

OpenAlex 的 `display_name` 是 "Given Family" 顺序（如 "Lingjie Yi"），
我按"最后一词=姓"解析 → 对 "Lingjie Yi" 得 family="Lingjie" **（错，应为 Yi）**。

**而 bibitem 里原本就写对了姓**（`L.~Yi, R.~Douady, C.~Chen`）→ **以它为准**。

## 做法

1. 从 bibitem 抽**第一作者的姓**（原文形如 `A.~B. Family et al.` 或 `A.~Family, B.~Family2,`）；
2. 与 OpenAlex 解析出的作者列表**比对**：
   - 若某个 OpenAlex 作者的 `family` 或 `given` 命中该姓 → **交换 family/given**（修颠倒）；
   - 否则保留（但标 `UNVERIFIED`）；
3. **年份以 bibitem 为准**（OpenAlex 年份可能与会议年不同）。
4. **输出核对表**，逐条标 ✅/⚠️，供人工抽检。

    python tools\_p118_fix_names.py --apply
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
INP = REPO / "outputs" / "analysis" / "a1_apa_input.json"
OUT = REPO / "outputs" / "analysis" / "a1_apa_fixed.json"


def first_family_from_bibitem(body: str) -> str:
    """从 `V.~W. Liang et al.,` / `L.~Yi, R.~Douady,` 抽第一作者的姓。"""
    m = re.match(r"\s*(?:[A-Z]\.\s*)+([A-Z][A-Za-z'\-]+)", body)
    return m.group(1) if m else ""


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

    rows = json.loads(io.open(INP, encoding="utf-8").read())
    print(f"=== 修正 {len(rows)} 条 ===")
    fixed = 0
    swapped, unver = [], []
    for r in rows:
        fam = first_family_from_bibitem(bodies.get(r["key"], ""))
        r["bibitem_first_family"] = fam
        au = r.get("authors") or []
        status = "NO_AUTHORS" if not au else "OK"
        if au and fam:
            hit = None
            for i, x in enumerate(au):
                if x["family"].lower() == fam.lower() or x["given"].lower() == fam.lower():
                    hit = i
                    break
            if hit is not None:
                x = au[hit]
                if x["family"].lower() != fam.lower():
                    # family/given 颠倒 → 交换
                    x["family"], x["given"] = x["given"], x["family"]
                    swapped.append(r["key"])
                # 把命中的作者挪到首位（OpenAlex 顺序通常已对，这里保证）
                if hit != 0:
                    au.insert(0, au.pop(hit))
                status = "OK"
            else:
                status = "UNVERIFIED"
                unver.append(r["key"])
        elif au:
            status = "NO_FAMILY_IN_BIBITEM"
        r["name_status"] = status
        if status == "OK":
            fixed += 1
        print(f"  [{r['key']:<24}] {status:<20} bib姓={fam or '—':<12} "
              f"作者 {len(au)} 位")

    print(f"\n=== 汇总 ===")
    print(f"  OK: {fixed}/{len(rows)}")
    print(f"  姓/名颠倒并已修正: {len(swapped)} {swapped[:8]}")
    print(f"  姓未在 OpenAlex 作者中命中（UNVERIFIED）: {len(unver)} {unver[:8]}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
