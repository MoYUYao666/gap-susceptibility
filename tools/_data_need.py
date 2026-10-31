# -*- coding: utf-8 -*-
r"""算出严格冻结 run 需要哪些图片（云端只上传这些，避免 4.2 GB 传输，2026-10-09）。

## 为什么要精确算

`src/dataset.py` 的 `__getitem__` 在 `Image.open` 失败时**静默回退到随机图像**
（`Image.new("RGB", ...)`）——**若图片缺失，实验会悄悄跑在假数据上**。
**故必须（a）只上传真正用到的图，（b）上传后校验零回退。**

## 需要哪些

`strict_freeze_control.py` 用 `create_dataloaders(..., max_samples=5000)`，
Flickr30k 的 train/val/test **各取 5000** → 最多 **15000 张**。
但 split 是先 shuffle 再截断还是直接截断，决定具体是哪 15000 张——**故直接实例化数据集读取样本名**。

    python tools\_data_need.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "outputs" / "analysis" / "needed_images.json"


def main() -> int:
    apply = "--apply" in sys.argv
    from dataset import Flickr30kDataset

    base = REPO / "flickr30k"
    need = {}
    for split in ("train", "val", "test"):
        for ms in (5000, 512):
            try:
                ds = Flickr30kDataset(data_dir=str(REPO / "flickr30k"), split=split, max_samples=ms)
                names = sorted({s["image"] for s in ds.samples})
                need[f"{split}_{ms}"] = names
                print(f"  {split:<6} max_samples={ms:<5} → {len(names)} 张唯一图 "
                      f"（样本 {len(ds.samples)}）")
            except Exception as e:
                print(f"  {split} max_samples={ms}: ❌ {str(e)[:80]}")

    allnames = sorted(set().union(*need.values())) if need else []
    print(f"\n  合计需上传 **{len(allnames)}** 张唯一图")
    tot = 0
    missing = []
    for n in allnames:
        p = base / "flickr30k-images" / n
        if p.exists():
            tot += p.stat().st_size
        else:
            missing.append(n)
    print(f"  本地体积 {tot/2**20:.0f} MB ｜ 本地缺失 {len(missing)} 张")
    if missing:
        print(f"    ⚠️ 缺失例：{missing[:5]}")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"splits": {k: len(v) for k, v in need.items()},
             "images": allnames, "n_images": len(allnames),
             "bytes": tot, "missing": missing}, ensure_ascii=False, indent=1))
        # 同时写一份纯名单，供 tar 打包用
        lst = REPO / "outputs" / "analysis" / "needed_images.txt"
        io.open(lst, "w", encoding="utf-8", newline="").write("\n".join(allnames) + "\n")
        print(f"  ✅ 已写 {OUT.relative_to(REPO)} 与 {lst.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
