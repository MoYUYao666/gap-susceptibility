# -*- coding: utf-8 -*-
r"""看清 8 条未解决的文献（并修 URL 编码）（2026-10-10）。

## 为什么

`48/56` 成功；剩 8 条分两类：
- **HTTP 400**（4 条）→ 疑似我的 URL 编码未处理特殊字符（如 `:` `&` `'`）；
- **相似度低**（4 条）→ 可能是**新论文（未收录）**或**标题不符**。

⚠️ **项目历史上有过"编造引用"事件（P3）**，故这 8 条须逐条看清。

    python tools\_p111_unresolved.py
"""
from __future__ import annotations

import io
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

BAD = ["imod", "chowers2026", "wan2026protect", "hu2022lora",
       "yuksekgonul2023when", "ovadia2019trust", "steck2024cosine", "huh2024platonic"]


def main() -> int:
    src = ""
    for f in (REPO / "paper_a1" / "main.tex",
              REPO / "paper_a1" / "related_work_bibitems.tex"):
        if f.exists():
            src += io.open(f, encoding="utf-8", errors="replace").read()

    res = json.loads(io.open(REPO / "outputs/analysis/a1_refs_openalex.json",
                             encoding="utf-8").read())
    rmap = {r["key"]: r for r in res}

    print("=== 8 条未解决的原始 bibitem（逐条）===")
    for key in BAD:
        m = re.search(r"\\bibitem(?:\[[^\]]*\])?\{(" + re.escape(key) + r")\}\s*(.*?)(?=\\bibitem|$)",
                      src, re.S)
        body = " ".join(m.group(2).split()) if m else "(未找到)"
        r = rmap.get(key, {})
        print(f"\n── [{key}]  method={r.get('method')} ｜ sim={r.get('similarity')}")
        print(f"   原始: {body[:260]}")
        print(f"   抽取的标题: {r.get('title','')[:140]}")
        if r.get("note"):
            print(f"   备注: {r['note']}")
        if r.get("error"):
            print(f"   错误: {r['error']}")

    print("\n=== 各类计数 ===")
    from collections import Counter
    c = Counter(r.get("method", "?").split("(")[0] for r in res)
    for k, v in c.most_common():
        print(f"  {k:<14} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
