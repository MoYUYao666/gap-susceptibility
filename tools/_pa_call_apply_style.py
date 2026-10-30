# -*- coding: utf-8 -*-
r"""给漏掉的脚本补上 `apply_style()` 调用（2026-10-06）。

## 问题

`apply_style()`（设 Times New Roman + STIX + 统一字号）在这 4 个脚本里**从未被调用**——
先前几轮重写 import 块时把它删掉了：
`_pa_rebuild_fig12.py`、`_pa_rebuild_fig10.py`、`_pa_fix_fig14_title.py`、`_fix_figure_overflow.py`

**后果**：这些图仍用 matplotlib 默认 **DejaVu Sans**（`pdffonts` 实测），
即"图片文字不是 Times New Roman"——**操作者指出的正是这一点**。

## 修法

在这 4 个脚本里 `matplotlib.use("Agg")` 之后插入 `apply_style()`，并**实测字体嵌入**验证。

    python tools\_pa_call_apply_style.py [--apply]
"""
from __future__ import annotations

import ast
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
T = REPO / "tools"

FILES = ["_pa_rebuild_fig12.py", "_pa_rebuild_fig10.py",
         "_pa_fix_fig14_title.py", "_fix_figure_overflow.py"]

ANCHOR = 'matplotlib.use("Agg")\n'
INSERT = 'matplotlib.use("Agg")\n    apply_style()                      # Times New Roman + STIX + 统一字号\n'


def main() -> int:
    apply = "--apply" in sys.argv
    for name in FILES:
        p = T / name
        s = io.open(p, encoding="utf-8").read()
        if "apply_style()" in s:
            print(f"  · {name}: 已有调用")
            continue
        if ANCHOR not in s:
            print(f"  ⚠ {name}: 未找到 matplotlib.use(\"Agg\") 锚点")
            continue
        s2 = s.replace(ANCHOR, INSERT, 1)
        if apply:
            try:
                ast.parse(s2)
            except SyntaxError as e:
                print(f"  ❌ {name}: 语法错误（{e}）")
                continue
            io.open(p, "w", encoding="utf-8", newline="").write(s2)
        print(f"  ✅ {name}: 已插入 apply_style()")

    if not apply:
        print("\n  （预演，加 --apply）")
        return 0

    # 重绘这 4 个脚本并实测字体
    print("\n  === 重绘并实测字体 ===")
    import glob
    for name in FILES:
        r = subprocess.run([sys.executable, str(T / name), "--apply"],
                           capture_output=True, cwd=REPO, text=True)
        err = next((l for l in (r.stderr or "").splitlines() if "Error" in l), "")
        if err:
            print(f"    {name:<34} ❌ {err.strip()[:70]}")
            continue
        print(f"    {name:<34} ✅ 重绘完成")

    print("\n  === pdffonts 实测（应含 Times/Nimbus/STIX，不含 DejaVuSans）===")
    for f in ["fig12_zeroshot_more", "fig10_layered_ft", "fig14_adapter_layered",
              "fig4_effective_rank", "fig1"]:
        pdf = REPO / "paper合" / "figures" / f"{f}.pdf"
        if not pdf.exists():
            continue
        r = subprocess.run(["pdffonts", str(pdf)], capture_output=True)
        txt = r.stdout.decode("utf-8", "ignore")
        fonts = sorted({l.split()[0].split("+")[-1] for l in txt.splitlines()[2:] if l.strip()})
        bad = [x for x in fonts if "DejaVu" in x]
        print(f"    {f:<26} {fonts}  {'❌ 仍含 DejaVu' if bad else '✅'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
