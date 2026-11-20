# -*- coding: utf-8 -*-
"""A4: frozen-encoder feature extraction over six datasets and five encoders.

Saves one .npz per (encoder, dataset) with L2-normalised image and text embeddings plus metadata.
No training and no test-set tuning: this script only materialises frozen features for the readout audit.
"""
from __future__ import annotations
import argparse, csv, io, json, os, re, zipfile
import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "outputs", "a4", "features")
CATALOG = os.path.join(REPO, "outputs", "a4", "a4_dataset_catalog.json")

ENCODERS = {
    "clip-b32": ("hfclip", "models/clip-vit-base-patch32"),
    "clip-b16": ("hfclip", "models/clip-vit-base-patch16"),
    "clip-l14": ("hfclip", "models/clip-vit-large-patch14"),
    "siglip": ("siglip", "models/siglip-base-patch16-224"),
    "openclip": ("openclip", "models/openclip"),
}


def _class_dataset(root, dataset):
    classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    items = []
    for c in classes:
        d = os.path.join(root, c)
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith((".jpg", ".jpeg", ".png")):
                items.append((os.path.join(d, fn), "a photo of a " + c.replace("_", " "), c.replace("_", " ")))
    return items


def build_items(dataset, limit=None):
    if dataset == "dtd":
        items = _class_dataset(os.path.join(REPO, "data", "dtd", "dtd", "images"), dataset)
    elif dataset == "inat":
        items = _class_dataset(os.path.join(REPO, "data", "inat_wild"), dataset)
    elif dataset == "nksid":
        root = os.path.join(REPO, "data", "NKSID", "NKSID")
        items = []
        classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
        for c in classes:
            d = os.path.join(root, c)
            for fn in sorted(os.listdir(d)):
                if fn.lower().endswith((".jpg", ".jpeg", ".png")):
                    items.append((os.path.join(d, fn), "a photo of a " + c.replace("_", " "), c.replace("_", " ")))
        # tire images live at the root in this release
        for fn in sorted(os.listdir(root)):
            if fn.lower().endswith((".jpg", ".jpeg", ".png")):
                items.append((os.path.join(root, fn), "a photo of a tire", "tire"))
    elif dataset == "marine":
        root = os.path.join(REPO, "data", "marine_captions")
        caps = json.load(io.open(os.path.join(root, "captions.json"), encoding="utf-8"))
        files = sorted(f for f in os.listdir(root) if f.lower().endswith((".jpg", ".jpeg", ".png")))
        items = []
        if isinstance(caps, dict) and isinstance(caps.get("captions"), list):
            pairs = list(zip(files, caps["captions"]))
        elif isinstance(caps, dict):
            pairs = list(caps.items())
        else:
            pairs = []
            for r in caps:
                pairs.append((r.get("image") or r.get("file") or r.get("filename"), r.get("caption") or r.get("text")))
        for fn, cap in pairs:
            p = os.path.join(root, fn)
            if os.path.exists(p) and cap:
                items.append((p, str(cap), None))
    elif dataset == "coco5k":
        root = os.path.join(REPO, "data", "a4", "coco5k")
        csvp = os.path.join(REPO, "data", "a4_raw", "coco5k", "test_5k_mscoco_2014.csv")
        imgdir = None
        for base, dirs, files in os.walk(root):
            if any(f.lower().endswith(".jpg") for f in files):
                imgdir = base; break
        items = []
        with io.open(csvp, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                caps = json.loads(r["raw"])
                p = os.path.join(imgdir, r["filename"]) if imgdir else os.path.join(root, "images_mscoco_2014_5k_test", r["filename"])
                if os.path.exists(p) and caps:
                    items.append((p, str(caps[0]).strip(), None))
    elif dataset == "flickr30k":
        root = os.path.join(REPO, "data", "a4", "flickr30k")
        csvp = os.path.join(REPO, "data", "a4_raw", "flickr30k", "flickr_annotations_30k.csv")
        imgdir = None
        for base, dirs, files in os.walk(root):
            if any(f.lower().endswith(".jpg") for f in files):
                imgdir = base; break
        items = []
        with io.open(csvp, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                raw = r.get("raw") or ""
                # the column may hold one caption per row or a JSON list; keep the row as one pair
                try:
                    caps = json.loads(raw) if raw.strip().startswith("[") else [raw]
                except Exception:
                    caps = [raw]
                p = os.path.join(imgdir, r["filename"]) if imgdir else os.path.join(root, "flickr30k-images", r["filename"])
                if os.path.exists(p) and caps:
                    items.append((p, str(caps[0]).strip(), None))
    else:
        raise SystemExit("unknown dataset " + dataset)
    DATASET_LIMIT = {"dtd": 2000, "nksid": 1200, "coco5k": 1000, "flickr30k": 1000}
    cap = DATASET_LIMIT.get(dataset)
    if cap and len(items) > cap:
        if all(l is not None for _, _, l in items):
            # stratified: keep the first cap/n_classes images of every class
            by = {}
            for it in items:
                by.setdefault(it[2], []).append(it)
            per = max(1, cap // len(by))
            items = [x for c in sorted(by) for x in by[c][:per]]
        else:
            # deterministic, evenly spaced subset for caption datasets
            step = max(1, len(items) // cap)
            items = items[::step][:cap]
    if limit:
        items = items[:limit]
    return items


def load_encoder(name):
    import torch
    kind, path = ENCODERS[name]
    path = os.path.join(REPO, path)
    if kind == "hfclip":
        from transformers import CLIPModel, CLIPProcessor
        m = CLIPModel.from_pretrained(path, local_files_only=True).eval().cuda()
        p = CLIPProcessor.from_pretrained(path, local_files_only=True)
        return {"kind": kind, "model": m, "processor": p, "name": name}
    if kind == "siglip":
        from transformers import AutoModel, AutoProcessor
        m = AutoModel.from_pretrained(path, local_files_only=True).eval().cuda()
        p = AutoProcessor.from_pretrained(path, local_files_only=True)
        return {"kind": kind, "model": m, "processor": p, "name": name}
    if kind == "openclip":
        import open_clip
        m, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained=os.path.join(path, "open_clip_model.safetensors"), device="cuda")
        m.eval()
        tok = open_clip.get_tokenizer("ViT-B-32")
        return {"kind": kind, "model": m, "processor": preprocess, "tokenizer": tok, "name": name}
    raise SystemExit("unknown encoder")


def encode_images(enc, paths, batch=48):
    import torch
    out = []
    with torch.no_grad():
        for i in range(0, len(paths), batch):
            imgs = [Image.open(p).convert("RGB") for p in paths[i:i + batch]]
            if enc["kind"] == "hfclip":
                inp = enc["processor"](images=imgs, return_tensors="pt")["pixel_values"].cuda()
                z = enc["model"].get_image_features(pixel_values=inp)
                if hasattr(z, "pooler_output"): z = z.pooler_output
            elif enc["kind"] == "siglip":
                inp = enc["processor"](images=imgs, return_tensors="pt")["pixel_values"].cuda()
                z = enc["model"].get_image_features(pixel_values=inp)
                if hasattr(z, "pooler_output"): z = z.pooler_output
                elif hasattr(z, "image_embeds"): z = z.image_embeds
            else:
                inp = torch.stack([enc["processor"](im) for im in imgs]).cuda()
                z = enc["model"].encode_image(inp)
            z = torch.nn.functional.normalize(z.float(), dim=-1)
            out.append(z.cpu().numpy())
    return np.concatenate(out, axis=0)


def encode_texts(enc, texts, batch=64):
    import torch
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            batch_texts = texts[i:i + batch]
            if enc["kind"] == "hfclip":
                inp = enc["processor"](text=batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=77)
                z = enc["model"].get_text_features(input_ids=inp["input_ids"].cuda(), attention_mask=inp["attention_mask"].cuda())
                if hasattr(z, "pooler_output"): z = z.pooler_output
            elif enc["kind"] == "siglip":
                inp = enc["processor"](text=batch_texts, return_tensors="pt", padding="max_length", truncation=True, max_length=64)
                ids = inp["input_ids"].cuda()
                mask = inp["attention_mask"].cuda() if "attention_mask" in inp else torch.ones_like(ids)
                z = enc["model"].get_text_features(input_ids=ids, attention_mask=mask)
                if hasattr(z, "pooler_output"): z = z.pooler_output
                elif hasattr(z, "text_embeds"): z = z.text_embeds
            else:
                tok = enc["tokenizer"](batch_texts).cuda()
                z = enc["model"].encode_text(tok)
            z = torch.nn.functional.normalize(z.float(), dim=-1)
            out.append(z.cpu().numpy())
    return np.concatenate(out, axis=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default="dtd,inat,nksid,marine,coco5k,flickr30k")
    ap.add_argument("--encoders", default=",".join(ENCODERS))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    cat = {}
    for ds in [x for x in a.datasets.split(",") if x]:
        items = build_items(ds, a.limit or None)
        paths = [p for p, t, l in items]; texts_all = [t for p, t, l in items]
        labels = [l for p, t, l in items]
        class_like = all(x is not None for x in labels)
        classes = sorted(set(labels)) if class_like else []
        if class_like:
            text_prompts = ["a photo of a " + c.replace("_", " ") for c in classes]
        else:
            text_prompts = texts_all
        cat[ds] = {"kind": "class" if class_like else "caption", "n_images": len(paths),
                   "n_classes": len(classes), "classes": classes}
        print("DATASET", ds, cat[ds], flush=True)
        for enc_name in [x for x in a.encoders.split(",") if x]:
            out_path = os.path.join(OUT, "%s__%s.npz" % (enc_name, ds))
            if os.path.exists(out_path):
                print("SKIP", out_path, flush=True); continue
            if not a.apply:
                print("PLAN", enc_name, ds, len(paths), "images", len(text_prompts), "texts", flush=True)
                continue
            enc = load_encoder(enc_name)
            img = encode_images(enc, paths)
            txt = encode_texts(enc, text_prompts)
            np.savez_compressed(out_path, img=img, txt=txt,
                                labels=np.array([classes.index(l) if class_like else i for i, l in enumerate(labels)]),
                                texts=np.array(text_prompts, dtype=object), paths=np.array(paths, dtype=object))
            print("WROTE", out_path, img.shape, txt.shape, flush=True)
            del enc
            import torch, gc
            gc.collect(); torch.cuda.empty_cache()
    json.dump(cat, io.open(CATALOG, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("catalog", CATALOG)


if __name__ == "__main__":
    main()
