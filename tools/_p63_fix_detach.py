# -*- coding: utf-8 -*-
r"""给 `_cloud_ssh.py` 加**正确的后台脱离**（修 paramiko 阻塞）（2026-10-09）。

## 根因（实测报错）

```
paramiko.buffered_pipe.PipeTimeout → TimeoutError
  在 run(c, "cd ... && nohup python x.py > log 2>&1 & echo started")
```

**`nohup ... &` 不够**：后台进程**仍持有 stdout 的 fd** →
paramiko 的 `stdout.read()` **等到通道关闭** → 阻塞。

## 修法

用 **`setsid`** 且把**三个流都重定向**（含 stdin）：

```sh
setsid nohup CMD < /dev/null > LOG 2>&1 & disown; echo started
```

    python tools\_p63_fix_detach.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_cloud_ssh.py"

FUNC = '''

def bg(c, cmd: str, log: str, cwd: str = "/root/autodl-tmp/work") -> None:
    """**正确脱离**地后台运行：`setsid` + 三流重定向 → paramiko 不再阻塞。

    实测教训：只用 `nohup ... &` 时后台进程仍持有 stdout 的 fd，
    `stdout.read()` 会**等到通道关闭**（`PipeTimeout`）。
    """
    full = (f"cd {cwd} && setsid nohup {cmd} < /dev/null > {log} 2>&1 & "
            f"disown; sleep 1; echo started")
    stdin, stdout, stderr = c.exec_command(full, timeout=60)
    try:
        out = stdout.read().decode("utf-8", "replace").strip()
    except Exception:
        out = "(detached)"
    print(f"  {out or '(detached)'}")
'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "def bg(" in t:
        print("  已加，跳过")
        return 0
    anchor = "\ndef main() -> int:"
    if t.count(anchor) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(anchor)}）")
        return 1
    t = t.replace(anchor, FUNC + anchor, 1)
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "def bg(" in t2 and "setsid nohup" in t2
    print("  ✅ 已加 `bg()`：setsid + 三流重定向，彻底脱离 paramiko 通道")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
