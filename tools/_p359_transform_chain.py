# -*- coding: utf-8 -*-
r"""核实「评测画廊是否继承 train transform」——按对象链取，不用代理判据（2026-10-12）。

## 我上一版的错

我读 `va.dataset.transform` → 那是 `Subset`，**没有 `.transform` 属性** → 于是打印
`RandomHorizontalFlip: False`，**是假阴性**。**必须沿 `.dataset` 链取到真正持有 transform 的对象。**

## 要建立的链条

`va`（DataLoader）→ `va.dataset`（`Subset`）→ `.dataset`（被包装的原 dataset）
→ 该对象的 `.transform`（或它在 `__getitem__` 里用了什么）

并**直接实测**：同一 index 取两次，张量是否不同。

    python tools\_p359_transform_chain.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "transform_chain.json"


def peel(obj, depth=0):
    """沿 .dataset 链展开，返回 [(层级, 类型, transform字符串)]"""
    out = []
    cur, d = obj, depth
    seen = set()
    while cur is not None and id(cur) not in seen and d < 8:
        seen.add(id(cur))
        tf = getattr(cur, "transform", None)
        out.append((d, type(cur).__name__, str(tf).replace("\n", " ")[:220] if tf is not None else None))
        nxt = getattr(cur, "dataset", None)
        if nxt is None:
            nxt = getattr(cur, "img_dataset", None)
        cur = nxt
        d += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    sys.path.insert(0, str(REPO))
    from src.dataset import create_dataloaders  # noqa

    tr, va, te = create_dataloaders(data_dir=str(REPO), dataset_name="flickr30k",
                                    batch_size=64, num_workers=0, max_samples=2000,
                                    image_size=224)

    rep = {"script": "tools/_p359_transform_chain.py", "chains": {}}
    print("=" * 100)
    print("① 三条 loader 的 .dataset 链与各层 transform")
    print("=" * 100)
    for name, dl in (("train", tr), ("val", va), ("test", te)):
        chain = peel(dl.dataset)
        rep["chains"][name] = chain
        print(f"\n  [{name}] loader.dataset = {type(dl.dataset).__name__}")
        for d, cls, tf in chain:
            print(f"     {'  '*d}L{d} {cls:<26} transform={'（无）' if tf is None else tf[:150]}")

    print()
    print("=" * 100)
    print("② 实测：同一 index 取两次，图像张量是否相同")
    print("=" * 100)
    import torch
    base = va.dataset
    real = base.dataset if hasattr(base, "dataset") else base
    tfs = [c for c in peel(base) if c[2] is not None]
    has_train_tf = any(("RandomHorizontalFlip" in (c[2] or "") or
                        "ColorJitter" in (c[2] or "")) for c in tfs)
    print(f"  val 链上是否存在带 RandomHorizontalFlip/ColorJitter 的 transform: {has_train_tf}")

    diffs, maxd = [], 0.0
    for i in range(5):
        x1 = real[i]
        x2 = real[i]
        im1 = x1["image"] if isinstance(x1, dict) else x1[0]
        im2 = x2["image"] if isinstance(x2, dict) else x2[0]
        d = float((im1 - im2).abs().max())
        diffs.append(d)
        maxd = max(maxd, d)
        print(f"    index {i}: max|Δ| = {d:.6f}")

    rep["val_chain_has_train_transform"] = has_train_tf
    rep["same_index_two_reads_max_abs_diff"] = diffs
    rep["max_abs_diff_overall"] = maxd
    rep["verdict"] = ("评测画廊确实带随机变换（每次评测为不同抽样）"
                      if maxd > 1e-6 else
                      "同一 index 两次读一致 → 未继承随机变换")
    print()
    print(f"  → 判定：{rep['verdict']}（最大差 {maxd:.6f}）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
