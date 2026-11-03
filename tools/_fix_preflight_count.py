# -*- coding: utf-8 -*-
r"""修正 `tools/_audit_paperA_preflight.py` 第⑥项的计数 bug，并核实真实图/表数量。

## Bug

原写法：`len(re.findall(r"\\label\{(fig|tab):", t))` —— **把图和表的 label 一起数了**，
于是图 12 个环境对 20 个 label、表 7 个对 20 个，**报出两个假问题**。

正确做法：**分别**数 `\label{fig:` 与 `\label{tab:`，并与各自的 `\begin{figure|table}` 比较。

    python tools\_fix_preflight_count.py [--apply]
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
F = REPO / "tools" / "_audit_paperA_preflight.py"

OLD = '''    print("\\n=== ⑥ 编号连续性 ===")
    for env, name in (("figure", "图"), ("table", "表")):
        n = len(re.findall(rf"\\\\begin\\{{{env}\\}}", t))
        lab = len(re.findall(rf"\\\\label\\{{(fig|tab):", t))
        print(f"  {name}: \\\\begin\\{{{env}\\}} {n} 个 ｜ 带 label {lab} 个")
        if n != lab:
            problems.append(f"{name}数量与带 label 数不符（{n} vs {lab}）")'''

NEW = '''    print("\\n=== ⑥ 编号连续性（图/表分别计数）===")
    # 修正：原写法 (fig|tab) 把两类一起数，导致 12 vs 20、7 vs 20 的假问题
    for env, pre, name in (("figure", "fig", "图"), ("table", "tab", "表")):
        n = len(re.findall(r"\\\\begin\\{" + env + r"\\}", t))
        lab = len(re.findall(r"\\\\label\\{" + pre + r":", t))
        status = "✅ 一致" if n == lab else f"⚠ 不一致（{n} vs {lab}）"
        print(f"  {name}: \\\\begin\\{{{env}\\}} {n} 个 ｜ \\\\label\\{{{pre}:*}} {lab} 个 ｜ {status}")
        if n != lab:
            problems.append(f"{name}的 \\\\begin 与 \\\\label 数不符（{n} vs {lab}）")'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "图/表分别计数" in t:
        print("  已修正，跳过")
    else:
        c = t.count(OLD)
        print(f"  旧代码命中: {c}")
        if c == 1 and apply:
            io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
            print("  ✅ 已修正计数逻辑")
        elif c != 1:
            print("  ⚠ 未唯一命中，请人工核对")

    # 独立核实真实数量
    body = "\n".join(io.open(f, encoding="utf-8", errors="ignore").read()
                     for f in sorted((PA / "sections").glob("*.tex")))
    print("\n=== 真实计数（独立核实）===")
    for env, pre, name in (("figure", "fig", "图"), ("table", "tab", "表")):
        n = len(re.findall(r"\\begin\{" + env + r"\}", body))
        lab = len(re.findall(r"\\label\{" + pre + r":", body))
        print(f"  {name}: \\begin{{{env}}} = {n} ｜ \\label{{{pre}:*}} = {lab} ｜ "
              + ("✅ 一致" if n == lab else f"⚠ 不一致"))
    r = subprocess.run(["pdftotext", str(PA / "main_nc.pdf"), "-"], capture_output=True)
    pt = r.stdout.decode("utf-8", "ignore")
    figs = sorted({int(x) for x in re.findall(r"Figure\s+(\d+)", pt)})
    tabs = sorted({int(x) for x in re.findall(r"Table\s+(\d+)", pt)})
    print(f"\n  PDF 中 Figure 编号: {figs}  → 最大 {max(figs) if figs else 0}")
    print(f"  PDF 中 Table 编号:  {tabs}  → 最大 {max(tabs) if tabs else 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
