# -*- coding: utf-8 -*-
r"""重建回复信：按「审稿意见原文 + 其下直接回复」组织（EM 逐条格式）（2026-10-13）。

## 操作者要求（2026-10-13 13:12）

> **"回复是三个审稿人的评论底下分别回复"**

## 与旧版的区别

**旧版**：`## R1.1` → `> 意见` → 回复正文（**意见只引一行摘要**）
**新版**：**每条意见的完整原文以引用块呈现**，**紧接其下就是回复** ⇒
审稿人在 EM 表单里逐条读"我的意见 → 作者答复"，无需来回对照。

**结构**：
```
# Response to Reviewers
（变更汇总表 + 篇幅说明 + 溯源纪律）
# Reviewer 1
## Comment R1.1
> <意见完整原文>
**Response.**
<回复>
...
# Reviewer 2
...
# Reviewer 3
...
```

    python tools\_p534_rebuild_letter_per_reviewer.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STRUCT = REPO / "outputs" / "analysis" / "p3_reviews_structured.json"
OLD = REPO / "docs" / "P3_RESPONSE_LETTER.md"
OUT = REPO / "docs" / "P3_RESPONSE_LETTER.md"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    items = json.loads(io.open(STRUCT, encoding="utf-8", errors="replace").read())
    old = io.open(OLD, encoding="utf-8", errors="replace").read()
    print(f"  意见 {len(items)} 条 ｜ 旧版 {len(old):,} 字符")

    # 提取旧版的：开头块（到 "# Reviewer 1" 之前）与每条回复正文
    i = old.find("# Reviewer 1")
    if i < 0:
        print("  🔴 旧版找不到 '# Reviewer 1'")
        return 1
    header = old[:i].rstrip()
    body = old[i:]

    # 按 "## Rxx.y" 切出各条回复
    parts = re.split(r"^## (R\d+\.\d+)\s*$", body, flags=re.M)
    replies = {}
    # parts = [前言, id1, 正文1, id2, 正文2, ...]
    for k in range(1, len(parts) - 1, 2):
        rid = parts[k].strip()
        txt = parts[k + 1]
        # 去掉旧版里的 "> 意见" 引用块（新版用结构化 JSON 的完整原文）
        txt = re.sub(r"^(?:> [^\n]*\n)+", "", txt.lstrip("\n"), count=1)
        # 去掉旧版残留的分节头（"# Reviewer N" 与紧随的 "---"）—— 新版自己会插入
        txt = re.sub(r"\n*---\n+# Reviewer \d+\s*$", "", txt)
        txt = re.sub(r"^---\n+# Reviewer \d+\s*", "", txt)
        replies[rid] = txt.strip()
    print(f"  解析出回复 {len(replies)} 条")
    miss = [it["id"] for it in items if it["id"] not in replies]
    if miss:
        print(f"  🔴 缺回复：{miss}")
        return 1

    out = [header, ""]
    cur_rev = None
    n = 0
    for it in items:
        rev = it["id"].split(".")[0]
        if rev != cur_rev:
            cur_rev = rev
            names = {"R1": "Reviewer 1", "R2": "Reviewer 2", "R3": "Reviewer 3"}
            out.append("")
            out.append("---")
            out.append("")
            out.append(f"# {names.get(rev, rev)}")
            out.append("")
        out.append(f"## Comment {it['id']}")
        out.append("")
        out.append("> " + it["comment"].replace("\n", "\n> "))
        out.append("")
        out.append("**Response.** " + replies[it["id"]])
        out.append("")
        n += 1
    text = "\n".join(out).rstrip() + "\n"
    print(f"  ⇒ 新版 {len(text):,} 字符（{n} 条，按审稿人分组）")

    # 核验
    for rev, cnt in (("R1", 5), ("R2", 5), ("R3", 23)):
        got = len(re.findall(rf"^## Comment {rev}\.", text, re.M))
        print(f"  {'✅' if got == cnt else '🔴'} Reviewer {rev[-1]}：{got} 条（应 {cnt}）")
    checks = {
        "每条都有 Response.": text.count("**Response.**") == len(items),
        "每条都有意见引用块": text.count("## Comment ") == len(items),
        "3.09× 仍在": "$3.09\\times$" in text,
        "无 'sharp phase transition'": "sharp phase transition" not in text,
    }
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")

    if not a.apply:
        print("  （预演）")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(text)
    print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
