#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Materialise a small Flickr30k fixture from the archive, without unpacking the whole 4.4 GB zip.

The supplement's decoder experiment (`tools/_p47_qwen_train.py`) used Flickr30k with `--maxsamples 400`. The loader
expands each image into its five captions and then truncates to 400, so **80 images** are enough; 120 are extracted
for headroom.

Layout the loader expects (`src/dataset.py:create_dataloaders` -> `data_dir/flickr30k/`):

    /root/p3/flickr30k/flickr30k-images/<filename>
    /root/p3/flickr30k/flickr30k.json          [{"image": <filename>, "captions": [c1..c5]}, ...]

The archive's annotation CSV has one row per image with a JSON list of five captions in `raw`, plus `split` and
`filename`.

    python _p1153_make_flickr_fixture.py [--n 120] [--apply]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import zipfile
from pathlib import Path

FLICKR = Path("/root/p3/data/flickr")
ZIP = FLICKR / "flickr30k-images.zip"
CSV = FLICKR / "flickr_annotations_30k.csv"
OUT = Path("/root/p3/flickr30k")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=120, help="number of images to materialise (each yields 5 samples)")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if not ZIP.exists() or not CSV.exists():
        print("  missing archive or annotations")
        return 2
    print(f"  zip {ZIP.stat().st_size:,} bytes | csv {CSV.stat().st_size:,} bytes")
    with zipfile.ZipFile(ZIP) as zf:
        bad = zf.testzip()
        if bad is not None:
            print(f"  !! corrupt member: {bad}")
            return 1
        names = set(zf.namelist())
        print(f"  zip ok, {len(names)} members; e.g. {sorted(names)[:2]}")

        rows = []
        with io.open(CSV, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("split") != "train":
                    continue
                rows.append(r)
                if len(rows) >= a.n:
                    break
        print(f"  annotations selected: {len(rows)} train images")

        if not a.apply:
            print("  (dry run)")
            return 0

        img_dir = OUT / "flickr30k-images"
        img_dir.mkdir(parents=True, exist_ok=True)
        records, missing, written = [], [], 0
        for r in rows:
            fn = r["filename"].strip()
            member = fn if fn in names else next((m for m in names if m.endswith("/" + fn)), None)
            if member is None:
                missing.append(fn)
                continue
            dest = img_dir / fn
            if not dest.exists() or dest.stat().st_size == 0:
                with zf.open(member) as src, open(dest, "wb") as dst:
                    dst.write(src.read())
                written += 1
            caps = json.loads(r["raw"])
            records.append({"image": fn, "captions": caps})
        print(f"  written {written} images, missing {len(missing)}")
        if missing[:5]:
            print("   e.g. missing:", missing[:5])
        (OUT / "flickr30k.json").write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
        print(f"  wrote {OUT / 'flickr30k.json'} ({len(records)} images x 5 captions = {5 * len(records)} samples)")
        print(f"  images on disk: {len(list(img_dir.glob('*.jpg')))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
