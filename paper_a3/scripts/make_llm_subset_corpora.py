# -*- coding: utf-8 -*-
r"""Build matched subset corpora for the LLM-caption arm comparison.

The LLM captions are generated for the first N unique images of the human corpus; every other provenance arm is
restricted to the same image list, one text per image, so all arms train on exactly the same images.

Outputs corpora/rsicd/subset<N>_<arm>.jsonl for human, segmented, templated, metadata and llmcaption.
"""
import argparse
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = ["human", "segmented", "templated", "metadata", "llmcaption"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="rsicd")
    ap.add_argument("--limit", type=int, default=3000)
    ap.add_argument("--intersect", action="store_true")
    args = ap.parse_args()
    base = os.path.join(ROOT, "corpora", args.dataset)

    order = []
    seen = set()
    for line in io.open(os.path.join(base, "human.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        if r["image_id"] in seen:
            continue
        seen.add(r["image_id"])
        order.append(r["image_id"])
    keep = order[:args.limit]
    if args.intersect:
        available = {}
        for arm in ARMS:
            path = os.path.join(base, arm + ".jsonl")
            if not os.path.exists(path):
                continue
            ids = set()
            for line in io.open(path, encoding="utf-8"):
                ids.add(json.loads(line)["image_id"])
            available[arm] = ids
        common = set.intersection(*available.values()) if available else set(keep)
        keep = [i for i in keep if i in common]
        print("intersection over %s: %d images" % (list(available), len(keep)))
    keep_set = set(keep)
    print("images kept: %d" % len(keep))

    for arm in ARMS:
        src = os.path.join(base, arm + ".jsonl")
        if not os.path.exists(src):
            print("  skip %s (missing)" % arm)
            continue
        out = os.path.join(base, "subset%d_%s.jsonl" % (len(keep), arm))
        written = set()
        with io.open(out, "w", encoding="utf-8", newline="") as f:
            for line in io.open(src, encoding="utf-8"):
                r = json.loads(line)
                if r["image_id"] not in keep_set or r["image_id"] in written:
                    continue
                written.add(r["image_id"])
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  wrote %s | rows %d" % (os.path.basename(out), len(written)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
