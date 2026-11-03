# -*- coding: utf-8 -*-
r"""处理收尾批次的自处理文件（12 个）（2026-10-14）。

## 逐项判断

| 文件 | 中文位置 | 处置 |
|---|---|---|
| `outputs/_oe_decision.txt` | `2026年9月18日 星期五 中国标准时间15:54:45` | 日期的本地化格式 ⇒ 译（同义：`Friday, 18 September 2026, 15:54:45 CST`） |
| `outputs/analysis/group_analysis.json` | **3 个 JSON 键** `RQ1: Rank 影响` 等 | **译**（在 `publish_clean` 的代码里 grep 不到这些键 ⇒ 非契约；仍是"全英文"目标） |
| `tools/audit/clean_bib.py` | `print('未引用条目:', ...)` | 控制台消息 ⇒ 译 |
| `src/gap_susceptibility.py` | 模块 docstring | 译 |
| `tools/_cloud_par16.sh` | `# 小文件先取（快）` | 注释 ⇒ 译 |
| `tools/audit/fix_paperA_round3.py` | **`paper合/...` 文件路径** | **不译**（路径必须逐字节一致） |
| `tools/clip_imagenet1k_ckpt_check.py` | **3 个 dict 键** `'frozen (论文 60.72)'` | **译**（仅显示标签；grep 无外部引用） |
| `tools/clip_tinyimagenet_ckpt_check.py` | 同上 | **译** |
| `tools/ap3_fulltext_lint.py` | 正则里的 `待补\|待填` | **保留**（占位符检测器的功能数据）+ 补英文标记 |
| `tools/audit_submission_pdfs.py` | 禁止串 `'公开仓库'` | **保留**（审计的匹配模式） |
| `outputs/tinyimagenet_ckpt_check.json` | 1 字符 | 查后处理 |
| `tools/audit/find_bib_placeholders.py` | 1 字符 | 查后处理 |

    python tools\_p600_self_translate_batch6.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"

EDITS = [
    ("outputs/_oe_decision.txt",
     "Date: 2026年9⽉18⽇ 星期五 中国标准时间15:54:45",
     "Date: Friday, 18 September 2026, 15:54:45 CST"),
    ("outputs/analysis/group_analysis.json",
     '"RQ1: Rank 影响": [', '"RQ1: rank effect": ['),
    ("outputs/analysis/group_analysis.json",
     '"RQ2: 位置影响": [', '"RQ2: position effect": ['),
    ("outputs/analysis/group_analysis.json",
     '"RQ3: 缺失模态": [', '"RQ3: missing modality": ['),
    ("tools/audit/clean_bib.py",
     "print('未引用条目:', unused if unused else '无')",
     "print('Unused entries:', unused if unused else 'none')"),
    ("tools/audit/clean_bib.py",
     "print('bib 条目:', len(keys2), '| 删除:', len(unused))",
     "print('bib entries:', len(keys2), '| removed:', len(unused))"),
    ("src/gap_susceptibility.py",
     "Gap Susceptibility — Γ_m 与 β 的计算模块",
     "Gap Susceptibility — computation module for Γ_m and β"),
    ("tools/_cloud_par16.sh",
     "# 小文件先取（快）",
     "# Fetch small files first (faster)"),
    ("tools/clip_imagenet1k_ckpt_check.py",
     "'frozen (论文 60.72)'", "'frozen (paper 60.72)'"),
    ("tools/clip_imagenet1k_ckpt_check.py",
     "'text_only_r8 (论文 59.06)'", "'text_only_r8 (paper 59.06)'"),
    ("tools/clip_imagenet1k_ckpt_check.py",
     "'both_r8 (论文 56.14)'", "'both_r8 (paper 56.14)'"),
    ("tools/clip_tinyimagenet_ckpt_check.py",
     "'frozen (论文 60.72)'", "'frozen (paper 60.72)'"),
    ("tools/clip_tinyimagenet_ckpt_check.py",
     "'text_only_r8 (论文 59.06)'", "'text_only_r8 (paper 59.06)'"),
    ("tools/clip_tinyimagenet_ckpt_check.py",
     "'both_r8 (论文 56.14)'", "'both_r8 (paper 56.14)'"),
]

# 保留项（记录理由）
KEEP = {
    "tools/audit/fix_paperA_round3.py": "Chinese inside file paths (paper合/...) — must stay byte-identical",
    "tools/ap3_fulltext_lint.py": "CJK inside the placeholder-detection regex — functional data",
    "tools/audit_submission_pdfs.py": "CJK inside the forbidden-string list used to audit built PDFs — functional data",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    applied = 0
    for rel, old, new in EDITS:
        p = PC / rel
        if not p.exists():
            print(f"  🔴 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        c = t.count(old)
        print(f"  {rel:<52} 命中 {c}")
        if c and a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p600")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            applied += c
    print()
    print(f"  {'✅ 已应用' if a.apply else '（预演）'} {applied} 处替换")
    print()
    print("  保留（功能数据，有意不译）：")
    for k, why in KEEP.items():
        print(f"     {k}\n        {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
