# -*- coding: utf-8 -*-
r"""诊断 A1 已填表的字体与日期绘制方式，为生成 P3 的表做准备。

    python tools/_inspect_form_pdf.py
"""
from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "paper_a1" / "_archive_prl" / "Authorship Confirmation submit.pdf"


def main() -> int:
    r = PdfReader(str(SRC))
    p = r.pages[0]
    res = p.get("/Resources")
    print("=== 页面资源 ===")
    if res:
        for k in res:
            print(f"  {k}: {type(res[k]).__name__}")

    print("\n=== 字体 ===")
    fonts = res.get("/Font") if res else None
    font_keys = []
    if fonts:
        for k, v in fonts.items():
            f = v.get_object()
            font_keys.append(k)
            print(f"  {k}: Subtype={f.get('/Subtype')} BaseFont={f.get('/BaseFont')} Encoding={f.get('/Encoding')}")

    print("\n=== XObject ===")
    xo = res.get("/XObject") if res else None
    if xo:
        for k, v in xo.items():
            o = v.get_object()
            print(f"  {k}: Subtype={o.get('/Subtype')} BBox={o.get('/BBox')}")

    data = p.get_contents().get_data().decode("latin-1", "ignore")
    print(f"\n=== 内容流片段（定位 y≈412 的绘制）===")
    # 找所有 Td/Tm/TJ/Tj 附近含 y 约 412 的片段
    for m in re.finditer(r"/\w+\s+[\d.]+\s+Tf|[\d.]+\s+[\d.]+\s+Td|[\d.-]+\s+[\d.-]+\s+[\d.-]+\s+[\d.-]+\s+[\d.-]+\s+[\d.-]+\s+Tm", data):
        seg = m.group(0)
        if "412" in seg or "411" in seg or "413" in seg:
            print("  ", seg)
    print("\n=== 含 Signature / Date 命令的上下文 ===")
    i = data.find("(Signature)")
    if i < 0:
        i = data.find("Signature")
    print(repr(data[max(0, i - 400): i + 400]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
