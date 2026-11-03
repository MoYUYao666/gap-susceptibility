# -*- coding: utf-8 -*-
r"""Materialise VQA-RAD into the LLaVA training/evaluation layout used by the P3 scripts.

Writes
-----
data/vqa_rad/images/train_XXXX.png, data/vqa_rad/images/test_XXXX.png
paper3/train-vqarad.parquet     (instruction/question, input='', output=answer, image=file name)
paper3/test-vqarad.parquet      (same layout, held-out split)

    python tools/_p1515_p3_vqa_prepare.py [--limit N]
"""
from __future__ import annotations

import argparse
import io
import os

import pandas as pd
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "data", "vqa_rad", "data")
IMGS = os.path.join(REPO, "data", "vqa_rad", "images")
TRAIN_OUT = os.path.join(REPO, "paper3", "train-vqarad.parquet")
TEST_OUT = os.path.join(REPO, "paper3", "test-vqarad.parquet")


def convert(split: str, limit=None) -> pd.DataFrame:
    import glob
    f = sorted(glob.glob(os.path.join(SRC, f"{split}-*.parquet")))[0]
    d = pd.read_parquet(f)
    if limit:
        d = d.head(limit)
    os.makedirs(IMGS, exist_ok=True)
    rows = []
    for i, row in d.iterrows():
        b = row["image"]["bytes"]
        name = f"{split}_{i:05d}.png"
        p = os.path.join(IMGS, name)
        if not os.path.exists(p):
            Image.open(io.BytesIO(b)).convert("RGB").save(p)
        rows.append({"instruction": str(row["question"]), "input": "", "output": str(row["answer"]), "image": name})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    tr = convert("train", a.limit)
    te = convert("test", a.limit)
    tr.to_parquet(TRAIN_OUT)
    te.to_parquet(TEST_OUT)
    print(f"train {len(tr)} -> {os.path.relpath(TRAIN_OUT, REPO)}")
    print(f"test  {len(te)} -> {os.path.relpath(TEST_OUT, REPO)}")
    print("images:", len(os.listdir(IMGS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
