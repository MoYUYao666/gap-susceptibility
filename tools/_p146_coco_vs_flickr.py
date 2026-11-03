# -*- coding: utf-8 -*-
r"""严格冻结协议下 Flickr30k vs COCO 的位置排序（判"数据集翻转"是否成立）（2026-10-10）。

## 为什么

`tab:position_strict` 只报 CLIP B/32 / OpenCLIP / CLIP B/16，**没有 COCO 行**。
而 COCO 的 `text_only` 我刚补齐（11 run）。

**要回答**：严格冻结协议下，COCO 上谁最保护？与 Flickr30k（`text_only`）是否相反？

    python tools\_p146_coco_vs_flickr.py [--apply]
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


def load(pattern: str, arm_from_path: bool = True):
    out = {}
    for f in sorted(glob.glob(str(REPO / pattern), recursive=True)):
        parts = Path(f).parts
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        fg = (d.get("final_gap") or {}).get("centroid_gap")
        ig = (d.get("initial_gap") or {}).get("centroid_gap")
        r1 = (d.get("final_retrieval") or {}).get("r1")
        if fg is None or ig is None:
            continue
        out.setdefault(("all", "all"), []).append(
            {"file": str(Path(f).relative_to(REPO)), "dcg": fg - ig, "r1": r1})
    return out


def summarise(pattern: str, tag: str, arm: str):
    xs, rs = [], []
    for f in sorted(glob.glob(str(REPO / pattern), recursive=True)):
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
    if not xs:
        print(f"  {tag:<12} {arm:<12} —— 无数据")
        return None
    m = st.mean(xs)
    sd = st.stdev(xs) if len(xs) > 1 else float("nan")
    rr = f"{st.mean(rs):.3f}" if rs else "—"
    print(f"  {tag:<12} {arm:<12} n={len(xs):<3} ΔCG={m:+.4f}"
          + (f" ± {sd:.4f}" if len(xs) > 1 else "") + f" ｜ R@1={rr}")
    return {"n": len(xs), "mean": round(m, 5),
            "sd": round(sd, 5) if len(xs) > 1 else None,
            "r1": round(st.mean(rs), 4) if rs else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    res = {}
    print("=== 严格冻结协议：Flickr30k（r4）===")
    for arm in ("text_only", "both", "vision_only"):
        v = summarise(f"outputs/strict_freeze_b32_r4/{arm}/seed*/results.json",
                      "Flickr30k", arm)
        if v:
            res[f"flickr30k|{arm}"] = v

    print("\n=== 严格冻结协议：COCO（text_only 为新跑，both 取自 coco_sweep）===")
    # COCO text_only：新跑 + 旧的 r4
    xs, rs = [], []
    pats = ["outputs/coco_sweep_text_only/**/results.json",
            "outputs/coco_sweep/r4/text_only/seed*/results.json"]
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
    if xs:
        m = st.mean(xs)
        print(f"  {'COCO':<12} {'text_only':<12} n={len(xs):<3} ΔCG={m:+.4f} ± "
              f"{st.stdev(xs):.4f} ｜ R@1={st.mean(rs):.3f}" if rs else "")
        res["coco|text_only"] = {"n": len(xs), "mean": round(m, 5),
                                 "sd": round(st.stdev(xs), 5),
                                 "r1": round(st.mean(rs), 4) if rs else None}
    for arm in ("both", "vision_only"):
        pats = [f"outputs/coco_sweep/r4/{arm}/seed*/results.json"]
        ys = []
        for p in pats:
            for f in sorted(glob.glob(str(REPO / p), recursive=True)):
                try:
                    d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
                except Exception:
                    continue
                fg = (d.get("final_gap") or {}).get("centroid_gap")
                ig = (d.get("initial_gap") or {}).get("centroid_gap")
                if fg is not None and ig is not None:
                    ys.append(fg - ig)
        if ys:
            m = st.mean(ys)
            print(f"  {'COCO':<12} {arm:<12} n={len(ys):<3} ΔCG={m:+.4f} ± "
                  f"{st.stdev(ys):.4f}")
            res[f"coco|{arm}"] = {"n": len(ys), "mean": round(m, 5),
                                  "sd": round(st.stdev(ys), 5)}

    print("\n=== 判定（r4 同秩对比）===")
    f_to = res.get("flickr30k|text_only", {}).get("mean")
    f_bo = res.get("flickr30k|both", {}).get("mean")
    c_to = res.get("coco|text_only", {}).get("mean")
    c_bo = res.get("coco|both", {}).get("mean")
    print(f"  Flickr30k r4:  text_only={f_to:+.4f}  both={f_bo:+.4f}  "
          f"→ 最保护 **{'text_only' if f_to > f_bo else 'both'}**")
    print(f"  COCO      r4:  text_only={c_to:+.4f}  both={c_bo:+.4f}  "
          f"→ 最保护 **{'text_only' if c_to > c_bo else 'both'}**")
    flip = (f_to > f_bo) and (c_to < c_bo)
    print(f"\n  → 严格冻结下**数据集翻转**: {'✅ 成立' if flip else '❌ 不成立'}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"per_arm": res, "flip_holds": bool(flip),
             "note": "r4 同秩对比；COCO text_only = 新跑 11 run + 旧 r4"},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
