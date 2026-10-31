# -*- coding: utf-8 -*-
r"""`paper合` 进度实测（2026-10-10）。

    python tools\_p138_paperhe_status.py
"""
from __future__ import annotations

import glob
import io
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=str(REPO), shell=True).stdout


def main() -> int:
    print("=" * 70)
    print("① 编译与页数")
    print("=" * 70)
    for m in ("main_springer", "main_nc"):
        pdf = REPO / "paper合" / f"{m}.pdf"
        log = REPO / "paper合" / f"{m}.log"
        pages = "?"
        if pdf.exists():
            o = sh(f'pdfinfo "{pdf}"')
            mm = re.search(r"Pages:\s+(\d+)", o)
            pages = mm.group(1) if mm else "?"
        errs = un = ov = "?"
        if log.exists():
            t = io.open(log, encoding="utf-8", errors="replace").read()
            errs = len(re.findall(r"^!", t, re.M))
            un = len(re.findall(r"(Citation|Reference) .* undefined", t))
            ov = len(re.findall(r"Overfull \\hbox", t))
        print(f"  {m:<16} {pages} 页 ｜ 错误 {errs} ｜ 未定义 {un} ｜ Overfull {ov}")

    print()
    print("=" * 70)
    print("② 门禁")
    print("=" * 70)
    o = subprocess.run([str(Path(r"D:\Anaconda\envs\pytorch\python.exe")),
                        "tools/_claim_ledger.py", "--apply"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(REPO))
    for ln in (o.stdout or "").splitlines():
        if "汇总" in ln or "❌" in ln:
            print("  " + ln.strip()[:110])
    print(f"  退出码: {o.returncode}")

    print()
    print("=" * 70)
    print("③ 数据完整性")
    print("=" * 70)
    for label, root in (("CLIP B/32 r4", "outputs/strict_freeze_b32_r4"),
                        ("CLIP B/16 r4", "outputs/strict_freeze_b16/r4"),
                        ("OpenCLIP r4", "outputs/strict_freeze_oclip/r4")):
        row = []
        for arm in ("text_only", "both", "vision_only"):
            n = len(glob.glob(str(REPO / root / arm / "seed*" / "results.json")))
            row.append(f"{arm}={n}")
        print(f"  {label:<14} " + "  ".join(row))
    print(f"  总 results.json: {len(glob.glob(str(REPO / 'outputs/strict_freeze_*/**/results.json'), recursive=True)) + len(glob.glob(str(REPO / 'outputs/strict_freeze_b32_r4/**/results.json'), recursive=True))}")

    print()
    print("=" * 70)
    print("④ 本次会话做的加固（可核）")
    print("=" * 70)
    items = [
        ("limitation 条目数", "paper合/sections/discussion.tex",
         r"\b(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth),"),
        ("补充材料 A–E 节", "paper合/sections/supplement.tex", r"\\section\*?\{[A-E]\}"),
    ]
    for tag, f, pat in items:
        p = REPO / f
        if p.exists():
            t = io.open(p, encoding="utf-8", errors="replace").read()
            hits = re.findall(pat, t)
            print(f"  {tag:<18} {len(hits)}  {hits[:9] if len(hits) <= 9 else hits[:9]}")
    for f, tag in (("outputs/analysis/dg_pred_bias.json", "dg_pred 偏差"),
                   ("outputs/analysis/alpha_precision.json", "f(DG0) 精度"),
                   ("outputs/analysis/driving_trajectory.json", "驱动项轨迹"),
                   ("outputs/analysis/oclip_effectsize.json", "OpenCLIP 效应量"),
                   ("outputs/analysis/seed_stability.json", "seed 稳定性")):
        p = REPO / f
        print(f"  {tag:<18} {'✅ ' + str(p.stat().st_size) + ' B' if p.exists() else '❌ 缺'}")

    print()
    print("=" * 70)
    print("⑤ COCO 补跑进度")
    print("=" * 70)
    n = len(glob.glob(str(REPO / "outputs/coco_sweep_text_only/**/results.json"), recursive=True))
    print(f"  text_only 新跑: {n}/11")
    log = REPO / "outputs" / "_coco_resume.log"
    if log.exists():
        lines = io.open(log, encoding="utf-8", errors="replace").read().splitlines()
        for ln in lines[-4:]:
            print("  " + ln.strip()[:100])
    old = len(glob.glob(str(REPO / "outputs/coco_sweep/**/results.json"), recursive=True))
    print(f"  旧 sweep（both + text_only 部分）: {old} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
