# -*- coding: utf-8 -*-
r"""查看收尾批次的 12 个文件里的中文上下文（决定能否安全翻译）（2026-10-14）。

    python tools\_p599_inspect_batch6.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
CJK = re.compile(r"[\u4e00-\u9fff]")

FILES = [
    "outputs/_oe_decision.txt",
    "outputs/analysis/group_analysis.json",
    "tools/audit/clean_bib.py",
    "src/gap_susceptibility.py",
    "tools/_cloud_par16.sh",
    "tools/audit/fix_paperA_round3.py",
    "tools/clip_imagenet1k_ckpt_check.py",
    "tools/clip_tinyimagenet_ckpt_check.py",
    "tools/ap3_fulltext_lint.py",
    "tools/audit_submission_pdfs.py",
    "outputs/tinyimagenet_ckpt_check.json",
    "tools/audit/find_bib_placeholders.py",
]


def main() -> int:
    for rel in FILES:
        p = PC / rel
        if not p.exists():
            print(f"  🔴 缺 {rel}")
            continue
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except UnicodeDecodeError as e:
            print(f"  ── {rel}: **非 UTF-8**（{e}）")
            continue
        n = len(CJK.findall(t))
        print("=" * 96)
        print(f"── {rel}（{n} 中文字符）")
        print("=" * 96)
        for m in re.finditer(r".{0,70}[\u4e00-\u9fff]+.{0,70}", t):
            ln = t[:m.start()].count("\n") + 1
            print(f"  L%-4d {' '.join(m.group(0).split())}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
