# -*- coding: utf-8 -*-
"""从定稿 PDF 提取标题/摘要/关键词，供 Editorial Manager 表单粘贴。

实现说明：本机未装 PyMuPDF，故用 `pdftotext -raw` 取文本，并以**摘要首句的固定短语**
锚定摘要起点（比按行号或首个 "Abstract" 字样可靠——标题栏也会出现该词，且标题换行会把
末行残片混进摘要）。

- 修复行末连字符断词（"Gen- eralized" -> "Generalized"）、合并换行
- 统计字数（EM 的摘要上限 300 词）

    python tools/_extract_em_fields.py
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PDF = REPO / "paper3" / "paper_ieee" / "main.pdf"

# 摘要首句的稳定短语（用于精确定位摘要起点）
ANCHOR = "We show that optimal PEFT rank allocation"


def clean(s: str) -> str:
    s = s.replace("\u00ad", "")
    s = re.sub(r"-\s*\n\s*", "", s)
    s = re.sub(r"\s*\n\s*", " ", s)
    return re.sub(r"\s{2,}", " ", s).strip()

def main() -> int:
    raw = subprocess.run(["pdftotext", "-raw", str(PDF), "-"], capture_output=True).stdout.decode("utf-8", "ignore")
    text = clean(raw)

    i = text.find(ANCHOR)
    if i < 0:
        print("FAIL: 找不到摘要锚点，请人工核对")
        return 1

    # 摘要终点：稿内固定出现的关键词/章节起点
    end_markers = ["Index Terms", "Keywords", "I. I NTRODUCTION", "I. INTRODUCTION"]
    ends = [text.find(m, i) for m in end_markers]
    ends = [e for e in ends if e > 0]
    j = min(ends) if ends else len(text)
    abstract = text[i:j].strip()

    # pdftotext 在行末断词时会留下连字符，合并后需补回几处**属于复合词**的连字符
    # （这些是稿件里的固定写法，逐条对照 main.tex 确认）
    fixes = {
        "smallperturbation": "small-perturbation",
        "decoderbased": "decoder-based",
        "Crossarchitecture": "Cross-architecture",
        "architecturedependent": "architecture-dependent",
        "encoderonly": "encoder-only",
    }
    for bad, good in fixes.items():
        abstract = abstract.replace(bad, good)

    # 标题：锚点之前的最后一段（去掉页码与署名）
    head = text[:i]
    head = re.sub(r"\s*Hongrui Wan.*$", "", head).strip()
    head = re.sub(r"^\d+\s*", "", head).strip()   # 去首页页码

    print("=" * 72)
    print("TITLE（EM 的 'Your title' 栏）")
    print("=" * 72)
    print(head)
    print()
    print("=" * 72)
    print("ABSTRACT（EM 的 'Your abstract' 栏）")
    print("=" * 72)
    print(abstract)
    n = len([w for w in abstract.split() if re.search(r"\w", w)])
    print()
    print(f"[字数 {n} / EM 上限 300 -> {'合规' if n <= 300 else '超限'}]")

    kw = ""
    m = re.search(r"(?:Index Terms|Keywords)[\s:—–-]*(.*?)(?:I\.\s*I?NTRODUCTION|$)", text, re.S)
    if m:
        kw = m.group(1).strip()
    print()
    print("=" * 72)
    print("KEYWORDS（EM 要求分号分隔）")
    print("=" * 72)
    if kw:
        parts = [p.strip() for p in re.split(r"[,;]", kw) if p.strip()]
        print("; ".join(parts))
        print(f"[{len(parts)} 个，取自稿内关键词块]")
    else:
        print("(稿内无关键词块——须自行填写，建议见下方候选)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
