# -*- coding: utf-8 -*-
r"""核验 `publish_clean/` 的移动完整性，并暂存以让 git 识别为重命名（2026-10-14）。

## 为什么要核

`_p574` 把 **1,282 个一次性脚本**从 `tools/` 移入 `tools/obsolete/20261014_p3_revision/`，
尚未 `git add`。**未暂存时 `git status` 显示为 `D`（删除）** —— 这是**表象**，
暂存后 git 会识别为 **rename**（`R`）。但**必须先证明移动是完整的**（源有 N 个，目标就有 N 个）。

    python tools\_p575_verify_and_stage.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
OBS = PC / "tools" / "obsolete" / "20261014_p3_revision"


def run(args, cwd=PC):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace"), r.stderr.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 100)
    print("① 移动完整性")
    print("=" * 100)
    now_root = sorted(p.name for p in (PC / "tools").glob("_*.py"))
    in_obs = sorted(p.name for p in OBS.glob("_*.py"))
    print(f"  tools/ 根层剩余 `_*.py` : {len(now_root)}（应为 0）")
    for n in now_root[:5]:
        print(f"     🔴 {n}")
    print(f"  obsolete/ 内 `_*.py`   : {len(in_obs)}")
    print(f"  obsolete/ 全部文件     : {len([p for p in OBS.rglob('*') if p.is_file()])}")

    # 每个移走的文件在源仓库（REPO/tools）是否都能找到 → 证明未丢内容
    src_tools = REPO / "tools"
    missing = [n for n in in_obs if not (src_tools / n).exists()]
    print(f"  与源仓库比对：obsolete 内 {len(in_obs)} 个，源仓库缺 {len(missing)} 个")
    for n in missing[:5]:
        print(f"     ⚠️ {n}")

    print()
    print("=" * 100)
    print("② 暂存（让 git 识别为 rename）")
    print("=" * 100)
    rc, out, err = run(["git", "add", "-A"])
    print(f"  git add -A rc={rc}")
    if err.strip():
        print("     [stderr] " + err.strip().splitlines()[0][:160])

    print()
    print("=" * 100)
    print("③ 暂存后的状态（R = rename，D = 真删除）")
    print("=" * 100)
    rc, out, _ = run(["git", "status", "--porcelain"])
    lines = [l for l in out.splitlines() if l.strip()]
    kinds = {}
    for l in lines:
        k = l[:2].strip() or "?"
        kinds[k] = kinds.get(k, 0) + 1
    for k, n in sorted(kinds.items(), key=lambda kv: -kv[1]):
        print(f"     {k:<4} {n}")
    dels = [l for l in lines if l.startswith("D ") or l.startswith(" D")]
    renames = [l for l in lines if l.startswith("R")]
    print()
    print(f"  **rename {len(renames)} ｜ 未配对删除 {len(dels)}**")
    for d in dels[:8]:
        print(f"     🔴 {d}")

    rc, out, _ = run(["git", "diff", "--cached", "--stat"])
    tail = out.strip().splitlines()[-1:] if out.strip() else [""]
    print(f"  暂存统计末行：{tail[0][:150]}")

    # 体积
    rc, out, _ = run(["git", "ls-files"])
    tracked = [x for x in out.splitlines() if x.strip()]
    tot = 0
    for t in tracked:
        p = PC / t
        if p.exists():
            tot += p.stat().st_size
    print(f"  将跟踪 {len(tracked)} 个文件 ｜ 磁盘占用 {tot/1024/1024:.1f} MB")
    big = sorted(((PC / t).stat().st_size, t) for t in tracked if (PC / t).exists())
    print("  最大的 5 个：")
    for sz, n in big[-5:]:
        print(f"     {sz/1024/1024:>7.2f} MB  {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
