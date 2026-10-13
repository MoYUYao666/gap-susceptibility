# -*- coding: utf-8 -*-
r"""给 `tools/_p47_qwen_train.py` 加 `--outdir`（2026-10-10）。

## 为什么必须加

脚本硬编码 `OUT = REPO/"outputs"/"vlm_strictfreeze"` → **新 seed 的 run 会写进同一目录**
（`{arm}_seed123.json` 等，虽不覆盖 `seed42` 文件，但与归档混在一起、且 `summary.json` 会被覆盖）。

**补 seed 需要独立目录**：
- `outputs/vlm_seeds/`（3 个新 seed）
- `outputs/vlm_seeds_repro/`（seed 42 复跑校验）

## 改动（3 处）

| # | 位置 | 改法 |
|---|---|---|
| 1 | 参数解析 | 加 `outdir`（默认取原 `OUT`） |
| 2 | `OUT.mkdir` 之前 | 用参数覆盖 `OUT` |
| 3 | 写入路径 | 已随 `OUT` 变（`{arm}_seed{seed}.json` 与 `summary.json`） |

    python tools\_p151_add_outdir.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p47_qwen_train.py"

OLD = ('    seed = (int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 42)\n')
NEW = OLD + (
    '    # 独立输出目录（补 seed 时不与归档混写）\n'
    '    if "--outdir" in argv:\n'
    '        OUT = REPO / argv[argv.index("--outdir") + 1]\n'
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"=== 锚点命中 {n} 处 ===")
    if n != 1:
        print("  ❌ 未唯一命中")
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
    bak = F.with_suffix(".py.bak_noseed")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(
            io.open(F, encoding="utf-8").read())
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    assert '"--outdir"' in t3 and "OUT = REPO / argv" in t3
    print("  ✅ 已加 --outdir")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
