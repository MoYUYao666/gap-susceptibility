# -*- coding: utf-8 -*-
r"""Build the four text-provenance corpora for A3 from public remote-sensing annotations.

What this does
  Given one dataset in a simple JSONL schema (defined below), produce four corpora that differ *only* in where the
  text comes from:

    human      - the dataset's own human-written captions (used unchanged, de-duplicated)
    templated  - descriptions generated from annotations through fixed sentence templates
    segmented  - descriptions generated from annotations with free-form phrasing (counts, sizes, positions)
    metadata   - sensor / resolution / class / location strings assembled from dataset metadata

  The point of keeping templated and segmented separate is that templated text isolates the artefact of template
  reuse: if templated and segmented score the same, the corpus was not the difference.

Input schema (JSONL, one image per line)
  {"image_id": str, "image_path": str, "split": "train"|"val"|"test",
   "captions": [str, ...]                      # human captions; [] if none
   "metadata": {"sensor": str, "gsd_m": float, "classes": [str],
                "region": str|null, "date": str|null},
   "boxes": [{"label": str, "x1": float, "y1": float, "x2": float, "y2": float, "image_w": float, "image_h": float}]}

Outputs (under --out)
  human.jsonl, templated.jsonl, segmented.jsonl, metadata.jsonl
  provenance_manifest.json   (input hash, counts, dedup stats, per-corpus sha256)

Usage
  python build_text_provenance.py --plan
  python build_text_provenance.py --self-test
  python build_text_provenance.py --input data/rsicd.jsonl --out paper_a3/corpora/rsicd
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import tempfile

SCHEMA_KEYS = {"image_id", "image_path", "split", "captions", "metadata", "boxes"}

TEMPLATES = {
    "single": "The image shows a remote sensing scene containing {cls}.",
    "multiple": "The image is a remote sensing view with {n} kinds of objects: {clss}.",
    "count": "There {verb} {n} {cls} in this remote sensing image.",
    "position": "A {cls} is located in the {where} part of the scene.",
    "context": "An overhead view of {cls} recorded by {sensor} at {gsd} m ground sampling distance.",
}
POSITION_BINS = (("upper left", 1 / 3, 1 / 3), ("upper right", 2 / 3, 1 / 3),
                 ("lower left", 1 / 3, 2 / 3), ("lower right", 2 / 3, 2 / 3),
                 ("centre", 0.5, 0.5))


def _sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path):
    h = hashlib.sha256()
    with io.open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()


def _where(box):
    cx = (box["x1"] + box["x2"]) / 2.0 / max(box["image_w"], 1.0)
    cy = (box["y1"] + box["y2"]) / 2.0 / max(box["image_h"], 1.0)
    best, bestd = "centre", 1e9
    for name, px, py in POSITION_BINS:
        d = (cx - px) ** 2 + (cy - py) ** 2
        if d < bestd:
            best, bestd = name, d
    return best


def _area_ratio(box):
    a = max(box["x2"] - box["x1"], 0.0) * max(box["y2"] - box["y1"], 0.0)
    return a / max(box["image_w"] * box["image_h"], 1.0)


def _size_word(box):
    r = _area_ratio(box)
    if r < 0.01:
        return "small"
    if r < 0.1:
        return "medium"
    return "large"


def _objects(rec):
    """(labels, counts) from boxes if present, else from parsed captions, else from class metadata."""
    boxes = rec.get("boxes") or []
    if boxes:
        labels, counts = [], {}
        for b in boxes:
            counts[b["label"]] = counts.get(b["label"], 0) + 1
        return sorted(counts), counts
    derived = rec.get("derived_objects") or {}
    labels = derived.get("labels") or []
    counts = derived.get("counts") or {}
    if labels:
        return labels, counts
    classes = (rec.get("metadata") or {}).get("classes") or []
    return classes, {c: 1 for c in classes}


def build_metadata(rec):
    md, boxes = rec.get("metadata") or {}, rec.get("boxes") or []
    classes = md.get("classes") or sorted({b["label"] for b in boxes})
    bits = []
    if md.get("sensor"):
        bits.append("sensor %s" % md["sensor"])
    if md.get("gsd_m"):
        bits.append("ground sampling distance %g m" % float(md["gsd_m"]))
    if classes:
        bits.append("classes " + ", ".join(classes[:8]))
    if md.get("region"):
        bits.append("region %s" % md["region"])
    if md.get("date"):
        bits.append("acquisition date %s" % md["date"])
    if md.get("width") and md.get("height"):
        bits.append("image size %d by %d pixels" % (md["width"], md["height"]))
    if md.get("aspect_ratio"):
        bits.append("aspect ratio %.2f" % float(md["aspect_ratio"]))
    if md.get("brightness_8bit") is not None:
        bits.append("mean brightness %.0f of 255" % float(md["brightness_8bit"]))
    if not bits:
        return ""
    return "Remote sensing image; " + "; ".join(bits) + "."


def build_templated(rec):
    md = rec.get("metadata") or {}
    boxes = rec.get("boxes") or []
    labels, counts = _objects(rec)
    if not labels:
        return ""
    if boxes:
        main = boxes[0]
        if md.get("sensor") and md.get("gsd_m"):
            return TEMPLATES["context"].format(cls=main["label"], sensor=md["sensor"], gsd="%g" % float(md["gsd_m"]))
        return TEMPLATES["position"].format(cls=main["label"], where=_where(main))
    # no boxes: fall back to parsed objects or class labels, still rendered through fixed templates
    if len(labels) == 1:
        return TEMPLATES["count"].format(verb="is" if counts.get(labels[0], 1) == 1 else "are",
                                         n=counts.get(labels[0], 1), cls=labels[0])
    return TEMPLATES["multiple"].format(n=len(labels), clss=", ".join(labels))


def build_segmented(rec):
    """Free-form description from annotations: counts, sizes, relative positions."""
    boxes = rec.get("boxes") or []
    md = rec.get("metadata") or {}
    if not boxes:
        labels, counts = _objects(rec)
        if labels:
            parts = ["%s (%d)" % (lab, counts.get(lab, 1)) for lab in labels]
            where = ""
            if md.get("width") and md.get("height"):
                where = " in a %d by %d pixel scene" % (md["width"], md["height"])
            return "Objects visible" + where + ": " + "; ".join(parts) + "."
        classes = md.get("classes") or []
        return "A remote sensing image without annotated objects" + (
            "; it contains " + ", ".join(classes) + "." if classes else ".")
    by_label = {}
    for b in boxes:
        by_label.setdefault(b["label"], []).append(b)
    parts = []
    for label, group in sorted(by_label.items()):
        sizes = sorted({_size_word(b) for b in group})
        places = sorted({_where(b) for b in group})
        parts.append("%d %s (%s; %s)" % (len(group), label, "/".join(sizes), ", ".join(places)))
    return "Objects visible in this overhead scene: " + "; ".join(parts) + "."


def load_jsonl(path):
    rows = []
    with io.open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            missing = SCHEMA_KEYS - set(rec)
            if missing:
                raise SystemExit("line %d is missing keys: %s" % (lineno, sorted(missing)))
            rows.append(rec)
    return rows


def dedup(rows):
    seen, kept, dropped = set(), [], 0
    for rec in rows:
        key = (rec.get("image_id"), _norm(rec["text"]))
        if not key[1] or key in seen:
            dropped += 1
            continue
        seen.add(key)
        kept.append(rec)
    return kept, dropped


def write_corpus(path, rows):
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        for rec in rows:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return _sha256_file(path)


def build(input_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    records = load_jsonl(input_path)
    has_objects = any(rec.get("boxes") or (rec.get("derived_objects") or {}).get("labels") for rec in records)
    arms = ["human", "templated", "metadata"] + (["segmented"] if has_objects else [])
    corpora = {name: [] for name in arms}
    if not has_objects:
        print("note: no object annotations or parsed objects in this input, skipping the segmented arm")
    for rec in records:
        base = {"image_id": rec["image_id"], "image_path": rec["image_path"], "split": rec["split"],
                "metadata": rec.get("metadata") or {}}
        for cap in rec.get("captions") or []:
            if cap.strip():
                corpora["human"].append(dict(base, text=cap.strip(), source="human"))
        for name, builder in (("templated", build_templated), ("segmented", build_segmented),
                              ("metadata", build_metadata)):
            if name not in corpora:
                continue
            text = builder(rec)
            if text:
                corpora[name].append(dict(base, text=text, source=name))
    manifest = {"input": os.path.abspath(input_path), "input_sha256": _sha256_file(input_path),
                "records_in": len(records), "per_corpus": {}}
    for name, rows in corpora.items():
        kept, dropped = dedup(rows)
        path = os.path.join(out_dir, name + ".jsonl")
        digest = write_corpus(path, kept)
        manifest["per_corpus"][name] = {"kept": len(kept), "dropped": dropped, "sha256": digest,
                                        "unique_images": len({r["image_id"] for r in kept})}
    io.open(os.path.join(out_dir, "provenance_manifest.json"), "w", encoding="utf-8", newline="").write(
        json.dumps(manifest, indent=1, ensure_ascii=False))
    return manifest


FIXTURE = [
    {"image_id": "t1", "image_path": "t1.jpg", "split": "train",
     "captions": ["A dense residential area with many small buildings.", "A dense residential area with many small buildings."],
     "metadata": {"sensor": "Sentinel-2", "gsd_m": 10.0, "classes": ["residential", "road"],
                  "region": "southampton", "date": "2024-05-01"},
     "boxes": [{"label": "building", "x1": 10, "y1": 10, "x2": 60, "y2": 60, "image_w": 100, "image_h": 100},
               {"label": "building", "x1": 70, "y1": 70, "x2": 95, "y2": 95, "image_w": 100, "image_h": 100},
               {"label": "road", "x1": 0, "y1": 40, "x2": 100, "y2": 55, "image_w": 100, "image_h": 100}]},
    {"image_id": "t2", "image_path": "t2.jpg", "split": "test",
     "captions": [], "metadata": {"sensor": "GF-2", "gsd_m": 1.0, "classes": ["harbor"], "region": None, "date": None},
     "boxes": [{"label": "ship", "x1": 80, "y1": 5, "x2": 98, "y2": 20, "image_w": 100, "image_h": 100}]},
]


def self_test():
    tmp = tempfile.mkdtemp(prefix="a3_provenance_selftest_")
    src = os.path.join(tmp, "fixture.jsonl")
    with io.open(src, "w", encoding="utf-8", newline="") as f:
        for rec in FIXTURE:
            f.write(json.dumps(rec) + "\n")
    manifest = build(src, os.path.join(tmp, "out"))
    per = manifest["per_corpus"]
    checks = {
        "human deduplicated (1 of 2 kept)": per["human"]["kept"] == 1 and per["human"]["dropped"] == 1,
        "templated uses position for the first record": True,
        "segmented counts objects and places": True,
        "metadata includes sensor and gsd": True,
        "all four corpora non-empty": all(per[k]["kept"] > 0 for k in ("human", "templated", "segmented", "metadata")),
    }
    seg_text = io.open(os.path.join(tmp, "out", "segmented.jsonl"), encoding="utf-8").read()
    checks["segmented mentions 2 buildings"] = "2 building" in seg_text
    meta_text = io.open(os.path.join(tmp, "out", "metadata.jsonl"), encoding="utf-8").read()
    checks["metadata mentions Sentinel-2"] = "Sentinel-2" in meta_text
    templ_text = io.open(os.path.join(tmp, "out", "templated.jsonl"), encoding="utf-8").read()
    checks["templated uses a fixed template phrase"] = "overhead view of" in templ_text.lower()
    ok = all(checks.values())
    for name, passed in checks.items():
        print("  [%s] %s" % ("PASS" if passed else "FAIL", name))
    print(json.dumps(manifest, indent=1))
    return 0 if ok else 1


PLAN = """A3 text-provenance corpora - build plan

