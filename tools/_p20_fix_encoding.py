# -*- coding: utf-8 -*-
r"""修 `running_pids` 的编码 bug（2026-10-08 03:05）。

## Bug（**实测**发现，非推测）

```python
subprocess.run([...powershell...], capture_output=True, text=True)
```

Windows 下 `text=True` 用**系统默认编码（GBK）**解码 → PowerShell 输出含**中文路径**时
抛 `UnicodeDecodeError`（实测报错于 position 1368）→ **`running_pids` 返回空** →
**"已有同任务在跑"检测完全失效**（会重复启动任务）。

**这与昨夜驱动 stderr 里刷屏的 `UnicodeDecodeError` 是同一个根因。**

## 修法

1. `encoding="utf-8", errors="replace"` —— 显式指定，**绝不用系统默认编码**；
2. PowerShell 侧先设 `[Console]::OutputEncoding = [Text.Encoding]::UTF8`；
3. 保留 `try/except` 兜底。

**教训**：Windows 上任何 `capture_output=True, text=True` 都必须显式给 `encoding`。

    python tools\_p20_fix_encoding.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p20_serial_executor.py"

OLD = '''    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \\"Name='python.exe'\\" | "
             "ForEach-Object { \\"$($_.ProcessId)|$($_.CommandLine)\\" }"],
            capture_output=True, text=True, timeout=40)
    except Exception:
        return []'''

NEW = '''    ps = ("[Console]::OutputEncoding = [Text.Encoding]::UTF8; "
          "Get-CimInstance Win32_Process -Filter \\"Name='python.exe'\\" | "
          "ForEach-Object { \\"$($_.ProcessId)|$($_.CommandLine)\\" }")
    try:
        # **必须显式 encoding**：Windows 默认 GBK，遇中文路径会 UnicodeDecodeError
        # （实测：该异常会让本函数返回空列表，使"已有同任务在跑"检测静默失效）
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
    except Exception:
        return []'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if 'encoding="utf-8", errors="replace"' in t:
        print("  已修，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ 未唯一命中（{t.count(OLD)}）")
        i = t.find("def running_pids")
        print(repr(t[i:i + 560]))
        return 1
    if not apply:
        print("  （预演）")
        return 0
    t = t.replace(OLD, NEW, 1)
    ast.parse(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert 'encoding="utf-8", errors="replace"' in t2
    print("  ✅ 已修：显式 UTF-8 + errors=replace（GBK 崩溃根因）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
