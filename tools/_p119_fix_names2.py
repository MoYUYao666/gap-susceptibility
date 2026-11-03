# -*- coding: utf-8 -*-
r"""修 `\bibitem` 姓提取：`~` 是 LaTeX 不换行空格，`\s` 匹配不到（2026-10-10）。

## 我的错

bibitem 形如 `D.~Hendrycks et al.,`，我用 `(?:[A-Z]\.\s*)+([A-Z][A-Za-z]+)` 提取
→ **`\s*` 不匹配 `~`** → 全部返回空。

**修法**：**先把 `~` 与 `\,` 归一化成空格**，再提取；并且**提取全部作者姓**
（不只第一个），以便与 OpenAlex 名单交叉核对。

    python tools\_p119_fix_names2.py --apply
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


def norm_tex(s: str) -> str:
    return (s.replace("~", " ").replace("\\,", " ").replace("\\ ", " ")
            .replace("{", "").replace("}", ""))


def bibitem_families(body: str) -> list:
    """从 `D.~Hendrycks et al.,` / `L. Yi, R. Douady, C. Chen,` 抽全部作者姓。"""
    b = norm_tex(body)
    # 取到第一个 ``...'' 之前（即作者区）
    cut = b.find("``")
    seg = b[:cut] if cut > 0 else b
    seg = seg.strip().strip(",")
    seg = re.sub(r"\bet al\.?$", "", seg).strip().strip(",")
    fams = []
    for part in seg.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(?:[A-Z]\.\s*)+([A-Z][A-Za-z'\-]+)$", part)
        if m:
            fams.append(m.group(1))
        else:
            # 形如 "M. Y. Levi" 或 "A. Sofer"
            m2 = re.match(r"^(?:[A-Z]\.\s*)+([A-Z][A-Za-z'\-]+)", part)
            if m2:
                fams.append(m2.group(1))
    return fams


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
    print(f"=== 重新提取（{len(rows)} 条）===")
    swapped, unver, ok = [], [], 0
    for r in rows:
        fams = bibitem_families(bodies.get(r["key"], ""))
        r["bibitem_families"] = fams
        au = r.get("authors") or []
        status = "NO_AUTHORS" if not au else ("OK" if fams else "NO_FAMILY")
        if au and fams:
            target = fams[0].lower()
            hit = None
            for i, x in enumerate(au):
                if (x["family"].lower() == target or x["given"].lower() == target
                        or x["display"].lower().endswith(" " + target)
                        or x["display"].lower().startswith(target + " ")):
                    hit = i
                    break
            if hit is not None:
                x = au[hit]
                # 修"姓/名颠倒"：若 family 不是目标姓而 given 是
                if x["family"].lower() != target:
                    x["family"], x["given"] = fams[0], x["family"]
                    swapped.append(r["key"])
                if hit != 0:
                    au.insert(0, au.pop(hit))
                status = "OK"
            else:
                status = "UNVERIFIED"
                unver.append(r["key"])
        r["name_status"] = status
        if status == "OK":
            ok += 1
        fam_disp = ",".join(fams[:3]) or "—"
        print(f"  [{r['key']:<24}] {status:<14} bib姓={fam_disp[:26]:<26} 作者 {len(au)}")

    print(f"\n=== 汇总 ===")
    print(f"  OK: {ok}/{len(rows)}")
    print(f"  颠倒已修正: {len(swapped)} {swapped}")
    print(f"  UNVERIFIED: {len(unver)} {unver[:10]}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