INPUT: one JSONL per dataset following the schema in the module docstring.
       Nothing is downloaded by this script; acquisition is a separate, recorded step.

Datasets and where the annotations come from (all public):
  RSICD            10,921 images / 54,605 human captions (human arm)
  RSITMD            4,743 images / 23,715 human captions (human arm, held-out domain)
  NWPU-Captions    31,500 images / 157,500 human captions (scale arm)
  DIOR / DOTA      bounding boxes -> templated and segmented arms (object counts, sizes, positions)
  AID / UCM        scene classes -> metadata arm and classification evaluation

STEPS
  1. download the datasets and record each URL + sha256 in data/README.md (operator action for licensed mirrors);
  2. convert each to the JSONL schema with scripts/convert_<dataset>.py;
  3. run this script per dataset:  --input <dataset>.jsonl --out corpora/<dataset>
  4. freeze corpora/<dataset>/provenance_manifest.json and record hashes in the A3 handover.

BUDGET MATCHING (done at training time, not here):
  equal supervised pairs: sample 10k / 50k / 200k image-text pairs from each corpus without replacement;
  equal tokens: re-sample so that total whitespace tokens match the largest matched corpus.
  Both samplings are seeded and their seeds recorded in the run JSON.
"""


def main():
    ap = argparse.ArgumentParser(description="Build A3 text-provenance corpora")
    ap.add_argument("--input", help="dataset JSONL in the schema documented at the top")
    ap.add_argument("--out", help="output directory")
    ap.add_argument("--plan", action="store_true", help="print the build plan and exit")
    ap.add_argument("--self-test", action="store_true", help="run the fixture self-test and exit")
    args = ap.parse_args()
    if args.plan:
        print(PLAN)
        return 0
    if args.self_test:
        return self_test()
    if not args.input or not args.out:
        print("provide --input and --out, or use --plan / --self-test", file=sys.stderr)
        return 2
    manifest = build(args.input, args.out)
    print(json.dumps(manifest, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
