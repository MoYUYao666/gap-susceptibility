# -*- coding: utf-8 -*-
r"""修 `_p173` 的**静默跳过**（第二次踩同一个坑）（2026-10-11）。

## 症状

COCO 修正驱动里，若干 run **7–8 秒就 ✅**（如 `r64/seed42/123/456`），
但**文件仍是旧的 batch=64**（mtime 10-10）→ **它们跳过了**。

## 根因（**与 `_p170` 修的是同一类问题，但我这次忘了用到 COCO**）

`experiments/strict_freeze_control.py` 的跳过逻辑：
```
path = "%s/%s/seed%d/results.json" % (OUT_DIR, tag, seed)
if os.path.exists(path): print("[skip] ... already done"); return
```
**只看 `OUT_DIR/tag/seedN/results.json` 是否存在** → 旧文件在，就跳过（rc=0）。

`_p170` 给 `_p169` 加了 `stash_old()`，但 `_p173`（COCO）**没有**。

## 修法

在 `run_one` 前，若 status 为 `rerun`/`bad`：把旧文件改名为
`results.batch{batch}.bak`（**保留证据**）。

    python tools\_p174_fix_coco_stash.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p173_coco_fix.py"

OLD = '''def run_one(rank: str, seed: str) -> bool:
    outdir = f"{BASE}/r{rank}"'''

NEW = '''def stash_old(rank: str, seed: str) -> str:
    """把旧结果改名备份（脚本按文件存在性跳过，不挪走就不会真跑）。"""
    f = REPO / BASE / f"r{rank}" / "text_only" / f"seed{seed}" / "results.json"
    if not f.exists():
        return "（无旧文件）"
    try:
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        b = d.get("batch_size", "?")
    except Exception:
        b = "?"
    if b == 128:
        return f"（已是 128，不动）"
    bak = f.with_suffix(f".batch{b}.bak")
    if bak.exists():
        bak.unlink()
    f.rename(bak)
    return f"旧文件(batch={b})→{bak.name}"


def run_one(rank: str, seed: str) -> bool:
    outdir = f"{BASE}/r{rank}"'''

OLD2 = '''    for rk, s in todo:
        log(f"▶ r{rk}/seed{s}")
        if run_one(rk, s):'''
NEW2 = '''    for rk, s in todo:
        log(f"▶ r{rk}/seed{s}")
        note = stash_old(rk, s)
        if note != "（已是 128，不动）":
            log(f"   {note}")
        if run_one(rk, s):'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n1, n2 = t.count(OLD), t.count(OLD2)
    print(f"=== 锚点：run_one 定义 {n1} ｜ main 循环 {n2} ===")
    if n1 != 1 or n2 != 1:
        return 1
    t = t.replace(OLD, NEW, 1).replace(OLD2, NEW2, 1)
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".py.bak")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(
            io.open(F, encoding="utf-8").read())
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("  ✅ 已加 stash_old（重跑前把旧 batch-64 文件改名）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
