# -*- coding: utf-8 -*-
"""A4 controlled PEFT block: LoRA training on class-labelled CLIP encoders.

Predeclared protocol: 2 backbones x 3 datasets x 3 ranks x 2 seeds = 36 runs, 3 epochs each.
Each checkpoint is evaluated for CG/DG, classification, i2t, t2i, ARI under original, mean-center,
gap-direction and random-direction conditions.
"""
from __future__ import annotations
import argparse, gc, glob, io, json, math, os, sys, time
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTDIR = os.path.join(REPO, "outputs", "a4", "controlled_peft")
SUMMARY = os.path.join(REPO, "outputs", "a4", "a4_controlled_peft_2026-11-10.json")
SPLIT_SEED = 2026
TOWER_TARGETS = {
    "both": r"(text_model|vision_model).*\.(q_proj|k_proj|v_proj)$",
    "text": r"text_model.*\.(q_proj|k_proj|v_proj)$",
    "vision": r"vision_model.*\.(q_proj|k_proj|v_proj)$",
}
BACKBONES = {"clip-b32": "models/clip-vit-base-patch32", "clip-b16": "models/clip-vit-base-patch16"}
DATASETS = {"dtd": ("data/dtd/dtd/images", "a photo of a {}"),
            "inat": ("data/inat_wild", "a photo of a {}"),
            "nksid": ("data/NKSID/NKSID", "a photo of a {}")}


def l2(x):
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(n, 1e-12)


def gap_stats(img, txt):
    mu_i, mu_t = img.mean(0), txt.mean(0)
    cg = float(np.linalg.norm(mu_i - mu_t))
    dg = float(np.sqrt(cg ** 2 + float(np.linalg.norm(img.std(0) - txt.std(0)) ** 2)))
    z = np.concatenate([img - img.mean(0), txt - txt.mean(0)], 0)
    cov = (z.T @ z) / max(1, len(z) - 1)
    w = np.clip(np.linalg.eigvalsh(cov), 1e-12, None); w = w / w.sum()
    return {"CG": cg, "DG": dg, "spec_eff_rank": float(np.exp(-(w * np.log(w)).sum())),
            "spec_top1_share": float(w[-1])}


def metrics_for(img, txt, labels):
    img, txt = l2(img), l2(txt)
    n, c = len(img), len(txt)
    s = img @ txt.T
    top1 = float((s.argmax(1) == labels).mean() * 100)
    d = s[np.arange(n), labels]
    rank_i2t = (s > d[:, None]).sum(1) + 1
    r1_i2t = float((rank_i2t <= 1).mean() * 100)
    r1_t2i = float((labels[s.argmax(0)] == np.arange(c)).mean() * 100)
    try:
        from sklearn.cluster import KMeans
        from sklearn.metrics import adjusted_rand_score
        pool = np.concatenate([img, txt], 0)
        lab = np.concatenate([labels, np.arange(c)], 0)
        pred = KMeans(n_clusters=c, n_init=5, random_state=0).fit_predict(pool)
        ari = float(adjusted_rand_score(lab, pred))
    except Exception:
        ari = None
    out = {"classification_top1": top1, "R1_i2t": r1_i2t, "R1_t2i": r1_t2i, "ARI": ari}
    out.update(gap_stats(img, txt))
    return out


def transform(img, txt, mode, seed=0):
    img, txt = l2(img.copy()), l2(txt.copy())
    if mode == "original":
        return img, txt
    if mode == "mean_center":
        return l2(img - img.mean(0)), l2(txt - txt.mean(0))
    mu_i, mu_t = img.mean(0), txt.mean(0)
    if mode == "gap_project":
        d = mu_i - mu_t
    elif mode == "random_project":
        d = np.random.RandomState(seed).normal(size=img.shape[1])
    else:
        raise ValueError(mode)
    d = d / max(np.linalg.norm(d), 1e-12)
    return l2(img - np.outer(img @ d, d)), l2(txt - np.outer(txt @ d, d))


