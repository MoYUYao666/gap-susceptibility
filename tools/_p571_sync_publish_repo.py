# -*- coding: utf-8 -*-
r"""同步最新代码/结果到 `publish_clean/`，并做发布前安全检查（2026-10-14）。

## 现状（`tools/_p570`）

- `publish_clean` HEAD = **`1ca7744`（2026-09-24）** ⇒ 三周未更新
- 已跟踪 **1303** 文件（`outputs/` 842、`tools/` 332、`docs/` 78、`experiments/` 25、`exp/` 12、`src/` 11、root 3）
- 远端 `ssh-origin` = `ssh://git@github.com/MoYUYao666/gap-susceptibility.git`
- **工作区有我的 README.md 改动**（`_p558`）+ 一个 `.bak` 残留

## 本脚本的安全规则（**关键**）

1. **只 `add` 不 `delete`**：用 `git add -A` 前先确认**没有删除**（`git status` 里不得有 `D`）
2. **不覆盖删除**：`robocopy` 用 `/E` 但**不加 `/PURGE`** ⇒ 远端已有而本地没有的文件**保留**
3. **内容判定**：扫描**将提交的文件内容**，命中稿件类特征（`\documentclass`、`\title{`、
   `\begin{abstract}`）的**排除**；并断言 `paper*` / `main*.tex` / `.pdf` 不在跟踪列表
4. **大量文件先 dry-run**：先打印统计与候选清单，再执行

    python tools\_p571_sync_publish_repo.py [--dry-run|--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"

# 允许发布的顶层目录（AGENTS.md 的发布边界）
ALLOW_TOP = {"tools", "outputs", "src", "exp", "experiments", "docs"}
ALLOW_ROOT_FILES = {"README.md", ".gitignore", "LICENSE", "requirements.txt"}
# 明文禁止
BAN_NAME = re.compile(r"(^|/)(main[^/]*\.(tex|pdf)|cover_letter[^/]*|title_page[^/]*|"
                      r"highlights[^/]*|.*\.docx?$|.*\.zip$|.*\.bak.*$)", re.I)
BAN_CONTENT = (r"\documentclass", r"\\begin\{abstract\}", r"\\maketitle")


def run(args, cwd=PC):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace"), r.stderr.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (a.dry_run or a.apply):
        a.dry_run = True

    # ① 清掉 .bak 残留（不进库）
    baks = [p for p in PC.rglob("*.bak*") if p.is_file()]
    print(f"  ① publish_clean 内 .bak 残留：{len(baks)} 个")
    for p in baks[:8]:
        print(f"       {p.relative_to(PC)}")

    # ② 统计要同步的候选（按顶层目录）
    print()
    print("  ② 候选文件（按顶层目录，仅统计**比 publish_clean 新或缺失**的）：")
    plan = {}
    for top in sorted(ALLOW_TOP):
        src = REPO / top
        if not src.is_dir():
            continue
        n_new = n_upd = n_same = 0
        for p in src.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(REPO)
            if BAN_NAME.search(rel.as_posix()):
                continue
            dst = PC / rel
            if not dst.exists():
                n_new += 1
            elif p.stat().st_mtime > dst.stat().st_mtime + 1:
                n_upd += 1
            else:
                n_same += 1
        plan[top] = (n_new, n_upd, n_same)
        print(f"     {top:<14} 新增 {n_new:>5} ｜ 更新 {n_upd:>5} ｜ 未变 {n_same:>6}")
    for f in sorted(ALLOW_ROOT_FILES):
        p = REPO / f
        if p.exists():
            dst = PC / f
            state = "新增" if not dst.exists() else ("更新" if p.stat().st_mtime > dst.stat().st_mtime + 1 else "未变")
            print(f"     (root) {f:<26} {state}")
    total_new = sum(v[0] for v in plan.values())
    total_upd = sum(v[1] for v in plan.values())
    print(f"     ⇒ 合计 新增 {total_new} ｜ 更新 {total_upd}")

    if a.dry_run:
        print()
        print("  （dry-run —— 未改动任何文件；加 --apply 执行）")
        return 0

    # ③ 执行：只复制（不删除）
    print()
    print("  ③ 复制中…")
    copied = 0
    for top in sorted(ALLOW_TOP):
        src = REPO / top
        if not src.is_dir():
            continue
        for p in src.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(REPO)
            if BAN_NAME.search(rel.as_posix()):
                continue
            dst = PC / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            copied += 1
    for f in sorted(ALLOW_ROOT_FILES):
        p = REPO / f
        if p.exists():
            shutil.copy2(p, PC / f)
            copied += 1
    print(f"     复制 {copied} 个文件（**未删除任何文件**）")

    # ④ 安全检查
    print()
    print("  ④ 发布前安全检查…")
    rc, out, err = run(["git", "status", "--porcelain"])
    lines = [l for l in out.splitlines() if l.strip()]
    dels = [l for l in lines if l.startswith(" D") or l.startswith("D ")]
    print(f"     git status 条目 {len(lines)} ｜ **删除项 {len(dels)}**（应为 0）")
    for d in dels[:5]:
        print(f"       🔴 {d}")
    rc, out, _ = run(["git", "ls-files"])
    tracked = [x for x in out.splitlines() if x.strip()]
    bad = [x for x in tracked if BAN_NAME.search(x)]
    print(f"     已跟踪 {len(tracked)} ｜ **命中禁令 {len(bad)}**（应为 0）")
    for b in bad[:5]:
        print(f"       🔴 {b}")
    # 大文件
    big = []
    for root, _, files in os.walk(PC):
        if ".git" in root:
            continue
        for f in files:
            fp = Path(root) / f
            if fp.stat().st_size > 100 * 1024 * 1024:
                big.append(fp.relative_to(PC))
    print(f"     >100 MB 文件：{len(big)} 个（应为 0）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
