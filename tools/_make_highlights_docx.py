# -*- coding: utf-8 -*-
"""生成 highlights.docx（Elsevier 门户接受的可编辑格式）。

不依赖 python-docx：直接写最小合法 OOXML 包。

    python tools/_make_highlights_docx.py [目标目录]
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

TITLE = "Highlights"
PAPER = ("Gradient Structure Laws as Predictors of PEFT Design: "
         "Zero-Shot Cross-Architecture Rank Allocation")
AUTHOR = "Hongrui Wan - University of Southampton"
BULLETS = [
    "The cross-modal gradient coupling is the unique admissible allocation statistic",
    "It transfers zero-shot: measured on CLIP, it predicts LLaVA rank allocation",
    "Constrained optimisation yields an exponential rank-allocation law",
    "A critical rank separates safe, damaging and collapsing allocation regimes",
    "Counterfactual tests show the coupling predicts allocation uncertainty",
]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def para(text: str, indent: bool = False) -> str:
    ppr = '<w:pPr><w:ind w:left="360"/></w:pPr>' if indent else ""
    return (f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


def main() -> int:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "paper3" / "paper_ieee" / "PRL_submission"
    out = out_dir / "highlights.docx"

    body = "".join([
        para(TITLE),
        para(""),
        para(PAPER),
        para(AUTHOR),
        para(""),
        *[para("•  " + b, indent=True) for b in BULLETS],
    ])

    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f'<w:body>{body}<w:sectPr/></w:body></w:document>')
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                     '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)

    # 自校验：能被打开、条目齐全、bullet 数正确
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        doc = z.read("word/document.xml").decode("utf-8")
    n_bullets = doc.count("•")
    print(f"写出 {out}  ({out.stat().st_size} bytes)")
    print(f"  包内条目: {names}")
    print(f"  项目符号数: {n_bullets}（应为 {len(BULLETS)}）")
    print(f"  最长条目: {max(len(b) for b in BULLETS)} 字符（上限 85）")
    return 0 if n_bullets == len(BULLETS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
