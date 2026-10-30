# -*- coding: utf-8 -*-
r"""Second-task probe: linear classification on the adapted image encoders.

Every main-grid cell saved its LoRA adapter. This script loads each adapter, extracts image features for the RSICD
train/test splits, fits a logistic-regression probe on the scene labels carried by the corpus metadata, and reports
top-1 accuracy per provenance arm. Same images, same adapter family, same schedule: only the text that trained the
adapter differs.

Usage
  python probe_classification.py [--site both] [--seed 0]
"""
import argparse
import collections
import io
import json
import os
import sys

import torch
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import train_lora_provenance as T  # noqa: E402

ARMS = ["human", "segmented", "templated", "metadata"]
OUT = os.path.join(ROOT, "runs", "classification_probe")


def load_rows(dataset="rsicd"):
    rows, seen = [], set()
    for line in io.open(os.path.join(ROOT, "corpora", dataset, "human.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        md = r.get("metadata") or {}
        classes = md.get("classes") or []
        label = classes[0] if classes else (md.get("class") or md.get("label"))
        if not label or r["image_id"] in seen:
            continue
        seen.add(r["image_id"])
        rows.append({"image_id": r["image_id"], "image_path": r["image_path"], "split": r["split"], "label": label})
    return rows


@torch.no_grad()
def embed(model, rows, images_root, preprocess, device, batch=64):
    feats = []
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        ims = []
        for r in chunk:
            with Image.open(os.path.join(images_root, r["image_path"])) as im:
                ims.append(preprocess(im.convert("RGB")))
        x = torch.stack(ims).to(device)
        feats.append(torch.nn.functional.normalize(model.encode_image(x), dim=-1).float().cpu())
    return torch.cat(feats).numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="both")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dataset", default="rsicd")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess, _, _ = T.build_model(os.path.join(ROOT, "models", "RemoteCLIP-ViT-B-32.pt"), args.site, device)
    images_root = os.path.join(ROOT, "data", args.dataset)
    rows = load_rows(args.dataset)
    train = [r for r in rows if r["split"] == "train"]
    test = [r for r in rows if r["split"] in ("test", "val")]
    print("train %d | test %d | classes %d" % (len(train), len(test), len(set(r["label"] for r in rows))))

    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score

    results = {}
    for arm in ARMS:
        prefix = args.dataset.split("_")[0]
        cand = os.path.join(ROOT, "runs", "adapter_export",
                            "%s_%s_10000_%s_s%d.pt" % (prefix, arm, args.site, args.seed))
        if not os.path.exists(cand):
            alt = [p for p in os.listdir(os.path.join(ROOT, "runs", "adapter_export"))
                   if p.startswith("%s_%s_" % (prefix, arm)) and args.site in p and p.endswith(".pt")]
            cand = os.path.join(ROOT, "runs", "adapter_export", alt[0]) if alt else None
        ckpt = cand
        if not ckpt or not os.path.exists(ckpt):
            print("  skip %s (no adapter)" % arm)
            continue
        state = torch.load(ckpt, map_location="cpu", weights_only=False)
        model.load_state_dict(state.get("state_dict", state), strict=False)
        xtr = embed(model, train, images_root, preprocess, device)
        xte = embed(model, test, images_root, preprocess, device)
        ytr = [r["label"] for r in train]
        yte = [r["label"] for r in test]
        clf = LogisticRegression(max_iter=2000, C=1.0)
        clf.fit(xtr, ytr)
        acc = accuracy_score(yte, clf.predict(xte))
        results[arm] = {"accuracy": round(float(acc), 4), "n_train": len(train), "n_test": len(test),
                        "checkpoint": os.path.basename(ckpt)}
        print("  %-10s accuracy %.4f" % (arm, acc))

    io.open(os.path.join(OUT, "classification_%s_%s_s%d.json" % (args.dataset, args.site, args.seed)),
            "w", encoding="utf-8", newline="").write(json.dumps(results, indent=1))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
