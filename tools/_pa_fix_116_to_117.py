# -*- coding: utf-8 -*-
r"""Paper A 整改 · 第 1 项：实验计数 116 → 117。

## 依据（实测，非照抄 P1）

解析 `paper合/sections/supplement.tex` 的 `tab:full_experiments`：
- 13 个目录节逐节加总 = **117**
- 表内 `\textbf{Total}` 行声明 = **117**
- 正文 6 处写 **116**（无来源）

→ 两处独立一致支持 117，故正文 116 为笔误。

**⚠️ 为什么不是"照抄 P1 的 116→117"**：P1 与 Paper A 是不同稿件，计数口径可能不同。
本项的 117 来自 **Paper A 自己的目录表**，与 P1 无关（P1 的 117 是另一条独立证据）。

## 安全设计

- 只替换 `116` 作为**实验计数**出现的 6 处（全部在已确认的上下文中），不做全局替换；
- 打印每处改动前后全文，便于人工复核；
- 幂等：重复运行不会二次改动。

    python tools\_pa_fix_116_to_117.py            # 预演
    python tools\_pa_fix_116_to_117.py --apply
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = ["conclusion.tex", "empirical.tex", "introduction.tex", "supplement.tex"]

# 已逐处确认：116 均指实验数。用「116」+ 邻近词定位，避免误伤（如页码、引用编号）
PATTERNS = [
    r"(spite?ning\s+)116\b",
    r"(spanning\s+)116\b",
    r"\(116 experiments\)",
    r"(all\s+)116( experiments)",
    r"116 experiments",
]


def main() -> int:
    apply = "--apply" in sys.argv
    total = 0
    for name in FILES:
        p = REPO / "paper合" / "sections" / name
        if not p.exists():
            print(f"  ⚠ 不存在：{name}")
            continue
        t = io.open(p, encoding="utf-8").read()
        if "116" not in t:
            print(f"  — {name}: 无 116")
            continue
        lines = t.splitlines(keepends=True)
        changed = 0
        for i, line in enumerate(lines):
            if "116" not in line:
                continue
            # 只处理含实验计数语境的 116
            if not re.search(r"116\s*(experiments|exp\b)|spanning\s+116|\(116\b|all\s+116", line):
                print(f"  ⚠ {name}:{i+1} 含 116 但语境不符，**跳过**：{line.strip()[:80]}")
                continue
            new = line.replace("116", "117")
            print(f"  ✅ {name}:{i+1}")
            print(f"       旧: {line.strip()[:150]}")
            print(f"       新: {new.strip()[:150]}")
            lines[i] = new
            changed += 1
        if changed and apply:
            io.open(p, "w", encoding="utf-8", newline="").write("".join(lines))
        total += changed
    print(f"\n共 {total} 处{'已改' if apply else '待改'}")
    if apply and total:
        # 断言：相关文件中不再有作为实验计数的 116
        left = 0
        for name in FILES:
            p = REPO / "paper合" / "sections" / name
            if p.exists():
                tt = io.open(p, encoding="utf-8").read()
                left += len(re.findall(r"116\s*(?:experiments|exp\b)|spanning\s+116|\(116\b|all\s+116", tt))
        assert left == 0, f"仍有 {left} 处 116 未改"
        print("✅ 断言通过：实验计数语境下已无 116")
    elif not apply:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
