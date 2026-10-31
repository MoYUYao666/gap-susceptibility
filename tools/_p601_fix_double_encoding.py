# -*- coding: utf-8 -*-
r"""修 `beta_pilot_results.json` 的双重编码，并做最终核验（2026-10-14）。

## 那个文件的问题

`outputs/theory/beta_pilot/beta_pilot_results.json` 自 **2026-09-24 首次提交**起就不是合法 UTF-8：
字节 `0xA1 0xAA` 是 **GBK 的 em dash `—`**，被当 UTF-8 写出 ⇒ 解码失败。
**⇒ 属"GBK 读 / UTF-8 写"双编码事故**（本项目已知问题类型），非本次引入。

修法：把该字节序列按 GBK 解回 `—`，再以 UTF-8 写出。

    python tools\_p601_fix_double_encoding.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
P = PC / "outputs" / "theory" / "beta_pilot" / "beta_pilot_results.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    b = P.read_bytes()
    print(f"  {len(b):,} 字节 ｜ 前 40: {b[:40]!r}")
    # 找所有非法 UTF-8 位置
    bad = []
    i = 0
    while i < len(b):
        try:
            b[i:].decode("utf-8")
            break
        except UnicodeDecodeError as e:
            pos = i + e.start
            bad.append((pos, b[pos:pos + 2]))
            i = pos + 1
    print(f"  非法 UTF-8 序列 {len(bad)} 处：{bad[:8]}")

    if not a.apply:
        print("  （预演）")
        return 0
    # 逐处把 2 字节 GBK 序列替换为其 UTF-8 形式
    out = bytearray()
    i = 0
    n = 0
    while i < len(b):
        try:
            b[i:].decode("utf-8")
            out += b[i:]
            break
        except UnicodeDecodeError as e:
            pos = i + e.start
            out += b[i:pos]
            seq = b[pos:pos + 2]
            try:
                ch = seq.decode("gbk")
            except Exception:
                ch = "?"
            out += ch.encode("utf-8")
            n += 1
            i = pos + 2
    # 校验
    try:
        t = bytes(out).decode("utf-8")
        json.loads(t)
        ok = True
    except Exception as e:
        print(f"  🔴 修后仍失败：{e}")
        return 1
    bak = P.with_suffix(".json.bak_p601")
    if not bak.exists():
        shutil.copy2(P, bak)
    P.write_bytes(bytes(out))
    t2 = P.read_bytes().decode("utf-8")
    print(f"  ✅ 替换 {n} 处 GBK 序列 ⇒ 文件现为合法 UTF-8 / 合法 JSON（{len(t2):,} 字符）")
    # 展示修复后的那段
    i = t2.find("Beta Pilot")
    print(f"     片段：…{t2[max(0,i-30):i+30]!r}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
