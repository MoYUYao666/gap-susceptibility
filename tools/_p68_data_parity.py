# -*- coding: utf-8 -*-
r"""**决定性对比 2**：本地与云端的**数据集前 1000 图是否同一批**（2026-10-09）。

## 已排除

| 假设 | 证据 |
|---|---|
| 模型权重不同 | ❌ 本地/云端 `image_embeds_hash` **完全相同**（−2.814） |
| 预处理不同 | ❌ `cos_ii` / `dist_it` / `cg` 完全一致到 7 位 |
| 脚本不同 | ❌ `strict_freeze_control.py` sha256 一致 |
| `n_trainable` 口径不同 | ❌ 完全相同 |

## 待查：**数据**

云端 `CG(initial) = 1.0712` vs 本地 `0.8187` —— **这是"两边看的图不同"的指纹**。

    python tools\_p68_data_parity.py [--apply]
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

REMOTE = r'''
import os, csv, glob, collections, hashlib, json
os.chdir("/root/autodl-tmp/work")

def summarize(tag, img_dir, csv_path):
    have = sorted(os.path.basename(p) for p in glob.glob(img_dir + "/*.jpg"))
    print("=== %s ===" % tag)
    print("  JPEG 数:", len(have))
    by = collections.OrderedDict()
    with open(csv_path, encoding="utf-8", errors="replace") as f:
        rd = csv.reader(f, delimiter="|")
        try: next(rd)
        except StopIteration: pass
        for row in rd:
            if len(row) >= 3:
                by.setdefault(row[0].strip(), []).append(row[2].strip())
    print("  CSV 图数:", len(by), "｜ 标注数:", sum(len(v) for v in by.values()))
    # 数据集取前 5000 条标注 → 哪些图
    samples = []
    for nm, caps in by.items():
        for c in caps:
            samples.append(nm)
        if len(samples) >= 5000:
            break
    uniq = sorted(set(samples[:5000]))
    print("  前 5000 标注覆盖的图数:", len(uniq))
    print("  前 10 图:", uniq[:10])
    print("  前 1000 图 md5:", hashlib.md5("".join(uniq).encode()).hexdigest()[:16])
    print("  CSV 首 3 图:", list(by.keys())[:3])
    print("  CSV md5:", hashlib.md5(open(csv_path,'rb').read()).hexdigest()[:16])
    return uniq

u = summarize("云端", "flickr30k/flickr30k-images", "flickr30k/results.csv")
json.dump({"uniq1000": u, "n_jpeg": len(glob.glob("flickr30k/flickr30k-images/*.jpg"))},
          open("_data_parity.json", "w"))
print()
print("=== 云端图片是否都在前 1000 ===")
have = set(os.path.basename(p) for p in glob.glob("flickr30k/flickr30k-images/*.jpg"))
print("  前 1000 图中云端缺失:", len([x for x in u if x not in have]))
'''


def main() -> int:
    apply = "--apply" in sys.argv

    print("=== 本地 ===")
    import csv as _csv
    import collections
    base = REPO / "flickr30k"
    imgs = sorted(p.name for p in (base / "flickr30k-images").glob("*.jpg"))
    print("  JPEG 数:", len(imgs))
    by = collections.OrderedDict()
    _csvpath = base / "results.csv"
    if not _csvpath.exists():
        _csvpath = base / "flickr30k-images" / "results.csv"
    print("  CSV 路径:", _csvpath.relative_to(REPO))
    with io.open(_csvpath, encoding="utf-8", errors="replace") as f:
        rd = _csv.reader(f, delimiter="|")
        try:
            next(rd)
        except StopIteration:
            pass
        for row in rd:
            if len(row) >= 3:
                by.setdefault(row[0].strip(), []).append(row[2].strip())
    print("  CSV 图数:", len(by), "｜ 标注数:", sum(len(v) for v in by.values()))
    samples = []
    for nm, caps in by.items():
        samples.extend([nm] * len(caps))
        if len(samples) >= 5000:
            break
    uniq = sorted(set(samples[:5000]))
    print("  前 5000 标注覆盖的图数:", len(uniq))
    print("  前 10 图:", uniq[:10])
    print("  前 1000 图 md5:", hashlib.md5("".join(uniq).encode()).hexdigest()[:16])
    print("  CSV 首 3 图:", list(by.keys())[:3])
    print("  CSV md5:", hashlib.md5(_csvpath.read_bytes()).hexdigest()[:16])

    print("\n=== 云端 ===")
    from _cloud_ssh import client, run
    c = client()
    try:
        io.open(REPO / "outputs" / "_remote_dp.py", "w", encoding="utf-8",
                newline="\n").write(REMOTE)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_dp.py"),
                 "/root/autodl-tmp/work/_dp.py")
        sftp.close()
        run(c, "/root/miniconda3/bin/python /root/autodl-tmp/work/_dp.py", timeout=600)
    finally:
        c.close()

    if apply:
        out = REPO / "outputs" / "analysis" / "data_parity.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps({
            "local": {"n_jpeg": len(imgs), "csv_images": len(by),
                      "uniq1000_md5": hashlib.md5("".join(uniq).encode()).hexdigest()},
            "note": "compare with cloud output printed above",
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
