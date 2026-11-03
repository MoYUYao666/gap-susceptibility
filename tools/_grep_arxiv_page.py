# -*- coding: utf-8 -*-
r"""在 arXiv 摘要页/HTML 中检索指定字符串，用于核对具体数值断言。

用于复核"某论文报了某个数字"这类断言——摘要含关键词只能证明"论文相关"，
真正核对数值需要能看到正文；本脚本给出**能查到/查不到**的明确结论，不含推测。

用法：
    python tools/_grep_arxiv_page.py 2307.06281 "36.7" "2.6" "CircularEval"
    python tools/_grep_arxiv_page.py 2310.03744 "87.3"
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("vc", REPO / "tools" / "_verify_citations.py")
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    aid, needles = sys.argv[1], sys.argv[2:]

    raw = vc.http_get(f"https://arxiv.org/abs/{aid}", UA)
    if not raw:
        print(f"取不到 https://arxiv.org/abs/{aid}")
        return 1
    text = re.sub(r"<script.*?</script>", " ", raw, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    ti = re.search(r'<meta name="citation_title" content="(.*?)"', raw)
    print(f"论文: {ti.group(1) if ti else aid}")
    print(f"页面可见文本长度: {len(text)} 字符\n")

    for n in needles:
        hits = [m.start() for m in re.finditer(re.escape(n), text)]
        if hits:
            print(f"  ✅ 「{n}」出现 {len(hits)} 次")
            for h in hits[:3]:
                snippet = text[max(0, h - 70): h + 70].strip()
                print(f"       …{snippet}…")
        else:
            print(f"  ❌ 「{n}」在 abs 页面**未出现**（注意：正文表格数值通常不在 abs 页面，需查全文 PDF）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
