# -*- coding: utf-8 -*-
r"""从综述里取「site dominates allocation」所依据的 3 篇完整书目（2026-10-07）。

用于给 Paper A 补引用——**不凭记忆写书目**（项目红线）。
综述是同一作者自己的稿件，取其 bibitem 即为其本人已核对过的书目。

    python tools\_get_site_dominates_bib.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
T = REPO / "paper_review_prl" / "main_prl.tex"

KEYS = ["zhang2023adalora", "wang2024loraga", "zanella2024cliplora"]


def main() -> int:
    t = io.open(T, encoding="utf-8").read()
    print(f"=== 综述 {T.name}：取 3 条书目 ===")
    for k in KEYS:
        # \bibitem{key} ... 到下一条 \bibitem 或 \end
        m = re.search(r"\\bibitem\{" + re.escape(k) + r"\}(.*?)(?=\\bibitem|\\end\{thebibliography\})",
                      t, re.S)
        if m:
            s = re.sub(r"\s+", " ", m.group(1)).strip()
            print(f"  ✅ {k}")
            print(f"     {s[:320]}")
        else:
            print(f"  ❌ {k} 未找到")
        print()

    print("=== 该结论在综述里的完整句子 ===")
    i = t.find("site dominates allocation")
    if i > 0:
        print("  " + re.sub(r"\s+", " ", t[max(0, i - 320):i + 480]).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
