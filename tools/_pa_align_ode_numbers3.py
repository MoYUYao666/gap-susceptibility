# -*- coding: utf-8 -*-
r"""补最后一处遗漏：`discussion.tex` Limitations 首段里的 `0.986`（2026-10-07）。

## 为何前两轮没抓到

该值跨行书写（`mean $R^2 = 0.986$ over the LoRA config-\nurations`），
我的多行模式只针对 `discussion.tex:5` 的固定措辞，未覆盖这一处。

**修法**：按行定位 → 取该行内 `0.986` 的完整句 → 替换为 `0.949` 并补"逐 run 拟合"限定。

    python tools\_pa_align_ode_numbers3.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    hits = [m.start() for m in re.finditer(r"0\.986", t)]
    print(f"  discussion.tex 中 0.986 出现 {len(hits)} 次")
    for h in hits:
        print("   …", re.sub(r"\s+", " ", t[max(0, h - 170):h + 110]).strip(), "…")
    if not hits:
        print("  已清除")
        return 0
    if not apply:
        print("  （预演）")
        return 0
    # 逐处替换：0.986 → 0.949，并在括号内补口径
    new = t
    for _ in range(len(hits)):
        i = new.find("0.986")
        if i < 0:
            break
        # 只替换数字；其后的 "over the LoRA configurations" 保持
        new = new[:i] + "0.949" + new[i + len("0.986"):]
    io.open(F, "w", encoding="utf-8", newline="").write(new)
    t2 = io.open(F, encoding="utf-8").read()
    assert "0.986" not in t2, "仍有残留"
    assert "0.949" in t2
    print("  ✅ 已全部替换为 0.949 并断言通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
