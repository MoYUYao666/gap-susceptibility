# -*- coding: utf-8 -*-
r"""实验 ④ 三臂判定：解码器 VLM 上的位置排序（2026-10-08）。

## 口径（三臂**完全一致**）

4-bit 量化 ｜ 400 样本 ｜ 3 epoch ｜ batch 4 ｜ rank 8 ｜ lr 1e-4 ｜ seed 42

**为何用 4-bit**：bf16 下 `vision_only` 实测 **27 min 未完成 1 个 epoch**
（`text_only` 为 2.4 min/epoch，**慢 13 倍**）→ 不可行；
4-bit 下同臂 **5.4 min/3 epoch**。

## 判据

比较三臂的 **`DG*` 跨度**（变化越小越"保护对齐"）与末值。

    python tools\_p49_qwen_verdict.py [--apply]
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
    print("=== 实验 ④：Qwen2-VL-2B 严格冻结三臂（4bit / 400 样本 / 3 epoch，seed 42）===")
    print(f"  {'臂':<12} {'n_trainable':>13} {'DG*(ep1→ep3)':>22} {'跨度':>9} {'CG 跨度':>9}")
    recs, ok = {}, True
    for arm in ARMS:
        p = D / f"{arm}_seed42.json"
        if not p.exists():
            print(f"  {arm:<12} ⏳ 缺结果")
            ok = False
            continue
        d = json.loads(io.open(p, encoding="utf-8").read())
        # 只接受统一口径的运行
        if not (d.get("4bit") and d.get("max_samples") == 400 and d.get("epochs") == 3):
            print(f"  {arm:<12} ⚠ 口径不一致（4bit={d.get('4bit')} max={d.get('max_samples')} "
                  f"ep={d.get('epochs')}）→ 跳过")
            ok = False
            continue
        dg = d["dg_star"]
        recs[arm] = d
        print(f"  {arm:<12} {d['n_trainable']:>13,} "
              f"{f'{dg[0]:.4f} → {dg[-1]:.4f}':>22} {d['dg_span']:>9.4f} {d['cg_span']:>9.4f}")

    if not ok or len(recs) < 3:
        print("\n  ❌ 三臂未齐或口径不一致，无法判定")
        return 1

    print("\n=== 逐 epoch DG* ===")
    for arm in ARMS:
        print(f"  {arm:<12} " + "  ".join(f"{x:.4f}" for x in recs[arm]["dg_star"]))

    best = min(recs, key=lambda a: recs[a]["dg_span"])
    print(f"\n=== 判定 ===")
    print(f"  最保护臂（DG* 跨度最小）= **{best}**")
    order = sorted(ARMS, key=lambda a: recs[a]["dg_span"])
    print(f"  排序（跨度升序）: {' < '.join(order)}")

    verdict = {
        "protocol": "Qwen2-VL-2B, strict-freeze, 4bit, 400 samples, 3 epochs, batch 4, seed 42",
        "dg_star_span": {a: recs[a]["dg_span"] for a in ARMS},
        "cg_span": {a: recs[a]["cg_span"] for a in ARMS},
        "dg_star_traj": {a: recs[a]["dg_star"] for a in ARMS},
        "n_trainable": {a: recs[a]["n_trainable"] for a in ARMS},
        "most_protective": best,
        "ordering": order,
    }

    print("\n=== 与双塔侧的一致性 ===")
    print("  双塔（对比式图文预训练骨干）: CLIP B/32、CLIP B/16、OpenCLIP B/32 → **text_only 最保护**")
    print(f"  解码器 VLM（Qwen2-VL-2B）  : → **{best}**")
    print(f"  {'✅ 一致' if best == 'text_only' else '⚠ 不一致'}")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(verdict, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
