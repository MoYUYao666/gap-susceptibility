# -*- coding: utf-8 -*-
r"""严格冻结协议下的数据集对比（**修正符号约定**）（2026-10-10）。

## 我上一版的错

ΔCG = 训练后 CG − 初始 CG。**越负 = 间隙收缩越多 = 越保护。**
我上一版写成"越大越保护"→ 判定反了。

**核对**：`tab:position_strict` 里 Flickr30k r4 是
`text_only=-0.0288`（**加粗**）｜`both=-0.0188`｜`vision_only=+0.0127`
→ 确认 **加粗的是最小（最负）值** → **越负越保护** ✅

    python tools\_p147_flip_corrected.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "dataset_flip_strict.json"


def gather(pats):
    xs, rs, files = [], [], []
    for p in pats:
        for f in sorted(glob.glob(str(REPO / p), recursive=True)):
            try:
                d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            except Exception:
                continue
            fg = (d.get("final_gap") or {}).get("centroid_gap")
            ig = (d.get("initial_gap") or {}).get("centroid_gap")
            if fg is None or ig is None:
                continue
            xs.append(fg - ig)
            r = (d.get("final_retrieval") or {}).get("r1")
            if r is not None:
                rs.append(r)
            files.append(str(Path(f).relative_to(REPO)))
    return xs, rs, files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # **只取新跑**（batch 128，5 seed）——与论文其它秩（r2/r8/r32/r64）同口径
    COCO = {"text_only": ["outputs/coco_sweep_text_only/r4/text_only/seed*/results.json"],
            "both": ["outputs/coco_sweep/r4/both/seed*/results.json"]}
    FLICK = {arm: [f"outputs/strict_freeze_b32_r4/{arm}/seed*/results.json"]
             for arm in ("text_only", "both", "vision_only")}

    res, lines = {}, []
    print("=== 同秩（r4）严格冻结对比 — **ΔCG 越负越保护** ===")
    for tag, spec in (("Flickr30k", FLICK), ("COCO", COCO)):
        for arm, pats in spec.items():
            xs, rs, files = gather(pats)
            if not xs:
                continue
            m = st.mean(xs)
            sd = st.stdev(xs) if len(xs) > 1 else None
            res[f"{tag}|{arm}"] = {"n": len(xs), "mean": round(m, 5),
                                   "sd": round(sd, 5) if sd else None,
                                   "r1": round(st.mean(rs), 4) if rs else None,
                                   "files": files}
            print(f"  {tag:<11} {arm:<12} n={len(xs):<2} ΔCG={m:+.4f}"
                  + (f" ± {sd:.4f}" if sd else "")
                  + (f" ｜ R@1={st.mean(rs):.3f}" if rs else ""))

    print("\n=== 判定 ===")
    verdict = {}
    for tag in ("Flickr30k", "COCO"):
        to = res.get(f"{tag}|text_only", {}).get("mean")
        bo = res.get(f"{tag}|both", {}).get("mean")
        if to is None or bo is None:
            print(f"  {tag}: 数据不全（text_only={to}, both={bo}）")
            continue
        # 越负越保护 → 取 min
        best = "text_only" if to < bo else "both"
        verdict[tag] = {"best": best, "text_only": to, "both": bo,
                        "margin": round(abs(to - bo), 5)}
        print(f"  {tag:<11} text_only={to:+.4f} ｜ both={bo:+.4f}  → 最保护 **{best}**"
              f"（差 {abs(to-b, ):.4f}）" if False else
              f"  {tag:<11} text_only={to:+.4f} ｜ both={bo:+.4f}  → 最保护 **{best}**"
              f"（差 {abs(to - bo):.4f}）")

    flip = (verdict.get("Flickr30k", {}).get("best") == "text_only"
            and verdict.get("COCO", {}).get("best") == "both")
    print(f"\n  → 严格冻结下 r4 的**数据集翻转**: {'✅ 成立' if flip else '❌ 不成立'}")

    print("\n=== 全秩趋势（COCO text_only，新跑）===")
    for rank in ("r2", "r8", "r32", "r64"):
        xs, _, _ = gather([f"outputs/coco_sweep_text_only/{rank}/text_only/seed*/results.json"])
        if xs:
            print(f"  {rank:<5} n={len(xs)}  ΔCG={st.mean(xs):+.4f} ± {st.stdev(xs):.4f}")
    print("\n=== 全秩趋势（COCO both，旧 sweep）===")
    for rank in ("r1", "r2", "r4", "r16", "r32", "r64"):
        xs, _, _ = gather([f"outputs/coco_sweep/{rank}/both/seed*/results.json"])
        if xs:
            print(f"  {rank:<5} n={len(xs)}  ΔCG={st.mean(xs):+.4f} ± {st.stdev(xs):.4f}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"r4": res, "verdict": verdict, "flip_holds_r4": bool(flip),
             "convention": "ΔCG 越负越保护"},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
