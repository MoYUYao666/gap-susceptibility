# -*- coding: utf-8 -*-
"""Near-duplicate and split-leakage audit for the four A3 corpora (Tier-1 addition, 2026-11-07).

Computes 64-bit dHash for every image in the four corpora, finds near-duplicate pairs (Hamming distance <= 6) via
banded candidate generation, and reports how many such pairs cross the official train/test split. Outputs a JSON and a
markdown summary under paper_a3/analysis/.
"""
import io
import json
import os
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPORA = {
    "rsicd": (os.path.join(ROOT, "corpora", "rsicd", "full_human.jsonl"), os.path.join(ROOT, "data", "rsicd")),
    "nwpu_captions": (os.path.join(ROOT, "corpora", "nwpu_captions", "human.jsonl"), os.path.join(ROOT, "data", "nwpu_captions")),
    "rsitmd": (os.path.join(ROOT, "corpora", "rsitmd", "human.jsonl"), os.path.join(ROOT, "data", "rsitmd")),
    "dior_rsvg": (os.path.join(ROOT, "corpora", "dior_rsvg", "human.jsonl"), os.path.join(ROOT, "data", "dior_rsvg")),
}


def dhash(path):
    with Image.open(path) as im:
        im = im.convert("L").resize((9, 8), Image.Resampling.BILINEAR)
        px = list(im.getdata())
    bits = 0
    for row in range(8):
        for col in range(8):
            left = px[row * 9 + col]
            right = px[row * 9 + col + 1]
            bits = (bits << 1) | (1 if left > right else 0)
    return bits


def load_items(corpus):
    path, root = CORPORA[corpus]
    seen, items = set(), []
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            iid = r["image_id"]
            if iid in seen:
                continue
            seen.add(iid)
            items.append((iid, os.path.join(root, r["image_path"]), r.get("split", "")))
    return items


def hamming(a, b):
    return bin(a ^ b).count("1")


def audit(corpus):
    items = load_items(corpus)
    print(corpus, "images:", len(items), flush=True)
    hashes = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, h in enumerate(ex.map(lambda it: dhash(it[1]), items)):
            hashes.append(h)
            if (i + 1) % 5000 == 0:
                print("  hashed", i + 1, flush=True)
    bands = defaultdict(list)
    for idx, h in enumerate(hashes):
        for band in range(4):
            bands[(band, (h >> (16 * band)) & 0xFFFF)].append(idx)
    pairs = set()
    for bucket in bands.values():
        for a in range(len(bucket)):
            for b in range(a + 1, len(bucket)):
                i, j = bucket[a], bucket[b]
                pairs.add((min(i, j), max(i, j)))
    near, exact, cross = [], 0, 0
    for i, j in pairs:
        if hamming(hashes[i], hashes[j]) <= 6:
            near.append((i, j))
            if hashes[i] == hashes[j]:
                exact += 1
            if items[i][2] != items[j][2]:
                cross += 1
    return {
        "corpus": corpus,
        "images": len(items),
        "near_duplicate_pairs": len(near),
        "exact_duplicate_pairs": exact,
        "cross_split_near_duplicate_pairs": cross,
        "examples": [{"a": items[i][0], "b": items[j][0], "split_a": items[i][2], "split_b": items[j][2],
                      "hamming": hamming(hashes[i], hashes[j])} for i, j in near[:10]],
    }


def main():
    out = {"generated": "2026-11-07", "dhash_bits": 64, "threshold": 6, "corpora": []}
    for corpus in CORPORA:
        out["corpora"].append(audit(corpus))
    os.makedirs(os.path.join(ROOT, "analysis"), exist_ok=True)
    io.open(os.path.join(ROOT, "analysis", "near_duplicates.json"), "w", encoding="utf-8",
            newline="").write(json.dumps(out, indent=1, ensure_ascii=False))
    lines = ["# Near-duplicate / leakage audit (2026-11-07)", "",
             "dHash-64, near-duplicate threshold Hamming <= 6, pair candidates from four 16-bit bands.", "",
             "| corpus | images | near-dup pairs | exact-dup pairs | cross-split pairs |", "|---|---|---|---|---|"]
    for c in out["corpora"]:
        lines.append("| %s | %d | %d | %d | %d |" % (c["corpus"], c["images"], c["near_duplicate_pairs"],
                                                     c["exact_duplicate_pairs"], c["cross_split_near_duplicate_pairs"]))
    io.open(os.path.join(ROOT, "analysis", "near_duplicates.md"), "w", encoding="utf-8",
            newline="").write("\n".join(lines) + "\n")
    print("wrote analysis/near_duplicates.json")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
