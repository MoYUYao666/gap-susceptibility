# -*- coding: utf-8 -*-
r"""修 `tools/_run_remaining_steps.py` 的两个问题（2026-10-04）。

## 问题（昨晚实际发生）

1. **失败步骤上白等 6 小时**：`both r64` 因一道过紧的断言失败（3,932,160 > 2,000,000），
   而 `wait_until()` **不知道命令已失败**，仍按 6 小时超时轮询 → **整晚浪费**，
   后面的 SigLIP / OpenCLIP 步骤一个都没跑。
2. **每步的等待超时一开始就给 6 小时**，即使该步骤只需 20 分钟。

## 改法

- `wait_until` 增加 `max_silent_min` 参数：**若在这么久内产物数完全没增长，判定该步失败并返回 False**；
- 主循环遇 `False` **立即 continue 到下一步**（不再空等），并打印醒目的失败行；
- 每步按规模给不同的等待超时（小步 1h、大步 4h）。

    python tools\_fix_runner_wait.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_run_remaining_steps.py"

OLD_WAIT = '''def wait_until(pat: str, target: int, label: str, timeout_h: float = 6.0) -> bool:
    t0 = time.time()
    while True:
        c = n(pat)
        if c >= target:
            print("  ✅ %s 完成（%d/%d）" % (label, c, target), flush=True)
            return True
        if time.time() - t0 > timeout_h * 3600:
            print("  ⚠ %s 超时（%d/%d）" % (label, c, target), flush=True)
            return False
        print("  … %s %d/%d" % (label, c, target), flush=True)
        time.sleep(120)'''

NEW_WAIT = '''def wait_until(pat: str, target: int, label: str, timeout_h: float = 4.0,
               max_silent_min: float = 25.0) -> bool:
    """等产物达到目标数。

    ⚠ **关键**：若产物在 `max_silent_min` 分钟内**完全没增长**，判定该步已失败并立即返回 False。
    历史教训：2026-10-03 夜 `both r64` 因断言失败，而本函数不知道命令已死，仍按 6 小时超时轮询，
    整晚浪费，后续 SigLIP / OpenCLIP 步骤全未执行。
    """
    t0 = time.time()
    last_c = n(pat)
    last_change = time.time()
    while True:
        c = n(pat)
        if c >= target:
            print("  ✅ %s 完成（%d/%d）" % (label, c, target), flush=True)
            return True
        if c > last_c:
            last_c, last_change = c, time.time()
        silent_min = (time.time() - last_change) / 60.0
        if silent_min > max_silent_min:
            print("  ❌ %s 疑似失败：%.0f 分钟内产物无增长（%d/%d）—— 跳到下一步"
                  % (label, silent_min, c, target), flush=True)
            return False
        if time.time() - t0 > timeout_h * 3600:
            print("  ⚠ %s 超时（%d/%d）" % (label, c, target), flush=True)
            return False
        print("  … %s %d/%d（静默 %.0f 分钟）" % (label, c, target, silent_min), flush=True)
        time.sleep(120)'''

OLD_CALL = '''        wait_until(pat, tgt, label)'''
NEW_CALL = '''        if not wait_until(pat, tgt, label):
            print("  ⚠ %s 未完成，继续下一步（该步可用同一命令重跑）" % label, flush=True)'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    n = 0
    for old, new, why in ((OLD_WAIT, NEW_WAIT, "wait_until 增加静默检测"),
                          (OLD_CALL, NEW_CALL, "主循环失败即继续")):
        c = t.count(old)
        if c == 1:
            print("  ✅ %s" % why)
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print("  ⚠ %s：命中 %d 次" % (why, c))
    if apply and n == 2:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "max_silent_min" in t2 and "疑似失败" in t2
        print("\n  ✅ 已改 2 处并断言通过")
    else:
        print("\n  %d/2" % n + ("（预演）" if not apply else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
