# -*- coding: utf-8 -*-
r"""Convert the water-tank sonar HDF5 array to PNG class directories for the A23 second-acoustic-corpus test.

Run with the system interpreter (h5py is available there): python tools/_p1413_prepare_watertank.py
"""
from __future__ import annotations

import io
import json
import os

import h5py
import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "data", "second_sonar", "watertank96.hdf5")
OUT = os.path.join(REPO, "outputs", "analysis", "watertank96_png")
META = os.path.join(REPO, "outputs", "analysis", "watertank96_meta.json")


def to_u8(a):
    a = a.astype(np.float32)
    lo, hi = float(a.min()), float(a.max())
    if hi - lo < 1e-9:
        return np.zeros_like(a, dtype=np.uint8)
    return ((a - lo) / (hi - lo) * 255.0).round().astype(np.uint8)


def main() -> int:
    with h5py.File(SRC, "r") as f:
        classes = [c.decode() if isinstance(c, bytes) else str(c) for c in f["class_names"][:]]
        splits = {s: (f["x_" + s][:], f["y_" + s][:]) for s in ("train", "val", "test")}
    counts = {}
    for split, (x, y) in splits.items():
        for ci, name in enumerate(classes):
            d = os.path.join(OUT, split, name)
            os.makedirs(d, exist_ok=True)
        for i in range(len(x)):
            ci = int(y[i])
            im = Image.fromarray(to_u8(x[i, :, :, 0])).resize((224, 224), Image.BICUBIC).convert("RGB")
            im.save(os.path.join(OUT, split, classes[ci], "%s_%05d.png" % (split, i)))
        counts[split] = len(x)
    meta = {"source": "data/second_sonar/watertank96.hdf5", "classes": classes, "counts": counts,
            "conversion": "per-split min-max to uint8, bicubic resize to 224, RGB"}
    io.open(META, "w", encoding="utf-8", newline="").write(json.dumps(meta, indent=1))
    print("classes:", classes)
    print("counts:", counts)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
