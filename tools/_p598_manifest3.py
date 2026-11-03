# -*- coding: utf-8 -*-
r"""生成第三轮（收尾）翻译清单（2026-10-14）。

    python tools\_p598_manifest3.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
CJK = re.compile(r"[\u4e00-\u9fff]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = subprocess.run(["git", "ls-files"], cwd=str(PC), capture_output=True)
    tracked = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
    items = []
    for rel in tracked:
        p = PC / rel
        if not p.exists():
            continue
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        n = len(CJK.findall(t))
        if n:
            items.append({"path": rel, "cjk": n, "ext": p.suffix.lower()})
    items.sort(key=lambda x: -x["cjk"])
    print(f"  剩余 {len(items)} 个 / {sum(i['cjk'] for i in items):,} 字符")
    B = 12
    batches = [items[i:i + B] for i in range(0, len(items), B)]
    print(f"  分 {len(batches)} 批（每批 ≤{B}）")
    for k, b in enumerate(batches, 1):
        print(f"     批 {k}: {len(b):>2} 个 / {sum(x['cjk'] for x in b):>4} 字符")
    print()
    for x in items:
        print(f"     {x['cjk']:>4}  {x['path']}")
    if a.apply:
        out = REPO / "outputs" / "analysis" / "translate_manifest3.json"
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps(
            {"batches": batches}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
