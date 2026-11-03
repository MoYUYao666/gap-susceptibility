# -*- coding: utf-8 -*-
r"""Record the exact evaluation protocol the strict-freeze control runs under (CPU only).

Two facts are needed before any CG/DG/R@1 number from the control can be read correctly, and
neither is stated in the paper's table caption:

1. WHICH data_dir RESOLVES.  `create_dataloaders` builds
   `data_root = os.path.join(data_dir, dataset_name)` and `Flickr30kDataset` then looks for
   `<data_root>/flickr30k.json`.  In this checkout the annotations are at
   `./flickr30k/flickr30k.json`, so `--data-dir .` (the control's default) resolves to
   `./flickr30k` and works; `--data-dir flickr30k` does NOT (it would need
   `flickr30k/flickr30k/`).  Recorded so a future run cannot silently point elsewhere.

2. HOW BIG THE RETRIEVAL GALLERY IS.  `max_samples` is applied to the DATASET *before* the
   80/10/10 `random_split` (src/dataset.py:401 then :416-425), so with the control's
   `--max-samples 5000` the retrieval evaluation runs on 0.1 x 5000 = 500 pairs, not 1000.
   Chance R@1 is therefore 1/500 = 0.002.  This is what makes the published R@1 column
   (e.g. 0.624 for CLIP B/32 text-only) interpretable rather than merely above zero.

OUTPUT
    outputs/analysis/dinov2_hetero/protocol_check.json

USAGE
    python tools/_p293c_protocol_check.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.chdir(REPO)
sys.path.insert(0, str(REPO))

from src.dataset import Flickr30kDataset, create_dataloaders  # noqa: E402

OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "protocol_check.json"
MAX_SAMPLES = 5000
BATCH = 128


def main():
    candidates = [".", "", "flickr30k", "data", "data/flickr30k"]
    resolved, table = None, []
    for c in candidates:
        root = os.path.join(c, "flickr30k") if c else "flickr30k"
        ok = os.path.exists(os.path.join(root, "flickr30k.json"))
        table.append({"data_dir": c, "data_root": root, "annotations_found": ok})
        print("data_dir=%-16r -> data_root=%-24r  %s" % (c, root, "OK" if ok else "missing"))
        if ok and resolved is None:
            resolved = c
    assert resolved is not None, "no candidate data_dir resolves to flickr30k.json"
    print("\nresolved data_dir = %r" % resolved)

    root = os.path.join(resolved, "flickr30k") if resolved else "flickr30k"
    ds_all = Flickr30kDataset(root, split="train", image_size=224, max_samples=None,
                              pre_tokenize=False)
    ds_cap = Flickr30kDataset(root, split="train", image_size=224, max_samples=MAX_SAMPLES,
                              pre_tokenize=False)
    n = len(ds_cap)
    tr, va, te = create_dataloaders(dataset_name="flickr30k", data_dir=resolved,
                                    batch_size=BATCH, max_samples=MAX_SAMPLES)

    out = {
        "script": "tools/_p293c_protocol_check.py",
        "source": "src/dataset.py:374-437 (create_dataloaders + random_split generator seed 42)",
        "data_dir_resolution": table,
        "data_dir_used": resolved,
        "corpus_captions_total": len(ds_all),
        "max_samples": MAX_SAMPLES,
        "cap_applied_before_split": True,
        "split_sizes": {"train": int(0.8 * n), "val": int(0.1 * n),
                        "test": n - int(0.8 * n) - int(0.1 * n)},
        "loader_dataset_sizes": {"train": len(tr.dataset), "val": len(va.dataset),
                                 "test": len(te.dataset)},
        "retrieval_gallery_pairs": len(va.dataset),
        "chance_R@1": 1.0 / len(va.dataset),
        "why_it_matters": (
            "the published R@1 column of the strict-freeze table is measured on a 500-pair "
            "gallery (chance 0.002), because max_samples caps the dataset before the split"),
    }
    assert out["split_sizes"]["val"] == len(va.dataset)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(json.dumps({k: v for k, v in out.items() if k != "data_dir_resolution"}, indent=2))
    print("[ok] wrote", OUT)


if __name__ == "__main__":
    main()
