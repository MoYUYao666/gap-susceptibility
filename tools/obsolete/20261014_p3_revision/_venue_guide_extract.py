# -*- coding: utf-8 -*-
r"""从 5 份 Guide 提取**可比字段**，每字段附出处（2026-10-07）。

候选刊（均属 Southampton Jisc–Elsevier 协议覆盖、免 APC，且无本线拒稿史）：

| 简称 | 刊名 | ISSN | Guide 文件 |
|---|---|---|---|
| **KBS** | Knowledge-Based Systems | 0950-7051 | `_guide_kbs.txt` |
| **ESWA** | Expert Systems with Applications | 0957-4174 | `_guide_eswa.txt` |
| **IVC** | Image and Vision Computing | 0262-8856 | `_guide_ivc.txt` |
| **CVIU** | Computer Vision and Image Understanding | 1077-3142 | `_guide_cviu.txt` |
| **IF** | Information Fusion | 1566-2535 | `_guide_infofusion.txt` |

**方法**：正则定位 + **打印命中位置的上下文**，供人工核对（不凭印象填表）。

    python tools\_venue_guide_extract.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
G = REPO / "期刊指南"

JOURNALS = {
    "KBS":  ("Knowledge-Based Systems", "0950-7051", "_guide_kbs.txt"),
    "ESWA": ("Expert Systems with Applications", "0957-4174", "_guide_eswa.txt"),
    "IVC":  ("Image and Vision Computing", "0262-8856", "_guide_ivc.txt"),
    "CVIU": ("Computer Vision and Image Understanding", "1077-3142", "_guide_cviu.txt"),
    "IF":   ("Information Fusion", "1566-2535", "_guide_infofusion.txt"),
}

# (字段名, 正则列表)  —— 命中即打印上下文，由人工判定
FIELDS = [
    ("Highlights 要求", [r"Highlights", r"85 characters", r"3 to 5"]),
    ("摘要词数",       [r"Abstract", r"\b250 words\b", r"\b200 words\b", r"\b300 words\b"]),
    ("关键词个数",     [r"[Kk]eywords", r"1 to 7", r"maximum of \d+ keywords"]),
    ("篇幅上限",       [r"page limit", r"maximum of \d+ pages", r"up to \d+ pages",
                        r"\d+\s*pages\b", r"no page limit"]),
    ("评审方式",       [r"anonymi[sz]ed", r"single-blind", r"double-blind",
                        r"peer review", r"reviewers? (?:are|remain)"]),
    ("文章类别",       [r"Article types", r"original papers", r"Research article",
                        r"Survey article", r"Review article", r"Full length"]),
    ("数据可用性",     [r"Data availability", r"Data statement", r"research data guideline"]),
    ("生成式 AI 声明", [r"generative AI", r"AI-assisted technologies"]),
    ("开放获取/APC",   [r"open access", r"article publishing charge", r"\bAPC\b"]),
]


def ctx(t: str, pat: str, span: int = 200, max_hits: int = 2) -> list[str]:
    out = []
    for m in list(re.finditer(pat, t, re.I))[:max_hits]:
        seg = re.sub(r"\s+", " ", t[max(0, m.start() - span // 2): m.start() + span]).strip()
        out.append(seg)
    return out


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for key, (name, issn, fn) in JOURNALS.items():
        if only and only.upper() != key:
            continue
        p = G / fn
        if not p.exists():
            print(f"  ⚠ 缺 {fn}")
            continue
        t = io.open(p, encoding="utf-8", errors="ignore").read()
        print("=" * 100)
        print(f"  【{key}】{name}（ISSN {issn}）  字符 {len(t)}")
        print("=" * 100)
        for fname, pats in FIELDS:
            hits = []
            for pat in pats:
                hits += ctx(t, pat, max_hits=1)
            if not hits:
                print(f"\n  ── {fname}：**未提及**")
                continue
            print(f"\n  ── {fname}：")
            for h in hits[:2]:
                print(f"     …{h[:230]}…")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
