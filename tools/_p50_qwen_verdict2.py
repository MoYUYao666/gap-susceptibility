# -*- coding: utf-8 -*-
r"""修正实验 ④ 的判据：**绝对跨度在初始值差 3 倍时不可比**（2026-10-08）。

## 我先前判据的缺陷（自我修正）

第一版用 **`DG*` 绝对跨度最小** 判"最保护"，得到 `vision_only`。
**但三臂的起始 `DG*` 相差 3 倍**：

| 臂 | DG*(ep1) | DG*(ep3) | 绝对跨度 | 相对降幅 |
|---|---|---|---|---|
| text_only | 0.7100 | 0.1851 | 0.5248 | **−73.9%** |
| both | 0.6364 | 0.1029 | 0.5335 | **−83.8%** |
| vision_only | **2.1759** | 1.9365 | **0.2394** | **−11.0%** |

**起点高的臂天然跨度大** → "绝对跨度最小"会把**"几乎不动"误判为"最保护"**。

## 论文的口径是什么

论文 `tab:position_strict` 的判据是 **`ΔCG = final − initial`**（**绝对变化**），
但**其各臂起点相同**（同一个冻结模型，LoRA B 零初始化 → 起点一致）→ 绝对变化可比。

**本实验的起点却不一致**（`vision_only` 的投影后文本侧嵌入受语言塔未训练影响更大）
→ **必须用相对变化，或先报告起点**。

## 修正后的判定（两个口径都报）

1. **相对降幅** `(final − initial)/initial`；
2. **绝对降幅** `final − initial`（**并标注起点不同**）。

    python tools\_p50_qwen_verdict2.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
D = REPO / "outputs" / "vlm_strictfreeze"
OUT = REPO / "outputs" / "analysis" / "qwen_verdict.json"
ARMS = ("text_only", "both", "vision_only")


def main() -> int:
    apply = "--apply" in sys.argv
    recs = {}
    for arm in ARMS:
        p = D / f"{arm}_seed42.json"
        d = json.loads(io.open(p, encoding="utf-8").read())
        assert d.get("4bit") and d.get("max_samples") == 400 and d.get("epochs") == 3, \
            f"{arm} 口径不一致"
        recs[arm] = d

    print("=== Qwen2-VL-2B 严格冻结三臂（4bit / 400 样本 / 3 epoch，seed 42）===")
    print(f"  {'臂':<12} {'DG*起点':>10} {'DG*末值':>10} {'绝对降幅':>10} {'相对降幅':>10} {'CG 降幅':>10}")
    rows = {}
    for arm in ARMS:
        dg = recs[arm]["dg_star"]
        cg = recs[arm]["cg"]
        abs_d = dg[0] - dg[-1]
        rel_d = abs_d / dg[0] if dg[0] else float("nan")
        cg_d = cg[0] - cg[-1]
        rel_cg = cg_d / cg[0] if cg[0] else float("nan")
        rows[arm] = {"dg0": dg[0], "dg1": dg[-1], "abs": abs_d, "rel": rel_d,
                     "cg_abs": cg_d, "cg_rel": rel_cg, "traj": dg}
        print(f"  {arm:<12} {dg[0]:>10.4f} {dg[-1]:>10.4f} {abs_d:>+10.4f} "
              f"{rel_d*100:>9.1f}% {rel_cg*100:>9.1f}%")

    print("\n=== 逐 epoch DG* ===")
    for arm in ARMS:
        print(f"  {arm:<12} " + "  ".join(f"{x:.4f}" for x in recs[arm]["dg_star"]))

    print("\n=== ⚠️ 起点不一致这一事实 ===")
    starts = [rows[a]["dg0"] for a in ARMS]
    print(f"  起点范围 {min(starts):.4f} – {max(starts):.4f}（相差 {max(starts)/min(starts):.1f} 倍）")
    print("  → **绝对跨度不可比**；须以**相对降幅**判定（或先对齐起点）")

    best_rel = max(ARMS, key=lambda a: rows[a]["rel"])
    best_abs = max(ARMS, key=lambda a: rows[a]["abs"])
    print("\n=== 判定 ===")
    print(f"  按**相对降幅**（DG* 缩小最多）  = **{best_rel}**（{rows[best_rel]['rel']*100:.1f}%）")
    print(f"  按**绝对降幅**                  = **{best_abs}**（{rows[best_abs]['abs']:+.4f}，"
          f"但起点 {rows[best_abs]['dg0']:.4f}）")
    order = sorted(ARMS, key=lambda a: -rows[a]["rel"])
    print(f"  相对降幅排序（大→小）: {' > '.join(order)}")

    print("\n=== 与双塔侧对照 ===")
    print("  双塔（对比式图文预训练）: CLIP B/32、CLIP B/16、OpenCLIP B/32 → text_only 相对最保护")
    print(f"  解码器 VLM（Qwen2-VL-2B）: 相对降幅最大 = **{best_rel}**")
    print(f"  {'✅ 方向一致' if best_rel in ('text_only', 'both') else '⚠ 不一致'}")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps({
            "protocol": "Qwen2-VL-2B strict-freeze 4bit 400 samples 3 epochs batch4 seed42",
            "rows": rows, "start_ratio": max(starts) / min(starts),
            "best_by_relative": best_rel, "best_by_absolute": best_abs,
            "order_by_relative": order,
            "caveat": "起点不一致（相差 %.1f 倍），绝对跨度不可比；判据用相对降幅"
                      % (max(starts) / min(starts)),
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
