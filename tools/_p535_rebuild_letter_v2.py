# -*- coding: utf-8 -*-
r"""把回复信重建为「审稿人分组 + 每条意见原文 + 其下回复」，并去掉重复分节头（2026-10-13）。

## 操作者要求

> **"回复是三个审稿人的评论底下分别回复"**

## 本脚本（幂等）

从 `outputs/analysis/p3_reviews_structured.json`（33 条意见原文）与当前回复信里解析出的回复正文，
重建为：

```
# Response to Reviewers（变更汇总表 + 篇幅说明 + 溯源纪律）
--- 
# Reviewer 1
## Comment R1.1
> <意见完整原文>
**Response.** <回复>
...
```

**并剥掉任何位置的残留分节头**（`# Reviewer N`）⇒ 保证"`# Reviewer` 恰好 3 次"。

    python tools\_p535_rebuild_letter_v2.py [--apply]
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
LETTER = REPO / "docs" / "P3_RESPONSE_LETTER.md"
BACKUP = REPO / "docs" / "P3_RESPONSE_LETTER.md.bak_p535"   # 原始版（## R1.1 格式，无重复头）

REV_TITLE = {"R1": "Reviewer 1", "R2": "Reviewer 2", "R3": "Reviewer 3"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    items = json.loads(io.open(STRUCT, encoding="utf-8", errors="replace").read())
    src = BACKUP if BACKUP.exists() else LETTER
    old = io.open(src, encoding="utf-8", errors="replace").read()
    print(f"  意见 {len(items)} 条 ｜ 源文件 {src.name}（{len(old):,} 字符）")

    i = old.find("# Reviewer 1")
    if i < 0:
        print("  🔴 找不到 '# Reviewer 1'")
        return 1
    header = old[:i].rstrip()
    body = old[i:]

    parts = re.split(r"^## (R\d+\.\d+)\s*$", body, flags=re.M)
    replies = {}
    for k in range(1, len(parts) - 1, 2):
        rid = parts[k].strip()
        txt = parts[k + 1]
        # 剥掉旧的 "> 意见" 引用块（新版用结构化 JSON 的完整原文）
        txt = re.sub(r"^(?:> [^\n]*\n)+", "", txt.lstrip("\n"), count=1)
        # 幂等：剥掉任何位置的残留分节头与分隔线
        txt = re.sub(r"\n*---\n+# Reviewer \d+\s*", "\n", txt)
        txt = re.sub(r"^---\n+# Reviewer \d+\s*", "", txt)
        replies[rid] = txt.strip()
    print(f"  解析出回复 {len(replies)} 条")
    miss = [it["id"] for it in items if it["id"] not in replies]
    if miss:
        print(f"  🔴 缺回复：{miss}")
        return 1

    out = [header, ""]
    cur = None
    for it in items:
        rev = it["id"].split(".")[0]
        if rev != cur:
            cur = rev
            out += ["", "---", "", f"# {REV_TITLE.get(rev, rev)}", ""]
        out += [f"## Comment {it['id']}", "",
                "> " + it["comment"].replace("\n", "\n> "), "",
                "**Response.** " + replies[it["id"]], ""]
    text = "\n".join(out).rstrip() + "\n"
    print(f"  ⇒ {len(text):,} 字符")

    print()
    print("  核验：")
    ok = True
    for r in ("1", "2", "3"):
        n = len(re.findall(rf"^# Reviewer {r}$", text, re.M))
        good = n == 1
        ok = ok and good
        print(f"  {'✅' if good else '🔴'} '# Reviewer {r}'：{n} 次（应 1）")
    n_head = len(re.findall(r"^# Reviewer", text, re.M))
    print(f"  {'✅' if n_head == 3 else '🔴'} 分节头总数：{n_head}（应 3）")
    for rev, cnt in (("R1", 5), ("R2", 5), ("R3", 23)):
        n = len(re.findall(rf"^## Comment {rev}\.", text, re.M))
        good = n == cnt
        ok = ok and good
        print(f"  {'✅' if good else '🔴'} {REV_TITLE[rev]}：{n} 条（应 {cnt}）")
    nc, nr = text.count("## Comment "), text.count("**Response.**")
    good = nc == len(items) == nr
    ok = ok and good
    print(f"  {'✅' if good else '🔴'} Comment {nc} ｜ Response {nr}（应各 {len(items)}）")
    for k in ("$3.09\\times$", "7{,}237{,}632", "0.2057", "$p = 0.100$", "runs\\[90\\]"):
        v = k in text
        ok = ok and v
        print(f"  {'✅' if v else '🔴'} 保留 {k}")
    for bad in ("sharp phase transition", "reduces uncertainty by"):
        v = bad not in text
        ok = ok and v
        print(f"  {'✅' if v else '🔴'} 无「{bad}」")

    if not a.apply:
        print("  （预演）")
        return 0 if ok else 2
    io.open(LETTER, "w", encoding="utf-8", newline="").write(text)
    print(f"\n  ✅ 已写 {LETTER.relative_to(REPO)}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
