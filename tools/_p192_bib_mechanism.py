# -*- coding: utf-8 -*-
r"""核查 paper合 的参考文献机制与条数（2026-10-11）。

## 疑点

`main_nc.tex` 里既无 `thebibliography` 也无 `\bibliography{}`，
而包里只有 `references.bib`（47 条 @ 条目）→ **引用到底怎么解析的？**

    python tools\_p192_bib_mechanism.py
"""
from __future__ import annotations

import io
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "paper合"
LS = SRC / "NC_submission" / "latex_source"


def main() -> int:
    for tag, root in (("当前", SRC), ("投稿包", LS)):
        print("=" * 78)
        print(f"{tag}：{root}")
        print("=" * 78)
        mf = root / "main_nc.tex"
        t = io.open(mf, encoding="utf-8", errors="replace").read()
        print(f"  main_nc.tex {len(t.splitlines())} 行")
        for pat, name in ((r"\\bibliography\{([^}]*)\}", "\\bibliography{}"),
                          (r"\\begin\{thebibliography\}", "thebibliography"),
                          (r"\\input\{([^}]*)\}", "\\input{}"),
                          (r"\\bibliographystyle\{([^}]*)\}", "\\bibliographystyle")):
            for m in re.finditer(pat, t):
                print(f"    {name}: {m.group(0)[:70]}")
        # 引用命令统计
        cites = re.findall(r"\\cite[tp]?\{([^}]*)\}", t)
        secs = "".join(io.open(f, encoding="utf-8", errors="replace").read()
                       for f in sorted((root / "sections").glob("*.tex")))
        cites += re.findall(r"\\cite[tp]?\{([^}]*)\}", secs)
        keys = set()
        for c in cites:
            keys |= {k.strip() for k in c.split(",") if k.strip()}
        print(f"    引用 key 数（去重）: {len(keys)}")
        bib = root / "references.bib"
        if bib.exists():
            nb = io.open(bib, encoding="utf-8", errors="replace").read()
            bk = set(re.findall(r"^@\w+\{([^,]+),", nb, re.M))
            print(f"    references.bib: {len(bk)} 条")
            print(f"      引用但 bib 里没有: {len(keys - bk)} {sorted(keys - bk)[:5]}")
            print(f"      bib 里有但未引用: {len(bk - keys)}")
        # 是否有 .bbl
        bbl = root / "main_nc.bbl"
        print(f"    main_nc.bbl: {'有，%d 行' % len(io.open(bbl, encoding='utf-8', errors='replace').read().splitlines()) if bbl.exists() else '无'}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
