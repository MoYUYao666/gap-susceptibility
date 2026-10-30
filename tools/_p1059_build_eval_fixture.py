# -*- coding: utf-8 -*-
r"""Rebuild exactly the held-out pairs the LLaVA sweep measured, for the metric recomputation.

The sweep's evaluation set was COCO val2014 ids in the annotation file's iteration order, taking
`--samples 1500` for training and the next `--eval-pairs 500` for evaluation. The images and the annotation
file are no longer on this laptop (they were removed in the 2026-10-16 cleanup), so this script fetches only
the 500 held-out images from the COCO server and trims the annotation to the first 2000 ids.

What it produces, so the recomputation is verifiable:

* `cloud_eval/val2014/` -- the 500 held-out images;
* `cloud_eval/annotations/captions_val2014.json` -- trimmed to the first 2000 ids, which preserves the id
  order and therefore the same train/eval split as the archived run;
* `cloud_eval/MANIFEST.json` -- the ids, their order hash, the annotation hash, and the rule used.

    python tools/_p1059_build_eval_fixture.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "cloud_eval"
ANN_URL = "http://images.cocodataset.org/annotations/annotations_trainval2014.zip"
IMG_URL = "http://images.cocodataset.org/val2014/COCO_val2014_{:012d}.jpg"
TRAIN = 1500
EVAL = 500
TOTAL_IDS = 2000


def fetch(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ids_file = OUT / "MANIFEST.json"

    if not a.apply:
        print(f"  would build {OUT} with {EVAL} held-out images (ids {TRAIN}..{TRAIN + EVAL} of {TOTAL_IDS})")
        return 0

    (OUT / "val2014").mkdir(parents=True, exist_ok=True)
    (OUT / "annotations").mkdir(parents=True, exist_ok=True)

    # 1. annotations, trimmed to the first 2000 ids in file order
    ann_zip = OUT / "_ann.zip"
    print("  downloading the COCO val2014 annotations ...")
    ann_zip.write_bytes(fetch(ANN_URL, timeout=300))
    with zipfile.ZipFile(ann_zip) as zf:
        raw = zf.read("annotations/captions_val2014.json")
    ann = json.loads(raw)
    by_img: dict[int, list[str]] = {}
    for c in ann["annotations"]:
        by_img.setdefault(c["image_id"], []).append(c["caption"])
    ids = list(by_img)[:TOTAL_IDS]
    trimmed = {
        "info": ann.get("info", {}),
        "licenses": ann.get("licenses", []),
        "images": [im for im in ann["images"] if im["id"] in set(ids)],
        "annotations": [c for c in ann["annotations"] if c["image_id"] in set(ids)],
    }
    ann_path = OUT / "annotations" / "captions_val2014.json"
    ann_path.write_text(json.dumps(trimmed), encoding="utf-8")
    ann_zip.unlink()
    print(f"  annotations trimmed: {len(trimmed['images'])} images, {len(trimmed['annotations'])} captions")

    held = ids[TRAIN:TRAIN + EVAL]
    (OUT / "ids.txt").write_text("\n".join(str(i) for i in held), encoding="utf-8")

    # 2. the held-out images
    def grab(img_id: int) -> tuple[int, bool]:
        dst = OUT / "val2014" / f"COCO_val2014_{img_id:012d}.jpg"
        if dst.exists() and dst.stat().st_size > 1000:
            return img_id, True
        try:
            data = fetch(IMG_URL.format(img_id), timeout=90)
            dst.write_bytes(data)
            return img_id, dst.stat().st_size > 1000
        except Exception:
            return img_id, False

    print(f"  downloading {len(held)} held-out images ...")
    ok = 0
    with ThreadPoolExecutor(max_workers=16) as ex:
        for i, (_img_id, good) in enumerate(ex.map(grab, held), 1):
            ok += good
            if i % 100 == 0:
                print(f"    {i}/{len(held)}")
    print(f"  images present: {ok}/{len(held)}")

    manifest = {
        "purpose": ("Held-out evaluation pairs of the archived LLaVA sweep, rebuilt for the DG*/CG "
                    "recomputation under the canonical src/dg_star_tracker.py definition."),
        "source": "COCO val2014, annotations_trainval2014.zip and val2014/*.jpg",
        "rule": (f"ids in annotation-file iteration order; training = first {TRAIN}, "
                 f"held-out = next {EVAL}, total ids kept = {TOTAL_IDS}"),
        "n_held_out": len(held),
        "ids_sha256": hashlib.sha256(("\n".join(str(i) for i in held)).encode()).hexdigest(),
        "annotation_sha256": hashlib.sha256(ann_path.read_bytes()).hexdigest(),
        "images_ok": ok,
    }
    ids_file.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"  wrote {ids_file.relative_to(REPO)}")
    print(f"    ids sha256: {manifest['ids_sha256'][:16]}")
    print(f"    ann sha256: {manifest['annotation_sha256'][:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
