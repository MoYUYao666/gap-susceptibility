# -*- coding: utf-8 -*-
r"""生成最终（第四次）翻译清单，覆盖 `7ee0059` 新收录的文件（2026-10-14）。

    python tools\_p609_manifest4.py --apply
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
            b = p.read_bytes()
            if b"\x00" in b[:4096]:
                continue
            t = b.decode("utf-8")
        except Exception:
            continue
        n = len(CJK.findall(t))
        if n:
            items.append({"path": rel, "cjk": n, "ext": p.suffix.lower()})
    items.sort(key=lambda x: -x["cjk"])
    tot = sum(i["cjk"] for i in items)
    print(f"  仍含中文：**{len(items)} 个 / {tot:,} 字符**")
    import collections
    e = collections.Counter(i["ext"] or "(none)" for i in items)
    print(f"  按扩展名：{dict(e)}")
    B = 12
    batches = [items[i:i + B] for i in range(0, len(items), B)]
    print(f"  分 {len(batches)} 批")
    for k, b in enumerate(batches, 1):
        print(f"     批 {k:>2}: {len(b):>2} 个 / {sum(x['cjk'] for x in b):>5} 字符")
    if a.apply:
        out = REPO / "outputs" / "analysis" / "translate_manifest4.json"
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps(
            {"total": tot, "batches": batches}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
