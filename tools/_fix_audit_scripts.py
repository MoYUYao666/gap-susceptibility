# -*- coding: utf-8 -*-
r"""修两个审计脚本的缺陷（2026-10-05 投稿前审核中发现）。

## 缺陷 A：`_audit_paperA_preflight.py` 第⑥项漏数 `longtable`

`supplement.tex` 用 `\begin{longtable}` 而非 `\begin{table}` → 该脚本数到 7 个 table 对 8 个 label，
**误报"数量不符"**。正确应为 **7 table + 1 longtable = 8**，与 8 个 label 一致 ✅。

## 缺陷 B：`_pa_final_check_nc.py` 的引用计数按数字制

它用 `\[\d+\]` 统计"PDF 中出现的编号引用标记"，**输出 "0 处"** ——
而本文用 `elsarticle-harv`（**作者-年份制**），实际有 **51 处** `X et al. (YYYY)`。
**在 44 条文献的稿子上报 0 处引用是误导性的**，必须改成两种制式都认。

    python tools\_fix_audit_scripts.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PRE = REPO / "tools" / "_audit_paperA_preflight.py"
FIN = REPO / "tools" / "_pa_final_check_nc.py"


def main() -> int:
    apply = "--apply" in sys.argv

    # ── 修 A：preflight 的表/图计数含 longtable
    a = io.open(PRE, encoding="utf-8").read()
    old_a = 'for env, pre, name in (("figure", "fig", "图"), ("table", "tab", "表")):\n        n = len(re.findall(rf"\\\\begin\\{{{env}\\}}", t))'
    new_a = ('# 注意：表也可能是 longtable（supplement.tex 用了它），只数 table 会漏\n'
             '    envs = {"figure": r"\\\\begin\\{figure\\}", "table": r"\\\\begin\\{(?:long)?table\\*?\\}"}\n'
             '    for env, pre, name in (("figure", "fig", "图"), ("table", "tab", "表")):\n'
             '        n = len(re.findall(envs[env], t))')
    if old_a in a:
        print("  ✅ preflight：命中表/图计数行")
        if apply:
            io.open(PRE, "w", encoding="utf-8", newline="").write(a.replace(old_a, new_a, 1))
    else:
        print("  ⚠ preflight：未命中（转义差异），改用手工替换")

    # ── 修 B：final_check 的引用计数认两种制式
    b = io.open(FIN, encoding="utf-8").read()
    import re as _re
    m = _re.search(r'[^\n]*\[\^?\\d\\\+\][^\n]*', b)
    old_b = None
    for cand in _re.finditer(r".*numbered citation.*|.*\\\[\\\\d\+\\\].*|.*\[\d\+\].*", b):
        old_b = cand.group(0)
        break
    if old_b:
        print(f"  ✅ final_check：命中引用计数行 → {old_b.strip()[:70]}")
    else:
        print("  ⚠ final_check：未定位到引用计数行，打印相关行：")
        for i, l in enumerate(b.splitlines(), 1):
            if "citation" in l.lower() or "引用标记" in l:
                print(f"     L{i}: {l.strip()[:100]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
