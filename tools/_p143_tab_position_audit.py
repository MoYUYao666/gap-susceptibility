# -*- coding: utf-8 -*-
r"""核对 `tab:position` 的 COCO 行对应哪个秩，并判"加粗 vs 表注"矛盾（2026-10-10）。

## 表里写的（`empirical.tex`）

| Dataset | Text-only | Both | Vision-only |
|---|---|---|---|
| Flickr30k | **−0.064** | −0.032 | −0.003 |
| COCO | **−0.041** | −0.052 | +0.031 |

**但表注说** *"MS-COCO **reverses** that ordering"* → 若真是反转，**COCO 行应加粗 `both`**。

## 本脚本

把归档里**所有** COCO / Flickr30k 的 (rank, arm) 均值与表中数字比对，
找出**每个数字出自哪个秩**，从而判断加粗对不对。

    python tools\_p143_tab_position_audit.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "tab_position_audit.json"

TABLE = {
    "Flickr30k": {"text_only": -0.064, "both": -0.032, "vision_only": -0.003},
    "COCO": {"text_only": -0.041, "both": -0.052, "vision_only": +0.031},
}


def collect(pattern: str):
    out = {}
    for f in sorted(glob.glob(str(REPO / pattern), recursive=True)):
        parts = Path(f).parts
        seed = next((x for x in parts if x.startswith("seed")), "?")
        arm = parts[-3] if len(parts) >= 3 and parts[-2].startswith("seed") else parts[-2]
        rank = parts[-4] if len(parts) >= 4 and parts[-3] == arm else parts[-3]
        d = json.loads(io.open(f, encoding="utf-8").read())
        fg = (d.get("final_gap") or {}).get("centroid_gap")
        ig = (d.get("initial_gap") or {}).get("centroid_gap")
        if fg is None or ig is None:
            continue
        out.setdefault((rank, arm), []).append(fg - ig)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    coco = collect("outputs/coco_sweep/**/results.json")
    coco.update({k: coco[k] for k in coco})
    newc = collect("outputs/coco_sweep_text_only/**/results.json")
    for k, v in newc.items():
        coco.setdefault(k, []).extend(v)

    print("=== COCO 各 (rank, arm) 的 ΔCG 均值 ===")
    means = {}
    for (rank, arm) in sorted(coco, key=lambda k: (int(k[0].lstrip("r")), k[1])):
        xs = coco[(rank, arm)]
        means[(rank, arm)] = st.mean(xs)
        print(f"  {rank:<5} {arm:<12} n={len(xs)}  {st.mean(xs):+.4f}")

    print("\n=== 与表中 COCO 行比对（找匹配的秩）===")
    for arm, target in TABLE["COCO"].items():
        best = None
        for (rank, a2), m in means.items():
            if a2 != arm:
                continue
            d = abs(m - target)
            if best is None or d < best[1]:
                best = (rank, d, m)
        if best:
            print(f"  {arm:<12} 表值 {target:+.4f}  → 最接近: {best[0]}（{best[2]:+.4f}，"
                  f"差 {best[1]:.4f}）{'  ✅ 精确匹配' if best[1] < 0.001 else ''}")

    print("\n=== 矛盾判定（COCO 行）===")
    # 找表值匹配的秩
    matched_rank = None
    for arm in ("text_only",):
        best = min(((r, abs(m - TABLE['COCO'][arm])) for (r, a2), m in means.items()
                    if a2 == arm), key=lambda x: x[1])
        matched_rank = best[0]
    print(f"  COCO 行对应秩: **{matched_rank}**")
    to = means.get((matched_rank, "text_only"))
    bo = means.get((matched_rank, "both"))
    vo = means.get((matched_rank, "vision_only"))
    print(f"    text_only={to:+.4f}  both={bo:+.4f}  vision_only={vo:+.4f}")
    winner = min([("text_only", to), ("both", bo), ("vision_only", vo)], key=lambda x: x[1])
    print(f"    **实际最保护 = {winner[0]}**（{winner[1]:+.4f}）")
    print(f"    表里加粗的是 = text_only")
    if winner[0] == "text_only":
        print("    → ✅ 加粗正确")
    else:
        print(f"    → 🔴 **矛盾**：表注说 COCO 'reverses'（both 更好），实际也是 "
              f"**{winner[0]}** 更好，**但表里加粗的是 text_only**")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps({
            "means": {f"{k[0]}|{k[1]}": round(v, 5) for k, v in means.items()},
            "matched_rank": matched_rank,
            "actual_winner": winner[0], "winner_value": round(winner[1], 5),
            "bold_in_table": "text_only",
            "table_values": TABLE["COCO"],
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
