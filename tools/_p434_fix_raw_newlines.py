# -*- coding: utf-8 -*-
r"""修 `_p432` 引入的编译错误（2026-10-12）。

## 病因（我的第 17 个错）

`_p432` 的 `BLOCK` 用了 **`r"..."` 原始字符串**，里面写的是 `"…every other run\n"` ——
**原始字符串里 `\n` 不是换行，而是字面的反斜杠+n** → 写进 `.tex` 后 LaTeX 把 `\n` 当成
未定义命令 → **27 个 `! Undefined control sequence`**。

**教训**：**LaTeX 文本里要真换行就不能用 raw string**；或统一用 `"\n"` 拼接。
本项目同类坑已多次（PowerShell here-string、引号嵌套、raw string）。

## 修法

把 `.tex` 里**字面的 `\n`**（反斜杠+n）替换为**真换行**。
**保守**：只替换「非行尾的 `\n` 且其后紧跟可见字符」的情形，并断言替换后 `\n` 序列不再出现。

    python tools\_p434_fix_raw_newlines.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    # 字面的反斜杠+n（不是 LaTeX 的 \\ 后跟 n，也不是真换行）
    n_before = len(re.findall(r"\\n(?=[A-Za-z\$\(])", t))
    print(f"  找到字面 '\\n' 序列 {n_before} 处")
    if n_before == 0:
        print("  ✅ 无需处理")
        return 0
    # 只替换字面的 \n（反斜杠 + n），且后跟可见字符
    t2 = re.sub(r"\\n(?=[A-Za-z\$\(])", "\n", t)
    n_after = len(re.findall(r"\\n(?=[A-Za-z\$\(])", t2))
    print(f"  替换后剩余 {n_after} 处")
    if n_after:
        print("  🔴 仍有残留")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p434")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t2)
    print("  ✅ 已修")
    # 打印修好的段落头部供核对
    i = t2.find("Seed provenance")
    print("  修后逐字（前 300 字符）：")
    print("    " + repr(t2[max(0, i - 60):i + 240]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
