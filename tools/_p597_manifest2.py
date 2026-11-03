# -*- coding: utf-8 -*-
r"""生成第二轮翻译清单：大文件给 workflow，小文件与非 Python 自处理（2026-10-14）。

    python tools\_p597_manifest2.py --apply
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

    ME = [i for i in items if i["cjk"] <= 60 or i["ext"] != ".py"]
    WF = [i for i in items if i not in ME]
    print(f"  自处理（≤60 字符 或 非 .py）：{len(ME)} 个 / {sum(i['cjk'] for i in ME):,} 字符")
    print(f"  交给 workflow：      {len(WF)} 个 / {sum(i['cjk'] for i in WF):,} 字符")

    B = 14
    batches = [WF[i:i + B] for i in range(0, len(WF), B)]
    print(f"  workflow 分批：{len(batches)} 批")
    for k, b in enumerate(batches, 1):
        print(f"     批 {k:>2}: {len(b):>2} 个 / {sum(x['cjk'] for x in b):>5} 字符")

    print()
    print("  自处理清单：")
    for i in ME:
        print(f"     {i['cjk']:>4}  {i['path']}")

    if a.apply:
        out = REPO / "outputs" / "analysis" / "translate_manifest2.json"
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps(
            {"self": ME, "batches": batches}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
