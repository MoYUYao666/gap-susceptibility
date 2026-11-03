# -*- coding: utf-8 -*-
r"""核实：`create_dataloaders` 产出的 train/val **实际图像集合**（2026-10-09）。

## 上一版判断有误，须更正

`tools/_data_verify.py` **直接实例化 `Flickr30kDataset`** → 得到"三者相同"，
**但它漏看了 `create_dataloaders` 内部的 `random_split`**（`dataset.py:417`）。
**故必须直接检查真实 loader 的 `dataset.indices` → 底层图像名。**

    python tools\_data_split_audit2.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))


def underlying(ds):
    """取 loader 的 dataset 实际用到的图像名集合（穿透 Subset）。"""
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
    n_tr = len(tr.dataset)
    print("=== 真实 loader 的样本数 ===")
    print(f"  train={n_tr} ｜ val={len(va.dataset)} ｜ test={len(te.dataset)}")
    print("\n=== 底层图像集合 ===")
    print(f"  train 唯一图 {len(A)} ｜ val {len(B)} ｜ test {len(C)}")
    print(f"  train∩val  = {len(A & B)}")
    print(f"  train∩test = {len(A & C)}")
    print(f"  val∩test   = {len(B & C)}")
    overlap = len(A & B) + len(A & C)
    print(f"\n  → {'✅ **无重叠**（真有留出集）' if overlap == 0 else '❌ **有重叠**'}")

    held_out = len(B - A)
    print(f"  val 中不在 train 的图: {held_out}/{len(B)}")

    verdict = ("held-out" if overlap == 0 else
               f"overlap({len(A & B)})")
    total_uniq = len(A | B | C)
    print(f"\n  需上传的唯一图（三 loader 合计）: **{total_uniq}**")

    if apply:
        out = REPO / "outputs" / "analysis" / "split_audit.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps({
            "sizes": {"train": n_tr, "val": len(va.dataset), "test": len(te.dataset)},
            "unique_images": {"train": len(A), "val": len(B), "test": len(C)},
            "overlap": {"train_val": len(A & B), "train_test": len(A & C),
                        "val_test": len(B & C)},
            "verdict": verdict,
            "total_unique_images_needed": total_uniq,
            "method": "inspected loader.dataset.indices through Subset",
        }, ensure_ascii=False, indent=1))
        lst = REPO / "outputs" / "analysis" / "needed_images.txt"
        io.open(lst, "w", encoding="utf-8", newline="").write(
            "\n".join(sorted(A | B | C)) + "\n")
        print(f"  ✅ 已写 {out.relative_to(REPO)} 与 needed_images.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
