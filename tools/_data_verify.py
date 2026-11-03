# -*- coding: utf-8 -*-
r"""核实：三个 split 是否同一批图 + 标注格式 + 图片体积（2026-10-09）。

    python tools\_data_verify.py [--apply]
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

DATA = REPO / "flickr30k"


def main() -> int:
    apply = "--apply" in sys.argv
    from dataset import Flickr30kDataset

    sets = {}
    for split in ("train", "val", "test"):
        ds = Flickr30kDataset(data_dir=str(DATA), split=split, max_samples=5000)
        sets[split] = [s["image"] for s in ds.samples]
        print(f"  {split:<6} {len(ds.samples)} 样本 ｜ 前 3: {[s['image'] for s in ds.samples[:3]]}")

    print("\n=== 三 split 是否同批图 ===")
    print(f"  train∩val  = {len(set(sets['train']) & set(sets['val']))}")
    print(f"  train∩test = {len(set(sets['train']) & set(sets['test']))}")
    same = sets["train"] == sets["val"] == sets["test"]
    print(f"  完全相同: {same}")

    uniq = sorted(set(sets["train"]) | set(sets["val"]) | set(sets["test"]))
    print(f"\n  唯一图合计 **{len(uniq)}** 张")
    tot = 0
    miss = []
    for n in uniq:
        p = DATA / "flickr30k-images" / n
        if p.exists():
            tot += p.stat().st_size
        else:
            miss.append(n)
    print(f"  本地上传体积约 **{tot/2**20:.0f} MB** ｜ 缺失 {len(miss)}")

    print("\n=== 标注文件 ===")
    csv = DATA / "flickr30k-images" / "results.csv"
    if csv.exists():
        with io.open(csv, encoding="utf-8", errors="replace") as f:
            head = [next(f).rstrip() for _ in range(2)]
        print(f"  {csv.relative_to(REPO)} ({csv.stat().st_size/2**20:.1f} MB)")
        for ln in head:
            print(f"    {ln[:100]}")
        print(f"    分隔符含 '|': {'|' in head[0]}")
    for extra in ("flickr30k.json", "captions.txt"):
        p = DATA / extra
        if p.exists():
            print(f"  {p.relative_to(REPO)} ({p.stat().st_size/2**20:.1f} MB)")

    if apply:
        out = REPO / "outputs" / "analysis" / "data_verify.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps(
            {"same_across_splits": same, "n_unique": len(uniq),
             "bytes": tot, "missing": miss,
             "note": "dataset.py:159 truncates before splitting, so all three "
                     "Flickr30k loaders see the same first max_samples samples"},
            ensure_ascii=False, indent=1))
        lst = REPO / "outputs" / "analysis" / "needed_images.txt"
        io.open(lst, "w", encoding="utf-8", newline="").write("\n".join(uniq) + "\n")
        print(f"\n  ✅ 已写 {out.relative_to(REPO)} 与 {lst.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
