# -*- coding: utf-8 -*-
r"""核验上游成员的编码损伤是否真已修复（2026-10-12）。

## 背景

上游成员用 `(Get-Content -Raw) -replace ... | Set-Content -Encoding utf8` 改文件
→ PowerShell 以 **GBK 读、UTF-8 写** → **文件内所有非 ASCII 字符双重编码**。
它报告已用 `_p293n`–`_p293q` 修复，并称"影响范围为零"。

**"看起来修好了"不是证据。 必须自己核：**
1. `_p293e_report.py` 能否 parse / 是否有编码损坏
2. `docs/PR_MORE_MODELS.md` 是否有 CJK 乱码、`?` 残留、粘连
3. **数字是否与归档一致**（内容而非编码）
4. 全仓库是否还有同类损伤的痕迹（**同一手法可能不止改过一个文件**）

    python tools\_p393_verify_encoding_repair.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import glob
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "encoding_repair_verify.json"


def bad_chars(t: str):
    """找可疑字符：替换符、私用区、非预期 CJK 之外的怪字。"""
    out = []
    for i, ch in enumerate(t):
        if ch == "\ufffd":
            out.append((i, ch, "REPLACEMENT CHAR"))
        elif 0xE000 <= ord(ch) <= 0xF8FF:
            out.append((i, ch, "PRIVATE USE"))
        elif ch == "?" and i > 0 and t[i-1] not in " \n\t([{'\"":
            out.append((i, ch, "mid-token ?"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 100)
    print("① 全仓库扫「疑似编码损伤」的文件（最近 2 天改动过的 .py / .md）")
    print("=" * 100)
    import os, time
    suspects = []
    for pat in ("tools/*.py", "docs/*.md", "*.md"):
        for f in glob.glob(str(REPO / pat)):
            p = Path(f)
            if time.time() - os.path.getmtime(p) > 2 * 86400:
                continue
            b = p.read_bytes()
            try:
                t = b.decode("utf-8")
            except UnicodeDecodeError as e:
                suspects.append((str(p.relative_to(REPO)), f"UTF-8 解码失败: {e}"))
                continue
            bc = bad_chars(t)
            if bc:
                suspects.append((str(p.relative_to(REPO)),
                                 f"{len(bc)} 处可疑（例：{bc[0][2]} @ {bc[0][0]}）"))
    if suspects:
        for rel, why in suspects:
            print(f"  🔴 {rel}: {why}")
    else:
        print("  ✅ 最近改动文件中未发现编码损伤")
    rep["suspects"] = suspects

    print()
    print("=" * 100)
    print("② `_p293e_report.py` 的可解析性与字符健康")
    print("=" * 100)
    for name in ("_p293e_report.py", "_p293n_repair_encoding.py",
                 "_p293o_repair_encoding2.py", "_p293p_repair.py", "_p293q_repair.py"):
        p = REPO / "tools" / name
        if not p.exists():
            cands = list((REPO / "tools").glob(name.replace("_p293p_repair", "_p293p*")
                                               .replace("_p293q_repair", "_p293q*")))
            if not cands:
                print(f"  ⚠️ 缺 {name}")
                continue
            p = cands[0]
        t = io.open(p, encoding="utf-8", errors="replace").read()
        try:
            ast.parse(t)
            ok = "✅ parse 通过"
        except SyntaxError as e:
            ok = f"🔴 SyntaxError: {e}"
        bc = bad_chars(t)
        print(f"  {p.name:<38} {ok} ｜ 可疑字符 {len(bc)}")
        rep[p.name] = {"parse": ok, "bad_chars": len(bc)}

    print()
    print("=" * 100)
    print("③ `docs/PR_MORE_MODELS.md` 内容健康 + 数字抽查")
    print("=" * 100)
    rp = REPO / "docs" / "PR_MORE_MODELS.md"
    if rp.exists():
        t = io.open(rp, encoding="utf-8", errors="replace").read()
        bc = bad_chars(t)
        cjk = len(re.findall(r"[\u4e00-\u9fff]", t))
        dbl = len(re.findall(r"  [^ \n]", t))
        print(f"  字符数 {len(t)} ｜ 可疑字符 {len(bc)} ｜ CJK {cjk} ｜ 疑似双空格 {dbl}")
        # 抽查关键数字是否在
        for k in ("0.3913", "0.00045", "0.0078", "4.605170", "14.2857",
                  "8.3371", "656,384", "0.289", "0.577"):
            print(f"     {'✅' if k in t else '⚠️ '} 含 {k}")
        rep["PR_MORE_MODELS"] = {"chars": len(t), "bad": len(bc), "cjk": cjk}
    else:
        print("  🔴 报告不存在")

    print()
    print("=" * 100)
    print("④ 数字与归档一致性抽查（防内容被改）")
    print("=" * 100)
    checks = [
        ("outputs/analysis/dinov2_hetero/logit_scale_provenance.json", "4.605170"),
        ("outputs/analysis/dinov2_hetero/pristine_clip_provenance.json", "A6308213"),
        ("outputs/analysis/dinov2_hetero/lora_update_norms.json", "8.3371"),
    ]
    for rel, needle in checks:
        p = REPO / rel
        if not p.exists():
            print(f"  ⚠️ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        print(f"  {'✅' if needle in t else '🔴'} {rel} 含 {needle}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
