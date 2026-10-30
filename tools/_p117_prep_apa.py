# -*- coding: utf-8 -*-
r"""整理 APA 转换所需的全部数据（2026-10-10）。

输出一张表：key / 作者（已解析）/ 年 / 标题 / 原始余部（venue）
→ 供生成 APA 条目。

    python tools\_p117_prep_apa.py [--apply]
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"
RES = REPO / "outputs" / "analysis" / "a1_refs_openalex.json"
OUT = REPO / "outputs" / "analysis" / "a1_apa_input.json"


def parse_original(src: str):
    out = {}
    for m in re.finditer(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}\s*(.*?)(?=\\bibitem|$)",
                         src, re.S):
        key, body = m.group(1), " ".join(m.group(2).split())
        t = re.search(r"``(.+?)''", body)
        title = t.group(1) if t else ""
        # 标题之后的余部（venue 信息）
        rest = body[t.end():] if t else body
        rest = re.sub(r"\s*%[- ].*$", "", rest).strip()
        rest = rest.replace("\\input{related_work_bibitems}", "").strip()
        rest = rest.replace("\\end{thebibliography}", "").replace("\\end{document}", "").strip()
        out[key] = {"body": body, "title": title.strip().rstrip(".,"),
                    "rest": rest.strip(" ,")}
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    src = ""
    for f in (A1 / "main.tex", A1 / "related_work_bibitems.tex"):
        if f.exists():
            src += io.open(f, encoding="utf-8", errors="replace").read()
    orig = parse_original(src)
    res = {r["key"]: r for r in json.loads(io.open(RES, encoding="utf-8").read())}

    rows = []
    print(f"=== {len(orig)} 条原始条目 ｜ {len(res)} 条解析结果 ===")
    miss = [k for k in orig if k not in res]
    print(f"  原始有但解析无: {len(miss)} {miss[:6]}")
    miss2 = [k for k in res if k not in orig]
    print(f"  解析有但原始无: {len(miss2)} {miss2[:6]}")

    for k, o in orig.items():
        r = res.get(k, {})
        rows.append({
            "key": k,
            "title": o["title"],
            "rest": o["rest"],
            "authors": r.get("authors", []),
            "n_authors": r.get("n_authors", 0),
            "year": r.get("year") or (re.search(r"\b(19|20)\d{2}\b", o["rest"]).group(0)
                                      if re.search(r"\b(19|20)\d{2}\b", o["rest"]) else None),
            "method": r.get("method", "?"),
        })

    print("\n=== 逐条（前 8 条示例）===")
    for r in rows[:8]:
        a = ", ".join(x["family"] for x in r["authors"][:3]) or "（无）"
        print(f"  [{r['key']:<22}] {r['year']} ｜ {a[:50]:<50} ｜ {r['rest'][:48]}")

    noauth = [r["key"] for r in rows if not r["authors"]]
    print(f"\n=== 无作者（将保留 et al.）: {len(noauth)} 条 ===")
    for k in noauth:
        print(f"  • [{k}]")
    noyear = [r["key"] for r in rows if not r["year"]]
    print(f"无年份: {len(noyear)} 条 {noyear}")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
