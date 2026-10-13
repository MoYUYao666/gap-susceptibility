# -*- coding: utf-8 -*-
r"""补丁：让统计审核脚本对 `mean=None` 不崩，并打印诊断（2026-10-11）。

    python tools\_p180_patch_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_audit_statistics.py"

OLD = '''        print(f"  {'✅' if ok else '🔴'} {ds:<10} {arm:<12} n={n} 论文 {pv:+.4f} ｜ "
              f"重算 {mean:+.4f}" + (f" ± {sd:.4f}" if sd else ""))'''
NEW = '''        disp = f"{mean:+.4f}" if mean is not None else "无数据"
        print(f"  {'✅' if ok else '🔴'} {ds:<10} {arm:<12} n={n} 论文 {pv:+.4f} ｜ "
              f"重算 {disp}" + (f" ± {sd:.4f}" if sd else ""))
        if mean is None:
            _g = load_group(root)
            print(f"      ↳ 诊断: root={root} rank={rank} 现有键="
                  f"{sorted(_g.keys())[:8]}")'''

OLD2 = '''        print(f"  {'✅' if ok else '🔴'} {rank:<5} n={n} 论文 {pv:+.4f} ｜ 重算 {mean:+.4f}"
              + (f" ± {sd:.4f}" if sd else ""))'''
NEW2 = '''        _disp = f"{mean:+.4f}" if mean is not None else "无数据"
        print(f"  {'✅' if ok else '🔴'} {rank:<5} n={n} 论文 {pv:+.4f} ｜ 重算 {_disp}"
              + (f" ± {sd:.4f}" if sd else ""))'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n1, n2 = t.count(OLD), t.count(OLD2)
    print(f"=== 锚点：① {n1} ｜ ② {n2} ===")
    if n1 != 1 or n2 != 1:
        return 1
    t = t.replace(OLD, NEW, 1).replace(OLD2, NEW2, 1)
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("  ✅ 已打补丁")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
