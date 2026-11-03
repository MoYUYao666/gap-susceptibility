# -*- coding: utf-8 -*-
r"""核对 presubmission inquiry（或任何对外信件）中引用的文献元数据是否与 refs_all.json 一致。

为什么需要：对外信件里引错作者/年份/刊名，编辑一眼可见，代价很高。
本脚本把信件 PDF 的文本与库中元数据逐条比对（作者姓氏、年份、刊名关键词）。

    python tools/_audit_letter_refs.py paper_review/presubmission_inquiry_inffusion.pdf
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REFS = REPO / "paper_review" / "refs_all.json"

CASES = [
    ("xu2026peftsurvey", ["Xu", "2026", "TPAMI", "Critical Review and Assessment"]),
    ("xin2024vpeftsurvey", ["Xin", "2026", "Computer Vision", "Survey and Benchmark"]),
    ("zhang2026halora", ["Zhang", "2026", "AAAI", "Hierarchical Budget Allocation"]),
    ("cho2026mars", ["Cho", "2026", "2603.00720", "Adaptive Rank Search"]),
    ("jin2024efficientmllm", ["Jin", "2024", "2405.10739", "Efficient Multimodal Large Language Models"]),
    ("zanella2024cliplora", ["Zanella", "2024", "CVPRW", "Low-Rank Few-Shot Adaptation"]),
]


def main() -> int:
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "paper_review" / "presubmission_inquiry_inffusion.pdf"
    if not pdf.exists():
        print(f"找不到 {pdf}")
        return 1
    out = subprocess.run(["pdftotext", "-raw", str(pdf), "-"], capture_output=True)
    text = re.sub(r"\s+", " ", out.stdout.decode("utf-8", "ignore"))

    refs = {e.get("key"): e for e in json.loads(REFS.read_text(encoding="utf-8"))}

    print(f"核对 {pdf.name} 中的 {len(CASES)} 条引用\n")
    bad = 0
    for key, needles in CASES:
        e = refs.get(key)
        if not e:
            print(f"  ❓ {key} 不在参考文献库中")
            bad += 1
            continue
        missing = [n for n in needles if n.lower() not in text.lower()]
        flag = "✅" if not missing else "❌"
        if missing:
            bad += 1
        print(f"  {flag} {key:<30} 库中: {(e.get('authors') or ['?'])[0]} / {e.get('year')} / {e.get('venue')}")
        if missing:
            print(f"       信件中未出现: {missing}")

    # 反向检查：信里有没有提到库中不存在的 arXiv id / DOI
    ids = set(re.findall(r"\b\d{4}\.\d{4,5}\b", text))
    known_ids = {str(e.get("arxiv_id")) for e in refs.values() if e.get("arxiv_id")}
    unknown = sorted(i for i in ids if i not in known_ids)
    print(f"\n信件中出现的 arXiv id: {sorted(ids)}")
    if unknown:
        print(f"  ❌ 这些 id 不在参考文献库中，需核实：{unknown}")
        bad += len(unknown)
    else:
        print("  ✅ 全部能在库中对上")

    print(f"\n结果：{'PASS' if not bad else f'FAIL（{bad} 项）'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
