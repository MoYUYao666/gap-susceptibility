# -*- coding: utf-8 -*-
r"""生成待译清单（供并行翻译 workflow 用）（2026-10-14）。

    python tools\_p593_make_translate_manifest.py --apply
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "translate_manifest.json"
CJK = re.compile(r"[\u4e00-\u9fff]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = subprocess.run(["git", "ls-files"], cwd=str(PC), capture_output=True)
    tracked = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
    items = []
    for rel in tracked:
        if rel.startswith("tools/obsolete/"):
            continue
        p = PC / rel
        if not p.exists():
            continue
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        n = len(CJK.findall(t))
        if n:
            items.append({"path": rel, "cjk": n, "bytes": p.stat().st_size,
                          "ext": p.suffix.lower(),
                          "lines": len(t.splitlines())})
    items.sort(key=lambda x: -x["cjk"])
    print(f"  待译 {len(items)} 个文件 / {sum(i['cjk'] for i in items):,} 中文字符")
    d = collections.Counter()
    for i in items:
        d[i["ext"] or "(none)"] += 1
    print(f"  按扩展名：{dict(d)}")
    per = collections.Counter()
    for i in items:
        per[i["path"].split("/")[0]] += 1
    print(f"  按目录：{dict(per)}")

    # 分批（每批 ~15 个文件，按 cjk 量均衡）
    BATCH = 15
    batches = [items[i:i + BATCH] for i in range(0, len(items), BATCH)]
    print(f"  分 {len(batches)} 批（每批 ≤{BATCH}）")
    for k, b in enumerate(batches, 1):
        print(f"     批 {k:>2}: {len(b):>2} 个 / {sum(x['cjk'] for x in b):>5} 字符  "
              f"（最大 {b[0]['path']}）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"total_files": len(items), "total_cjk": sum(i["cjk"] for i in items),
             "batches": batches}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
