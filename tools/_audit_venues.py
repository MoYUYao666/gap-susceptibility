# -*- coding: utf-8 -*-
r"""逐条对照"稿件标注的 venue"与"Crossref 记录的实际刊名"，抓 venue 错配。

动机：核验器对"arXiv 页面核到 + 稿件标注会议名"的条目只给 ⚠️ 警告（因为 arXiv 页面
本身不含发表信息）。但多数会议论文在 Crossref 有正式 DOI，**可以据 DOI 反查真实刊名**，
从而把"venue 是否写对"也纳入核验。

用法：
    python tools/_audit_venues.py            # 读 paper_review/refs_all.json
输出：控制台逐条结论 + paper_review/venue_report.md
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIR = REPO / "paper_review"
spec = importlib.util.spec_from_file_location("vc", REPO / "tools" / "_verify_citations.py")
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)

# 我方标注的简称 → Crossref 刊名里应出现的关键词（宽松匹配，只用于提示人工确认）
HINTS = {
    "neurips": ("advances in neural information processing", "neurips", "neural information"),
    "nips": ("advances in neural information processing", "neural information"),
    "icml": ("international conference on machine learning", "proceedings of machine learning research", "icml"),
    "iclr": ("international conference on learning representations", "iclr"),
    "cvpr": ("computer vision and pattern recognition", "cvpr"),
    "iccv": ("international conference on computer vision", "iccv"),
    "eccv": ("european conference on computer vision", "eccv"),
    "emnlp": ("empirical methods in natural language processing", "emnlp"),
    "acl": ("annual meeting of the association for computational linguistics", "acl"),
    "naacl": ("north american chapter", "naacl"),
    "eacl": ("european chapter", "eacl"),
    "coling": ("international conference on computational linguistics",),
    "aaai": ("aaai conference on artificial intelligence", "aaai"),
    "ijcai": ("international joint conference on artificial intelligence", "ijcai"),
    "eacl": ("european chapter",),
    "semeval": ("semeval", "semantic evaluation"),
}


def main() -> int:
    refs = json.loads((DIR / "refs_all.json").read_text(encoding="utf-8"))
    print(f"对照 {len(refs)} 条的 venue 标注\n")

    ok, mismatch, unknown, no_doi = [], [], [], []
    for e in refs:
        key = e.get("key")
        venue = (e.get("venue") or "").strip()
        doi = (e.get("doi") or "").strip()
        if not doi or "arxiv" in doi.lower() or venue.lower() in ("", "arxiv"):
            (no_doi if not doi or "arxiv" in doi.lower() else unknown).append(key)
            continue
        m = vc.crossref_by_doi(doi)
        if not m:
            unknown.append(key)
            continue
        real = vc.cr_norm(m)["venue"] or ""
        vlow = venue.lower()
        hint = None
        for short, kws in HINTS.items():
            if short in vlow:
                hint = kws
                break
        if hint is None:
            ok.append((key, venue, real, "无预设关键词，未判定"))
            continue
        if any(k in real.lower() for k in hint):
            ok.append((key, venue, real, "吻合"))
        else:
            mismatch.append((key, venue, real, doi))

    print(f"=== ✅ 判定吻合或无预设关键词：{len(ok)} ===")
    for key, v, real, note in ok[:40]:
        print(f"  {key:<28} 标注『{v}』 | Crossref『{real[:52]}』 | {note}")
    print(f"\n=== ❌ venue 可能错配：{len(mismatch)} ===")
    for key, v, real, doi in mismatch:
        print(f"  {key:<28} 标注『{v}』 | Crossref『{real[:60]}』 | {doi}")
    print(f"\n=== ⚠️ 无正式 DOI（arXiv-only 或仅 arXiv DOI）：{len(no_doi)} ===")
    for k in no_doi[:40]:
        print(f"  {k}")
    print(f"\n=== ❓ 有 DOI 但 Crossref 查不到 / venue 为空：{len(unknown)} ===")
    for k in unknown[:20]:
        print(f"  {k}")

    lines = ["# venue 对照报告", "",
             f"合计 **{len(refs)}** 条 ｜ 吻合或无预设词 **{len(ok)}** ｜ "
             f"**可能错配 {len(mismatch)}** ｜ 无正式 DOI **{len(no_doi)}** ｜ 查不到 **{len(unknown)}**", ""]
    if mismatch:
        lines += ["## ❌ 可能错配（需人工确认，**不得直接入表**）", "",
                  "| key | 稿件标注 | Crossref 实际刊名 | DOI |", "|---|---|---|---|"]
        lines += [f"| `{k}` | {v} | {r} | {d} |" for k, v, r, d in mismatch]
        lines.append("")
    lines += ["## ⚠️ 无正式 DOI（引用时须标为 arXiv 预印本）", ""]
    lines += [f"- `{k}`" for k in no_doi]
    lines += ["", "> 说明：Crossref 刊名字符串与会议简称形态不同（如 NeurIPS 记为",
              "> 'Advances in Neural Information Processing Systems'），故用关键词宽松匹配；",
              "> 标为「无预设关键词」者未做判定，需人工过目。"]
    (DIR / "venue_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n写出 {(DIR / 'venue_report.md').relative_to(REPO)}")
    return 1 if mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())
