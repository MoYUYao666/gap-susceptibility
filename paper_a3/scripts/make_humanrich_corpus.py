# -*- coding: utf-8 -*-
r"""Build the human-rich provenance arm: the corpus's five human captions concatenated into one long description.

Motivation: GAIA (IEEE GRSM 2026) and OSM-CLIP (Applied Sciences 2026) report that rich generated/geographic text can
beat the text a corpus already has. This arm tests whether the difference is provenance or information density: it keeps
the images and the human source but packs five captions into one, so the pair carries more information than a single
caption at the same pair count.

Usage
  python make_humanrich_corpus.py --dataset rsicd
  python make_humanrich_corpus.py --dataset nwpu_captions
"""
import argparse
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = {"rsicd": os.path.join(ROOT, "data", "rsicd.jsonl"),
           "nwpu_captions": os.path.join(ROOT, "data", "nwpu_captions.jsonl")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=sorted(SOURCES))
    args = ap.parse_args()
    src = SOURCES[args.dataset]
    rows = [json.loads(l) for l in io.open(src, encoding="utf-8") if l.strip()]
    by_image = {}
    for r in rows:
        caps = [c.strip().rstrip(".") for c in r.get("captions", []) if c and c.strip()]
        if not caps:
            continue
        joined = ". ".join(caps) + "."
        key = r["image_id"]
        if key in by_image:
            continue
        by_image[key] = {
            "image_id": key,
            "image_path": r["image_path"],
            "split": r["split"],
            "text": joined,
            "metadata": r.get("metadata", {}),
            "derived_objects": r.get("derived_objects", {}),
            "boxes": [],
            "source": "human-rich",
        }
    out_dir = os.path.join(ROOT, "corpora", args.dataset)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "humanrich.jsonl")
    with io.open(out, "w", encoding="utf-8", newline="") as f:
        for r in by_image.values():
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote %s | %d images | mean words %.1f" % (
        out, len(by_image), sum(len(r["text"].split()) for r in by_image.values()) / max(1, len(by_image))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
