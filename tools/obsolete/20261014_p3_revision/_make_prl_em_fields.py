# -*- coding: utf-8 -*-
r"""生成 PRL 综述投稿时门户要填的字段（纯文本，可直接粘贴）。

清掉 markdown 强调符号；并给出与 P3 同一套 IAPR 分类建议。

    python tools/_make_prl_em_fields.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"
OUT = REPO / "paper_review_prl" / "UPLOAD" / "EM_fields.txt"

TITLE = "Allocation, not selection: comparability in parameter-efficient multimodal adaptation"

KEYWORDS = ["parameter-efficient fine-tuning", "multimodal models", "vision-language models",
            "comparability", "evaluation protocol", "reporting standards"]

CLASSIFICATIONS = [
    ("Classification and decision processes", "other learning algorithms and training procedures"),
    ("Classification and decision processes", "neural networks, radial basis functions"),
    ("Classification and decision processes", "performance evaluation, benchmarking procedures and systems"),
    ("Statistical feature extraction and analysis", "feature extraction, representation, reduction, selection"),
    ("Image and video understanding", "Object Detection, Recognition, and Categorization"),
]

CREDIT = ["Conceptualization", "Methodology", "Formal analysis", "Investigation",
          "Writing – original draft", "Writing – review & editing", "Visualization"]


def clean(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\1", s)
    s = s.replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip()


def main() -> int:
    md = MD.read_text(encoding="utf-8")
    m = re.search(r"## Abstract\s*(.+?)\n\n\*\*Keywords", md, re.S)
    abstract = clean(m.group(1)) if m else ""
    n_words = len(abstract.split())

    lines = [
        "=== Your title ===", TITLE, "",
        f"=== Your abstract ===（{n_words} 词，PRL 上限 250）", abstract, "",
        "=== Your keywords ===（分号分隔）", "; ".join(KEYWORDS), "",
        "=== Article type ===",
        "Commentary   （PRL 指南：commentaries 含 'subject reviews'；ALL CAPS 或下拉里选 Commentary）", "",
        "=== Classifications（IAPR 体系，选 3-5 项；与 P3 同一套，重心压在分类与决策）===",
    ]
    for i, (a, b) in enumerate(CLASSIFICATIONS, 1):
        lines.append(f"  {i}) {a}  →  {b}")
    lines += [
        "",
        "=== Author / CRediT ===",
        "  Hongrui Wan  |  University of Southampton  |  contact@example.com",
        "  " + "; ".join(CREDIT),
        "  说明：本稿为批判性综述，未做新实验，故不填 Software / Data curation / Funding acquisition",
        "",
        "=== Do you want to share data? ===",
        "  N/A — 本稿是文献综述，不产生新数据（若门户必填，选 'No new data were created' 或等价项）",
        "",
        "=== 上传文件与 item type ===",
        "  Manuscript.pdf                  → Manuscript",
        "  Highlights.txt                  → Highlights（单独文件，强制）",
        "  Cover Letter.pdf                → Cover Letter",
        "  Authorship Confirmation.pdf     → Cover Letter  ← 同类型，但必须上传",
        "",
        "=== 提交时两个必选项 ===",
        "  ⚠️ License = CC BY（否则图书馆不批免费 OA）",
        "  ⚠️ 费用栏应显示 'To pay on acceptance: 0.00'（若非 0 先别提交）",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    print(f"写出 {OUT.relative_to(REPO)}")
    print(f"  摘要 {n_words} 词（上限 250）{'✅' if n_words <= 250 else '❌'}")
    print(f"  关键词 {len(KEYWORDS)} 个（上限 7）{'✅' if len(KEYWORDS) <= 7 else '❌'}")
    print(f"  摘要中是否残留 markdown 星号: {'❌ 有' if '*' in abstract else '✅ 无'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
