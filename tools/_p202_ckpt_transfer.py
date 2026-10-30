# -*- coding: utf-8 -*-
r"""核实 `sec:ckpt_transfer` 里"τ 早期下降 1.00→0.75"的归档出处（2026-10-12）。

## 为什么

新标题主打 *"Zero-Overhead Monitor"*。若正文已有"**τ 比 top-1 更早动作**"的实证，
那这个卖点就是**有支撑的**；但必须能指到具体归档文件（本项目唯一原则）。

    python tools\_p202_ckpt_transfer.py [--apply]
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
MAIN = REPO / "paper_a1" / "main.tex"
OUT = REPO / "outputs" / "analysis" / "a1_ckpt_transfer.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8", errors="replace").read()

    print("=" * 86)
    print("① 论文里 `sec:ckpt_transfer` 的全文")
    print("=" * 86)
    i = t.find("sec:ckpt_transfer")
    if i < 0:
        print("  ❌ 未找到")
    else:
        s = t.rfind("\\subsection", 0, i)
        e = t.find("\\subsection", i + 10)
        seg = t[s if s > 0 else max(0, i - 900):e if e > 0 else i + 2200]
        print(" ".join(seg.split())[:2400])

    print()
    print("=" * 86)
    print("② 该段是否指名归档文件")
    print("=" * 86)
    for m in re.finditer(r"Section~\\ref\{sec:ckpt_transfer\}", t):
        s = " ".join(t[max(0, m.start() - 250):m.start() + 250].split())
        print(f"   …{s[:480]}…")
    # 找数字 0.75 / 58.5 的出处线索
    print()
    print("=" * 86)
    print("③ 搜 0.75 / 58.5 / epoch 3 的归档出处")
    print("=" * 86)
    pats = [r"0\.75", r"58\.5"]
    for p in pats:
        print(f"  ── 「{p}」在 outputs/ 里 ──")
        n = 0
        for f in sorted(glob.glob(str(REPO / "outputs" / "**" / "*.json"), recursive=True)):
            txt = io.open(f, encoding="utf-8", errors="replace").read()
            if re.search(p, txt):
                n += 1
                if n <= 6:
                    print("     " + str(Path(f).relative_to(REPO)))
        print(f"     共 {n} 个文件含此串")

    print()
    print("=" * 86)
    print("④ 含逐 epoch tau 的文件（早停演示的数据基础）")
    print("=" * 86)
    fs = sorted(glob.glob(str(REPO / "outputs" / "a1_class_aligned" / "*" / "seed*"
                                 / "eval_epoch*.json")))
    print(f"  outputs/a1_class_aligned/*/seed*/eval_epoch*.json: {len(fs)} 个")
    if fs:
        d = json.loads(io.open(fs[0], encoding="utf-8", errors="replace").read())
        print(f"  示例 {Path(fs[0]).relative_to(REPO)}:")
        print("    " + json.dumps(d, ensure_ascii=False)[:300])
    other = sorted(glob.glob(str(REPO / "outputs" / "**" / "*epoch*.json"), recursive=True))
    print(f"\n  全 outputs 里含 'epoch' 的 json: {len(other)} 个")
    for f in other[:10]:
        print("     " + str(Path(f).relative_to(REPO)))

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"ckpt_transfer_section_found": i >= 0,
             "per_epoch_files": len(fs)}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
