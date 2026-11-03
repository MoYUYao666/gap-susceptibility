# -*- coding: utf-8 -*-
r"""校验本任务所有 `p3d_*.json` 归档是**严格 UTF-8**（按字节判，不靠 PowerShell 显示）。

## 为什么

项目规矩：**判编码先看字节**（hex 头、NUL 计数、严格 UTF-8 解码、定位非法字节偏移），
不要凭 PowerShell 的显示下结论——本项目曾因此留下过两条错误结论。
本脚本对每个文件做：严格 UTF-8 解码 + 逐字节扫描非法偏移 + 打印首个中文字段的原文。

    python tools\_p471_check_encoding.py
"""
from __future__ import annotations

import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A = REPO / "outputs" / "analysis"
bad = 0
files = sorted(A.glob("p3d_*.json"))
print(f"=== 校验 {len(files)} 个 p3d_*.json 的编码（按字节）===")
for p in files:
    raw = p.read_bytes()
    # 逐字节严格解码，定位第一个非法偏移
    off = None
    try:
        raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as e:
        off = e.start
    bom = raw[:3] == b"\xef\xbb\xbf"
    nul = raw.count(b"\x00")
    tail = raw[:3].hex()
    status = "OK" if (off is None and not bom and nul == 0) else "BAD"
    if status == "BAD":
        bad += 1
    print(f"  [{status}] {p.name:<44} bytes={len(raw):>8} head={tail} "
          f"BOM={bom} NUL={nul}" + (f" 首个非法 UTF-8 偏移={off}" if off is not None else ""))

# 抽一个中文字段，证明"显示成乱码"是读侧的问题
p = A / "p3d_qwen_ranksweep_mp50176.json"
if p.exists():
    raw = p.read_bytes()
    txt = raw.decode("utf-8")
    i = txt.find("E_train")
    print(f"\n  抽样（{p.name}，严格 UTF-8 解码）:")
    print("    " + txt[i:i + 60].replace("\n", " "))
    print("    ↑ 若在 PowerShell 里显示成 '鍦ㄨ缁冩潯浠? 之类，那是 **UTF-8 被按 GBK 解码** 的显示问题，")
    print("      文件本身是合法 UTF-8（上面已严格解码通过）。读的时候显式 encoding='utf-8' 即可。")

print(f"\n=== {len(files) - bad}/{len(files)} 通过 ===")
raise SystemExit(1 if bad else 0)
