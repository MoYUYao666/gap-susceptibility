# -*- coding: utf-8 -*-
r"""验证 model-coverage 对 `tab:position_strict` R@1 列的三类归因（2026-10-12）。

## 待验证的三条主张

1. **OpenCLIP 行**：ΔCG 来自 `strict_freeze_oclip/r4`（rank4），
   但 R@1 来自 `strict_freeze_openclip`（rank8，n_tr=196,608/491,520/294,912）。
2. **`CLIP B/32 r4 / text_only = 0.621`** 来自**非严格冻结**的
   `outputs/flickr30k_seeds/rq2_text_only`（n_trainable = **145,170,177**）。
3. `CLIP B/32 r4 / both = 0.679` 与 `CLIP B/16 r4 / text_only = 0.651`
   在**全归档里找不到任何来源**。

## 方法

逐条**直接读归档算 5-seed 均值**，不看他人结论。

    python tools\_p325_verify_r1_attribution.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "r1_attribution_verify.json"


def mean_r1(files):
    vals, seeds, nts = [], [], set()
    for f in files:
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        v = (d.get("final_task_metrics") or {}).get("R@1")
        if v is None:
            continue
        vals.append(v)
        seeds.append(d.get("seed"))
        nts.add(d.get("n_trainable_params"))
    return vals, seeds, nts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 104)
    print("主张 ①：OpenCLIP 行 —— ΔCG 与 R@1 是否来自两棵不同的树？")
    print("=" * 104)
    for key in ("strict_freeze_oclip/r4", "strict_freeze_openclip"):
        for arm in ("text_only", "both", "vision_only"):
            files = sorted(glob.glob(str(REPO / "outputs" / key / arm / "seed*" / "results.json")))
            if not files:
                continue
            vals, seeds, nts = mean_r1(files)
            dc = []
            for f in files:
                d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
                fin = (d.get("final_gap") or {}).get("centroid_gap")
                ini = (d.get("initial_gap") or {}).get("centroid_gap")
                if fin is not None and ini is not None:
                    dc.append(fin - ini)
            print(f"  {key:<26} {arm:<12} n={len(vals)} n_tr={sorted(map(str,nts))} "
                  f"seeds={sorted(map(str,seeds))}")
            print(f"      R@1 均值 = {sum(vals)/len(vals):.6f}  ｜ "
                  f"ΔCG 均值 = {(sum(dc)/len(dc) if dc else float('nan')):+.6f}")
            rep[f"{key}/{arm}"] = {
                "n": len(vals), "n_train": sorted(map(str, nts)),
                "seeds": sorted(map(str, seeds)),
                "R1_mean": round(sum(vals) / len(vals), 6) if vals else None,
                "dCG_mean": round(sum(dc) / len(dc), 6) if dc else None,
            }

    print()
    print("论文 OpenCLIP 行：ΔCG +0.0802/+0.0864/+0.0996 ｜ R@1 0.643/0.680/0.672")
    print("  → 若 ΔCG 命中 r4 树 且 R@1 命中 rank8 树，则主张 ① 成立")
    print(f"      r4 树   R@1 = {rep.get('strict_freeze_oclip/r4/text_only',{}).get('R1_mean')} / "
          f"{rep.get('strict_freeze_oclip/r4/both',{}).get('R1_mean')} / "
          f"{rep.get('strict_freeze_oclip/r4/vision_only',{}).get('R1_mean')}")
    print(f"      rank8树 R@1 = {rep.get('strict_freeze_openclip/text_only',{}).get('R1_mean')} / "
          f"{rep.get('strict_freeze_openclip/both',{}).get('R1_mean')} / "
          f"{rep.get('strict_freeze_openclip/vision_only',{}).get('R1_mean')}")

    print()
    print("=" * 104)
    print("主张 ②：CLIP B/32 r4 text_only 的 0.621 是否来自非严格冻结的旧约定？")
    print("=" * 104)
    for key in ("strict_freeze_b32_r4/text_only", "flickr30k_seeds/rq2_text_only"):
        files = sorted(glob.glob(str(REPO / "outputs" / key / "**" / "results.json"),
                                 recursive=True))
        if not files:
            print(f"  ⚠️  {key}: 无文件")
            continue
        vals, seeds, nts = mean_r1(files)
        if not vals:
            continue
        print(f"  {key}")
        print(f"      n={len(vals)} n_tr={sorted(map(str,nts))} seeds={sorted(map(str,seeds))}")
        print(f"      R@1 各值 = {[round(v,4) for v in vals]} → 均值 {sum(vals)/len(vals):.6f}"
              f"  （论文 0.621）")
        rep[key] = {"n": len(vals), "n_train": sorted(map(str, nts)),
                    "R1_values": [round(v, 4) for v in vals],
                    "R1_mean": round(sum(vals) / len(vals), 6)}

    print()
    print("=" * 104)
    print("主张 ③：两格在全归档里是否真的找不到来源？")
    print("=" * 104)
    targets = {"CLIP_B32_r4/both": 0.679, "CLIP_B16_r4/text_only": 0.651}
    # 全归档：按 (目录, n_trainable) 分组
    groups = defaultdict(list)
    allf = glob.glob(str(REPO / "outputs" / "**" / "results.json"), recursive=True)
    print(f"  扫描 {len(allf)} 个 results.json …")
    for f in allf:
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        if "initial_gap" not in d or "final_gap" not in d:
            continue
        v = (d.get("final_task_metrics") or {}).get("R@1")
        if v is None:
            continue
        parts = Path(f).relative_to(REPO).parts[1:-1]
        groups["/".join(parts)].append(v)
    print(f"  得到 {len(groups)} 个 (目录) 组")
    for tgt_name, tgt in targets.items():
        hits = []
        for g, vs in groups.items():
            if len(vs) < 3:
                continue
            m = sum(vs) / len(vs)
            if round(m, 3) == tgt:
                hits.append((g, round(m, 6), len(vs)))
        hits.sort(key=lambda x: abs(x[1] - tgt))
        print(f"\n  {tgt_name}  论文 {tgt}")
        if hits:
            print(f"     🎯 有 {len(hits)} 个组四舍五入命中：")
            for g, m, n in hits[:6]:
                print(f"        {m:.6f}  n={n}  {g}")
        else:
            print("     🔴 无任何组命中（附近最接近的 5 个）：")
            near = sorted(((g, sum(vs) / len(vs), len(vs)) for g, vs in groups.items()
                           if len(vs) >= 3), key=lambda x: abs(x[1] - tgt))[:5]
            for g, m, n in near:
                print(f"        {m:.6f}  n={n}  {g}")
        rep[f"target_{tgt_name}"] = {"published": tgt,
                                     "hits": [{"dir": g, "mean": m, "n": n} for g, m, n in hits[:10]]}

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
