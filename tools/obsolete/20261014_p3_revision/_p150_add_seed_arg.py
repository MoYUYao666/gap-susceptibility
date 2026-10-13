# -*- coding: utf-8 -*-
r"""给 `tools/_p47_qwen_train.py` 加 `--seed` 支持（2026-10-10）。

## 为什么

脚本把 seed **硬编码**为 42：`torch.manual_seed(42)` 与输出名 `{arm}_seed42.json`。
**要补 seed 必须先让它可参数化**，否则新 run 会覆盖旧的 42 号结果。

## 改动（4 处，均可断言）

| # | 位置 | 改法 |
|---|---|---|
| 1 | 参数解析 | 加 `seed = int(argv[...+1]) if "--seed" in argv else 42` |
| 2 | 训练前 | `torch.manual_seed(seed)` |
| 3 | 输出名 | `f"{arm}_seed{seed}.json"` |
| 4 | 写入记录 | 加 `"seed": seed` 字段 |

    python tools\_p150_add_seed_arg.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p47_qwen_train.py"

EDITS = [
    # (old, new, 说明)
    ('    use_4bit = "--4bit" in argv\n',
     '    use_4bit = "--4bit" in argv\n'
     '    seed = (int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 42)\n',
     "加 --seed 参数"),
    ('        torch.manual_seed(42)\n',
     '        torch.manual_seed(seed)\n',
     "torch seed 用参数值"),
    ('        p = OUT / f"{arm}_seed42.json"\n',
     '        p = OUT / f"{arm}_seed{seed}.json"\n',
     "输出名用参数 seed"),
    ('        rec = {"arm": arm, "n_trainable": n_tr, "n_vis": n_vis, "n_lang": n_lang,\n',
     '        rec = {"arm": arm, "seed": seed, "n_trainable": n_tr, "n_vis": n_vis,\n'
     '               "n_lang": n_lang,\n',
     "记录 seed 字段"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()

    print(f"=== {F.name}（{len(t.splitlines())} 行）===")
    ok = 0
    for old, new, tag in EDITS:
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠'} 命中 {n} × {tag}")
        if n == 1:
            t = t.replace(old, new, 1)
            ok += 1
    print(f"  → {ok}/{len(EDITS)} 处命中")

    if ok != len(EDITS):
        print("  ❌ 未全部命中，不写入")
        return 1
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1

    if not a.apply:
        print("\n  （预演）")
        return 0
    bak = F.with_suffix(".py.bak_noseed")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(
            io.open(F, encoding="utf-8").read())
        print(f"  ✅ 备份 {bak.name}")
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in ("--seed", "torch.manual_seed(seed)", "_seed{seed}.json", '"seed": seed'):
        assert k in t2, f"断言失败：缺 {k}"
    print("  ✅ 已加 --seed 支持（4 处）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
