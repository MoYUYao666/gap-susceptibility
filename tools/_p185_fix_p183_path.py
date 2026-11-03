# -*- coding: utf-8 -*-
r"""修 `_p183` 的 out-dir（**又是缺 rank 段**）（2026-10-11）。

## 症状

`coco_sweep_text_only/r16/text_only/seed42` **8 秒 rc=1**（两次重试都失败）。

## 根因（**与 `_p169` 同一个错**）

脚本要求 `--out-dir` 含 `"r{rank}"` 子串（防污染校验），否则 `raise SystemExit`。
我的 JOBS 写的是**基础路径** `outputs/coco_sweep_text_only`，而 rank 是分开的字段
→ 传进去的 `--out-dir` 不含 rank → 被拒。

## 修法

`run_one` 里把 `--out-dir` 拼成 `f"{outdir}/r{rank}"`（与 `_p173` 一致）。

    python tools\_p185_fix_p183_path.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p183_coco_general.py"

OLD = '''    cmd = [PY, "experiments/strict_freeze_control.py",
           "--dataset", "coco", "--data-dir", ".",
           "--out-dir", outdir, "--name", f"coco_{arm}_r{rank}_",'''
NEW = '''    cmd = [PY, "experiments/strict_freeze_control.py",
           "--dataset", "coco", "--data-dir", ".",
           "--out-dir", f"{outdir}/r{rank}", "--name", f"coco_{arm}_r{rank}_",'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"=== 锚点命中 {n} ===")
    if n != 1:
        return 1
    t2 = t.replace(OLD, NEW, 1)
    try:
        ast.parse(t2)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    print("  ✅ 已修：--out-dir 补上 /r{rank}")

    # 清理被写错的目录（基础路径下的 text_only/、both/）
    import shutil
    for bad in ("outputs/coco_sweep_text_only/text_only",
                "outputs/coco_sweep/both"):
        p = REPO / bad
        if p.exists():
            files = list(p.rglob("results.json"))
            if files:
                dst = p.with_name(p.name + ".MISPLACED_no_rank_segment")
                if dst.exists():
                    shutil.rmtree(dst)
                p.rename(dst)
                print(f"  ✅ 错位目录改名：{bad} → {dst.name}（{len(files)} 个结果）")
            else:
                shutil.rmtree(p)
                print(f"  ✅ 空目录已删：{bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