def load_dataset(spec, limit_train=0, limit_test=0):
    from PIL import Image
    root, tpl = DATASETS[spec]
    root = os.path.join(REPO, root)
    classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith("."))
    items = []
    for ci, c in enumerate(classes):
        d = os.path.join(root, c)
        for f in sorted(os.listdir(d)):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                items.append((os.path.join(d, f), ci))
    if spec == "nksid":
        for f in sorted(os.listdir(root)):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                items.append((os.path.join(root, f), len(classes) - 1 if False else len(classes)))
        # tire images at the root are a separate class; append class name deterministically
        if any(f.lower().endswith((".jpg", ".jpeg", ".png")) for f in os.listdir(root)):
            classes = classes + ["tire"]
    # stratified 70/30 split, fixed seed
    rng = np.random.RandomState(SPLIT_SEED)
    train, test = [], []
    for ci in range(len(classes)):
        idx = [i for i, (_, y) in enumerate(items) if y == ci]
        rng.shuffle(idx)
        k = int(round(len(idx) * 0.7))
        train += [items[i] for i in idx[:k]]
        test += [items[i] for i in idx[k:]]
    if limit_train: train = train[:limit_train]
    if limit_test: test = test[:limit_test]
    train_pil = [Image.open(p).convert("RGB") for p, y in train]
    test_pil = [Image.open(p).convert("RGB") for p, y in test]
    return train_pil, np.asarray([y for p, y in train]), test_pil, np.asarray([y for p, y in test]), classes, tpl


def encode_images(model, proc, pil, device, batch=48):
    import torch
    core = model.base_model.model if hasattr(model, "peft_config") else model
    out = []
    with torch.no_grad():
        for i in range(0, len(pil), batch):
            inp = proc(images=pil[i:i + batch], return_tensors="pt").to(device)
            z = core.get_image_features(pixel_values=inp["pixel_values"])
            if hasattr(z, "pooler_output"): z = z.pooler_output
            elif hasattr(z, "image_embeds"): z = z.image_embeds
            out.append(torch.nn.functional.normalize(z.float(), dim=-1).cpu().numpy())
    return np.concatenate(out, 0)


def encode_texts(model, proc, texts, device, batch=64):
    import torch
    core = model.base_model.model if hasattr(model, "peft_config") else model
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            inp = proc(text=texts[i:i + batch], return_tensors="pt", padding=True, truncation=True, max_length=77).to(device)
            z = core.get_text_features(input_ids=inp["input_ids"], attention_mask=inp["attention_mask"])
            if hasattr(z, "pooler_output"): z = z.pooler_output
            elif hasattr(z, "text_embeds"): z = z.text_embeds
            out.append(torch.nn.functional.normalize(z.float(), dim=-1).cpu().numpy())
    return np.concatenate(out, 0)


