# -*- coding: utf-8 -*-
r"""从 GitHub 发布库移除 `docs/`（2026-10-14）。

## 操作者要求

> **"不要放 docs"**

## 先看清 `docs/` 里有什么（决定是否需要保留历史）

`publish_clean/` 现有 **78 + 新增** 个 `docs/` 文件，含方法报告与审计记录。
**⚠️ 其中可能含不该公开的内容**（如审稿意见解析、投稿策略、内部决策）。

## 本脚本步骤

1. 清点 `publish_clean/docs/`（内容与体积）
2. **移到本地暂存区**（`_removed_from_publish/docs/`，**不删除**）
3. `git rm -r --cached docs` + 提交 + 推送
4. **重打 tag 并重建 Release**（让 Zenodo 快照也不含 `docs/`）
5. 更新同步脚本：**永久排除 `docs/`**

    python tools\_p582_remove_docs_from_publish.py [--dry-run|--apply]
"""
from __future__ import annotations

import argparse
import collections
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
DOCS = PC / "docs"
KEEP = REPO / "_removed_from_publish" / "docs"

SUSPECT = ["review", "referee", "审稿", "投稿", "submission", "strategy", "decision",
           "rebuttal", "response", "reviewer", "cover_letter", "highlights"]


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

    files = [p for p in DOCS.rglob("*") if p.is_file()] if DOCS.exists() else []
    tot = sum(p.stat().st_size for p in files)
    print(f"  publish_clean/docs/：{len(files)} 个文件 / {tot/1024:.0f} KB")
    rc, out, _ = run(["git", "ls-files", "docs"])
    tracked = [x for x in out.splitlines() if x.strip()]
    print(f"  其中 git 已跟踪：{len(tracked)} 个")

    print()
    print("  按子目录：")
    d = collections.Counter()
    for p in files:
        rel = p.relative_to(DOCS)
        d[str(rel.parent) if len(rel.parts) > 1 else "(根)"] += 1
    for k, n in d.most_common(20):
        print(f"     {k:<40} {n:>4}")

    print()
    print("  ⚠️ 文件名/内容含敏感关键词的（公开前须确认）：")
    hits = []
    for p in files:
        low = p.name.lower()
        if any(s in low for s in SUSPECT):
            hits.append(p.relative_to(DOCS).as_posix())
    print(f"     命中 {len(hits)} 个：")
    for h in hits[:15]:
        print(f"       {h}")

    if a.dry_run:
        print()
        print("  （dry-run；加 --apply 执行移除）")
        return 0

    # 本地留存
    KEEP.mkdir(parents=True, exist_ok=True)
    rc, out, _ = run(["git", "rm", "-r", "--cached", "-q", "docs"])
    print(f"\n  ① git rm --cached docs：rc={rc}")
    print(f"  ② 本地文件保留在 {KEEP.relative_to(REPO)}（**不删除**）")
    for p in files:
        dst = KEEP / p.relative_to(DOCS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(p, dst)
    print(f"     已复制 {len(files)} 个文件")

    # 从工作区删掉（索引已移除，工作区也清掉以免再被 add）
    import shutil
    shutil.rmtree(DOCS, ignore_errors=True)
    print(f"  ③ 已从 publish_clean 工作区移除 docs/")

    # .gitignore 加固
    gi = PC / ".gitignore"
    t = gi.read_text(encoding="utf-8", errors="replace") if gi.exists() else ""
    if "docs/ 不入发布库" not in t:
        gi.write_text(t.rstrip() + "\n\n# docs/ 不入发布库（2026-10-14 操作者要求）\ndocs/\n",
                      encoding="utf-8", newline="")
        print("  ④ .gitignore 已加 docs/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
