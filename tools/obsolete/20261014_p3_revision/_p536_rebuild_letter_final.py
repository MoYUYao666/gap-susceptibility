# -*- coding: utf-8 -*-
r"""把回复信重建为「审稿人分组 + 每条意见原文 + 其下回复」（2026-10-13）。

## 操作者要求

> **"回复是三个审稿人的评论底下分别回复"**

## 数据来源（**用 git 取原始版，避免 PowerShell 重定向破坏编码**）

- **意见原文**：`outputs/analysis/p3_reviews_structured.json`（33 条）
- **回复正文**：`git show eaa41c2:docs/P3_RESPONSE_LETTER.md`（原始版，`## R1.1` 格式）

**⚠️ 教训**：`git show ... > file` 在 PowerShell 里会把 UTF-8 当 UTF-16 处理（本次 41,456 → 84,362 字符）
⇒ **必须用 Python 读 stdout 字节并显式解码**。

    python tools\_p536_rebuild_letter_final.py [--apply]
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
STRUCT = REPO / "outputs" / "analysis" / "p3_reviews_structured.json"
LETTER = REPO / "docs" / "P3_RESPONSE_LETTER.md"
REV = {"R1": "Reviewer 1", "R2": "Reviewer 2", "R3": "Reviewer 3"}
COMMIT = "eaa41c2"


def git_show(path: str) -> str:
    r = subprocess.run(["git", "show", f"{COMMIT}:{path}"], cwd=str(REPO),
                       capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    items = json.loads(io.open(STRUCT, encoding="utf-8", errors="replace").read())
    old = git_show("docs/P3_RESPONSE_LETTER.md")
    print(f"  意见 {len(items)} 条 ｜ git 原始版 {len(old):,} 字符")

    i = old.find("# Reviewer 1")
    if i < 0:
        # 原始版没有分节头，用 "## R1.1" 定位
        i = old.find("## R1.1")
    if i < 0:
        print("  🔴 定位失败")
        return 1
    header = old[:i].rstrip()
    body = old[i:]

    parts = re.split(r"^## (R\d+\.\d+)\s*$", body, flags=re.M)
    print(f"  切出 {len(parts)} 段（应 {2*len(items)+1}）")
    replies = {}
    for k in range(1, len(parts) - 1, 2):
        rid = parts[k].strip()
        txt = parts[k + 1]
        txt = re.sub(r"^(?:> [^\n]*\n)+", "", txt.lstrip("\n"), count=1)   # 去旧引用块
        txt = re.sub(r"\n*---\n+# Reviewer \d+\s*", "\n", txt)             # 幂等去分节头
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
            out += ["", "---", "", f"# {REV.get(rev, rev)}", ""]
        out += [f"## Comment {it['id']}", "",
                "> " + it["comment"].replace("\n", "\n> "), "",
                "**Response.** " + replies[it["id"]], ""]
    text = "\n".join(out).rstrip() + "\n"
    print(f"  ⇒ 新版 {len(text):,} 字符")

    print()
    print("  核验：")
    ok = True
    n_head = len(re.findall(r"^# Reviewer", text, re.M))
    ok = ok and n_head == 3
    print(f"  {'✅' if n_head == 3 else '🔴'} 分节头总数 {n_head}（应 3）")
    for rev, cnt in (("R1", 5), ("R2", 5), ("R3", 23)):
        n = len(re.findall(rf"^## Comment {rev}\.", text, re.M))
        ok = ok and n == cnt
        print(f"  {'✅' if n == cnt else '🔴'} {REV[rev]}：{n} 条（应 {cnt}）")
    nc, nr = text.count("## Comment "), text.count("**Response.**")
    ok = ok and nc == len(items) == nr
    print(f"  {'✅' if nc == len(items) == nr else '🔴'} Comment {nc} ｜ Response {nr}")
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
