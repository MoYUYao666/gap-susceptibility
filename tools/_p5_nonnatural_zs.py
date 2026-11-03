# -*- coding: utf-8 -*-
r"""实验 ⑥（选项 A，**零 GPU**）：非自然图像域上"gap 变化小 ⇒ 零样本保持更好"是否成立（2026-10-07）。

## 动机

论文的零样本结论（`fig12` / `empirical.tex`）建立在 **Flickr30k 微调 → DTD/Food101 零样本**上，
而严格冻结对照三臂的 **gap 变化**测量在 **CLIP B/32 + Flickr30k** 上。
**两者从未配对分析过**：论文说"text-only 保持对齐"，但**没有量化"保持对齐"是否真的转化为
"零样本保持更好"**——而这正是 DG 作为"健康信号"的**外部效度**检验。

审稿人会问：**"你说 gap 是健康信号，那 gap 小的臂在别的域上真的更好吗？"**

## 数据（均已在盘，无需 GPU）

| 来源 | 内容 |
|---|---|
| `outputs/analysis/strict_control_summary.json` | 严格冻结三臂的 **CGΔ / DGΔ** |
| `outputs/dtd_food101_zs_check.json` | DTD(1880,47类) / Food101(25250,101类) 三臂零样本 |
| `outputs/zeroshot_extra.json` | 同上（另一套模板/协议） |

## 检验

**H1**：三臂中 **gap 变化最小**的臂，在 DTD/Food101 上零样本**保持最好**（相对 frozen 的损失最小）。
**H2**：跨两个数据集与该两套零样本协议，**排序是否稳定**。

    python tools\_p5_nonnatural_zs.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "nonnatural_zs_check.json"

ARMS = ("text_only", "both", "vision_only")
LABEL = {"text_only": "Text-only", "both": "Both", "vision_only": "Vision-only"}
# 零样本文件里的 arm 名
ZS_KEY = {"text_only": "text_only_r8", "both": "both_r8", "vision_only": "vision_only_r8"}
ZS_KEY2 = {"text_only": "Text-only", "both": "Both", "vision_only": "Vision-only"}


def main() -> int:
    apply = "--apply" in sys.argv

    sc = json.loads(io.open(REPO / "outputs/analysis/strict_control_summary.json",
                            encoding="utf-8").read())
    zs1 = json.loads(io.open(REPO / "outputs/dtd_food101_zs_check.json",
                             encoding="utf-8").read())["results"]
    zs2 = json.loads(io.open(REPO / "outputs/zeroshot_extra.json", encoding="utf-8").read())

    print("  === 严格冻结三臂的 gap 变化（CLIP B/32, Flickr30k）===")
    print(f"  {'臂':<14} {'CGΔ':>9} {'|CGΔ| 排序':>11} {'DG 有效秩Δ(vis)':>16}")
    order = []
    for a in ARMS:
        c = sc["configs"][a]
        order.append((a, c["cg_delta_mean"], c["vision_rank_delta_mean"]))
    for rank, (a, cg, dv) in enumerate(sorted(order, key=lambda x: abs(x[1])), 1):
        print(f"  {LABEL[a]:<14} {cg:>+9.4f} {rank:>11} {dv:>+16.4f}")
    best_gap = min(order, key=lambda x: abs(x[1]))[0]
    print(f"  → gap 变化最小的臂: **{LABEL[best_gap]}**")

    print("\n  === 零样本（相对 frozen 的损失，单位：百分点）===")
    rows = {}
    for name, res, keymap in (("dtd_food101_zs_check", zs1, ZS_KEY),
                              ("zeroshot_extra", zs2, ZS_KEY2)):
        for ds in ("DTD", "Food101"):
            if ds not in res:
                continue
            r = res[ds]
            # 找 frozen
            frozen = None
            for k in ("frozen", "Frozen"):
                if k in r:
                    frozen = r[k]
                    break
            if frozen is None:
                continue
            line = []
            for a in ARMS:
                k = keymap[a]
                if k in r:
                    line.append((a, r[k] - frozen))
            rows[(name, ds)] = line
            print(f"  [{name}] {ds:<9} frozen={frozen:.2f}  ｜ " +
                  " ｜ ".join(f"{LABEL[a]} {d:+.2f}" for a, d in line))

    print("\n  === H1：gap 变化最小的臂是否零样本保持最好 ===")
    hits = miss = 0
    for key, line in rows.items():
        if not line:
            continue
        best_zs = max(line, key=lambda x: x[1])[0]   # 损失最小（最接近 0）
        ok = (best_zs == best_gap)
        hits += ok
        miss += not ok
        print(f"  {key[0][:22]:<24} {key[1]:<9} 零样本最优={LABEL[best_zs]:<12} "
              f"gap 最优={LABEL[best_gap]:<12} {'✅ 一致' if ok else '❌ 不一致'}")
    print(f"\n  一致 {hits}/{hits+miss}")

    print("\n  === H2：排序是否跨数据集/协议稳定 ===")
    print("  各条件下按零样本损失从小到大:")
    sigs = []
    for key, line in rows.items():
        s = tuple(a for a, _ in sorted(line, key=lambda x: -x[1]))
        sigs.append(s)
        print(f"    {key[0][:22]:<24} {key[1]:<9} {' > '.join(LABEL[a] for a in s)}")
    print(f"  不同排序数: {len(set(sigs))}/{len(sigs)} "
          f"{'✅ 稳定' if len(set(sigs)) == 1 else '⚠ 存在差异'}")

    print("\n  === 结论 ===")
    if hits == hits + miss:
        print("    ✅ **支持**：gap 变化最小的臂在非自然图像域上零样本保持最好（全部条件一致）")
    elif hits == 0:
        print("    ❌ **不支持**：零样本最优臂与 gap 最优臂在所有条件下都不一致")
    else:
        print(f"    ⚠ **部分支持**（{hits}/{hits+miss}）→ 论文措辞应收紧")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"gap_deltas": {a: {"cg_delta": c, "vision_rank_delta": d} for a, c, d in order},
             "best_gap_arm": best_gap,
             "zs_rows": {f"{k[0]}|{k[1]}": [(a, d) for a, d in v] for k, v in rows.items()},
             "h1_hits": hits, "h1_total": hits + miss,
             "distinct_orderings": len(set(sigs))}, ensure_ascii=False, indent=1))
        print(f"    ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
