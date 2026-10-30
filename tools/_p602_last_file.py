# -*- coding: utf-8 -*-
r"""译完最后一个文件（`ap3_a1_revision_verify.py` 的 19 个中文检查标签）（2026-10-14）。

## 判据

该文件的 19 个 `checks` 字典键是**仅用于 `print` 的检查项标签**：
`bad = [k for k, v in checks.items() if not v]` 只用值不用键，键不参与任何查找
⇒ **翻译安全**（不构成数据契约）。

    python tools\_p602_last_file.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "publish_clean" / "tools" / "ap3_a1_revision_verify.py"

PAIRS = [
    ("'F1 表题已更新为 strictly LoRA-only'", "'F1 caption updated to strictly LoRA-only'"),
    ("'F1 epoch10 τ = 0.711'", "'F1 epoch10 tau = 0.711'"),
    ("'F1 epoch10 top-1 = 58.05'", "'F1 epoch10 top-1 = 58.05'"),
    ("'F1 epoch10 val = 2.364'", "'F1 epoch10 val = 2.364'"),
    ("'F1 旧的\"平台化\"叙述已删'", "'F1 old \"plateau\" narrative removed'"),
    ("'F1 新的\"两阶段\"叙述'", "'F1 new \"two-stage\" narrative'"),
    ("'F2 块7 严格 LoRA 数字'", "'F2 block 7 strict-LoRA numbers'"),
    ("'F2 块7 重建轨迹数字'", "'F2 block 7 reconstruction-trajectory numbers'"),
    ("'F2 旧的 0.76/0.73/0.71 已删'", "'F2 old 0.76/0.73/0.71 removed'"),
    ("'F3 τ ≥ 0.930'", "'F3 tau >= 0.930'"),
    ("'F3 orth 变体区间'", "'F3 orth variant interval'"),
    ("'F3 旧的 above 0.93 已删'", "'F3 old \"above 0.93\" removed'"),
    ("'S2 Qwen 负 λ 行'", "'S2 Qwen negative-lambda row'"),
    ("'S2 对称性叙述'", "'S2 symmetry narrative'"),
    ("'S2 multicolumn 宽度已改 7'", "'S2 multicolumn width changed to 7'"),
    ("'S3 折大小披露'", "'S3 fold-size disclosure'"),
    ("'S4 高斯界边界'", "'S4 Gaussian-bound edge case'"),
    ("'无重复的 tabular 结束'", "'no duplicated tabular end'"),
    ("'花括号平衡'", "'brace balance'"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(P, encoding="utf-8", errors="replace").read()
    applied = 0
    miss = []
    for old, new in PAIRS:
        c = t.count(old)
        if c == 1:
            t = t.replace(old, new)
            applied += 1
        else:
            miss.append((old, c))
    print(f"  替换 {applied}/{len(PAIRS)}")
    for old, c in miss:
        print(f"     ⚠️ 命中 {c}：{old}")
    import re
    left = len(re.findall(r"[\u4e00-\u9fff]", t))
    print(f"  残留中文 {left} 个")
    if not a.apply:
        print("  （预演）")
        return 0
    bak = P.with_suffix(".py.bak_p602")
    if not bak.exists():
        shutil.copy2(P, bak)
    io.open(P, "w", encoding="utf-8", newline="").write(t)
    import ast
    ast.parse(io.open(P, encoding="utf-8").read())
    print(f"  ✅ 已写并 ast.parse 通过 ｜ 残留中文 {len(re.findall(r'[一-鿿]', io.open(P, encoding='utf-8').read()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
