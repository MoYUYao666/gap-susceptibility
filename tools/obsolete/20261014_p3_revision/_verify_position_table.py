# -*- coding: utf-8 -*-
r"""核对论文 `tab:position_strict` 的每一个数字（可复现原则，2026-10-08 07:40）。

## 为什么

论文表的 caption 声明：*"every patch-32 backbone puts text-only smallest and **every patch-16
backbone puts both there**"*。**③b 实测 CLIP B/16 给出 text_only 最小** → **需立刻核对全表**，
确认是"规律错了"还是"我读错了表"。

同时：我 ③a 实测 OpenCLIP text_only = **+0.0798**，论文写 **+0.0694** → **必须查清差异**
（5-seed 均值 vs 单 seed？不同 rank？）

## 判据

论文每个数字都必须能在**指定归档路径**复算出来（相对容差 0.5%）。
**不能复算的，就是要处理的无来源数字。**

    python tools\_verify_position_table.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "position_table_verification.json"

# 论文表格值（empirical.tex tab:position_strict）
PAPER = {
    "CLIP B/32":     {"patch": 32, "text_only": -0.0465, "both": -0.0258, "vision_only": +0.0106},
    "OpenCLIP B/32": {"patch": 32, "text_only": +0.0694, "both": +0.0881, "vision_only": +0.0925},
    "SigLIP B/16":   {"patch": 16, "text_only": +0.0664, "both": -0.0114, "vision_only": +0.0522},
    "BioCLIP B/16":  {"patch": 16, "text_only": -0.3671, "both": -0.4515, "vision_only": -0.2927},
}

ARCHIVE = {
    "CLIP B/32":     "outputs/strict_freeze",
    "OpenCLIP B/32": "outputs/strict_freeze_openclip",
    "SigLIP B/16":   "outputs/siglip",
    "BioCLIP B/16":  "outputs/strict_freeze_bioclip",
}


def cg_delta(f: Path) -> float | None:
    try:
        d = json.loads(io.open(f, encoding="utf-8").read())
    except Exception:
        return None
    g = d.get("initial_gap", {}).get("centroid_gap") if isinstance(d.get("initial_gap"), dict) else None
    h = d.get("final_gap", {}).get("centroid_gap") if isinstance(d.get("final_gap"), dict) else None
    if g is None or h is None:
        return None
    return h - g


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== 逐个复算论文表格值 ===")
    report = {}
    bad = 0
    for name, paper in PAPER.items():
        root = REPO / ARCHIVE[name]
        print(f"\n  ── {name}（归档 {ARCHIVE[name]}）──")
        if not root.exists():
            print("     ❌ 归档目录不存在")
            report[name] = {"archive": ARCHIVE[name], "exists": False}
            bad += 1
            continue
        rec = {"archive": ARCHIVE[name], "patch": paper["patch"], "arms": {}}
        for arm in ("text_only", "both", "vision_only"):
            files = glob.glob(str(root / "**" / arm / "seed*" / "results.json"), recursive=True)
            vals = [v for v in (cg_delta(Path(f)) for f in files) if v is not None]
            if not vals:
                print(f"     {arm:<12} 无归档 run")
                rec["arms"][arm] = {"paper": paper[arm], "n": 0}
                bad += 1
                continue
            m = st.mean(vals)
            ok = abs(m - paper[arm]) <= max(0.0005, abs(paper[arm]) * 0.005)
            bad += not ok
            print(f"     {arm:<12} 论文 {paper[arm]:+.4f} ｜ 归档均值 {m:+.4f}（n={len(vals)}）"
                  f" ｜ {'✅' if ok else '❌'}")
            rec["arms"][arm] = {"paper": paper[arm], "computed": round(m, 6), "n": len(vals),
                                "pass": bool(ok), "values": [round(v, 5) for v in vals]}
        # 最保护臂判定
        if all(rec["arms"][a].get("computed") is not None for a in rec["arms"]):
            best = min(("text_only", "both", "vision_only"), key=lambda a: rec["arms"][a]["computed"])
            rec["most_protective"] = best
            print(f"     → 最保护臂 = {best}")

    print("\n  === 规律检验（论文措辞）===")
    print("     论文：patch-32 → text_only 最小；patch-16 → both 最小")
    for name, rec in report.items():
        if "most_protective" not in rec:
            continue
        p = rec["patch"]
        expect = "text_only" if p == 32 else "both"
        got = rec["most_protective"]
        print(f"     {name:<16} patch={p:<3} 预期 {expect:<10} 实测 {got:<10} "
              f"{'✅' if got == expect else '❌ 违反规律'}")

    print(f"\n  === 结论 ===\n     复算失败 {bad} 项")
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print(f"     ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
