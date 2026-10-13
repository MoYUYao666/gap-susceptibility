# -*- coding: utf-8 -*-
r"""查：本地 strict-freeze run 实际用了**哪些图 / 多少张**（2026-10-09）。

## 假设

**云端只上传了 1000 张图** → `results.csv`（31783 图）里前 200 张图各 5 条标注 = 1000 条。
**本地有全部 31783 张图** → 前 1000 张图 × 5 = 5000 条。
**→ 图数差 5 倍（1000 vs 200），标注数差 5 倍（5000 vs 1000）** → 可解释 CGΔ 的差异。

**本脚本核实本地实际用到的图集**（不靠推断）。

    python tools\_p65_local_images.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "outputs" / "analysis" / "local_image_sets.json"


def underlying(ds):
    cur = ds
    for _ in range(4):
        if hasattr(cur, "indices"):
            base = cur.dataset
            idxs = list(cur.indices)
            if hasattr(base, "samples"):
                return {base.samples[i]["image"] for i in idxs}
            cur = base
        else:
            break
    if hasattr(cur, "samples"):
        return {s["image"] for s in cur.samples}
    return set()


def main() -> int:
    apply = "--apply" in sys.argv
    from src.dataset import create_dataloaders

    tr, va, te = create_dataloaders(dataset_name="flickr30k", data_dir=str(REPO),
                                    batch_size=128, max_samples=5000)
    A, B, C = underlying(tr.dataset), underlying(va.dataset), underlying(te.dataset)
    allimg = A | B | C
    print("=== 本地（全部 31783 图可用）===")
    print(f"  样本数: train={len(tr.dataset)} val={len(va.dataset)} test={len(te.dataset)}")
    print(f"  唯一图: train={len(A)} val={len(B)} test={len(C)} ｜ 合计 {len(allimg)}")
    print(f"  图:标注 比 ≈ 1:{(len(tr.dataset)+len(va.dataset)+len(te.dataset))/max(len(allimg),1):.1f}")

    # 云端只有前 1000 张图 → 模拟：拦截 dataset，只保留图名在前 1000 张集内的样本
    first1000 = set(sorted(allimg)[:1000])
    n_avail = sum(1 for s in tr.dataset.dataset.samples if s["image"] in first1000) \
        if hasattr(tr.dataset, "dataset") else 0
    print("\n=== 云端条件模拟（只有前 1000 张图）===")
    print(f"  前 1000 张图覆盖的标注条数（train 全集）= {n_avail}")
    print(f"  → 云端 max_samples=5000 实际只能取到 **{min(5000, n_avail)}** 条"
          f"（{n_avail//5 if n_avail else 0} 张图 × 5 标注）")
    print("  ⚠️ 即**云端有效标注数 ≈ 1000 条**（非 5000），图为 **200 张**（非 1000）")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps({
            "local": {"train": len(tr.dataset), "val": len(va.dataset),
                      "test": len(te.dataset),
                      "unique_images": len(allimg)},
            "first1000_available_captions_train": n_avail,
            "cloud_effective": {"captions": min(5000, n_avail),
                                "images": n_avail // 5 if n_avail else 0},
            "hypothesis": "cloud had only the first 1000 images, so max_samples=5000 "
                          "yielded ~%d captions over ~%d images instead of 5000 over 1000"
                          % (min(5000, n_avail), n_avail // 5 if n_avail else 0),
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
