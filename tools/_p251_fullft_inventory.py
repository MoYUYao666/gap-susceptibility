# -*- coding: utf-8 -*-
r"""查 `outputs/` 里全量微调（full fine-tuning）的既有结果（供 R1.6）（2026-10-12）。

## 为什么先查

R1.6 要求"全量微调的 lr 扫描"。但**先要看仓库里已有什么**——
也许已有多个 lr 的 full-FT 结果，那就**不必重新训练**（8 GB 显存跑 full-FT 有风险）。

    python tools\_p251_fullft_inventory.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "fullft_inventory.json"


def peek(f):
    try:
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
    except Exception:
        return None
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 96)
    print("① 文件/目录名含 full / fullft / full_ft 的归档")
    print("=" * 96)
    hits = []
    for pat in ("outputs/**/*full*", "outputs/**/*ft*", "outputs/**/*finetune*"):
        for f in sorted(glob.glob(str(REPO / pat), recursive=True)):
            p = Path(f)
            if p.is_dir():
                continue
            hits.append(p)
    seen = set()
    for p in hits:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        print(f"  {p.relative_to(REPO)}  ({p.stat().st_size:,} B)")

    print()
    print("=" * 96)
    print("② JSON 里含 'full' 键或 lr 字段的记录")
    print("=" * 96)
    found = []
    for f in sorted(glob.glob(str(REPO / "outputs" / "**" / "*.json"), recursive=True)):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        if re.search(r"full[_ -]?(fine|ft)|fullft", t, re.I):
            rel = str(Path(f).relative_to(REPO))
            found.append(rel)
            print(f"  {rel}")
    print(f"  → 共 {len(found)} 个")

    print()
    print("=" * 96)
    print("③ 是否有「多个学习率」的痕迹")
    print("=" * 96)
    lr_files = []
    for f in sorted(glob.glob(str(REPO / "outputs" / "**" / "*.json"), recursive=True)):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        lrs = set(re.findall(r'"(?:lr|learning_rate)"\s*:\s*([0-9.eE+-]+)', t))
        if len(lrs) >= 3:
            lr_files.append((str(Path(f).relative_to(REPO)), sorted(lrs)))
    for rel, lrs in lr_files[:15]:
        print(f"  {rel}\n      lr 值: {lrs}")
    if not lr_files:
        print("  🔴 没有含 ≥3 个不同 lr 的归档")

    print()
    print("=" * 96)
    print("④ 结论")
    print("=" * 96)
    if lr_files:
        print("  → 已有多个 lr 的归档，**可能不必重新训练**（需确认是否 full-FT）")
    else:
        print("  → **没有**多 lr 归档 → 若要回应 R1.6，需真训练（8 GB 显存跑 full-FT 有风险）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"full_files": [str(p.relative_to(REPO)) for p in seen],
             "json_with_full": found,
             "lr_files": [{"file": r, "lrs": l} for r, l in lr_files]},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
