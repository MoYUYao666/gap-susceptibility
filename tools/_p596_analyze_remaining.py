# -*- coding: utf-8 -*-
r"""分析剩余 119 个待译文件的**性质**：管线 vs 一次性（2026-10-14）。

## 为什么要分

`tools/obsolete/`（1,282 个一次性脚本）已排除。
**但 `tools/` 顶层里还有多少是"一次性分析脚本"？** 若比例高，更好的做法是
**把它们一并归入 `tools/obsolete/`**（本地留档），而不是逐个翻译 ——
**符合操作者"只推代码与结果 JSON、可重跑管线"的边界，也更快。**

    python tools\_p596_analyze_remaining.py
"""
from __future__ import annotations

import collections
import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
CJK = re.compile(r"[\u4e00-\u9fff]")

# 可重跑管线的特征（在 docstring 里声明了 __main__ 且接受 CLI 参数、被 README 引用等）
PIPELINE_HINTS = ("argparse", "if __name__")


def main() -> int:
    r = subprocess.run(["git", "ls-files"], cwd=str(PC), capture_output=True)
    tracked = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
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
            left[rel] = (n, t)

    print(f"  待译 {len(left)} 个 / {sum(n for n, _ in left.values()):,} 字符")
    print()

    # ① 被 README / 文档引用？（引用 = 更像管线）
    refs = {}
    for rel in left:
        base = Path(rel).name
        rr = subprocess.run(["git", "grep", "-l", "-F", base, "--", "*.md"],
                            cwd=str(PC), capture_output=True)
        refs[rel] = [x for x in rr.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]

    # ② 分类
    cat = collections.Counter()
    details = collections.defaultdict(list)
    for rel, (n, t) in left.items():
        is_py = rel.endswith(".py")
        has_main = "if __name__" in t
        has_argparse = "argparse" in t
        is_ref = bool(refs[rel])
        if not is_py:
            k = "非 Python（md/json/sh/txt）"
        elif is_ref:
            k = "被文档引用（管线）"
        elif has_main and has_argparse:
            k = "有 __main__ + argparse"
        elif has_main:
            k = "仅 __main__"
        else:
            k = "无 __main__（模块/片段）"
        cat[k] += 1
        details[k].append((n, rel))

    print("  分类：")
    for k, v in cat.most_common():
        tot = sum(n for n, _ in details[k])
        print(f"     {k:<28} {v:>4} 个 ｜ {tot:>6,} 字符")

    print()
    print("  「被文档引用」的（**这些应当翻译而不是排除**）：")
    for n, rel in sorted(details["被文档引用（管线）"], reverse=True):
        print(f"     {n:>5}  {rel}  ← {refs[rel][:2]}")

    print()
    print("  非 Python 的（文档/数据）：")
    for n, rel in sorted(details["非 Python（md/json/sh/txt）"], reverse=True):
        print(f"     {n:>5}  {rel}")

    print()
    print("  按目录：")
    d = collections.Counter()
    dc = collections.Counter()
    for rel, (n, _) in left.items():
        top = rel.split("/")[0]
        d[top] += 1
        dc[top] += n
    for k in sorted(d, key=lambda x: -dc[x]):
        print(f"     {k:<16} {d[k]:>4} 个 ｜ {dc[k]:>6,} 字符")

    print()
    print("  按前缀（tools/ 下的家族）：")
    fam = collections.Counter()
    famc = collections.Counter()
    for rel, (n, _) in left.items():
        if not rel.startswith("tools/"):
            continue
        name = Path(rel).name
        m = re.match(r"^([a-z0-9]+?)_", name)
        pre = m.group(1) if m else "(other)"
        fam[pre] += 1
        famc[pre] += n
    for k in sorted(fam, key=lambda x: -famc[x]):
        print(f"     {k:<14} {fam[k]:>4} 个 ｜ {famc[k]:>6,} 字符")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
