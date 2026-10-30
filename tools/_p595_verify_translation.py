# -*- coding: utf-8 -*-
r"""核验翻译结果：全库中文残留 + 语法完整性（2026-10-14）。

## 为什么要"以实际文件为准"

`_p593` 生成 manifest 时，`tools/obsolete/` 的排除操作**同时在进行**
⇒ 多批 agent 报告"清单里的路径不存在"。
**⇒ 不看清单，直接扫当前实际文件。**

    python tools\_p595_verify_translation.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import collections
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
    print(f"  已跟踪文件 {len(tracked)}")

    left = {}
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
            left[rel] = n

    print(f"  仍含中文：**{len(left)} 个文件 / {sum(left.values()):,} 字符**")
    if left:
        print()
        d = collections.Counter()
        dc = collections.Counter()
        for f, n in left.items():
            top = f.split("/")[0] if "/" in f else "(root)"
            d[top] += 1
            dc[top] += n
        for k in sorted(d, key=lambda x: -dc[x]):
            print(f"     {k:<18} {d[k]:>4} 个 ｜ {dc[k]:>7,} 字符")
        print()
        print("  最多的 30 个：")
        for f, n in sorted(left.items(), key=lambda kv: -kv[1])[:30]:
            print(f"     {n:>5}  {f}")

    # 语法核验
    print()
    print("=" * 100)
    print("语法核验（Python / JSON）")
    print("=" * 100)
    bad_py, bad_json, ok_py, ok_json = [], [], 0, 0
    for rel in tracked:
        p = PC / rel
        if not p.exists():
            continue
        if p.suffix == ".py":
            try:
                ast.parse(io.open(p, encoding="utf-8", errors="strict").read())
                ok_py += 1
            except Exception as e:
                bad_py.append((rel, str(e)[:80]))
        elif p.suffix == ".json":
            try:
                json.loads(io.open(p, encoding="utf-8", errors="strict").read())
                ok_json += 1
            except Exception as e:
                bad_json.append((rel, str(e)[:80]))
    print(f"  .py  : 通过 {ok_py} ｜ **失败 {len(bad_py)}**")
    for f, e in bad_py[:10]:
        print(f"        🔴 {f}: {e}")
    print(f"  .json: 通过 {ok_json} ｜ **失败 {len(bad_json)}**")
    for f, e in bad_json[:10]:
        print(f"        🔴 {f}: {e}")

    if a.apply:
        out = REPO / "outputs" / "analysis" / "publish_cjk_after.json"
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps(
            {"tracked": len(tracked), "with_cjk": len(left), "cjk": sum(left.values()),
             "files": left, "bad_py": bad_py, "bad_json": bad_json},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
