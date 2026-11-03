# -*- coding: utf-8 -*-
r"""修 `_p20_serial_executor.py`：GPU 忙时应**阻塞等待**而非跳过任务（2026-10-08 02:56）。

## Bug

原逻辑：

```python
if gpu_used_mb() > 2000:
    time.sleep(120)
    if gpu_used_mb() > 2000:
        return "blocked"      # ← 任务被**丢弃**，不再重试
```

**后果**：执行器启动时若 GPU 被占（例如 α 重跑已在跑），**第一个任务就被永久丢弃**，
且 `main()` 收到 "blocked" 后 `break` → **整个队列停摆**。**这是静默丢数据。**

## 修法

改为**轮询等待直到 GPU 空闲**（上限可配，默认 8 h），超时才放弃。
**等 GPU 是正常的等待，不是失败。**

    python tools\_p20_fix_gpu_wait.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p20_serial_executor.py"

OLD = '''    used = gpu_used_mb()
    if used > 2000:
        log(f"⏳ {name}: GPU 已被占 {used} MB → 等 120 s 重试")
        time.sleep(120)
        if gpu_used_mb() > 2000:
            log(f"⚠ {name}: GPU 仍被占，跳过本轮")
            return "blocked"'''

NEW = '''    # **等 GPU 空闲**（轮询）。注意：等 GPU 是正常等待，**不是失败**——
    # 若此处"跳过任务"，执行器会在启动时把首个任务永久丢弃（静默丢数据）。
    t_wait = time.time()
    waited = False
    while gpu_used_mb() > 2000:
        if not waited:
            log(f"⏳ {name}: GPU 已被占 {gpu_used_mb()} MB → 轮询等待（不跳过）")
            waited = True
        if time.time() - t_wait > GPU_WAIT_MAX:
            log(f"⚠ {name}: 等 GPU 超时（{GPU_WAIT_MAX//3600} h）→ 本轮放弃")
            return "gpu_timeout"
        time.sleep(60)
    if waited:
        log(f"✅ {name}: GPU 已空闲 → 开跑")'''

ANCHOR = "LOG = REPO / \"outputs\" / \"_serial_executor.log\""
ADD = ANCHOR + "\nGPU_WAIT_MAX = 8 * 3600   # 等 GPU 空闲的上限（等 GPU 是正常等待，不是失败）"


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "轮询等待（不跳过）" in t:
        print("  已修，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ 未唯一命中（{t.count(OLD)}）")
        return 1
    if t.count(ANCHOR) != 1:
        print("  ❌ 常量锚点未唯一命中")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    t = t.replace(ANCHOR, ADD, 1).replace(OLD, NEW, 1)
    ast.parse(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "GPU_WAIT_MAX" in t2 and "轮询等待（不跳过）" in t2
    assert 'return "blocked"' not in t2, "旧的 skipped 分支仍在"
    print("  ✅ 已修：GPU 忙时轮询等待（上限 8 h），不再丢弃任务")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
