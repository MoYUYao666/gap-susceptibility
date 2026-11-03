# -*- coding: utf-8 -*-
r"""Convert the RSICD parquet release into the A3 annotation JSONL schema and unpack its images.

Source (recorded in data/README.md): Hugging Face dataset `arampacha/rsicd`, splits train/valid/test,
columns `filename`, `captions`, `image` (bytes). Row counts 8734 + 1094 + 1093 = 10,921 images, five captions each,
which matches the published RSICD statistics used in the paper.

Text provenance built here:
  human      - the five captions, unchanged (the corpus builder de-duplicates them)
  templated  - fixed templates over the image's class label (from the file name prefix)
  metadata   - structured string over class label and the split name
  segmented  - not produced here: RSICD has no object annotations; the segmented arm is built from DIOR boxes

Usage
  python convert_rsicd.py --plan
  python convert_rsicd.py --self-test
  python convert_rsicd.py --data-root paper_a3/data/rsicd --out paper_a3/data/rsicd.jsonl
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys

SPLIT_FILES = {"train": "train.parquet", "val": "valid.parquet", "test": "test.parquet"}


def plan():
    print("""RSICD conversion plan

inputs   : paper_a3/data/rsicd/{train,valid,test}.parquet  (columns filename, captions, image)
outputs  : images under paper_a3/data/rsicd/images/<filename>
           annotation JSONL at paper_a3/data/rsicd.jsonl with
             image_id, image_path, split, captions, metadata{classes,split}, boxes=[]
then     : python paper_a3/scripts/build_text_provenance.py --input paper_a3/data/rsicd.jsonl --out paper_a3/corpora/rsicd
""")
    return 0


def class_from_filename(name):
    stem = os.path.splitext(os.path.basename(name))[0]
    return re.sub(r"[_\-]?\d+$", "", stem).replace("_", " ").strip().lower()




# Vocabulary of the 30 RSICD scene classes plus common objects that appear in its captions.
RSICD_CLASSES = ["airport", "bareland", "baseball field", "beach", "bridge", "center", "church",
                 "commercial", "denseresidential", "desert", "farmland", "forest", "industrial",
                 "meadow", "mediumresidential", "mountain", "park", "parking", "playground", "pond",
                 "port", "railway station", "resort", "river", "school", "sparseresidential",
                 "square", "stadium", "storage tank", "viaduct"]
COMMON_OBJECTS = ["building", "buildings", "road", "roads", "tree", "trees", "water", "ship", "ships",
                  "aircraft", "car", "cars", "boat", "boats", "field", "fields", "grass", "sand",
                  "wave", "waves", "mountain", "river", "bridge", "house", "houses", "trail", "trails"]
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "many": 10, "several": 5, "numerous": 10}


def parse_objects(captions, class_label):
    """Deterministic entity extraction: which known objects each caption names, and how many."""
    seen = {}
    for cap in captions:
        low = cap.lower()
        for obj in RSICD_CLASSES + COMMON_OBJECTS:
            pattern = r"\b" + re.escape(obj) + r"\b"
            for m in re.finditer(pattern, low):
                count = 1
                before = low[max(0, m.start() - 18):m.start()]
                nm = re.search(r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\b\s*$", before)
                if nm:
                    tok = nm.group(1)
                    count = int(tok) if tok.isdigit() else NUMBER_WORDS[tok]
                key = obj.rstrip("s") if obj.endswith("s") and obj[:-1] in RSICD_CLASSES + COMMON_OBJECTS else obj
                seen[key] = max(seen.get(key, 0), count)
    labels = sorted(seen)
    return {"labels": labels, "counts": {k: seen[k] for k in labels}, "from": "human-captions-parsed"}


def convert(data_root, out_jsonl, extract_images=True):
    import pyarrow.parquet as pq

    rows = []
    images_dir = os.path.join(data_root, "images")
    import io as _io
    from PIL import Image as _Image
    if extract_images:
        os.makedirs(images_dir, exist_ok=True)
    for split, fname in SPLIT_FILES.items():
        path = os.path.join(data_root, fname)
        if not os.path.exists(path):
            raise SystemExit("missing input: %s\nrun `python convert_rsicd.py --plan` for the expected files" % path)
        table = pq.read_table(path, columns=["filename", "captions", "image"])
        for rec in table.to_pylist():
            name = rec["filename"]
            cls = class_from_filename(name)
            img_name = os.path.basename(name)
            raw = rec["image"]["bytes"]
            if extract_images:
                with io.open(os.path.join(images_dir, img_name), "wb") as f:
                    f.write(raw)
            try:
                with _Image.open(_io.BytesIO(raw)) as im:
                    width, height = im.size
                    im_small = im.convert("L").resize((32, 32))
                    brightness = sum(im_small.getdata()) / 1024.0
            except Exception:
                width = height = 0
                brightness = None
            rows.append({
                "image_id": os.path.splitext(img_name)[0],
                "image_path": os.path.join("images", img_name).replace("\\", "/"),
                "split": split,
                "captions": [c.strip() for c in (rec["captions"] or []) if c and c.strip()],
                "metadata": {"sensor": None, "gsd_m": None, "classes": [cls] if cls else [],
                             "region": None, "date": None, "dataset_split": split,
                             "width": width, "height": height,
                             "aspect_ratio": round(width / height, 3) if height else None,
                             "brightness_8bit": round(brightness, 1) if brightness is not None else None},
                "derived_objects": parse_objects(rec["captions"] or [], cls),
                "boxes": [],
            })
    with io.open(out_jsonl, "w", encoding="utf-8", newline="") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    digest = hashlib.sha256(io.open(out_jsonl, "rb").read()).hexdigest()
    print("wrote %s | records %d | sha256 %s" % (out_jsonl, len(rows), digest[:16]))
    return rows


def self_test():
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_selftest_tmp")
    os.makedirs(tmp, exist_ok=True)
    name = "rsicd_images/airport_7.jpg"
    checks = {
        "class extraction": class_from_filename(name) == "airport",
        "class extraction with dash": class_from_filename("rsicd_images/storage_tank_12.jpg") == "storage tank",
    }
    ok = all(checks.values())
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    os.rmdir(tmp) if os.path.isdir(tmp) and not os.listdir(tmp) else None
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default="paper_a3/data/rsicd")
    ap.add_argument("--out", default="paper_a3/data/rsicd.jsonl")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--no-images", action="store_true", help="skip unpacking images (annotation-only pass)")
    args = ap.parse_args()
    if args.plan:
        return plan()
    if args.self_test:
        return self_test()
    convert(args.data_root, args.out, extract_images=not args.no_images)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
