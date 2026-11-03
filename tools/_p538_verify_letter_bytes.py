# -*- coding: utf-8 -*-
r"""按字节核验回复信两个副本的编码与内容一致性（2026-10-13）。

    python tools\_p538_verify_letter_bytes.py
"""
from __future__ import annotations

import hashlib
import io
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [
    REPO / "docs" / "P3_RESPONSE_LETTER.md",
    REPO / "SUBMISSION" / "P3_PRL_revision" / "response" / "P3_RESPONSE_LETTER.md",
    REPO / "SUBMISSION" / "P3_PRL_revision" / "response" / "P3_RESPONSE_LETTER.txt",
]


def main() -> int:
    print("=" * 96)
    print("逐文件字节核验（项目规矩：判编码先看字节）")
    print("=" * 96)
    print(f"  {'文件':<58} {'字节':>8} {'字符':>8} {'NUL':>5} {'BOM':>5}")
    hashes = {}
    for f in FILES:
        if not f.exists():
            print(f"  🔴 缺 {f.relative_to(REPO)}")
            return 1
        b = f.read_bytes()
        nul = b.count(b"\x00")
        bom = b[:3] == b"\xef\xbb\xbf"
        try:
            t = b.decode("utf-8")
            dec = "✅ UTF-8 合法"
        except UnicodeDecodeError as e:
            t = ""
            dec = f"🔴 非法 UTF-8 @ {e.start}"
        hashes[f.name] = hashlib.sha256(b).hexdigest()[:16]
        print(f"  {str(f.relative_to(REPO))[:56]:<58} {len(b):>8,} {len(t):>8,} "
              f"{nul:>5} {str(bom):>5}  {dec}")
    print()
    print("  sha256（前 16 位）：")
    for k, v in hashes.items():
        print(f"     {k:<48} {v}")
    uniq = set(hashes.values())
    print()
    print(f"  ⇒ 三个副本内容{'**完全一致**' if len(uniq) == 1 else '**不一致**'}（{len(uniq)} 个不同摘要）")
    print()
    print("=" * 96)
    print("结构核验")
    print("=" * 96)
    t = io.open(FILES[0], encoding="utf-8").read()
    import re
    print(f"  分节头（# Reviewer）：{len(re.findall(r'^# Reviewer', t, re.M))} 个（应 3）")
    print(f"  Comment 标题：{t.count('## Comment ')} 个（应 33）")
    print(f"  Response 块：{t.count('**Response.**')} 个（应 33）")
    print(f"  意见引用块（> 起始行）：{len(re.findall(r'^> ', t, re.M))} 行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
