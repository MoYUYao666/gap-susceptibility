# -*- coding: utf-8 -*-
r"""修 `_p169_batchfix_queue.py`：重跑前**先移走旧文件**（2026-10-10 晚）。

## 根因（实测）

`experiments/strict_freeze_control.py` 有跳过逻辑：

```
[skip] text_only seed=123 already done
```

→ 只要 `OUT_DIR/tag/seed{seed}/results.json` 存在，**脚本直接退出（8 秒，rc=0）**，
**不管配置是否相同**。所以我的"重跑覆盖"根本没发生。

## 修法

在 `run_one` 之前，若判定为 `rerun`：
**把旧文件改名为 `results.json.batch{batch}.bak`**（保留证据，不静默删除）→ 脚本才会真跑。

## 另注

脚本自己的防御检查也说明了同一设计意图：
> `[拒绝运行] --rank 4 但 --out-dir=... 未包含 rank 标识。`
> 原因：跳过逻辑按 OUT_DIR/tag/seed 判断，不同 rank 共用目录会导致后跑的 rank 直接复用前一个的结果。

    python tools\_p170_fix_queue_rerun.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p169_batchfix_queue.py"

OLD = '''def run_one(tag, outdir, model, dataset, rank, extra, arm, seed) -> bool:
    cmd = [PY, "experiments/strict_freeze_control.py",'''

NEW = '''def stash_old(outdir: str, arm: str, seed: str) -> str:
    """把旧结果改名备份（脚本按文件存在性跳过，不挪走就不会真跑）。

    返回说明字符串。
    """
    f = REPO / outdir / arm / f"seed{seed}" / "results.json"
    if not f.exists():
        return "（无旧文件）"
    try:
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        b = d.get("batch_size", "?")
    except Exception:
        b = "?"
    bak = f.with_suffix(f".batch{b}.bak")
    if bak.exists():
        bak.unlink()
    f.rename(bak)
    return f"旧文件(batch={b})→{bak.name}"


def run_one(tag, outdir, model, dataset, rank, extra, arm, seed) -> bool:
    cmd = [PY, "experiments/strict_freeze_control.py",'''

# 在 main 的循环里调用 stash_old
OLD2 = '''        log(f"▶ [{st}] {tag}/r{rank}/{arm}/seed{seed}")
        if run_one(tag, outdir, model, dataset, rank, extra, arm, seed):'''
NEW2 = '''        log(f"▶ [{st}] {tag}/r{rank}/{arm}/seed{seed}")
        if st == "rerun":
            note = stash_old(outdir, arm, seed)
            log(f"   {note}")
        if run_one(tag, outdir, model, dataset, rank, extra, arm, seed):'''


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
    print("  ✅ 已加 stash_old（重跑前把旧文件改名成 .batch64.bak）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
