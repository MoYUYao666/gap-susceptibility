# -*- coding: utf-8 -*-
r"""Build the length-control corpora: the same human caption repeated five times.

This is the control for the human-rich arm: same number of words as five concatenated captions, but no additional
information. If the human-rich gain came from token count alone, this arm would show it.

Outputs corpora/<dataset>/repeated.jsonl with one text per image.
"""
import argparse
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(dataset, repeats=5):
    src = os.path.join(ROOT, "corpora", dataset, "human.jsonl")
    rows = [json.loads(line) for line in io.open(src, encoding="utf-8") if line.strip()]
    seen = {}
    for r in rows:
        if r["image_id"] in seen:
            continue
        seen[r["image_id"]] = r
    out = os.path.join(ROOT, "corpora", dataset, "repeated.jsonl")
    lengths = []
    with io.open(out, "w", encoding="utf-8", newline="") as f:
        for image_id, r in seen.items():
            text = " ".join([r["text"]] * repeats)
            lengths.append(len(text.split()))
            f.write(json.dumps({
                "image_id": image_id, "image_path": r["image_path"], "split": r["split"],
                "text": text, "metadata": r.get("metadata", {}), "derived_objects": {},
                "boxes": [], "source": "repeated",
            }, ensure_ascii=False) + "\n")
    print("wrote %s | images %d | mean words %.1f" % (out, len(seen), sum(lengths) / len(lengths)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="rsicd,nwpu_captions")
    args = ap.parse_args()
    for ds in [d.strip() for d in args.dataset.split(",") if d.strip()]:
        build(ds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
