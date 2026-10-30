# -*- coding: utf-8 -*-
r"""重算全部表格（批次统一 128 后 + 5 seed）（2026-10-11）。

## 要重算的三张表

| # | 表 | 内容 |
|---|---|---|
| 1 | `tab:position_strict` | 三骨干 × 三臂，**5 seed 均值 ± sd** |
| 2 | "数据集翻转"段 | COCO vs Flickr30k，**同秩同批次** |
| 3 | `tab:vlm` | 解码器 VLM，**13 seed** |

## 另算

- **OpenCLIP 效应量**（批次修正后，本会话先前算的 $0.52/0.55$ sd 基于混批次数据）

    python tools\_p175_recompute_all.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "recomputed_tables.json"


def load(pattern: str, want_batch: int = 128):
    """返回 {(arm, rank): [ΔCG, ...]}"""
    out = {}
    for f in sorted(glob.glob(str(REPO / pattern), recursive=True)):
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        if d.get("batch_size") != want_batch:
            continue
        fg = (d.get("final_gap") or {}).get("centroid_gap")
        ig = (d.get("initial_gap") or {}).get("centroid_gap")
        if fg is None or ig is None:
            continue
        p = Path(f).parts
        arm = next((x for x in p if x in ("text_only", "both", "vision_only")), "?")
        rank = next((x for x in p if x and x[0] == "r" and x[1:].isdigit()), None)
        if rank is None:
            # 组名里带 rank 的形式（如 strict_freeze_b32_r4 → r4）
            import re as _re
            m = None
            for seg in p:
                m = _re.search(r"_r(\d+)$", seg)
                if m:
                    rank = "r" + m.group(1)
                    break
            if rank is None:
                rank = "r4"      # 该组只有 r4 一种配置
        out.setdefault((arm, rank), []).append(fg - ig)
    return out


def stat(vals):
    n = len(vals)
    return {"n": n, "mean": round(st.mean(vals), 5),
            "sd": round(st.stdev(vals), 5) if n > 1 else None,
            "vals": [round(v, 5) for v in vals]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    res = {}

    # ── ① 严格冻结三骨干（r4，5 seed）──
    print("=" * 82)
    print("① tab:position_strict ｜ 三骨干 × 三臂（batch 128，n=5）")
    print("=" * 82)
    t1 = {}
    for label, pat in (("CLIP B/32 (WIT)", "outputs/strict_freeze_b32_r4/**/results.json"),
                       ("CLIP B/16 (WIT)", "outputs/strict_freeze_b16/r4/**/results.json"),
                       ("OpenCLIP B/32 (LAION)", "outputs/strict_freeze_oclip/r4/**/results.json")):
        d = load(pat)
        row = {}
        for arm in ("text_only", "both", "vision_only"):
            v = d.get((arm, "r4"), [])
            if v:
                row[arm] = stat(v)
        t1[label] = row
        print(f"\n  {label}")
        for arm in ("text_only", "both", "vision_only"):
            if arm in row:
                s = row[arm]
                print(f"    {arm:<12} n={s['n']}  ΔCG = {s['mean']:+.4f}"
                      + (f" ± {s['sd']:.4f}" if s['sd'] else "")
                      + f"   {s['vals']}")
        # 最保护 = 最负
        if row:
            best = min(row, key=lambda k: row[k]["mean"])
            print(f"    → 最保护: **{best}**")
    res["position_strict"] = t1

    # ── ② 数据集翻转（同秩同批次）──
    print()
    print("=" * 82)
    print("② 数据集翻转 ｜ Flickr30k vs COCO（batch 128，同秩对比）")
    print("=" * 82)
    fl = load("outputs/strict_freeze_b32_r4/**/results.json")
    co_to = load("outputs/coco_sweep_text_only/**/results.json")
    co_bo = load("outputs/coco_sweep/**/results.json")
    t2 = {}
    for rank in ("r2", "r4", "r8", "r16", "r32", "r64"):
        row = {}
        if (("text_only", rank) in fl):
            row["flickr|text_only"] = stat(fl[("text_only", rank)])
        if (("both", rank) in fl):
            row["flickr|both"] = stat(fl[("both", rank)])
        if (("text_only", rank) in co_to):
            row["coco|text_only"] = stat(co_to[("text_only", rank)])
        for src, tag in ((co_bo, "coco_old"),):
            if (("both", rank) in src):
                row["coco|both"] = stat(src[("both", rank)])
            if (("text_only", rank) in src) and "coco|text_only" not in row:
                row["coco|text_only"] = stat(src[("text_only", rank)])
        if row:
            t2[rank] = row
    for rank in sorted(t2, key=lambda x: int(x[1:])):
        row = t2[rank]
        parts = []
        for k in ("flickr|text_only", "flickr|both", "coco|text_only", "coco|both"):
            if k in row:
                s = row[k]
                parts.append(f"{k.split('|')[1]}({k.split('|')[0][:4]})={s['mean']:+.4f}"
                             + (f"±{s['sd']:.4f}" if s['sd'] else ""))
        if parts:
            print(f"  {rank:<5} " + " ｜ ".join(parts))
    res["dataset_flip"] = t2

    # ── ③ VLM（13 seed）──
    print()
    print("=" * 82)
    print("③ tab:vlm ｜ 解码器 VLM（bf16，13 seed）")
    print("=" * 82)
    vp = REPO / "outputs" / "analysis" / "vlm_bf16_detail.json"
    if vp.exists():
        vd = json.loads(io.open(vp, encoding="utf-8").read())
        for arm in ("text_only", "vision_only", "both"):
            s = vd["summary"].get(arm)
            if s:
                print(f"  {arm:<12} n={s['n']}  DG* 相对变化 {s['dg_rel_mean']:+.1f}%"
                      f" ± {s['dg_rel_sd']:.1f}  范围 {min(s['dg_rel'])}–{max(s['dg_rel'])}"
                      f" ｜ CG {s['cg_mean']:.4f} ± {s['cg_sd']:.4f}")
        res["vlm"] = vd["summary"]

    # ── ④ OpenCLIP 效应量（批次修正后）──
    print()
    print("=" * 82)
    print("④ OpenCLIP 效应量（批次修正后重算）")
    print("=" * 82)
    oc = load("outputs/strict_freeze_oclip/r4/**/results.json")
    t4 = {}
    for arm in ("text_only", "both", "vision_only"):
        v = oc.get((arm, "r4"), [])
        if v:
            t4[arm] = stat(v)
    if len(t4) >= 2:
        order = sorted(t4, key=lambda k: t4[k]["mean"])
        print("  由保护强到弱：" + " < ".join(f"{k}({t4[k]['mean']:+.4f})" for k in order))
        for i in range(len(order) - 1):
            a1, a2 = order[i], order[i + 1]
            diff = abs(t4[a1]["mean"] - t4[a2]["mean"])
            s1, s2 = t4[a1]["sd"], t4[a2]["sd"]
            if s1 and s2:
                psd = (s1 ** 2 + s2 ** 2) ** 0.5
                k = diff / psd if psd else float("nan")
                print(f"    {a1} vs {a2}: |Δ|={diff:.4f} pooled_sd={psd:.4f} → "
                      f"**{k:.2f} sd**")
    res["oclip_effectsize"] = t4

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
