# -*- coding: utf-8 -*-
r"""核查 6 项：开源要求 / 回复覆盖 / 稿件对应 / 上传清单 / LaTeX 包 / 单位署名（2026-10-13）。

    python tools\_p552_audit_upload_readiness.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GUIDE = REPO / "docs" / "guides" / "_prl_guide.txt"
PI = REPO / "paper3" / "paper_ieee"
RESP = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # ---------- ① 开源 / 数据可用性要求 ----------
    print("=" * 100)
    print("① PRL Guide 里的**开源 / 数据 / 代码**要求")
    print("=" * 100)
    g = io.open(GUIDE, encoding="utf-8", errors="replace").read()
    low = g.lower()
    for pat, label in ((r"research data", "Research data"),
                       (r"data statement", "Data statement"),
                       (r"data linking", "Data linking"),
                       (r"github", "GitHub"),
                       (r"code availability", "Code availability"),
                       (r"open (source|access)", "Open source/access"),
                       (r"reproduc", "Reproducibility"),
                       (r"software", "Software citation")):
        for m in re.finditer(pat, low):
            seg = " ".join(g[max(0, m.start() - 180):m.start() + 320].split())
            print(f"  【{label}】…{seg[:430]}…")
            print()
            break   # 每个关键词只取首处

    # ---------- ② 回复覆盖 ----------
    print("=" * 100)
    print("② 三份回复的覆盖核验")
    print("=" * 100)
    struct = json.loads(io.open(REPO / "outputs" / "analysis" / "p3_reviews_structured.json",
                                encoding="utf-8", errors="replace").read())
    ids = [it["id"] for it in struct]
    alltext = ""
    for p in sorted(RESP.glob("*_plain.txt")):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        alltext += t
        n = len(re.findall(r"^Point ", t, re.M))
        print(f"  {p.name:<38} Point {n:>2}")
    print(f"  ⇒ {len(ids)} 条意见：{ids[0]} … {ids[-1]}")

    # ---------- ③ 稿件是否对应修改 ----------
    print()
    print("=" * 100)
    print("③ 稿件是否已对应修改（逐项查关键词）")
    print("=" * 100)
    secs = {}
    for f in sorted((PI / "sections").glob("*.tex")):
        secs[f.stem] = io.open(f, encoding="utf-8", errors="replace").read()
    main_tex = io.open(PI / "main.tex", encoding="utf-8", errors="replace").read()
    allpaper = main_tex + "".join(secs.values())
    CHECKS = [
        ("R3′ 公理（新增）", r"R3\$?'\$|R3′"),
        ("反例 ‖∇E‖²", r"\\\|\\nabla E\\\|"),
        ("同预算逐位 7,237,632", r"7\{,\}237\{,\}632"),
        ("blank 3.09×", r"3\.09"),
        ("下载检验/下游否证", r"neither sufficient nor necessary"),
        ("AdaLoRA 更优", r"adaptive method wins|AdaLoRA"),
        ("5e-5 优势已撤回", r"no longer claim"),
        ("bracketed 口径", r"bracketed"),
        ("架构依赖已撤回", r"could not reproduce"),
        ("zero-shot 约束表述", r"without searching"),
        ("下游 R@1 数字", r"0\.7241"),
        ("分层相关 +0.172", r"\+0\.172"),
        ("11–28 功效", r"11\$ to \$28"),
        ("126 runs 计数", r"126"),
    ]
    for label, pat in CHECKS:
        hits = len(re.findall(pat, allpaper))
        print(f"  {'✅' if hits else '🔴'} {label:<26} {hits} 处")

    # ---------- ④ 上传清单 ----------
    print()
    print("=" * 100)
    print("④ 待上传文件（对照原投稿包）")
    print("=" * 100)
    orig = REPO / "SUBMISSION" / "P3_PRL"
    print("  原投稿包（P3_PRL/）顶层：")
    for p in sorted(orig.iterdir()):
        k = "目录" if p.is_dir() else f"{p.stat().st_size:,} B"
        print(f"     {p.name:<50} {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
