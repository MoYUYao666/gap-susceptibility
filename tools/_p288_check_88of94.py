# -*- coding: utf-8 -*-
r"""核 `88 of 94`（停止规则 vs 训练到收敛）是否存在归档（2026-10-12）。

**项目铁律**：无来源的数字一律删除。

    python tools\_p288_check_88of94.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "stopping_rule_provenance.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 92)
    print("① 找含「停止规则 / stopping rule」的归档")
    print("=" * 92)
    cands = []
    for f in glob.glob(str(REPO / "outputs" / "**" / "*.json"), recursive=True):
        if "lit_pool" in f or "claim_ledger" in f or "audit" in f:
            continue
        t = io.open(f, encoding="utf-8", errors="replace").read()
        if re.search(r"stopping|stop_rule|early_stop|plateau", t, re.I):
            cands.append(f)
    for f in cands[:16]:
        print("  " + str(Path(f).relative_to(REPO)))
    print(f"  → 共 {len(cands)} 个")

    print()
    print("=" * 92)
    print("② 在这些文件里找 88 / 94 / 0.936（88/94）")
    print("=" * 92)
    found = []
    for f in cands:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for pat in (r"\b88\b", r"\b94\b", r"0\.9362", r"0\.936"):
            for m in re.finditer(pat, t):
                found.append((str(Path(f).relative_to(REPO)), m.group(0),
                              " ".join(t[max(0, m.start() - 70):m.start() + 50].split())))
    if found:
        for rel, v, ctx in found[:14]:
            print(f"  {rel:<52} {v:>6}  …{ctx[:90]}…")
    else:
        print("  🔴 无命中")
    print(f"  → 共 {len(found)} 处")

    print()
    print("=" * 92)
    print("③ 判定")
    print("=" * 92)
    if not found:
        print("  🔴 `88 of 94` **在归档里找不到来源**")
        print("     → 按项目铁律：**删除该数字**，保留定性陈述（或改写为可核对的形式）")
    else:
        print("  ⚠️ 有命中——需人工判断是否就是该统计量")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"candidate_files": [str(Path(f).relative_to(REPO)) for f in cands],
             "hits": [{"file": r, "value": v, "context": c} for r, v, c in found]},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
