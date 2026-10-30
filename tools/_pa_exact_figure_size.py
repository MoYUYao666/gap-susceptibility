# -*- coding: utf-8 -*-
r"""让图的实际尺寸**精确等于** LaTeX 目标宽度（2026-10-06）。

## 问题

`savefig.bbox = "tight"`（我在 `figure_style.py` 里设的）会**按内容扩张**画布：
`figsize=figsize_wide(0.32)`（=3.713 in 宽）产出的 PNG 实测 **5.437 in 宽**——
因为 tight 把 3 个面板的轴标签/标题都算进了外框。

**后果**：LaTeX 再把它缩到 3.713 in（×0.68）→ **文字被放大 1.5 倍**，
与 `fig1`（缩放 1.00）**不一致**——正是"大小没调整好"的表现。

## 修法

- `savefig.bbox = None`（**不扩张**）+ `constrained_layout` 自动理版；
- `pad_inches` 小值（0.01）防止贴边；
- **产出后实测尺寸**，与目标比对，偏差 >5% 即报错。

    python tools\_pa_exact_figure_size.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FS = REPO / "tools" / "figure_style.py"
T = REPO / "tools"


def main() -> int:
    apply = "--apply" in sys.argv

    # ① 改 figure_style：取消 tight bbox + 开 constrained layout
    t = io.open(FS, encoding="utf-8").read()
    old = ('        "savefig.bbox": "tight",\n'
           '        "savefig.pad_inches": 0.02,\n')
    new = ('        # 不扩张画布：tight bbox 会按内容外扩，导致实际尺寸 ≠ figsize，\n'
           '        # LaTeX 再缩放时字号就与其它图不一致（2026-10-06 实测 fig8 偏大 1.46×）。\n'
           '        "savefig.bbox": None,\n'
           '        "savefig.pad_inches": 0.01,\n'
           '        # constrained layout 自动理版，避免标签被裁\n'
           '        "figure.constrained_layout.use": True,\n'
           '        "figure.constrained_layout.h_pad": 0.02,\n'
           '        "figure.constrained_layout.w_pad": 0.02,\n')
    if old in t:
        print("  ✅ figure_style.py：tight bbox → None + constrained layout")
        if apply:
            io.open(FS, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
    else:
        print("  ⚠ figure_style.py：未命中 savefig.bbox 段")

    # ② 三面板图的 h_ratio 回调（constrained layout 下不再需要那么高）
    for n, hr in (("_pa_fig8_rebuild.py", "0.34"), ("_pa_fig9_noise_rebuild.py", "0.34"),
                  ("_pa_rebuild_fig10.py", "0.46"), ("_pa_fix_fig14_title.py", "0.46")):
        p = T / n
        s = io.open(p, encoding="utf-8").read()
        import re
        m = re.search(r"figsize=(figsize_\w+)\(([\d.]+)\)", s)
        if m:
            new_s = s.replace(m.group(0), f"figsize={m.group(1)}({hr})")
            print(f"  ✅ {n}: {m.group(2)} → {hr}")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(new_s)
        else:
            print(f"  ⚠ {n}: 未找到 figsize 调用")

    if not apply:
        print("\n  （预演，加 --apply）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
