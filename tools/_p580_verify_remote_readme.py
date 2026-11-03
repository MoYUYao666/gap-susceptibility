# -*- coding: utf-8 -*-
r"""核验远端 GitHub 的 README 是否已是新版（2026-10-14）。

    python tools\_p580_verify_remote_readme.py
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
REPO_SLUG = "MoYUYao666/gap-susceptibility"

NEW_MARKS = ["Hardware and environment", "Data availability", "Citation",
             "additivity axiom", "bracketed", "126 + 57", "PRL (Revise)"]
OLD_MARKS = ["the unique admissible PEFT allocation statistic", "reduces uncertainty by",
             "phase transition at $r_c", "Prepared for IEEE TNNLS", "181 runs",
             "ICLR format backup"]


def main() -> int:
    print("=" * 100)
    print("① 通过 GitHub API 读远端 README（匿名 + gh 两条路）")
    print("=" * 100)
    text = ""
    r = subprocess.run(["gh", "api", f"repos/{REPO_SLUG}/readme", "--jq", ".content"],
                       capture_output=True)
    if r.returncode == 0:
        import base64
        try:
            text = base64.b64decode(r.stdout.decode().strip()).decode("utf-8", errors="replace")
            print("  ✅ 经 `gh api` 取到远端 README")
        except Exception as e:
            print(f"  ⚠️ 解码失败：{e}")
    else:
        print(f"  ⚠️ `gh api` 失败（rc={r.returncode}）：{r.stderr.decode('utf-8', errors='replace')[:120]}")

    if text:
        print(f"     远端 README：{len(text):,} 字符 / {len(text.splitlines())} 行")
        print()
        print("  新四节/新口径：")
        for m in NEW_MARKS:
            print(f"     {'✅' if m in text else '🔴'} {m}")
        print("  旧主张（应全为 0）：")
        ok = True
        for m in OLD_MARKS:
            n = text.count(m)
            ok = ok and n == 0
            print(f"     {'✅' if n == 0 else '🔴'} 「{m}」：{n} 处")
        print()
        print("  远端 README 开头 12 行：")
        for l in text.splitlines()[:12]:
            print("     " + l[:100])

    print()
    print("=" * 100)
    print("② 本地 vs 远端 一致性")
    print("=" * 100)
    local = io.open(PC / "README.md", encoding="utf-8", errors="replace").read()
    print(f"  本地 publish_clean/README.md：{len(local):,} 字符")
    if text:
        same = local.strip() == text.strip()
        print(f"  {'✅ 一致' if same else '⚠️ 不一致（可能行尾差异）'}")
        if not same:
            print(f"     本地旧主张残留：{[m for m in OLD_MARKS if m in local]}")
            print(f"     远端旧主张残留：{[m for m in OLD_MARKS if m in text]}")
    r = subprocess.run(["git", "log", "-1", "--pretty=%h | %ad | %s", "--date=short"],
                       cwd=str(PC), capture_output=True)
    print(f"  本地 HEAD：{r.stdout.decode().strip()}")
    r = subprocess.run(["git", "ls-remote", "ssh-origin", "main"], cwd=str(PC), capture_output=True)
    print(f"  远端 main：{r.stdout.decode().strip()[:60]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
