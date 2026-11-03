# -*- coding: utf-8 -*-
r"""把 `tools/obsolete/` 移出发布库（本地保留），并清点剩余待译内容（2026-10-14）。

## 操作者裁决

> **"排除 tools/obsolete/，其余全译"**

## 为什么这是对的

`tools/obsolete/` 是 **1,282 个一次性修订脚本**（一个会话一个），**占发布库中文的 94%**
（~320,000 / 342,221 字符），且**本就不是维护目标** —— 它们记录了每个结论的产生过程，
但可重跑管线在 `tools/` 顶层。**排除它们在库内，本地留档即可。**

    python tools\_p592_drop_obsolete_translate.py [--apply]
"""
from __future__ import annotations

import argparse
import collections
import io
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
OBS = PC / "tools" / "obsolete"
KEEP = REPO / "_removed_from_publish" / "tools_obsolete"
CJK = re.compile(r"[\u4e00-\u9fff]")


def run(args, cwd=PC):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace"), r.stderr.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    files = [p for p in OBS.rglob("*") if p.is_file()] if OBS.exists() else []
    tot = sum(p.stat().st_size for p in files)
    print(f"  tools/obsolete/：{len(files)} 个文件 / {tot/1024/1024:.1f} MB")

    print()
    print("  剩余待译（已跟踪、含中文、非 obsolete）：")
    rc, out, _ = run(["git", "ls-files"])
    tracked = [x for x in out.splitlines() if x.strip()]
    todo = {}
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
            todo[rel] = n
    print(f"     **{len(todo)} 个文件 / {sum(todo.values()):,} 中文字符**")
    d = collections.Counter()
    dc = collections.Counter()
    for f, n in todo.items():
        top = f.split("/")[0] if "/" in f else "(root)"
        d[top] += 1
        dc[top] += n
    for k in sorted(d, key=lambda x: -dc[x]):
        print(f"       {k:<16} {d[k]:>4} 个 ｜ {dc[k]:>7,} 字符")
    print()
    print("  完整清单（按中文量降序，前 60）：")
    for f, n in sorted(todo.items(), key=lambda kv: -kv[1])[:60]:
        print(f"     {n:>5}  {f}")

    if not a.apply:
        print()
        print("  （预演；加 --apply 执行排除）")
        return 0

    # 本地留档 + 从索引与工作区移除
    KEEP.mkdir(parents=True, exist_ok=True)
    for p in files:
        dst = KEEP / p.relative_to(OBS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
    print(f"\n  ① 已复制 {len(files)} 个到 {KEEP.relative_to(REPO)}（**不删除**）")
    rc, _, _ = run(["git", "rm", "-r", "--cached", "-q", "tools/obsolete"])
    print(f"  ② git rm --cached tools/obsolete：rc={rc}")
    shutil.rmtree(OBS, ignore_errors=True)
    print(f"  ③ 已从 publish_clean 工作区移除")

    gi = PC / ".gitignore"
    t = gi.read_text(encoding="utf-8", errors="replace") if gi.exists() else ""
    if "tools/obsolete" not in t:
        gi.write_text(t.rstrip() + "\n\n# 一次性/存档脚本不入发布库（2026-10-14）\ntools/obsolete/\n",
                      encoding="utf-8", newline="")
        print("  ④ .gitignore 已加 tools/obsolete/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
