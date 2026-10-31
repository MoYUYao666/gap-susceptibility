# -*- coding: utf-8 -*-
r"""Convert the official RSITMD release into the A3 annotation JSONL schema.

Sources (recorded in data/README.md):
  official archive  RSITMD.zip (569 MB) from the authors' Baidu/Google Drive links in the AMFMN repository;
                    provides `dataset_RSITMD.json` (4,743 images, five captions each) and the images;
  mirror archive    RsITMD mirror on the model hub used only for the train/val/test split mapping, because the official
                    annotation JSON does not carry splits.

Outputs: images under paper_a3/data/rsitmd/images/<split>/<filename>, annotations at paper_a3/data/rsitmd.jsonl

Usage
  python convert_rsitmd.py --self-test
  python convert_rsitmd.py
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "rsitmd")
ANNOT = os.path.join(DATA, "annotations", "dataset_RSITMD.json")
MIRROR_ZIP = os.path.join(DATA, "rsitmd.zip")
OUT_JSONL = os.path.join(ROOT, "data", "rsitmd.jsonl")

OBJECT_VOCAB = ["airport", "bareland", "baseball field", "beach", "bridge", "center", "church", "commercial",
                "denseresidential", "desert", "farmland", "forest", "industrial", "meadow", "mediumresidential",
                "mountain", "park", "parking", "playground", "pond", "port", "railway station", "resort", "river",
                "school", "sparseresidential", "square", "stadium", "storage tank", "viaduct",
                "airplane", "aircraft", "ship", "boat", "boat", "car", "cars", "tree", "trees", "building",
                "buildings", "road", "roads", "grass", "water", "sand", "wave", "waves", "field", "fields",
                "house", "houses", "trail", "trails", "runway", "runways", "harbor", "harbour", "dock", "docks"]
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "many": 10, "several": 5, "numerous": 10, "some": 3}


def parse_objects(captions):
    seen = {}
    for cap in captions:
        low = cap.lower()
        for obj in OBJECT_VOCAB:
            m = re.search(r"\b" + re.escape(obj) + r"s?\b", low)
            if not m:
                continue
            count = 1
            before = low[max(0, m.start() - 18):m.start()]
            nm = re.search(r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\b\s*$", before)
            if nm:
                tok = nm.group(1)
                count = int(tok) if tok.isdigit() else NUMBER_WORDS[tok]
            label = obj[:-1] if obj.endswith("s") and obj[:-1] in OBJECT_VOCAB else obj
            if label.endswith("s") and label[:-1] in OBJECT_VOCAB:
                label = label[:-1]
            seen[label] = max(seen.get(label, 0), count)
    labels = sorted(seen)
    return {"labels": labels, "counts": {k: seen[k] for k in labels}, "from": "human-captions-parsed"}


def class_from_filename(name):
    stem = os.path.splitext(os.path.basename(name))[0]
    return re.sub(r"[_\-]?\d+$", "", stem).replace("_", " ").strip().lower()


def split_map():
    if not os.path.exists(MIRROR_ZIP):
        raise SystemExit("missing split source: %s" % MIRROR_ZIP)
    z = zipfile.ZipFile(MIRROR_ZIP)
    mapping = {}
    for n in z.namelist():
        parts = n.split("/")
        if len(parts) > 2 and parts[-1].lower().endswith((".tif", ".tiff", ".jpg", ".png")):
            mapping[parts[-1]] = parts[1]
    return mapping


def convert():
    from PIL import Image
    data = json.loads(io.open(ANNOT, encoding="utf-8-sig").read())
    images = data["images"]
    splits = split_map()
    z = zipfile.ZipFile(MIRROR_ZIP)
    img_dir = os.path.join(DATA, "images")
    os.makedirs(img_dir, exist_ok=True)
    rows = []
    for rec in images:
        fname = rec["filename"]
        split = splits.get(fname, "train")
        out_dir = os.path.join(img_dir, split)
        os.makedirs(out_dir, exist_ok=True)
        target = os.path.join(out_dir, fname)
        if not os.path.exists(target):
            src = next((n for n in z.namelist() if n.endswith("/" + fname)), None)
            if src is None:
                raise SystemExit("image %s not found in %s" % (fname, MIRROR_ZIP))
            with io.open(target, "wb") as f:
                f.write(z.read(src))
        try:
            with Image.open(target) as im:
                width, height = im.size
                small = im.convert("L").resize((32, 32))
                brightness = sum(small.getdata()) / 1024.0
        except Exception:
            width = height = 0
            brightness = None
        captions = [s["raw"].strip() for s in rec.get("sentences", []) if s.get("raw", "").strip()]
        rows.append({
            "image_id": os.path.splitext(fname)[0],
            "image_path": os.path.join("images", split, fname).replace("\\", "/"),
            "split": split,
            "captions": captions,
            "metadata": {"sensor": None, "gsd_m": None, "classes": [class_from_filename(fname)],
                         "region": None, "date": None, "dataset_split": split,
                         "width": width, "height": height,
                         "aspect_ratio": round(width / height, 3) if height else None,
                         "brightness_8bit": round(brightness, 1) if brightness is not None else None},
            "derived_objects": parse_objects(captions),
            "boxes": [],
        })
    with io.open(OUT_JSONL, "w", encoding="utf-8", newline="") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    digest = hashlib.sha256(io.open(OUT_JSONL, "rb").read()).hexdigest()
    print("wrote %s | records %d | sha256 %s" % (OUT_JSONL, len(rows), digest[:16]))
    return rows


def self_test():
    checks = {
        "class extraction": class_from_filename("baseballfield_452.tif") == "baseballfield",
        "parsed object with count": parse_objects(["two ships near the port"])["counts"].get("ship") == 2,
        "parsed object lowercase": "boat" in parse_objects(["A boat on the river"])["labels"],
    }
    ok = all(checks.values())
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    convert()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
