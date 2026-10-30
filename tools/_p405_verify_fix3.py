# -*- coding: utf-8 -*-
r"""核验 task-7 报告最终版 + 那个"把断言变成穷举"的机器产物（2026-10-12）。

## 待核

1. `docs/PR_FAIRNESS_FIX3.md` 里**全称否定已消失**（`没有极小值` / `No interior minimum` 等）
2. `tools/_p264_fullft_tables.py` 现在**逐点枚举内部极小值**（而非断言不存在）
3. 产物 `pr_fullft_tables.md` T7 与 `pr_fullft_verdict.json` 里有该枚举与 note
4. §5.3 的同类全称否定已改为**写明检索范围**

    python tools\_p405_verify_fix3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REP = REPO / "docs" / "PR_FAIRNESS_FIX3.md"
TBL = REPO / "tools" / "_p264_fullft_tables.py"
T7 = REPO / "outputs" / "analysis" / "pr_fullft_tables.md"
VER = REPO / "outputs" / "analysis" / "pr_fullft_verdict.json"
OUT = REPO / "outputs" / "analysis" / "fix3_verify.json"

BANNED = [r"没有极小值", r"不存在.{0,6}极小值", r"No interior minimum",
          r"不含任何版本记录", r"no version.{0,20}recorded"]
# 允许出现（因为是在说明"该列表为空才可写全称否定"）
ALLOW_CTX = ("只有", "仅当", "only valid when", "list is empty", "穷举")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 96)
    print("① 报告里是否还有全称否定（排除「说明判据」的语境）")
    print("=" * 96)
    if not REP.exists():
        print("  🔴 报告不存在")
        return 1
    t = io.open(REP, encoding="utf-8", errors="replace").read()
    print(f"  字符 {len(t)} ｜ 行 {len(t.splitlines())}")
    hits = []
    for pat in BANNED:
        for m in re.finditer(pat, t):
            ctx = t[max(0, m.start() - 120):m.start() + 160]
            allowed = any(k in ctx for k in ALLOW_CTX)
            hits.append({"pattern": pat, "allowed": allowed,
                         "ctx": " ".join(ctx.split())[:200]})
    real = [h for h in hits if not h["allowed"]]
    for h in hits:
        print(f"  {'（说明判据，允许）' if h['allowed'] else '🔴 仍在'} {h['pattern']}")
        print(f"        …{h['ctx']}…")
    print(f"  → 需处理 {len(real)} 处")
    rep["banned_hits"] = hits

    print()
    print("=" * 96)
    print("② `_p264_fullft_tables.py` 是否逐点穷举内部极小值")
    print("=" * 96)
    if TBL.exists():
        s = io.open(TBL, encoding="utf-8", errors="replace").read()
        for k in ("interior_minima", "margin_to_left", "margin_to_right",
                  "interior_minima_note"):
            print(f"  {'✅' if k in s else '🔴'} 含 {k}")
        rep["script_has_enumeration"] = all(
            k in s for k in ("interior_minima", "interior_minima_note"))
    else:
        print("  🔴 脚本不存在")
        rep["script_has_enumeration"] = False

    print()
    print("=" * 96)
    print("③ 产物里的枚举结果")
    print("=" * 96)
    if VER.exists():
        d = json.loads(io.open(VER, encoding="utf-8", errors="replace").read())
        sh = d.get("shape") or {}
        im = sh.get("interior_minima_functional_regime")
        note = sh.get("interior_minima_note")
        print(f"  interior_minima_functional_regime = {json.dumps(im, ensure_ascii=False)}")
        print(f"  interior_minima_note = {note}")
        rep["interior_minima"] = im
        rep["note"] = note
    else:
        print("  ⚠️ 无 verdict 文件")
    if T7.exists():
        s = io.open(T7, encoding="utf-8", errors="replace").read()
        print(f"  表文件 T7 段含 interior_minima: {'interior_minima' in s}")

    print()
    print("=" * 96)
    print("④ §5.3 的版本记录否定是否已限定检索范围")
    print("=" * 96)
    for pat in (r"13", r"0 命中", r"undetermined|未定"):
        n = len(re.findall(pat, t))
        print(f"  {pat:<28} 出现 {n} 次")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0 if not real else 2


if __name__ == "__main__":
    raise SystemExit(main())
