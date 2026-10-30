# -*- coding: utf-8 -*-
r"""实验 ⑥（修正版）：用**论文自己的"保护"定义**检验零样本外部效度（2026-10-07）。

## 第一版的缺陷（自我修正）

`tools/_p5_nonnatural_zs.py` 把"gap 保持"定义为 **|CGΔ| 最小**，据此判定"零样本最优臂 ≠ gap 最优臂（0/4）"。

**但这个定义与论文不符**。论文的"保护"（Visual Fragility / Protect, Don't Perturb）指的是
**CGΔ 最负（gap 收窄）**，而非"变化幅度最小"。三臂的 CGΔ：

| 臂 | CGΔ | 按"收窄最多"排序 | 按"|变化| 最小"排序 |
|---|---|---|---|
| **Text-only** | **−0.0465** | **1（最保护）** | 3 |
| Both | −0.0258 | 2 | 2 |
| Vision-only | **+0.0106** | 3（**反向**，gap 变宽） | 1 |

**→ 两种定义给出相反的"最优臂"**。第一版用错了定义，故结论无效。

## 本版检验（按论文定义）

**H1'**：**CGΔ 最负**的臂（= Text-only），在 DTD/Food101 零样本上保持最好。
**H2'**：该排序是否跨两个数据集与两套零样本协议稳定。

## ⚠️ 一个数据缺口（必须如实标注）

**零样本数据只有 2 个臂**（`text_only_r8` / `both_r8`，另一套只有 Text-only/Both），
**没有 vision_only** → **无法检验"gap 变宽的臂是否零样本更差"**。
这是本检验的**实质局限**：只能比较 text-only vs both。

    python tools\_p5_nonnatural_zs2.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "nonnatural_zs_check2.json"

ARMS = ("text_only", "both", "vision_only")
LABEL = {"text_only": "Text-only", "both": "Both", "vision_only": "Vision-only"}
ZS_KEY = {"text_only": "text_only_r8", "both": "both_r8", "vision_only": "vision_only_r8"}
ZS_KEY2 = {"text_only": "Text-only", "both": "Both", "vision_only": "Vision-only"}


def main() -> int:
    apply = "--apply" in sys.argv
    sc = json.loads(io.open(REPO / "outputs/analysis/strict_control_summary.json",
                            encoding="utf-8").read())
    zs1 = json.loads(io.open(REPO / "outputs/dtd_food101_zs_check.json",
                             encoding="utf-8").read())["results"]
    zs2 = json.loads(io.open(REPO / "outputs/zeroshot_extra.json", encoding="utf-8").read())

    cg = {a: sc["configs"][a]["cg_delta_mean"] for a in ARMS}
    print("  === 三臂 CGΔ（论文口径：越负=越保护）===")
    for rank, a in enumerate(sorted(ARMS, key=lambda x: cg[x]), 1):
        print(f"  {LABEL[a]:<14} {cg[a]:>+9.4f}   保护性排序 {rank}")
    most_prot = min(ARMS, key=lambda x: cg[x])
    print(f"  → 最保护臂 = **{LABEL[most_prot]}**（CGΔ={cg[most_prot]:+.4f}）")

    rows, avail = {}, set()
    for name, res, km in (("dtd_food101_zs_check", zs1, ZS_KEY),
                          ("zeroshot_extra", zs2, ZS_KEY2)):
        for ds in ("DTD", "Food101"):
            if ds not in res:
                continue
            r = res[ds]
            frozen = r.get("frozen", r.get("Frozen"))
            if frozen is None:
                continue
            line = [(a, r[km[a]] - frozen) for a in ARMS if km[a] in r]
            for a, _ in line:
                avail.add(a)
            rows[(name, ds)] = line

    print(f"\n  === 零样本（相对 frozen，百分点）===")
    for (name, ds), line in rows.items():
        print(f"  [{name[:22]}] {ds:<9} " + " ｜ ".join(f"{LABEL[a]} {d:+.2f}" for a, d in line))
    print(f"\n  ⚠️ 零样本可用臂: {sorted(LABEL[a] for a in avail)}"
          f"  → **{LABEL['vision_only']} 缺失**，故无法检验「gap 变宽是否导致零样本更差」")

    print(f"\n  === H1'：最保护臂（{LABEL[most_prot]}）是否零样本保持最好 ===")
    hits = tot = 0
    for (name, ds), line in rows.items():
        if not line:
            continue
        best = max(line, key=lambda x: x[1])[0]
        tot += 1
        ok = best == most_prot
        hits += ok
        print(f"  {name[:22]:<24} {ds:<9} 零样本最优={LABEL[best]:<11} "
              f"{'✅ 与最保护臂一致' if ok else '❌ 不一致'}")
    print(f"\n  一致 **{hits}/{tot}**")

    print(f"\n  === H2'：排序稳定性 ===")
    sigs = []
    for key, line in rows.items():
        s = tuple(a for a, _ in sorted(line, key=lambda x: -x[1]))
        sigs.append(s)
        print(f"    {key[0][:22]:<24} {key[1]:<9} {' > '.join(LABEL[a] for a in s)}")
    print(f"  不同排序 {len(set(sigs))}/{len(sigs)}")

    print(f"\n  === 结论 ===")
    if hits == tot and len(set(sigs)) == 1:
        print(f"    ✅ **支持**：最保护臂（{LABEL[most_prot]}）在全部 {tot} 个非自然图像条件下零样本保持最好，")
        print("       且排序跨数据集/协议稳定 → **gap 作为健康信号在其它域具有外部效度**")
    elif hits >= tot * 0.75:
        print(f"    ⚠ **基本支持**（{hits}/{tot}），但排序不完全稳定 → 措辞应留余地")
    else:
        print(f"    ❌ **不支持**（{hits}/{tot}）")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"cg_delta": cg, "most_protective_arm": most_prot,
             "zs_available_arms": sorted(avail),
             "vision_only_missing": "vision_only" not in avail,
             "rows": {f"{k[0]}|{k[1]}": [(a, d) for a, d in v] for k, v in rows.items()},
             "h1_hits": hits, "h1_total": tot,
             "distinct_orderings": len(set(sigs))}, ensure_ascii=False, indent=1))
        print(f"    ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
