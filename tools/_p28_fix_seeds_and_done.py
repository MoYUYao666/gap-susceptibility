# -*- coding: utf-8 -*-
r"""修执行器两处 bug（2026-10-08 10:25）。

## Bug 1：COCO 任务 `--seeds` 传成单个字符串

```python
"--seeds", "42 123 456",   # ← argparse 当成一个参数
```
**实测**：`strict_freeze_control.py: error: argument --seeds: invalid int value: '42 123 456'`
→ **12 个 COCO 任务全部 rc=2、30 秒一个、空转**。

**修**：`"--seeds", *"42 123 456".split()` → 三个独立参数。

## Bug 2：实验 A 被误判"已完成"

`_p21_alpha_trainer_based.py` **无条件**写 `alpha_trainer_based.json`（**未对齐时也写**，
内容为 `"aligned": false`）。而执行器的 `task_done()` **只看文件存在** → 把
**100 样本的诊断运行**当成实验 A 完成 → **跳过真正的实验**。

**修**：A 的完成判据改为**读 JSON 要求 `aligned == true` 且 `passed` 字段存在**（真正跑完才有）。

    python tools\_p28_fix_seeds_and_done.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p20_serial_executor.py"

OLD_SEEDS = '''             "--seeds", "42 123 456", "--epochs", "10", "--max-samples", "5000",'''
NEW_SEEDS = '''             "--seeds", *"42 123 456".split(), "--epochs", "10", "--max-samples", "5000",'''

OLD_DONE = '''    if done.name == "alpha_from_gradients.json":'''
NEW_DONE = '''    # 实验 A 的判据：**必须 aligned 且真跑完**——该脚本未对齐时也会写文件
    # （内容 `"aligned": false`），只看存在会把 100 样本的诊断运行当成完成（实测踩过）。
    if done.name == "alpha_trainer_based.json":
        try:
            d = json.loads(io.open(done, encoding="utf-8").read())
        except Exception as e:
            return False, f"读结果失败（{e}）"
        if not d.get("aligned"):
            return False, "未对齐（诊断运行残留）"
        if "passed" not in d:
            return False, "缺 passed 字段（未真正跑完）"
        return True, f"aligned={d.get('aligned')} passed={d.get('passed')}"
    if done.name == "alpha_from_gradients.json":'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "aligned 且真跑完" in t and '"--seeds", *"42 123 456".split()' in t:
        print("  已修，跳过")
        return 0
    for old, tag in ((OLD_SEEDS, "seeds 拆分"), (OLD_DONE, "A 完成判据")):
        if t.count(old) != 1:
            print(f"  ❌ {tag} 未唯一命中（{t.count(old)}）")
            return 1
    if not apply:
        print("  （预演）")
        return 0
    t = t.replace(OLD_SEEDS, NEW_SEEDS, 1).replace(OLD_DONE, NEW_DONE, 1)
    ast.parse(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert '"--seeds", *"42 123 456".split()' in t2 and "aligned 且真跑完" in t2
    print("  ✅ 两处已修：seeds 拆分为独立参数；A 须 aligned=true 才算完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
