# -*- coding: utf-8 -*-
r"""查 A1 的 top-k 消融是否已写进论文（2026-10-10）。

    python tools\_p93_a1_topk_status.py
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    # ① 消融产物
    f = REPO / "outputs" / "a1_rr_e2_topk.json"
    print("=== top-k 消融产物 ===")
    if f.exists():
        d = json.loads(io.open(f, encoding="utf-8").read())
        print(f"  {f.relative_to(REPO)}（{f.stat().st_size:,} B）")
        if isinstance(d, dict):
            ks = [k for k in d if re.fullmatch(r"\d+", str(k))]
            print(f"  顶层键: {list(d.keys())[:10]}")
            if ks:
                print(f"  k 取值: {sorted(int(x) for x in ks)}")
            # 取一个示例条目
            for k, v in list(d.items())[:3]:
                print(f"    {k}: {json.dumps(v, ensure_ascii=False)[:160]}")
        else:
            print(f"  （list，{len(d)} 项）：{json.dumps(d[0], ensure_ascii=False)[:200]}")
    else:
        print("  ❌ 不存在")

    # ② 论文里有没有写
    t = io.open(REPO / "paper_a1" / "main.tex", encoding="utf-8", errors="replace").read()
    print("\n=== 论文里与 top-k 有关的表述 ===")
    pats = [r"top-\$?k", r"top-5", r"top-1", r"\$k\s*\\in", r"top-\$k\$"]
    found = False
    for p in pats:
        for m in list(re.finditer(p, t))[:4]:
            s = " ".join(t[max(0, m.start() - 200):m.start() + 220].split())
            print(f"  [{p}] {s[:320]}")
            print()
            found = True
    if not found:
        print("  （未找到）")

    # ③ 论文里数据集提及次数
    print("=== 论文提及的数据集次数 ===")
    for d in ("ImageNet", "Flickr30k", "COCO", "DTD", "Food-101", "iNat"):
        n = len(re.findall(re.escape(d), t, re.I))
        print(f"  {d:<12} {n} 次")

    # ④ 表格标题列表（看有几个结果表）
    print("\n=== 论文的表格 ===")
    for m in re.finditer(r"\\caption\{([^}]{0,150})", t):
        print("  •", m.group(1)[:140])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
