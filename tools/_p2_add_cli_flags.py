# -*- coding: utf-8 -*-
r"""给 `_p2_alpha_from_gradients.py` 加命令行开关（2026-10-07）。

操作者选 B：先只跑 `both` 臂（α 最非零）以快速得到结论方向。

**开关**：`--arms both` ｜ `--seeds 42,123,456` ｜ `--epochs 10`

**实现要点**：`CONFIGS/SEEDS/EPOCHS` 在 `main()` 内是**局部名**，
故必须在**任何赋值之前**声明 `global`，否则 `SyntaxError:
name 'X' is assigned to before global declaration`。

    python tools\_p2_add_cli_flags.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p2_alpha_from_gradients.py"

OLD = '''    apply = "--apply" in sys.argv
    smoke = "--smoke" in sys.argv
    # 命令行开关：--arms both ｜ --seeds 42,123,456 ｜ --epochs 10
    if "--arms" in sys.argv:
        want = sys.argv[sys.argv.index("--arms") + 1].split(",")
        ALL = {"text_only": dict(apply_to_vision=False, apply_to_text=True),
               "both":      dict(apply_to_vision=True,  apply_to_text=True),
               "vision_only": dict(apply_to_vision=True, apply_to_text=False)}
        CONFIGS = {k: ALL[k] for k in want if k in ALL}
    if "--seeds" in sys.argv:
        SEEDS = [int(x) for x in sys.argv[sys.argv.index("--seeds") + 1].split(",")]
    if "--epochs" in sys.argv:
        EPOCHS = int(sys.argv[sys.argv.index("--epochs") + 1])'''

NEW = '''    apply = "--apply" in sys.argv
    smoke = "--smoke" in sys.argv
    # 配置可在命令行覆盖（操作者选 B：先只跑 both 臂）
    global EPOCHS, SEEDS, CONFIGS, MAX_SAMPLES
    if smoke:
        EPOCHS, SEEDS, MAX_SAMPLES = 1, [42], 128
        CONFIGS = {"text_only": dict(apply_to_vision=False, apply_to_text=True)}
        print("  [SMOKE] 1 臂 × 1 seed × 1 epoch × 128 样本")
    ALL_ARMS = {"text_only": dict(apply_to_vision=False, apply_to_text=True),
                "both":      dict(apply_to_vision=True,  apply_to_text=True),
                "vision_only": dict(apply_to_vision=True, apply_to_text=False)}
    if "--arms" in sys.argv:
        want = sys.argv[sys.argv.index("--arms") + 1].split(",")
        CONFIGS = {k: ALL_ARMS[k] for k in want if k in ALL_ARMS}
    if "--seeds" in sys.argv:
        SEEDS = [int(x) for x in sys.argv[sys.argv.index("--seeds") + 1].split(",")]
    if "--epochs" in sys.argv:
        EPOCHS = int(sys.argv[sys.argv.index("--epochs") + 1])
    if "--maxsamples" in sys.argv:
        MAX_SAMPLES = int(sys.argv[sys.argv.index("--maxsamples") + 1])'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "--arms" in t and "global EPOCHS, SEEDS, CONFIGS, MAX_SAMPLES" in t:
        print("  已加开关，跳过")
        return 0
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        return 1
    print("  ✅ 命中开关块")
    if not apply:
        print("  （预演）")
        return 0
    new = t.replace(OLD, NEW, 1)
    # 移除旧的 smoke 块（已在上面统一处理）
    old_smoke = '''    if smoke:
        global EPOCHS, SEEDS, MAX_SAMPLES, CONFIGS
        EPOCHS, SEEDS, MAX_SAMPLES = 1, [42], 128
        CONFIGS = {"text_only": dict(apply_to_vision=False, apply_to_text=True)}
        print("  [SMOKE] 1 臂 × 1 seed × 1 epoch × 128 样本")
'''
    if old_smoke in new:
        new = new.replace(old_smoke, "", 1)
        print("  ✅ 已移除重复的 smoke 块")
    try:
        ast.parse(new)
    except SyntaxError as e:
        print(f"  ❌ 语法错误：{e}")
        return 1
    io.open(F, "w", encoding="utf-8", newline="").write(new)
    print("  ✅ 已写入并语法通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
