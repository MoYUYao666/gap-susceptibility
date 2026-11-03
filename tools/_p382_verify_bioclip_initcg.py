# -*- coding: utf-8 -*-
r"""核 BioCLIP 的 `initial CG = 1.79` 是否有归档出处（2026-10-12）。

## 我自己的错

审计成员（dinov2-auditor）告诉我 BioCLIP 组 "initial CG 1.79"，
**我没核就转达给了 model-coverage**。对方指出
`outputs/strict_freeze_bioclip/results_partial.json::summary` **没有 initial CG 字段**。

**→ 必须查到出处，否则按项目铁律"无来源的数字一律删除"，我的转达要撤回。**

    python tools\_p382_verify_bioclip_initcg.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "bioclip_initcg_provenance.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 100)
    print("① BioCLIP 归档里所有 `initial` / `cg` 相关字段")
    print("=" * 100)
    found = {}
    for f in glob.glob(str(REPO / "outputs" / "**" / "*bioclip*"), recursive=True) + \
            glob.glob(str(REPO / "outputs" / "**" / "results_partial.json"), recursive=True):
        p = Path(f)
        if not p.is_file():
            continue
        rel = str(p.relative_to(REPO))
        if p.suffix == ".json":
            try:
                d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
            except Exception:
                continue
            print(f"\n  {rel}")
            s = json.dumps(d)
            for m in re.finditer(r'"(initial[^"]*|cg_init[^"]*|initial_cg[^"]*|prev_cg[^"]*)"\s*:\s*([-\d.eE]+)', s):
                print(f"     {m.group(1)} = {m.group(2)}")
            # 直接找 1.79
            for m in re.finditer(r'1\.7\d{1,3}', s):
                i = max(0, m.start() - 90)
                print(f"     ≈1.79 出现: …{s[i:m.start()+40]}…")
        else:
            t = io.open(p, encoding="utf-8", errors="replace").read()
            hits = [m.group(0) for m in re.finditer(r'1\.7\d{1,3}', t)]
            if hits:
                print(f"\n  {rel}（文本）含 1.7x: {hits[:6]}")

    print()
    print("=" * 100)
    print("② 全库搜 1.79 附近与 BioCLIP 同现")
    print("=" * 100)
    n = 0
    for f in glob.glob(str(REPO / "outputs" / "**" / "*.json"), recursive=True):
        if "lit_pool" in f or "claim_ledger" in f:
            continue
        t = io.open(f, encoding="utf-8", errors="replace").read()
        if "1.79" in t and re.search(r"bioclip|bio_clip", t, re.I):
            n += 1
            print(f"  🎯 {Path(f).relative_to(REPO)}")
            if n >= 6:
                break
    if n == 0:
        print("  🔴 无命中")

    print()
    print("=" * 100)
    print("③ 判定")
    print("=" * 100)
    if n == 0:
        print("  🔴 `initial CG = 1.79` **在归档里找不到出处**")
        print("     → 按项目铁律：**我的转达撤回**，且**任何稿/报告不得使用该数字**，")
        print("        除非另行核到（可能在 run_log.txt / 论文 supplement）")
    else:
        print("  ⚠️ 有同现文件，需人工确认是否就是该字段")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"searched": True, "found_179_with_bioclip": n,
             "verdict": "no_source" if n == 0 else "needs_manual_check"},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
