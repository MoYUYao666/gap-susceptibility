# -*- coding: utf-8 -*-
r"""核对 `publish_clean/` 的发布状态（2026-10-14）。

    python tools\_p570_check_publish_repo.py
"""
from __future__ import annotations

import io
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"


def run(args, cwd):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace"), r.stderr.decode("utf-8", errors="replace")


def main() -> int:
    print(f"  publish_clean 存在: {PC.exists()}")
    if not PC.exists():
        return 1
    for label, args in (("branch", ["git", "rev-parse", "--abbrev-ref", "HEAD"]),
                        ("HEAD", ["git", "log", "-1", "--pretty=%h | %ad | %s", "--date=short"]),
                        ("最近 5 次提交", ["git", "log", "-5", "--pretty=%h %ad %s", "--date=short"]),
                        ("远端", ["git", "remote", "-v"]),
                        ("工作区状态", ["git", "status", "--short"]),
                        ("已跟踪文件数", ["git", "ls-files"])):
        rc, out, err = run(args, PC)
        print()
        print(f"  ── {label}（rc={rc}）")
        if label == "已跟踪文件数":
            lines = [x for x in out.splitlines() if x.strip()]
            print(f"     {len(lines)} 个文件")
            dirs = {}
            for x in lines:
                d = x.split("/")[0] if "/" in x else "(root)"
                dirs[d] = dirs.get(d, 0) + 1
            for d, n in sorted(dirs.items(), key=lambda kv: -kv[1]):
                print(f"       {d:<24} {n}")
        else:
            for l in out.strip().splitlines()[:8]:
                print("     " + l)
        if err.strip():
            print("     [stderr] " + err.strip().splitlines()[0][:140])
    print()
    print("  ── 与远端的关系")
    rc, out, err = run(["git", "log", "--oneline", "-3", "origin/main"], PC)
    if rc == 0:
        print("     origin/main 最近 3 次：")
        for l in out.strip().splitlines():
            print("       " + l)
    else:
        print(f"     ⚠️ 读 origin/main 失败（rc={rc}）：{err.strip().splitlines()[:1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
