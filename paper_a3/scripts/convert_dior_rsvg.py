# -*- coding: utf-8 -*-
r"""Convert DIOR-RSVG annotations into the A3 annotation JSONL schema.

Sources (recorded in data/README.md):
  Annotations.zip  - 17,402 VOC XML files, each with the image size, one or more objects, and a human description per
                     object (the DIOR-RSVG referring-expression data);
  img.zip          - JPEG images for a 7,500-image variant, kept for reference only (ids do not match the XMLs);
  JPEGImages.zip   - the 800x800 DIOR images whose names match the XMLs (fetched in parallel; images are needed for
                     training, not for building the text corpora).

Object boxes are used by build_text_provenance.py for the templated and segmented arms, so on this dataset those arms
are generated from real ground-truth annotations rather than from parsed captions.

Split note: the split lists shipped with the mirror index 38,320 queries (0-9,999), not image ids, so this converter
rebuilds an 80/10/10 split deterministically from a sha1 of the image id and records that as a deliberate deviation.

Usage
  python convert_dior_rsvg.py --self-test
  python convert_dior_rsvg.py [--out paper_a3/data/dior_rsvg.jsonl]
"""
import argparse
import hashlib
import io
import json
import os
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "dior_rsvg")
ANNOT_ZIP = os.path.join(DATA, "Annotations.zip")
OUT_JSONL = os.path.join(ROOT, "data", "dior_rsvg.jsonl")


def split_of(image_id):
    h = int(hashlib.sha1(image_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    return "train" if h < 80 else ("val" if h < 90 else "test")


def parse_xml(text):
    root = ET.fromstring(text)
    fname = (root.findtext("filename") or "").strip()
    size = root.find("size")
    width = int(size.findtext("width")) if size is not None else 0
    height = int(size.findtext("height")) if size is not None else 0
    boxes, descriptions = [], []
    for obj in root.findall("object"):
        label = (obj.findtext("name") or "").strip()
        bb = obj.find("bndbox")
        if bb is None or not label:
            continue
        boxes.append({
            "label": label,
            "x1": float(bb.findtext("xmin")), "y1": float(bb.findtext("ymin")),
            "x2": float(bb.findtext("xmax")), "y2": float(bb.findtext("ymax")),
            "image_w": width, "image_h": height,
        })
        desc = (obj.findtext("description") or "").strip()
        if desc:
            descriptions.append(desc)
    return fname, width, height, boxes, descriptions


def convert(out_jsonl):
    z = zipfile.ZipFile(ANNOT_ZIP)
    rows = []
    for name in sorted(n for n in z.namelist() if n.lower().endswith(".xml")):
        fname, width, height, boxes, descriptions = parse_xml(z.read(name))
        if not fname:
            fname = os.path.basename(name).replace(".xml", ".jpg")
        image_id = os.path.splitext(fname)[0]
        split = split_of(image_id)
        seen, caps = set(), []
        for d in descriptions:
            key = d.lower()
            if key not in seen:
                seen.add(key)
                caps.append(d)
        rows.append({
            "image_id": image_id,
            "image_path": os.path.join("images", fname).replace("\\", "/"),
            "split": split,
            "captions": caps,
            "metadata": {"sensor": None, "gsd_m": None,
                         "classes": sorted({b["label"] for b in boxes}),
                         "region": None, "date": None, "dataset_split": split,
                         "width": width, "height": height,
                         "aspect_ratio": round(width / height, 3) if height else None,
                         "brightness_8bit": None},
            "boxes": boxes,
        })
    with io.open(out_jsonl, "w", encoding="utf-8", newline="") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    digest = hashlib.sha256(io.open(out_jsonl, "rb").read()).hexdigest()
    from collections import Counter
    counts = Counter(r["split"] for r in rows)
    print("wrote %s | records %d | splits %s | sha256 %s" % (out_jsonl, len(rows), dict(counts), digest[:16]))
    return rows


def self_test():
    sample = """<annotation><filename>00001.jpg</filename><size><width>800</width><height>600</height><depth>3</depth></size>
    <object><name>golffield</name><bndbox><xmin>133</xmin><ymin>237</ymin><xmax>684</xmax><ymax>672</ymax></bndbox>
    <description>A green and brown golf field</description></object></annotation>"""
    fname, w, h, boxes, descs = parse_xml(sample)
    checks = {
        "filename parsed": fname == "00001.jpg",
        "size parsed": (w, h) == (800, 600),
        "box parsed": len(boxes) == 1 and boxes[0]["label"] == "golffield" and boxes[0]["x2"] == 684.0,
        "description parsed": descs == ["A green and brown golf field"],
        "split deterministic": split_of("00001") == split_of("00001"),
    }
    ok = all(checks.values())
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_JSONL)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    convert(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
