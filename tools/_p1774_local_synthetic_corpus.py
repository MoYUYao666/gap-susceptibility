# -*- coding: utf-8 -*-
r"""Build a deterministic local corpus for the SigLIP pipeline check, without any download.

The laptop can only reach ModelScope (hf-mirror and huggingface.co are unreachable from it), and the Flickr30k image
pack lives on the HF mirror, so the real corpus cannot be fetched locally. For the question B1 is meant to answer -
does the attention-mask / sequence-length fix remove the `device-side assert`? - real photographs are irrelevant: the
code path is identical for any image-caption pairs.

This script writes `local_runs/work/flickr30k/` with 1000 deterministic 224x224 images (colour/texture patterns) and
five caption variants each, i.e. 5000 pairs, matching the layout `src/dataset.py` expects. The generated data are
clearly synthetic and are only used for the local pipeline check; they are not paper data.
"""
import io
import json
import os

import numpy as np
from PIL import Image

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.join("local_runs", "work", "flickr30k")
IMG = os.path.join(ROOT, "flickr30k-images")
os.makedirs(IMG, exist_ok=True)
rng = np.random.default_rng(20261027)

COLOURS = ["red", "green", "blue", "cyan", "magenta", "yellow", "grey", "orange"]
SHAPES = ["disc", "square", "stripes", "checker"]

rows = []
for i in range(1000):
    base = rng.integers(0, 256, size=3).astype(np.uint8)
    img = np.zeros((224, 224, 3), np.uint8)
    img[:, :] = base
    kind = SHAPES[i % len(SHAPES)]
    colour = COLOURS[i % len(COLOURS)]
    yy, xx = np.mgrid[0:224, 0:224]
    if kind == "disc":
        mask = (yy - 112) ** 2 + (xx - 112) ** 2 < 60 ** 2
    elif kind == "square":
        mask = (abs(yy - 112) < 50) & (abs(xx - 112) < 50)
    elif kind == "stripes":
        mask = (yy // 16) % 2 == 0
    else:
        mask = ((yy // 16) + (xx // 16)) % 2 == 0
    img[mask] = np.array([c for c in "012"], dtype=np.uint8) if False else 220
    name = "synth%04d.jpg" % i
    Image.fromarray(img).save(os.path.join(IMG, name), quality=92)
    caps = ["a %s %s on a plain background" % (colour, kind),
            "a synthetic %s patch" % colour,
            "the %s pattern %d" % (kind, i),
            "a coarse %s texture" % colour,
            "an image of a %s shape" % kind]
    rows.append({"image": name, "captions": caps})

json.dump(rows, io.open(os.path.join(ROOT, "flickr30k.json"), "w", encoding="utf-8"), indent=0)
print("synthetic corpus:", len(rows), "images,", sum(len(r["captions"]) for r in rows), "pairs ->", ROOT)
