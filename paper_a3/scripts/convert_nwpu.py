# -*- coding: utf-8 -*-
r"""Convert the NWPU-Captions parquet shards into the A3 annotation JSONL schema.

Source (recorded in data/README.md): Hugging Face dataset `caglarmert/NWPU-captions`, four shards
train-00000/00001 (12,600 rows each), validation and test (3,150 each) = 31,500 images, five captions per image,
157,500 captions in total, matching the published NWPU-Captions statistics.

Text provenance: human captions are the dataset's; templated / segmented / metadata arms are derived mechanically from
the captions (parsed objects) and the computed image statistics, exactly as for RSICD.

Usage
  python convert_nwpu.py --self-test
  python convert_nwpu.py [--data-root paper_a3/data/nwpu_captions] [--out paper_a3/data/nwpu_captions.jsonl]
"""
import argparse
import hashlib
import io
import json
import os
import sys

import convert_rsitmd as rsitmd  # reuse the caption parser vocabulary and logic

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLITS = {"train": ["train0.parquet", "train1.parquet"], "val": ["valid.parquet"], "test": ["test.parquet"]}


def convert(data_root, out_jsonl):
    import pyarrow.parquet as pq
    from PIL import Image

    rows = []
    images_root = os.path.join(data_root, "images")
    os.makedirs(images_root, exist_ok=True)
    for split, shards in SPLITS.items():
        out_dir = os.path.join(images_root, split)
        os.makedirs(out_dir, exist_ok=True)
        for shard in shards:
            path = os.path.join(data_root, shard)
            if not os.path.exists(path):
                raise SystemExit("missing shard: %s (see paper_a3/data/README.md for the fetch command)" % path)
            table = pq.read_table(path)
            for rec in table.to_pylist():
                name = rec["file_name"]
                raw = rec["image"]["bytes"]
                target = os.path.join(out_dir, name)
                if not os.path.exists(target):
                    with io.open(target, "wb") as f:
                        f.write(raw)
                try:
                    with Image.open(io.BytesIO(raw)) as im:
                        width, height = im.size
                        small = im.convert("L").resize((32, 32))
                        brightness = sum(small.getdata()) / 1024.0
                except Exception:
                    width = height = 0
                    brightness = None
                captions = [rec["caption_%d" % i].strip() for i in range(1, 6) if rec.get("caption_%d" % i)]
                parsed = rsitmd.parse_objects(captions)
                classes = parsed["labels"][:1] if parsed["labels"] else []
                rows.append({
                    "image_id": os.path.splitext(name)[0],
                    "image_path": os.path.join("images", split, name).replace("\\", "/"),
                    "split": split,
                    "captions": captions,
                    "metadata": {"sensor": None, "gsd_m": None, "classes": classes,
                                 "region": None, "date": None, "dataset_split": split,
                                 "width": width, "height": height,
                                 "aspect_ratio": round(width / height, 3) if height else None,
                                 "brightness_8bit": round(brightness, 1) if brightness is not None else None},
                    "derived_objects": parsed,
                    "boxes": [],
                })
    with io.open(out_jsonl, "w", encoding="utf-8", newline="") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    digest = hashlib.sha256(io.open(out_jsonl, "rb").read()).hexdigest()
    print("wrote %s | records %d | sha256 %s" % (out_jsonl, len(rows), digest[:16]))
    return rows


def self_test():
    checks = {
        "split shard plan covers four files": sum(len(v) for v in SPLITS.values()) == 4,
        "caption parser reused": rsitmd.parse_objects(["two ships near the port"])["counts"].get("ship") == 2,
    }
    ok = all(checks.values())
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=os.path.join(ROOT, "data", "nwpu_captions"))
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "nwpu_captions.jsonl"))
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    convert(args.data_root, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
