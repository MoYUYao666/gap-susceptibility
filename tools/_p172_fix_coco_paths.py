# -*- coding: utf-8 -*-
r"""修 COCO 队列的路径 bug：`--out-dir` 必须是**含 rank 的子目录**（2026-10-11）。

## 根因（实测）

`experiments/strict_freeze_control.py`：
1. 输出路径 = `"%s/%s/seed%d" % (OUT_DIR, tag, seed)` —— **只有 OUT_DIR 与 tag 两层**；
2. `--rank != 8` 时校验 `"r{rank}" in OUT_DIR`，**否则 `raise SystemExit`**（rc=1）；
3. **r8 时 `--name` 不改变 `tag`**（脚本对 rank 8 有特例），所以 r8 的 run
   写进了 `OUT_DIR/text_only/seedN/` —— **放错了一级**。

**我的队列传的是基础路径** `outputs/coco_sweep_text_only`：
- `r2`/`r32`/`r64` → **校验拒绝**（rc=1，7 秒）→ 16 个失败；
- `r8` → 通过，但**写进基础目录** → **4 个错位结果**。

## 修法

`outdir = 基础路径 + "/r{rank}"` → 校验通过，且落点与旧结构一致
（`outputs/coco_sweep_text_only/r8/text_only/seed42/`）。

## 同时清理

**基础目录下的 `text_only/`（4 个 batch=128 的错位结果）→ 改名加 `.misplaced` 标记**，
不静默删除。

    python tools\_p172_fix_coco_paths.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
Q = REPO / "tools" / "_p169_batchfix_queue.py"
MISPLACED = REPO / "outputs" / "coco_sweep_text_only" / "text_only"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # ── ① 改队列：outdir 含 rank ──
    t = io.open(Q, encoding="utf-8", errors="replace").read()
    OLD = ('    ("coco_to", "outputs/coco_sweep_text_only", None, "coco", "{r}", '
           '["--alpha-mult", "2"],\n'
           '     [("text_only", ["42", "123", "456", "789", "1011"])]),')
    n = 0
    for r in ("2", "8", "32", "64"):
        old_i = OLD.replace("{r}", r)
        new_i = old_i.replace('"outputs/coco_sweep_text_only"',
                              f'"outputs/coco_sweep_text_only/r{r}"')
        if t.count(old_i) == 1:
            t = t.replace(old_i, new_i, 1)
            n += 1
    print(f"=== 队列改 outdir 含 rank：{n}/4 处 ===")
    if n == 4:
        try:
            ast.parse(t)
        except SyntaxError as e:
            print(f"  ❌ 语法错误: {e}")
            return 1
        if a.apply:
            io.open(Q, "w", encoding="utf-8", newline="").write(t)
            print("  ✅ 队列已改（outdir = .../r2, /r8, /r32, /r64）")

    # ── ② 清理错位结果 ──
    print("\n=== 基础目录下的错位结果 ===")
    if MISPLACED.exists():
        files = sorted(MISPLACED.rglob("results.json"))
        for f in files:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            print(f"  {f.relative_to(REPO)}  batch={d.get('batch_size')}")
        if a.apply:
            dst = MISPLACED.with_name("text_only.MISPLACED_no_rank_segment")
            if dst.exists():
                print(f"  ⚠️ {dst.name} 已存在，先删旧的")
                import shutil
                shutil.rmtree(dst)
            MISPLACED.rename(dst)
            print(f"  ✅ 已改名 → {dst.name}（保留证据，不删）")
        else:
            print("  （预演：将改名为 text_only.MISPLACED_no_rank_segment）")
    else:
        print("  （无）")

    # ── ③ 待补 run 清单 ──
    print("\n=== 待补的 COCO run ===")
    todo = []
    for rank in ("2", "8", "32", "64"):
        for seed in ("42", "123", "456", "789", "1011"):
            f = (REPO / "outputs" / "coco_sweep_text_only" / f"r{rank}" / "text_only"
                 / f"seed{seed}" / "results.json")
            if not f.exists():
                todo.append((rank, seed))
                continue
            try:
                d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            except Exception:
                todo.append((rank, seed))
                continue
            if d.get("batch_size") != 128:
                todo.append((rank, seed))
    print(f"  共 {len(todo)} 个")
    from collections import Counter
    for k, v in sorted(Counter(r for r, _ in todo).items()):
        print(f"    r{k:<3} {v} run")
    if a.apply:
        out = REPO / "outputs" / "analysis" / "coco_todo.json"
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps(
            [{"rank": r, "seed": s} for r, s in todo], ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
