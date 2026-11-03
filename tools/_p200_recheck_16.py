# -*- coding: utf-8 -*-
r"""核查 09-15 对抗性审查的 16 个"新问题"在**当前稿**里是否仍然存在（2026-10-12）。

## 为什么

`docs/A1_ADVERSARIAL_REVIEW.md`（09-15）列了 N1–N16 与 D1–D3。
此后稿子改过多次（PRL 整改、重定位、文献转 APA）。
**必须逐条复核，不能假设已修**——否则会把"已修"当"未修"，或反之。

    python tools\_p200_recheck_16.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper_a1" / "main.tex"
RW = REPO / "paper_a1" / "related_work.tex"
OUT = REPO / "outputs" / "analysis" / "a1_recheck16.json"

# (编号, 一句话, 检查用的正则 —— 命中说明"该问题的证据仍在")
CHECKS = [
    ("N1", "引用了评审无法获得的文档",
     r"revision_additions|_superseded|内部文档|internal document"),
    ("N2/D1", "Results 与自家表格/Related Work 矛盾",
     r"necessary, not sufficient|sufficient, not necessary"),
    ("N3", "中文镜像仍含撤回的主张",
     r"main_zh"),
    ("N4", "摘要里残留编辑片段",
     r"\\emph\{diagnostic\}\s*\\emph\{implicitly\}"),
    ("N5", "载重的 prose 主张被自家结果否证",
     r"unconditional form of that reading"),
    ("N6", "头条 gap-growth 数字在自己评测器下不可复现",
     r"\+0\.033.{0,120}\+0\.114|\+0\.114.{0,120}\+0\.033"),
    ("N8", "archived checkpoint 的 50k 数字来自论文未描述的协议",
     r"50{,}?0?00|50k"),
    ("N9", "图 2 混了两个样本量而表注未说明",
     r"fig:lambda|Figure~\\ref\{fig:lambda\}"),
    ("N10", "同一项目里三个不同的 condition 计数",
     r"\b34\b.{0,300}\b5\b|condition[s]? count"),
    ("N12", "「预测等于测量」被当作验证",
     r"self-consistency check|not independent validation"),
    ("N13", "Related Work 有让步而 Limitation 没有",
     r"Limitations?"),
    ("N15", "论文依赖的 r=-0.827 是项目自己标记为不可用的",
     r"-0\.827"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    text = ""
    for f in (MAIN, RW):
        if f.exists():
            text += io.open(f, encoding="utf-8", errors="replace").read() + "\n"
    print("=" * 88)
    print("09-15 的 16 个问题 → 当前稿复核")
    print("=" * 88)
    res = []
    for num, desc, pat in CHECKS:
        ms = list(re.finditer(pat, text, re.S))
        n = len(ms)
        # 命中 ≠ 问题仍在（有些正则匹配的是"修正后的正确表述"）
        print(f"\n  [{num}] {desc}")
        print(f"     正则命中 {n} 处")
        for m in ms[:2]:
            s = " ".join(text[max(0, m.start() - 160):m.start() + 200].split())
            print(f"       …{s[:300]}…")
        res.append({"id": num, "desc": desc, "pattern": pat, "hits": n})

    print()
    print("=" * 88)
    print("需要**人工判定**的（正则无法自动判'已修/未修'）")
    print("=" * 88)
    print("  以下问题性质上需要读上下文才能判，已在上文打印命中处，请逐条人工确认：")
    print("   N1（引用内部文档）｜N2/D1（自家矛盾）｜N5（prose 被否证）｜N6（头条数字）")
    print("   N8（50k 协议）｜N9（图 2 样本量）｜N10（condition 计数）｜N13（让步）｜N15（r=-0.827）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