def run_one(backbone, dataset, rank, seed, epochs, limit_train, limit_test, outdir, tower="both"):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import CLIPModel, CLIPProcessor
    suffix = "" if tower == "both" else "__" + tower
    key = f"{backbone}__{dataset}__r{rank}__s{seed}" + suffix
    path = os.path.join(outdir, key + ".json")
    if os.path.exists(path):
        print("SKIP", key, flush=True); return
    local = os.path.join(REPO, BACKBONES[backbone])
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(seed); np.random.seed(seed)
    torch.cuda.empty_cache()
    proc = CLIPProcessor.from_pretrained(local, local_files_only=True)
    base = CLIPModel.from_pretrained(local, local_files_only=True)
    cfg = LoraConfig(r=rank, lora_alpha=2 * rank, lora_dropout=0.05, bias="none",
                     target_modules=TOWER_TARGETS[tower])
    model = get_peft_model(base, cfg).to(device)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=5e-4, weight_decay=0.0)
    train_pil, train_y, test_pil, test_y, classes, tpl = load_dataset(dataset, limit_train, limit_test)
    texts = [tpl.format(c.replace("_", " ")) for c in classes]
    by_class = {c: [i for i, y in enumerate(train_y) if y == c] for c in range(len(classes))}
    valid_classes = [c for c in range(len(classes)) if by_class[c]]
    n_classes = min(16, len(valid_classes))
    steps_per_epoch = max(1, len(train_pil) // n_classes)
    payload = {"run": {"backbone": backbone, "dataset": dataset, "rank": rank, "seed": seed, "tower": tower,
                       "epochs": epochs, "n_train": len(train_pil), "n_test": len(test_pil),
                       "n_classes": len(classes), "split_seed": SPLIT_SEED,
                       "target": TOWER_TARGETS[tower], "lr": 5e-4, "trainable_tensors": len(params)},
               "epochs": []}
    rng = np.random.RandomState(seed)
    for ep in range(1, epochs + 1):
        model.train(); t0 = time.time(); losses = []
        for st in range(steps_per_epoch):
            cs = rng.choice(valid_classes, size=n_classes, replace=False)
            sel = [int(rng.choice(by_class[int(c)])) for c in cs]
            imgs = [train_pil[i] for i in sel]
            btexts = [texts[int(c)] for c in cs]
            img_in = proc(images=imgs, return_tensors="pt").to(device)
            txt_in = proc(text=btexts, return_tensors="pt", padding=True, truncation=True, max_length=77).to(device)
            out = model(pixel_values=img_in["pixel_values"], input_ids=txt_in["input_ids"],
                        attention_mask=txt_in["attention_mask"], return_loss=True)
            loss = out.loss
            opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0); opt.step()
            losses.append(float(loss.item()))
        model.eval()
        img = encode_images(model, proc, test_pil, device)
        txt = encode_texts(model, proc, texts, device)
        rec = {"epoch": ep, "train_loss": float(np.mean(losses)), "seconds": round(time.time() - t0, 1), "conditions": {}}
        for mode in ("original", "mean_center", "gap_project", "random_project"):
            a, b = transform(img, txt, mode, seed=seed)
            rec["conditions"][mode] = metrics_for(a, b, test_y)
        payload["epochs"].append(rec)
        print("DONE", key, "ep", ep, "loss %.3f" % np.mean(losses), "CG %.3f" % rec["conditions"]["original"]["CG"], flush=True)
        os.makedirs(outdir, exist_ok=True)
        json.dump(payload, io.open(path, "w", encoding="utf-8"), indent=1)
    del model, base, opt
    gc.collect(); torch.cuda.empty_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbones", default="clip-b32,clip-b16")
    ap.add_argument("--datasets", default="dtd,inat,nksid")
    ap.add_argument("--ranks", default="4,16,64")
    ap.add_argument("--seeds", default="42,43")
    ap.add_argument("--towers", default="both")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--limit-train", type=int, default=0)
    ap.add_argument("--limit-test", type=int, default=0)
    ap.add_argument("--outdir", default=OUTDIR)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        a.backbones, a.datasets, a.ranks, a.seeds, a.towers, a.epochs = "clip-b32", "dtd", "4", "42", "both", 1
        a.limit_train, a.limit_test = 120, 60
        a.outdir = os.path.join(REPO, "outputs", "a4", "controlled_peft_smoke")
    bbs = [x for x in a.backbones.split(",") if x]; dss = [x for x in a.datasets.split(",") if x]
    rks = [int(x) for x in a.ranks.split(",") if x]; sds = [int(x) for x in a.seeds.split(",") if x]
    tts = [x for x in a.towers.split(",") if x]
    print("MATRIX", len(bbs), "x", len(dss), "x", len(rks), "x", len(sds), "x", len(tts), "=", len(bbs) * len(dss) * len(rks) * len(sds) * len(tts), "runs", flush=True)
    for bb in bbs:
        for ds in dss:
            for rk in rks:
                for sd in sds:
                    for tw in tts:
                        run_one(bb, ds, rk, sd, a.epochs, a.limit_train, a.limit_test, a.outdir, tw)
    # merge per-run files
    runs = []
    for f in sorted(glob.glob(os.path.join(a.outdir, "*.json"))):
        try: runs.append(json.load(io.open(f, encoding="utf-8")))
        except Exception: pass
    if runs:
        summary_path = SUMMARY if os.path.abspath(a.outdir) == os.path.abspath(OUTDIR) else os.path.join(a.outdir, "summary.json")
        json.dump({"n_runs": len(runs), "runs": runs}, io.open(summary_path, "w", encoding="utf-8"), indent=1)
        print("SUMMARY", summary_path, "runs", len(runs), flush=True)


if __name__ == "__main__":
    main()
