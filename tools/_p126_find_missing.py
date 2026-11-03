# -*- coding: utf-8 -*-
r"""查书目块里缺的 2 条 + 中文提示文字混进文献表（2026-10-10）。

## 现象

`bibitem 共 54 条`（应 56）；且书目块内出现**中文**（"作者未能查证，见备注"）
→ 那是我给"无作者"条目写的**中文提示**，**不该出现在投稿的文献表里**。

    python tools\_p126_find_missing.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper_a1" / "main.tex"
FIXED = REPO / "outputs" / "analysis" / "a1_apa_fixed.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8", errors="replace").read()
    i = t.find("\\begin{thebibliography}")
    j = t.find("\\end{thebibliography}")
    block = t[i:j]

    inblock = set(re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}", block))
    want = {r["key"] for r in json.loads(io.open(FIXED, encoding="utf-8").read())}
    missing = sorted(want - inblock)
    extra = sorted(inblock - want)
    print(f"=== 块内 {len(inblock)} 条 ｜ 应有 {len(want)} 条 ===")
    print(f"  缺: {len(missing)} {missing}")
    print(f"  多: {len(extra)} {extra}")

    print("\n=== 块内含中文的行（我的提示文字，应删除/改英文）===")
    for n, ln in enumerate(block.splitlines(), 1):
        if re.search(r"[\u4e00-\u9fff]", ln):
            print(f"  L{n}: {ln.strip()[:150]}")

    print("\n=== 缺的条目在 JSON 里的内容 ===")
    rows = {r["key"]: r for r in json.loads(io.open(FIXED, encoding="utf-8").read())}
    for k in missing:
        r = rows.get(k)
        if r:
            print(f"  [{k}] year={r.get('year')} authors={len(r.get('authors') or [])} "
                  f"title={r['title'][:70]}")

    if a.apply:
        # ① 删掉中文提示行（含 ⚠️ 的整条 bibitem 若只剩提示）
        lines = block.splitlines()
        keep = []
        for ln in lines:
            if re.search(r"[\u4e00-\u9fff]", ln) and "\\bibitem" not in ln:
                continue          # 纯提示行 → 丢
            if "\\bibitem" in ln and re.search(r"[\u4e00-\u9fff]", ln):
                # 该条只有提示 → 改为英文备注
                ln = re.sub(r"%\s*⚠️[^\n]*", "", ln)
                ln = ln.replace("作者未能查证，见 ENVIRONMENT 备注",
                                "[authors not verifiable from public records]")
                ln = re.sub(r"[\u4e00-\u9fff，]+", "", ln)
            keep.append(ln)
        newblock = "\n".join(keep)
        t2 = t[:i] + newblock + t[j:]
        io.open(MAIN, "w", encoding="utf-8", newline="").write(t2)
        print("\n  ✅ 已清理中文提示行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
