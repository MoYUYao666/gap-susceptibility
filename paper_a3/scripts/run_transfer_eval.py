# -*- coding: utf-8 -*-
r"""Cross-corpus transfer matrix (strengthening experiment 3).

Take adapters trained on one corpus and evaluate the same retrieval task on the test splits of the OTHER corpora, with
frozen adapters (inference only). The question: does the provenance ordering survive a change of corpus?

Adapters come from the main grid at the joint site (`both`), seeds 0, for the human, templated and metadata arms of
RSICD and NWPU-Captions. Evaluation is text-to-image and image-to-text R@1 on the target corpus's test split, with the
target corpus's own images (no target training).

Outputs
  analysis/transfer_matrix.json   rows: source corpus, arm, target corpus, R@1 i2t/t2i, n
  analysis/transfer_matrix.md     the same as a Markdown table

Usage
  python run_transfer_eval.py [--seeds 0] [--sources rsicd,nwpu_captions]
"""
import argparse
import glob
import io
import json
import os
import sys

import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import train_lora_provenance as T  # reuse the model builder and the metrics

DATASETS = {"rsicd": "data/rsicd", "rsitmd": "data/rsitmd", "nwpu_captions": "data/nwpu_captions"}
TARGETS = ["rsicd", "rsitmd", "nwpu_captions"]
ARMS = ["human", "templated", "metadata"]


class EvalSet(Dataset):
    def __init__(self, rows, images_root, preprocess, tokenizer):
        self.rows = rows
        self.images_root = images_root
        self.preprocess = preprocess
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        with Image.open(os.path.join(self.images_root, r["image_path"])) as im:
            image = self.preprocess(im.convert("RGB"))
        return image, r["text"]


def load_target(dataset, max_pairs=600):
    path = os.path.join(ROOT, "corpora", dataset, "budgets", "human_10000_pairs.jsonl")
    if not os.path.exists(path):
        path = os.path.join(ROOT, "corpora", dataset, "human.jsonl")
    rows = [json.loads(l) for l in io.open(path, encoding="utf-8") if l.strip()]
    test = [r for r in rows if r["split"] == "test"][:max_pairs]
    return test if test else rows[-max_pairs:]


def evaluate_adapter(adapter_path, model, rows, images_root, device, preprocess, tokenizer, batch=32):
    state = torch.load(adapter_path, map_location="cpu", weights_only=False)
    missing, unexpected = model.load_state_dict(state["state_dict"], strict=False)
    model.eval()
    ds = EvalSet(rows, images_root, preprocess, tokenizer)
    loader = DataLoader(ds, batch_size=batch, shuffle=False)
    img_embs, txt_embs = [], []
    with torch.no_grad():
        for images, texts in loader:
            images = images.to(device)
            tokens = tokenizer(list(texts)).to(device)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                img_embs.append(F.normalize(model.encode_image(images), dim=-1).float())
                txt_embs.append(F.normalize(model.encode_text(tokens), dim=-1).float())
    return T.retrieval_metrics(torch.cat(img_embs), torch.cat(txt_embs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.path.join(ROOT, "models", "RemoteCLIP-ViT-B-32.pt"))
    ap.add_argument("--source-runs", default=os.path.join(ROOT, "runs", "full_10k"))
    ap.add_argument("--seeds", default="0")
    ap.add_argument("--sources", default="rsicd,nwpu_captions")
    args = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    seeds = [int(s) for s in args.seeds.split(",")]

    model, preprocess, tokenizer, adapted = T.build_model(args.model, "both", device)
    results = []
    for source in [s.strip() for s in args.sources.split(",") if s.strip()]:
        for arm in ARMS:
            for seed in seeds:
                adapter = os.path.join(args.source_runs, "%s_%s_10000_both_s%d.pt" % (source, arm, seed))
                if not os.path.exists(adapter):
                    print("missing adapter:", adapter)
                    continue
                for target in TARGETS:
                    rows = load_target(target)
                    metrics = evaluate_adapter(adapter, model, rows, os.path.join(ROOT, DATASETS[target]),
                                               device, preprocess, tokenizer)
                    results.append({"source_corpus": source, "arm": arm, "seed": seed, "target_corpus": target,
                                    "n": len(rows), **metrics})
                    print("%-15s %-9s s%d -> %-15s R@1 i2t %.4f t2i %.4f" % (
                        source, arm, seed, target, metrics["R@1_i2t"], metrics["R@1_t2i"]), flush=True)

    os.makedirs(os.path.join(ROOT, "analysis"), exist_ok=True)
    io.open(os.path.join(ROOT, "analysis", "transfer_matrix.json"), "w", encoding="utf-8", newline="").write(
        json.dumps({"note": "frozen adapters from the main grid, evaluated on other corpora's test splits",
                    "rows": results}, indent=1))
    md = ["# Cross-corpus transfer matrix", "",
          "Frozen adapters trained on the source corpus, evaluated on the target corpus test split (no target training).",
          "", "| source | arm | target | n | R@1 i2t | R@1 t2i |", "|---|---|---|---|---|---|"]
    for r in results:
        md.append("| %s | %s | %s | %d | %.4f | %.4f |" % (r["source_corpus"], r["arm"], r["target_corpus"],
                                                            r["n"], r["R@1_i2t"], r["R@1_t2i"]))
    io.open(os.path.join(ROOT, "analysis", "transfer_matrix.md"), "w", encoding="utf-8", newline="").write("\n".join(md) + "\n")
    print("wrote analysis/transfer_matrix.{json,md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
