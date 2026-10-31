# -*- coding: utf-8 -*-
r"""修执行器两个致命缺陷（2026-10-08 10:02）——**任务名含非法字符导致整个队列崩溃**。

## 实测故障

```
File "tools/_p20_serial_executor.py", line 230, in run_task
    with io.open(tlog, "a", encoding="utf-8") as f:
FileNotFoundError: [Errno 2] No such file or directory: 'A:_α_由梯度预测(trainer基座).log'
```

**两个缺陷**：

| # | 缺陷 | 后果 |
|---|---|---|
| 1 | 任务名 `"A: α 由梯度预测(trainer基座)"` 含 **`:`**（Windows 文件名非法），净化只去掉了**空格和斜杠** | `io.open` 抛 `FileNotFoundError` |
| 2 | **异常逃出 `main()` 的 for 循环** | **整个执行器进程退出** → **队列里 12 个 COCO 任务全被丢弃** |

**这是"一个任务的日志文件名错误，导致整个 36 h 队列停摆"**——与昨夜"三个驱动撞车"同属**架构脆弱**。

## 修法

1. **文件名净化**：只保留 `[A-Za-z0-9._-]` 与 CJK，其余替换为 `_`（并限长 80）；
2. **`main()` 循环包 `try/except`**：任一任务抛异常 → **记日志、标 fail、继续下一个**（**绝不中断队列**）；
3. **`run_task` 内的文件打开也包保护**（双保险）。

    python tools\_p26_fix_executor_crash.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p20_serial_executor.py"

OLD_LOG = '''    tlog = logdir / (name.replace(" ", "_").replace("/", "-").replace("=", "") + ".log")'''
NEW_LOG = '''    # **文件名净化**：任务名可能含 Windows 非法字符（实测 `:` 直接抛 FileNotFoundError，
    # 且异常逃出 main() 的循环会把整个队列带走）。只保留安全字符 + CJK，限长 80。
    import re as _re
    safe = _re.sub(r"[^0-9A-Za-z._\\-\\u4e00-\\u9fff]+", "_", name).strip("_")[:80] or "task"
    tlog = logdir / (safe + ".log")'''

OLD_MAIN = '''    stats = {}
    for name, cmd, done, timeout in build_queue():
        st = run_task(name, cmd, done, timeout, logdir)
        stats[name] = st
        if st == "blocked":
            log("   因 GPU 被占而停止本轮（避免争抢）")
            break'''
NEW_MAIN = '''    stats = {}
    for name, cmd, done, timeout in build_queue():
        # **任何单任务异常都不得杀死队列**（实测：一个非法日志文件名曾让整个 36 h 队列停摆）
        try:
            st = run_task(name, cmd, done, timeout, logdir)
        except Exception as e:
            st = "crashed"
            log(f"❌ {name} 抛异常（已捕获，队列继续）: {type(e).__name__}: {str(e)[:160]}")
        stats[name] = st
        if st == "blocked":
            log("   因 GPU 被占而停止本轮（避免争抢）")
            break'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "safe = _re.sub" in t and "已捕获，队列继续" in t:
        print("  已修，跳过")
        return 0
    for old, tag in ((OLD_LOG, "日志文件名净化"), (OLD_MAIN, "main 循环异常保护")):
        if t.count(old) != 1:
            print(f"  ❌ {tag} 未唯一命中（{t.count(old)}）")
            return 1
    t = t.replace(OLD_LOG, NEW_LOG, 1).replace(OLD_MAIN, NEW_MAIN, 1)
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "safe = _re.sub" in t2 and "已捕获，队列继续" in t2
    print("  ✅ 两处已修：文件名净化 + 单任务异常不中断队列")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
