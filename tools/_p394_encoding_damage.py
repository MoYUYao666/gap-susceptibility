# -*- coding: utf-8 -*-
r"""收紧版：只检测**真正的编码损伤**（2026-10-12）。

## 上一版的错

我用"mid-token `?`"当判据 → **43+ 个文件误报**（正当问号、`"?"` 字面量、正则里的 `?`）。
**"看起来可疑"不是证据。**

## 真正该检测的（两类，各自可判定）

1. **双重编码**：UTF-8 字节被按 GBK 解码后再按 UTF-8 编码 → 出现**典型的乱码序列**。
   判据：文本里存在 `[\u00c0-\u00ff][\u0080-\u00ff]` 这类 Latin-1 高位区的连排，
   或**可被 `s.encode('latin-1').decode('utf-8')` 还原出合法汉字**的模式。
2. **替换符 U+FFFD**（`\ufffd`）与**私用区**（`\ue000-\uf8ff`）。

    python tools\_p394_encoding_damage.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "encoding_damage_scan.json"

# 双重编码的可靠特征：Latin-1 高位连排（如 "æ–‡ä»¶" 这类）
DOUBLE_ENC = re.compile(r"[\u00c2-\u00ef][\u0080-\u00bf]")
MOJIBAKE_HINT = re.compile(r"[\u00e4\u00e5\u00e6\u00e7\u00e8\u00e9\u00ea\u00eb\u00c3\u00c2]"
                           r"[\u0080-\u00bf\u00a0-\u00ff]")


def damage(t: str):
    out = []
    for i, ch in enumerate(t):
        if ch == "\ufffd":
            out.append((i, "U+FFFD"))
        elif 0xE000 <= ord(ch) <= 0xF8FF:
            out.append((i, "private-use"))
    n_dbl = len(DOUBLE_ENC.findall(t))
    n_hint = len(MOJIBAKE_HINT.findall(t))
    return out, n_dbl, n_hint


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    res = {"suspects": [], "clean": 0}

    print("=" * 100)
    print("只检双重编码 / U+FFFD / 私用区（最近 3 天改动）")
    print("=" * 100)
    for pat in ("tools/*.py", "docs/*.md", "*.md", "src/*.py", "experiments/*.py",
                "paper合/sections/*.tex", "paper_a1/*.tex"):
        for f in glob.glob(str(REPO / pat)):
            p = Path(f)
            if time.time() - os.path.getmtime(p) > 3 * 86400:
                continue
            b = p.read_bytes()
            try:
                t = b.decode("utf-8")
            except UnicodeDecodeError as e:
                res["suspects"].append({"file": str(p.relative_to(REPO)),
                                        "why": f"UTF-8 解码失败: {str(e)[:80]}"})
                continue
            bad, n_dbl, n_hint = damage(t)
            if bad or n_dbl or n_hint:
                res["suspects"].append({
                    "file": str(p.relative_to(REPO)),
                    "why": f"U+FFFD/私用区 {len(bad)} ｜ 双重编码特征 {n_dbl} ｜ mojibake 提示 {n_hint}",
                    "sample": t[max(0, (bad[0][0] if bad else 0) - 40):
                                (bad[0][0] if bad else 0) + 60] if bad else "",
                })
            else:
                res["clean"] += 1

    if res["suspects"]:
        for s in res["suspects"]:
            print(f"  🔴 {s['file']}: {s['why']}")
            if s.get("sample"):
                print(f"        …{s['sample']!r}…")
    else:
        print(f"  ✅ 无损伤（已检 {res['clean']} 个文件）")

    print()
    print("=" * 100)
    print("专项：上游报告与产出脚本")
    print("=" * 100)
    for rel in ("docs/PR_MORE_MODELS.md", "tools/_p293e_report.py",
                "tools/_p293n_repair_encoding.py", "tools/_p293o_repair_encoding2.py",
                "tools/_p293p_repair_spacing.py"):
        p = REPO / rel
        if not p.exists():
            cands = list((REPO / "tools").glob(Path(rel).stem.replace("_p293p_repair_spacing",
                                                                      "_p293p*") + "*"))
            if cands:
                p = cands[0]
            else:
                print(f"  ⚠️ 缺 {rel}")
                continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        bad, n_dbl, n_hint = damage(t)
        cjk = len(re.findall(r"[\u4e00-\u9fff]", t))
        flag = "✅" if not (bad or n_dbl or n_hint) else "🔴"
        print(f"  {flag} {p.name:<34} 字符 {len(t):>7} ｜ CJK {cjk:>5} ｜ "
              f"FFFD/PUA {len(bad)} ｜ 双编码 {n_dbl} ｜ 提示 {n_hint}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}｜干净 {res['clean']} 个、可疑 {len(res['suspects'])} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
