# -*- coding: utf-8 -*-
"""A1 full rare-species 400-class evaluation, memory-safe (2026-11-08, CPU).

The HF `datasets` loader used by `tools/a1_rr_e3_benchmarks.py` decodes all 4.1 GB of images and hits
MemoryError on the 16 GB laptop. This version streams the parquet files with pyarrow, decodes each image
only when it is embedded, and reuses the exact surgery-grid / tau estimator of the E3 script (imported as a
module) so the full-class row is directly comparable with the 50-class subset row already in the paper.
"""
import glob
import importlib.util
import io
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
os.chdir(REPO)

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402
from PIL import Image  # noqa: E402
from transformers import CLIPModel, CLIPProcessor  # noqa: E402

OUT = "outputs/analysis/a1_rr_e3_full_rare_2026-11-08.json"
DATA = "data/rare-species-full"
BATCH = 32
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def load_e3():
    p = os.path.join(REPO, "tools", "a1_rr_e3_benchmarks_fixed.py")
    spec = importlib.util.spec_from_file_location("a1e3", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def class_index(files):
    from collections import Counter
    counts = Counter()
    for f in files:
        t = pq.read_table(f, columns=["sciName"])
        counts.update(t.column("sciName").to_pylist())
    names = sorted(counts)
    idx = {n: i for i, n in enumerate(names)}
    return names, idx, counts


def main():
    e3 = load_e3()
    files = sorted(glob.glob(os.path.join(DATA, "*.parquet")))
    names, class_idx, counts = class_index(files)
    print("rare-species full: %d files, %d classes, %d images" % (len(files), len(names), sum(counts.values())), flush=True)
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", local_files_only=True).to(DEVICE).eval()
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", local_files_only=True)

    # stream embeddings
    feats, labels = [], []
    t0 = time.time()
    for f in files:
        pf = pq.ParquetFile(f)
        for batch in pf.iter_batches(batch_size=BATCH, columns=["file_name", "sciName"]):
            rows = batch.to_pylist()
            imgs = []
            labs = []
            for r in rows:
                name = r["sciName"]
                labs.append(class_idx[name])
                b = r["file_name"]
                data = b.get("bytes") if isinstance(b, dict) else None
                if data is None:
                    path = b.get("path") if isinstance(b, dict) else None
                    data = open(path, "rb").read()
                imgs.append(Image.open(io.BytesIO(data)).convert("RGB"))
            inp = proc(images=imgs, return_tensors="pt").to(DEVICE)
            with torch.no_grad():
                vout = model.vision_model(**inp)
                pooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                emb = F.normalize(model.visual_projection(pooled), dim=-1)
            feats.append(emb)
            labels.extend(labs)
    base = torch.cat(feats).to(DEVICE)
    labels = np.array(labels)
    print("embedded %d images in %.1fs" % (len(labels), time.time() - t0), flush=True)

    texts = ["a photo of a %s" % n.replace("_", " ") for n in names]
    ti = proc(text=texts, return_tensors="pt", padding=True).to(DEVICE)
    with torch.no_grad():
        tout = model.text_model(**ti)
        pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
        tf = F.normalize(model.text_projection(pooled), dim=-1).to(DEVICE)

    # Flickr30k gap direction, protocol-identical to the E3 script
    from torch.utils.data import DataLoader
    from src.dataset import Flickr30kDataset, _collate_fn
    ds_f = Flickr30kDataset("flickr30k", split="train", max_samples=None, pre_tokenize=True)
    val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
    loader = DataLoader(val_ds, batch_size=BATCH, shuffle=False, num_workers=0, collate_fn=_collate_fn)
    fi, ft = [], []
    with torch.no_grad():
        for b in loader:
            out = model(pixel_values=b["image"].to(DEVICE), input_ids=b["input_ids"].to(DEVICE),
                        attention_mask=b["attention_mask"].to(DEVICE), return_loss=False)
            fi.append(F.normalize(out.image_embeds, dim=-1))
            ft.append(F.normalize(out.text_embeds, dim=-1))
    flickr_gap = torch.cat(ft).mean(0) - torch.cat(fi).mean(0)
    self_gap = tf.mean(0) - base.mean(0)
    print("flickr gap %.4f self gap %.4f" % (flickr_gap.norm(), self_gap.norm()), flush=True)

    out = {
        "meta": {
            "script": "tools/a1_rr_e3_full_rare_mem.py",
            "experiment": "A1 full rare-species 400-class evaluation (subset-limit removal)",
            "model": "openai/clip-vit-base-patch32 (frozen)",
            "template": e3.TEMPLATE, "surgery_grid": e3.GRID, "topk_for_tau": e3.TOPK,
            "data": "data/rare-species-full (imageomics/rare-species parquet, 9 shards)",
            "n_classes_total": len(names), "n_images": int(len(labels)),
            "class_counts_min": int(min(counts.values())), "class_counts_max": int(max(counts.values())),
            "flickr30k_gap_norm": round(float(flickr_gap.norm()), 6),
        },
        "benchmarks": {},
    }
    for label, g in (("flickr30k", flickr_gap), ("self", self_gap)):
        r = e3.analyse("rare_species_full", tf, base, labels, g, label, model)
        out["benchmarks"]["rare_species_full_%s" % label] = {"loaded": True, "result": r}
        print("done", label, "top1@0", r["top1_frozen"], "tau@1", r["surgery"]["1.0"]["tau"], flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1, ensure_ascii=False))
    print("WROTE", OUT, flush=True)


if __name__ == "__main__":
    main()
