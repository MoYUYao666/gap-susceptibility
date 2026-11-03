# -*- coding: utf-8 -*-
r"""清点 GitHub **已跟踪**文件里的中文（2026-10-14）。

## 为什么只算已跟踪

`publish_clean/` 工作区有 3,588 个文件，但 **`.gitignore` 已排除 `*.log` 等**；
只用工作区统计会把不入库的也算进来（我上一版就错在这里）。

    python tools\_p591_chinese_tracked.py [--apply]
"""
from __future__ import annotations

import argparse
import collections
import io
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
    print(f"  已跟踪文件：{len(tracked)} 个")

    per = {}
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
            per[rel] = n
    tot = sum(per.values())
    print(f"  含中文的已跟踪文件：**{len(per)} / {len(tracked)}** ｜ 中文字符 **{tot:,}**")

    print()
    print("  按顶层目录：")
    d = collections.Counter()
    dc = collections.Counter()
    for f, n in per.items():
        top = f.split("/")[0] if "/" in f else "(root)"
        d[top] += 1
        dc[top] += n
    for k in sorted(d, key=lambda x: -dc[x]):
        print(f"     {k:<26} {d[k]:>5} 个文件 ｜ {dc[k]:>8,} 字符")

    print()
    print("  按文件类型：")
    e = collections.Counter()
    ec = collections.Counter()
    for f, n in per.items():
        ext = Path(f).suffix.lower() or "(none)"
        e[ext] += 1
        ec[ext] += n
    for k in sorted(e, key=lambda x: -ec[x])[:12]:
        print(f"     {ext:<12} {e[k]:>5} 个 ｜ {ec[k]:>8,} 字符")

    print()
    print("  中文最多的 15 个：")
    for f, n in sorted(per.items(), key=lambda kv: -kv[1])[:15]:
        print(f"     {n:>6}  {f}")

    if a.apply:
        out = REPO / "outputs" / "analysis" / "publish_chinese_tracked.json"
        import json
        out.parent.mkdir(parents=True, exist_ok=True)
        io.open(out, "w", encoding="utf-8", newline="").write(
            json.dumps({"tracked": len(tracked), "with_cjk": len(per),
                        "cjk_chars": tot, "files": per}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
