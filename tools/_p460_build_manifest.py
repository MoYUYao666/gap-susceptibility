# -*- coding: utf-8 -*-
r"""P3 审稿补实验 F+G 组：构建**真实图文对**清单（2026-10-12）。

## 为什么

审稿人 R3.13/R3.14/R3.23 要求"用真实图文对重跑关键实验"，R1.3/R2.3/R3.15/R3.16
要求下游指标。本仓库 `data/` 下**没有**图文数据，但根目录有：

    flickr30k/flickr30k.json      31,783 图像 × 5 描述
    flickr30k/flickr30k-images/   31,785 个 jpg
    coco/annotations/captions_{val2014,train2014}.json
    coco/{val2014,train2014}/     40,504 / 82,783 个 jpg

本脚本把"哪张图配哪句描述"**固化成 JSON 清单**，后续所有实验（`_p431` 起）
只读这份清单，不再自己抽样——这样每个数字都能指到清单里的具体条目。

## 划分规则（确定性、可复现）

官方 Karpathy split 文件本地**没有**，故本清单自建划分，规则如下（写死）：

1. 按 `file_name` **字典序**排序（消除文件系统枚举顺序的影响）；
2. `numpy.random.default_rng(42).permutation(n)` 打乱；
3. 前 1000 张 → `test`（评测用）；紧接 1000 张 → `val`（备用）；其余 → `train_pool`。
4. 训练子集从 `train_pool` **按打乱后的顺序取前 N 张**，每张取**第 1 条**描述
   （确定性；论文主实验每样本 1 条 caption）。

**注意**：这不是 Karpathy 官方 split，故绝对 R@1 数值不可与文献直接比；
**但本实验只用它做"同一清单下不同配置的相对比较"**，这一用途不受影响。

## 完整性检查（全称，非抽样）

对清单里每个条目**逐个** `os.path.isfile` 检查，missing 必须为 0；
检查条数、缺失条数、缺失样本名一并归档——即"机器穷举"而非"看起来都在"。

## 用法

    python tools\_p460_build_manifest.py            # 预演（只打印）
    python tools\_p460_build_manifest.py --apply    # 写 outputs/analysis/p3d_manifest.json

编号说明：本脚本原为 `_p430`，因 `task-9` 已占用 `_p430`/`_p431`/`_p432`，
2026-10-12 整体改为 `_p460+`（见 `docs/P3_DOWNSTREAM.md`）。
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3d_manifest.json"

SEED = 42
N_TEST = 1000
N_VAL = 1000
TRAIN_SIZES = [16, 128, 1024]

FLICKR_JSON = REPO / "flickr30k" / "flickr30k.json"
FLICKR_IMGDIR = REPO / "flickr30k" / "flickr30k-images"
COCO_VAL_ANN = REPO / "coco" / "annotations" / "captions_val2014.json"
COCO_TRAIN_ANN = REPO / "coco" / "annotations" / "captions_train2014.json"
COCO_VAL_IMGDIR = REPO / "coco" / "val2014"
COCO_TRAIN_IMGDIR = REPO / "coco" / "train2014"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_records_flickr() -> list[dict]:
    """[{'image': 'x.jpg', 'captions': [...]}, ...] —— 原样读出，不改写文本。"""
    data = json.loads(io.open(FLICKR_JSON, encoding="utf-8").read())
    recs = []
    for item in data:
        caps = [c for c in item["captions"] if isinstance(c, str) and c.strip()]
        if caps:
            recs.append({"image": item["image"], "captions": caps})
    return recs


def build_records_coco(ann_path: Path) -> list[dict]:
    data = json.loads(io.open(ann_path, encoding="utf-8").read())
    id2file = {im["id"]: im["file_name"] for im in data["images"]}
    by_img: dict[str, list[str]] = {}
    order: list[str] = []
    for ann in data["annotations"]:
        fn = id2file.get(ann["image_id"])
        cap = ann.get("caption")
        if fn is None or not isinstance(cap, str) or not cap.strip():
            continue
        if fn not in by_img:
            by_img[fn] = []
            order.append(fn)
        by_img[fn].append(cap)
    return [{"image": fn, "captions": by_img[fn]} for fn in order]


def split_records(recs: list[dict], seed: int, n_test: int, n_val: int):
    """字典序 + 固定 seed 打乱 → (test, val, train_pool)。"""
    import numpy as np

    recs = sorted(recs, key=lambda r: r["image"])
    perm = np.random.default_rng(seed).permutation(len(recs))
    ordered = [recs[i] for i in perm]
    test = ordered[:n_test]
    val = ordered[n_test:n_test + n_val]
    pool = ordered[n_test + n_val:]
    return test, val, pool


def check_files(recs: list[dict], imgdir: Path) -> dict:
    """逐个检查（全称穷举），返回缺失清单。"""
    missing = [r["image"] for r in recs if not (imgdir / r["image"]).is_file()]
    return {"checked": len(recs), "missing_count": len(missing),
            "missing": missing[:20], "imgdir": str(imgdir.relative_to(REPO))}


def train_sel(pool: list[dict], n: int) -> list[dict]:
    """训练子集：池内前 n 张，每张取第 1 条描述。"""
    return [{"image": r["image"], "caption": r["captions"][0]} for r in pool[:n]]


def build_dataset(name: str, recs: list[dict], imgdir: Path, imgdir_all: list[Path]) -> dict:
    test, val, pool = split_records(recs, SEED, N_TEST, N_VAL)
    integrity = {
        "annotated_images": {"checked": len(recs), "source": str(
            (FLICKR_JSON if name == "flickr30k" else COCO_VAL_ANN).relative_to(REPO))},
        "test_files": check_files(test, imgdir),
        "train_pool_files": None,   # 池子太大，不逐张查（只查 train_sel 与 test）
        "train_sel_files": {},
    }
    sels = {}
    for n in TRAIN_SIZES:
        s = train_sel(pool, n)
        sels[str(n)] = s
        integrity["train_sel_files"][str(n)] = check_files(s, imgdir)
    return {
        "annotations": str((FLICKR_JSON if name == "flickr30k" else COCO_VAL_ANN).relative_to(REPO)),
        "image_dir": str(imgdir.relative_to(REPO)),
        "n_annotated_images": len(recs),
        "n_captions_total": sum(len(r["captions"]) for r in recs),
        "split_rule": ("sorted(file_name) then numpy default_rng(%d).permutation; "
                       "test=first %d, val=next %d, train_pool=rest" % (SEED, N_TEST, N_VAL)),
        "n_test": len(test), "n_val": len(val), "n_train_pool": len(pool),
        "test": [{"image": r["image"], "captions": r["captions"]} for r in test],
        "train_sel": sels,
        "integrity": integrity,
    }


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== P3 F+G：构建真实图文清单 ===")
    if not FLICKR_JSON.exists() or not COCO_VAL_ANN.exists():
        print("!! 缺数据文件"); return 1

    f_recs = build_records_flickr()
    c_recs = build_records_coco(COCO_VAL_ANN)
    c_tr_recs = build_records_coco(COCO_TRAIN_ANN)
    print(f"  flickr30k  : {len(f_recs)} 图像, "
          f"{sum(len(r['captions']) for r in f_recs)} 描述")
    print(f"  coco val   : {len(c_recs)} 图像, "
          f"{sum(len(r['captions']) for r in c_recs)} 描述")
    print(f"  coco train : {len(c_tr_recs)} 图像（备用池）")

    out = {
        "experiment": "p3_fg_real_image_text_manifest",
        "script": "tools/_p460_build_manifest.py",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "why": ("P3 审稿 R3.13/R3.14/R3.23 要求真实图文对；R1.3/R2.3/R3.15/R3.16 要求下游指标。"
                "本清单固定抽样，供 _p431 起的实验只读引用。"),
        "note_not_karpathy": ("本划分不是 Karpathy 官方 split（本地无该文件）。"
                             "仅用于同一清单内的相对比较；绝对 R@1 不可与文献直接对比。"),
        "seed": SEED, "n_test": N_TEST, "n_val": N_VAL, "train_sizes": TRAIN_SIZES,
        "sources": {
            "flickr30k/flickr30k.json": {"sha256": sha256_of(FLICKR_JSON),
                                          "bytes": FLICKR_JSON.stat().st_size},
            "coco/annotations/captions_val2014.json": {"sha256": sha256_of(COCO_VAL_ANN),
                                                        "bytes": COCO_VAL_ANN.stat().st_size},
            "coco/annotations/captions_train2014.json": {"sha256": sha256_of(COCO_TRAIN_ANN),
                                                          "bytes": COCO_TRAIN_ANN.stat().st_size},
        },
        "datasets": {
            "flickr30k": build_dataset("flickr30k", f_recs, FLICKR_IMGDIR, [FLICKR_IMGDIR]),
            "coco": build_dataset("coco", c_recs, COCO_VAL_IMGDIR, [COCO_VAL_IMGDIR, COCO_TRAIN_IMGDIR]),
        },
        "coco_train2014_pool": {
            "image_dir": "coco/train2014",
            "n_annotated_images": len(c_tr_recs),
            "n_captions_total": sum(len(r["captions"]) for r in c_tr_recs),
        },
    }

    ok = True
    for name, d in out["datasets"].items():
        ti = d["integrity"]["test_files"]
        print(f"  {name:<10} test={d['n_test']} val={d['n_val']} pool={d['n_train_pool']} "
              f"| test 缺失 {ti['missing_count']}/{ti['checked']}")
        if ti["missing_count"]:
            ok = False
        for n, si in d["integrity"]["train_sel_files"].items():
            print(f"      train_sel[{n}]: 缺失 {si['missing_count']}/{si['checked']}")
            if si["missing_count"]:
                ok = False

    assert ok, "有图像文件缺失，清单不可用"
    assert out["datasets"]["flickr30k"]["n_test"] == N_TEST
    assert out["datasets"]["coco"]["n_test"] == N_TEST
    assert len(out["datasets"]["flickr30k"]["train_sel"]["1024"]) == 1024

    if not apply:
        print("\n（预演；加 --apply 写文件）")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}  "
          f"({OUT.stat().st_size/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
