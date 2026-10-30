# -*- coding: utf-8 -*-
r"""诊断：README 为什么没更新（2026-10-14）。

## 怀疑

`_p558` 改的是 **`publish_clean/README.md`**（含撤回的主张更正 + 四节新增）；
但 `_p571`/`_p574` 的同步**把仓库根 `README.md` 复制进 `publish_clean/`** ⇒ **覆盖掉了那些改动**。
若仓库根 `README.md` 是旧的，则发布的是旧的。

    python tools\_p578_diagnose_readme.py
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"

MARK_OLD = ["the unique admissible PEFT allocation statistic",
            "reduces uncertainty by", "phase transition at $r_c", "Prepared for IEEE TNNLS",
            "181 runs"]
MARK_NEW = ["Hardware and environment", "Data availability", "Citation", "126 + 57",
            "bracketed", "additivity axiom"]

FILES = [("仓库根 README", REPO / "README.md"),
         ("publish_clean README", PC / "README.md")]


def main() -> int:
    print("=" * 100)
    print("① 两个 README 的现状")
    print("=" * 100)
    for label, p in FILES:
        if not p.exists():
            print(f"  🔴 {label}: 不存在（{p}）")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        print(f"  ── {label}: {len(t):,} 字符 / {len(t.splitlines())} 行 ｜ {p}")
        old = [m for m in MARK_OLD if m in t]
        new = [m for m in MARK_NEW if m in t]
        print(f"     旧主张残留：{old if old else '无'}")
        print(f"     新四节：   {new if new else '无'}")

    print()
    print("=" * 100)
    print("② git 里的版本（远端 main）")
    print("=" * 100)
    for ref in ("HEAD", "origin/main", "ssh-origin/main"):
        r = subprocess.run(["git", "show", f"{ref}:README.md"], cwd=str(PC), capture_output=True)
        if r.returncode != 0:
            print(f"  ⚠️ {ref}: 读取失败")
            continue
        t = r.stdout.decode("utf-8", errors="replace")
        old = [m for m in MARK_OLD if m in t]
        new = [m for m in MARK_NEW if m in t]
        print(f"  ── {ref}: {len(t):,} 字符")
        print(f"     旧主张残留：{old if old else '无'}")
        print(f"     新四节：   {new if new else '无'}")
        print(f"     含 'School of Electronics'：{'School of Electronics' in t}")

    print()
    print("=" * 100)
    print("③ 结论")
    print("=" * 100)
    root = io.open(REPO / "README.md", encoding="utf-8", errors="replace").read() \
        if (REPO / "README.md").exists() else ""
    pc = io.open(PC / "README.md", encoding="utf-8", errors="replace").read()
    if pc == root:
        print("  ⇒ 两个文件**相同** ⇒ 同步时被仓库根版本覆盖 ⇒ 根版本是旧的 ⇒ 发布的是旧 README")
    else:
        print("  ⇒ 两个文件不同 ⇒ 需看哪个是新的")
    print(f"     仓库根含新四节：{[m for m in MARK_NEW if m in root]}")
    print(f"     publish_clean 含新四节：{[m for m in MARK_NEW if m in pc]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
