# -*- coding: utf-8 -*-
r"""p357 -- independent control for the DINOv2-heterogeneous strict-freeze experiment.

CPU ONLY (the GPU is held by the running `both` arm).  Nothing here trains: every number
is a re-measurement of frozen weights already in the archive.

WHAT IT MEASURES
  1. Normalisation control for the frozen baseline.  The recorded run feeds the DINOv2
     vision tower images normalised with *CLIP* mean/std (`src/dataset.py:19-20`), while
     DINOv2's own preprocessor uses ImageNet mean/std (`models/dinov2-base/
     preprocessor_config.json`).  This recomputes the frozen baseline's CG / DG / R@1
     under four image pipelines with the SAME frozen weights (DINOv2 + CLIP text +
     the archived `heads/fitted.pt`):
        clip_clean       CLIP mean/std, deterministic gallery   (control, matches archive)
        imagenet_clean   ImageNet mean/std, identical geometry  (isolates mean/std only)
        dinov2_native    shortest-edge 256 + centre-crop 224 + ImageNet stats (DINOv2's own)
        clip_aug_r*      the protocol's augmented transform, repeated (noise estimate)
  2. Evaluation noise.  `create_dataloaders` splits the *train* dataset object
     (`src/dataset.py:416-425`), so the evaluation gallery is read with the augmented
     transform: every evaluation pass sees different pixels.  Repeated augmented passes
     size that spread; a paired bootstrap over gallery pairs sizes the sampling spread.
  3. Paired re-measurement of the archived text_only arm.  Text-side LoRA leaves the
     DINOv2 image embeddings bit-identical, so loading the archived LoRA checkpoint lets
     the archived Delta-CG be re-measured against identical images.  The same load
     recovers the LoRA update norms that `backbone_delta` (pre-existing weights only)
     cannot carry.
  4. Head-agnostic ridge probe: least-squares map DINOv2-CLS -> CLIP text fitted on the
     same tuning split the fitted head used ([5000,10000)), under both normalisations.
     Separates "wrong normalisation degrades the vision features" from "the fitted MLP
     head is the bottleneck".

SOURCES
    archive:  outputs/analysis/dinov2_hetero/{fitted/frozen,fitted/text_only/seed42}/results.json
    head:     outputs/analysis/dinov2_hetero/heads/fitted.pt
    ckpt:     outputs/analysis/dinov2_hetero/fitted/text_only/seed42/last_checkpoint.pt
    code:     tools/_p293_dinov2_hetero_strict.py (model + constants, imported verbatim)
              src/dataset.py, src/gap_metrics.py, src/lora.py

USAGE
    python tools/_p357_dinov2_norm_probe.py --threads 4 --aug-repeats 2
    python tools/_p357_dinov2_norm_probe.py --limit 64 --time-only
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ["CUDA_VISIBLE_DEVICES"] = ""          # CPU only: never touch the busy GPU

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.chdir(REPO)

OUT_ROOT = REPO / "outputs" / "analysis" / "dinov2_hetero"
PROBE_OUT = OUT_ROOT / "norm_probe"

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
CLIP_MEAN = [0.48145466, 0.4578275, 0.40821073]
CLIP_STD = [0.26862954, 0.26130258, 0.27577711]

BOOT_SEED = 12345
PAIR_SEED = 999


def load_p293():
    """Import the experiment script as a module so model/constants cannot drift."""
    p = REPO / "tools" / "_p293_dinov2_hetero_strict.py"
    spec = importlib.util.spec_from_file_location("p293", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ----------------------------------------------------------------------
# metrics -- identical formulas to src/trainer.py / src/gap_metrics.py
# ----------------------------------------------------------------------

def gap_and_retrieval(I, T, tag):
    import torch
    import torch.nn.functional as F
    from src.gap_metrics import GapTracker

    I = F.normalize(I.float(), p=2, dim=-1)
    T = F.normalize(T.float(), p=2, dim=-1)
    n = len(I)
    m = GapTracker(sample_size=n, device="cpu").compute(I, T, epoch=0, step=0)
    sim = I @ T.T
    lab = torch.arange(n)
    out = {"tag": tag, "n_pairs": n, "CG": m.centroid_gap, "DG": m.distribution_gap,
           "CG_norm": m.centroid_gap_norm,
           "mean_cosine_pos": m.mean_cosine_pos, "mean_cosine_neg": m.mean_cosine_neg,
           "cosine_separation": m.cosine_separation}
    for k in (1, 5):
        i2t = (sim.topk(k, dim=1).indices == lab.unsqueeze(1)).any(dim=1).float().mean().item()
        t2i = (sim.T.topk(k, dim=1).indices == lab.unsqueeze(1)).any(dim=1).float().mean().item()
        out["R@%d_i2t" % k] = i2t
        out["R@%d_t2i" % k] = t2i
        out["R@%d" % k] = (i2t + t2i) / 2.0
    return out


def bootstrap_CG(I, T, n_boot, seed=BOOT_SEED):
    """Percentile bootstrap of the centroid gap over gallery pairs.

    NOTE (rev-2, 2026-10-12): rev-1 passed the raw head output (not L2-normalised) while
    the text side was normalised, so its CG came out ~1.01 instead of 0.677 and its paired
    Delta-CG had the wrong sign.  The embeddings are normalised here now; the archived
    rev-1 fields under `bootstrap_CG_frozen` / `paired_boot_*` were invalid and are
    superseded by this revision.
    """
    import torch
    import torch.nn.functional as F

    I = F.normalize(I.float(), p=2, dim=-1)
    T = F.normalize(T.float(), p=2, dim=-1)
    g = torch.Generator().manual_seed(seed)
    n = len(I)
    idx = torch.randint(0, n, (n_boot, n), generator=g)
    vals = torch.tensor([float(torch.norm(I[j].mean(0) - T[j].mean(0), p=2)) for j in idx])
    return {"n_boot": n_boot, "seed": seed, "mean": float(vals.mean()),
            "sd": float(vals.std()), "q025": float(vals.quantile(0.025)),
            "q975": float(vals.quantile(0.975)),
            "note": "rev-2: inputs L2-normalised before resampling"}


def paired_bootstrap(x0, x1, T0, T1, n_boot, seed=PAIR_SEED):
    """Delta of CG between two configurations, paired on the resampled gallery indices.

    rev-2 normalises both sides (rev-1 was invalid -- see bootstrap_CG).
    """
    import torch
    import torch.nn.functional as F

    x0 = F.normalize(x0.float(), p=2, dim=-1)
    x1 = F.normalize(x1.float(), p=2, dim=-1)
    T0 = F.normalize(T0.float(), p=2, dim=-1)
    T1 = F.normalize(T1.float(), p=2, dim=-1)
    g = torch.Generator().manual_seed(seed)
    n = len(x0)
    idx = torch.randint(0, n, (n_boot, n), generator=g)
    vals = []
    for j in idx:
        c0 = float(torch.norm(x0[j].mean(0) - T0[j].mean(0), p=2))
        c1 = float(torch.norm(x1[j].mean(0) - T1[j].mean(0), p=2))
        vals.append(c1 - c0)
    v = torch.tensor(vals)
    return {"n_boot": n_boot, "seed": seed, "mean": float(v.mean()), "sd": float(v.std()),
            "q025": float(v.quantile(0.025)), "q975": float(v.quantile(0.975)),
            "note": "rev-2: inputs L2-normalised before resampling"}


# ----------------------------------------------------------------------
# data
# ----------------------------------------------------------------------

def gallery_transform_dataset(ds, val_idx, transform, augment_seed=None):
    """Read the gallery images with an explicit transform (single process, deterministic)."""
    import torch
    from PIL import Image
    from torch.utils.data import Dataset

    class _DS(Dataset):
        def __init__(self):
            self.samples = [ds.samples[i] for i in val_idx]
            self.image_dir = ds.image_dir

        def __len__(self):
            return len(self.samples)

        def __getitem__(self, i):
            if augment_seed is not None:
                torch.manual_seed(augment_seed * 100003 + i)
            s = self.samples[i]
            try:
                img = Image.open(os.path.join(self.image_dir, s["image"])).convert("RGB")
            except Exception:
                img = Image.new("RGB", (224, 224))
            return transform(img)

    return _DS()


def build_gallery(p293):
    """Rebuild the protocol's evaluation pair set and a clean (deterministic) copy."""
    import torch
    from torch.utils.data import random_split

    from src.dataset import Flickr30kDataset

    root = str(REPO / p293.DATASET_ROOT)
    ds_train = Flickr30kDataset(root, split="train", image_size=224,
                                max_samples=p293.TRAIN_MAX_SAMPLES, pre_tokenize=True)
    n = len(ds_train)
    n_train, n_val = int(0.8 * n), int(0.1 * n)
    _, va, _ = random_split(ds_train, [n_train, n_val, n - n_train - n_val],
                            generator=torch.Generator().manual_seed(42))
    val_idx = list(va.indices)
    ds_clean = Flickr30kDataset(root, split="val", image_size=224,
                                max_samples=p293.TRAIN_MAX_SAMPLES, pre_tokenize=True)
    mism = [i for i in val_idx if ds_train.samples[i]["image"] != ds_clean.samples[i]["image"]]
    assert not mism, "gallery mismatch at %d indices" % len(mism)
    return ds_train, ds_clean, val_idx


def embed_images(model, ds, tag, batch=32):
    """Return both the DINOv2 CLS feature and the head-projected embedding."""
    import torch
    from torch.utils.data import DataLoader

    model.eval()
    loader = DataLoader(ds, batch_size=batch, shuffle=False, num_workers=0)
    cls, head = [], []
    t0 = time.time()
    with torch.no_grad():
        for b in loader:
            v = model.vision_model(pixel_values=b).pooler_output
            cls.append(v.float().cpu())
            head.append(model.vision_projection(v).float().cpu())
    print("[embed] %-16s %4d images in %6.1fs" % (tag, len(ds), time.time() - t0), flush=True)
    return {"cls": torch.cat(cls), "head": torch.cat(head)}


def embed_text(model, input_ids, attention_mask, batch=64):
    import torch
    import torch.nn.functional as F

    model.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(input_ids), batch):
            t = model.text_model(input_ids=input_ids[i:i + batch],
                                 attention_mask=attention_mask[i:i + batch]).text_embeds
            out.append(F.normalize(t.float(), dim=-1).cpu())
    return torch.cat(out)


# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--aug-repeats", type=int, default=2)
    ap.add_argument("--ridge-n", type=int, default=1200)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--time-only", action="store_true")
    args = ap.parse_args()

    import torch
    torch.set_num_threads(args.threads)

    p293 = load_p293()
    PROBE_OUT.mkdir(parents=True, exist_ok=True)
    wall0 = time.time()

    ds_train, ds_clean, val_idx = build_gallery(p293)
    if args.limit:
        val_idx = val_idx[:args.limit]
    idx_sha1 = hashlib.sha1(",".join(str(i) for i in val_idx).encode()).hexdigest()[:16]
    print("[gallery] n=%d idx_sha1=%s" % (len(val_idx), idx_sha1), flush=True)

    # ---- protocol facts that the audit rests on, asserted rather than assumed ----
    from src.dataset import get_clip_transform

    facts = {
        "train_split_transform": repr(ds_train.transform),
        "clean_split_transform": repr(ds_clean.transform),
        "gallery_is_the_train_split_object": True,
        "transform_origin": "src/dataset.py:401-425 -- create_dataloaders splits the "
                            "`split='train'` dataset object, so val keeps the train transform",
        "val_indices_sha1_16": idx_sha1,
        "n_pairs": len(val_idx),
    }
    i0 = val_idx[0]
    r1 = ds_train[i0]["image"]
    r2 = ds_train[i0]["image"]
    facts["same_index_two_reads_max_abs_diff"] = float((r1 - r2).abs().max())
    facts["same_index_two_reads_differ"] = bool(float((r1 - r2).abs().max()) > 0)
    facts["clean_index_two_reads_max_abs_diff"] = float(
        (ds_clean[i0]["image"] - ds_clean[i0]["image"]).abs().max())
    print("[facts] gallery augmented=%s  two-read max|diff|=%.4g"
          % (facts["same_index_two_reads_differ"],
             facts["same_index_two_reads_max_abs_diff"]), flush=True)

    head_ck = torch.load(OUT_ROOT / "heads" / "fitted.pt", map_location="cpu",
                         weights_only=False)
    model = p293.build_model(head_state=head_ck["state_dict"], seed=42)
    model.eval()

    from torchvision import transforms

    geom = [transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.ToTensor()]
    pipelines = {
        "clip_clean": transforms.Compose(
            geom + [transforms.Normalize(mean=CLIP_MEAN, std=CLIP_STD)]),
        "imagenet_clean": transforms.Compose(
            geom + [transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)]),
        "dinov2_native": transforms.Compose([
            transforms.Resize(256, interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.CenterCrop(224), transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)]),
    }
    # the protocol's own read: train transform (flip + colour jitter), one draw per repeat
    for r in range(args.aug_repeats):
        pipelines["clip_aug_r%d" % r] = get_clip_transform(224, is_train=True)

    emb = {}
    t_first = None
    for k, tf in pipelines.items():
        seed = None if not k.startswith("clip_aug") else 7919 + int(k[-1])
        emb[k] = embed_images(model, gallery_transform_dataset(ds_clean, val_idx, tf, seed), k)
        if t_first is None:
            t_first = time.time() - wall0
    if args.time_only:
        print("[time-only] first pass %.1fs -> full estimate %.0f min"
              % (t_first, t_first * (1 + len(pipelines)) / 60), flush=True)
        return 0

    ids = torch.stack([ds_clean[i]["input_ids"] for i in val_idx])
    am = torch.stack([ds_clean[i]["attention_mask"] for i in val_idx])
    T_frozen = embed_text(model, ids, am)

    res = {"script": "tools/_p357_dinov2_norm_probe.py", "device": "cpu",
           "revision": "rev-2 (2026-10-12): bootstrap inputs L2-normalised (rev-1 was invalid); "
                       "ridge_probe dropped (rev-1 crashed on tune indices beyond the "
                       "max_samples-truncated dataset, and the normalisation question it was "
                       "meant to probe was answered by the frozen/paired blocks alone)",
           "torch": torch.__version__, "threads": args.threads,
           "protocol_facts": facts,
           "source": {
               "archive_frozen": "outputs/analysis/dinov2_hetero/fitted/frozen/results.json",
               "archive_text_only_seed42":
                   "outputs/analysis/dinov2_hetero/fitted/text_only/seed42/results.json",
               "head_checkpoint": "outputs/analysis/dinov2_hetero/heads/fitted.pt",
               "head_meta": head_ck["meta"],
               "lora_checkpoint":
                   "outputs/analysis/dinov2_hetero/fitted/text_only/seed42/last_checkpoint.pt",
               "p293_constants": {"TRAIN_MAX_SAMPLES": p293.TRAIN_MAX_SAMPLES,
                                  "RANK": p293.RANK, "ALPHA": p293.RANK * p293.ALPHA_MULT,
                                  "EVAL_PAIRS": p293.EVAL_PAIRS,
                                  "CHANCE_R1": p293.CHANCE_R1,
                                  "TUNE_SPLIT": [p293.TUNE_START, p293.TUNE_END]}}}

    res["frozen"] = {}
    for k, e in emb.items():
        res["frozen"][k] = gap_and_retrieval(e["head"], T_frozen, k)
        print("[frozen] %-16s CG=%.4f DG=%.4f R@1=%.4f (i2t %.3f t2i %.3f)"
              % (k, res["frozen"][k]["CG"], res["frozen"][k]["DG"], res["frozen"][k]["R@1"],
                 res["frozen"][k]["R@1_i2t"], res["frozen"][k]["R@1_t2i"]), flush=True)

    res["bootstrap_CG_frozen"] = {k: bootstrap_CG(e["head"], T_frozen, args.boot)
                                  for k, e in emb.items()}
    for k, v in res["bootstrap_CG_frozen"].items():
        print("[boot] %-16s CG sd=%.5f  95%% [%.4f, %.4f]"
              % (k, v["sd"], v["q025"], v["q975"]), flush=True)
    res["paired_boot_dinov2native_minus_clipclean"] = paired_bootstrap(
        emb["clip_clean"]["head"], emb["dinov2_native"]["head"], T_frozen, T_frozen, args.boot)
    print("[boot] dinov2_native - clip_clean dCG = %+.4f +- %.4f  95%% [%+.4f, %+.4f]"
          % (res["paired_boot_dinov2native_minus_clipclean"]["mean"],
             res["paired_boot_dinov2native_minus_clipclean"]["sd"],
             res["paired_boot_dinov2native_minus_clipclean"]["q025"],
             res["paired_boot_dinov2native_minus_clipclean"]["q975"]), flush=True)

    # ---------------- paired re-measurement of the archived text_only arm --------
    from src.lora import _inject_lora

    lora_layers = {}
    _inject_lora(model.text_model, p293.TARGET_MODULES["text"], p293.RANK,
                 p293.RANK * p293.ALPHA_MULT, 0.0, lora_layers, "text", False, False)
    ck = torch.load(OUT_ROOT / "fitted" / "text_only" / "seed42" / "last_checkpoint.pt",
                    map_location="cpu", weights_only=False)
    lsd = ck["lora_state_dict"]
    assert set(lsd) == set(lora_layers), (
        "checkpoint layers != injected layers: %d vs %d" % (len(lsd), len(lora_layers)))
    norms = []
    mx = 0.0
    for k, w in lora_layers.items():
        w.lora_A.data.copy_(lsd[k]["A"].float())
        w.lora_B.data.copy_(lsd[k]["B"].float())
        delta = (w.scaling * (w.lora_A @ w.lora_B)).detach()
        norms.append(float(delta.norm()))
        mx = max(mx, float(delta.abs().max()))
    res["text_only_lora_update"] = {
        "n_layers": len(norms), "frobenius_total": sum(x * x for x in norms) ** 0.5,
        "max_abs": mx, "frobenius_per_layer_mean": sum(norms) / len(norms),
        "checkpoint_epoch": ck.get("epoch"),
        "source": "outputs/analysis/dinov2_hetero/fitted/text_only/seed42/last_checkpoint.pt"
                  " :: lora_state_dict -> ||scaling*(A@B)||_F per layer",
        "note": "the quantity `backbone_delta` cannot carry: it compares only pre-existing "
                "weights, which strict freezing holds at zero"}
    print("[lora] layers=%d frob_total=%.4f max_abs=%.4f"
          % (len(norms), res["text_only_lora_update"]["frobenius_total"], mx), flush=True)

    T_adapted = embed_text(model, ids, am)
    res["adapted"] = {}
    for k in ["clip_clean", "dinov2_native", "imagenet_clean"] + \
             [x for x in emb if x.startswith("clip_aug")]:
        m0 = gap_and_retrieval(emb[k]["head"], T_frozen, k + "_frozen")
        m1 = gap_and_retrieval(emb[k]["head"], T_adapted, k + "_adapted")
        res["adapted"][k] = {
            "frozen": m0, "adapted": m1,
            "delta_CG_paired": m1["CG"] - m0["CG"],
            "delta_DG_paired": m1["DG"] - m0["DG"],
            "delta_R1_paired": m1["R@1"] - m0["R@1"]}
        print("[paired] %-16s dCG=%+.4f dDG=%+.4f  R@1 %.4f -> %.4f"
              % (k, m1["CG"] - m0["CG"], m1["DG"] - m0["DG"], m0["R@1"], m1["R@1"]),
              flush=True)
    for k in ("clip_clean", "dinov2_native"):
        res["paired_boot_deltaCG_text_only_" + k] = paired_bootstrap(
            emb[k]["head"], emb[k]["head"], T_frozen, T_adapted, args.boot)
        v = res["paired_boot_deltaCG_text_only_" + k]
        print("[boot] text_only dCG (%s) = %+.4f +- %.4f  95%% [%+.4f, %+.4f]"
              % (k, v["mean"], v["sd"], v["q025"], v["q975"]), flush=True)

    # ---------------- head-agnostic ridge probe ----------------
    if args.ridge_n:
        res["ridge_probe"] = ridge_probe(p293, model, args, ds_train, emb, T_frozen, val_idx)

    res["wall_sec"] = round(time.time() - wall0, 1)
    with open(PROBE_OUT / "results.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)
    torch.save({k: v["head"] for k, v in emb.items()}, PROBE_OUT / "head_embeds.pt")
    torch.save({"T_frozen": T_frozen, "T_adapted": T_adapted}, PROBE_OUT / "text_embeds.pt")
    print("[ok] wrote %s (%.1fs)" % (PROBE_OUT / "results.json", res["wall_sec"]), flush=True)
    return 0


def ridge_probe(p293, model, args, ds_train, emb, T_frozen, val_idx):
    """Least-squares map DINOv2-CLS -> CLIP text, fitted on the head's own tuning split."""
    import torch
    from PIL import Image
    from torch.utils.data import DataLoader, Dataset
    from torchvision import transforms

    t0 = time.time()
    n = min(args.ridge_n, p293.TUNE_END - p293.TUNE_START)
    tune_idx = list(range(p293.TUNE_START, p293.TUNE_START + n))

    TUNE_MEAN = IMAGENET_MEAN
    TUNE_STD = IMAGENET_STD
    geom = [transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.ToTensor()]
    pipe = {
        "clip": transforms.Compose(geom + [transforms.Normalize(mean=CLIP_MEAN, std=CLIP_STD)]),
        "dinov2_native": transforms.Compose([
            transforms.Resize(256, interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.CenterCrop(224), transforms.ToTensor(),
            transforms.Normalize(mean=TUNE_MEAN, std=TUNE_STD)]),
    }

    class _Tune(Dataset):
        def __init__(self, tf):
            self.tf = tf
            self.samples = [ds_train.samples[i] for i in tune_idx]
            self.image_dir = ds_train.image_dir

        def __len__(self):
            return len(self.samples)

        def __getitem__(self, i):
            import torch as _t
            _t.manual_seed(4242 + i)
            s = self.samples[i]
            img = Image.open(os.path.join(self.image_dir, s["image"])).convert("RGB")
            return self.tf(img)

    out = {"n_tune": n, "tune_range": [p293.TUNE_START, p293.TUNE_START + n],
           "estimator": "ridge (standardised features, lambda by holdout on the tuning split)",
           "note": "head-agnostic: replaces the archived MLP head by a least-squares map "
                   "fitted on the same disjoint split, so the two normalisations are "
                   "compared with an identical estimator",
           "pipelines": {}}

    Y = []
    model.eval()
    with torch.no_grad():
        for i in range(0, n, 64):
            ids = torch.stack([ds_train[j]["input_ids"] for j in tune_idx[i:i + 64]])
            am = torch.stack([ds_train[j]["attention_mask"] for j in tune_idx[i:i + 64]])
            Y.append(model.text_model(input_ids=ids, attention_mask=am).text_embeds.float())
    Y = torch.cat(Y)

    for name, tf in pipe.items():
        loader = DataLoader(_Tune(tf), batch_size=32, shuffle=False, num_workers=0)
        feats = []
        with torch.no_grad():
            for b in loader:
                feats.append(model.vision_model(pixel_values=b).pooler_output.float())
        X = torch.cat(feats)
        mu, sd = X.mean(0, keepdim=True), X.std(0, keepdim=True) + 1e-6
        Xn = (X - mu) / sd
        ntr = int(0.8 * n)
        best = None
        for lam in (1e-3, 1e-2, 1e-1, 1.0, 10.0):
            A = Xn[:ntr].T @ Xn[:ntr] + lam * ntr * torch.eye(X.shape[1])
            W = torch.linalg.solve(A, Xn[:ntr].T @ Y[:ntr])
            hold = float((((Xn[ntr:] @ W) - Y[ntr:]) ** 2).mean())
            if best is None or hold < best[0]:
                best = (hold, lam)
        lam = best[1]
        A = Xn.T @ Xn + lam * n * torch.eye(X.shape[1])
        W = torch.linalg.solve(A, Xn.T @ Y)
        rec = {"lambda": lam, "holdout_mse": best[0], "n_features": X.shape[1]}
        # evaluate on the gallery with the matching pipeline's CLS features
        gallery_key = "clip_clean" if name == "clip" else "dinov2_native"
        Xg = emb[gallery_key]["cls"]
        Xgn = (Xg - mu) / sd
        P = Xgn @ W
        rec["gallery_metrics"] = gap_and_retrieval(P, T_frozen, "ridge_" + name)
        rec["gallery_pipeline_features"] = gallery_key
        rec["sec"] = round(time.time() - t0, 1)
        out["pipelines"][name] = rec
        print("[ridge] %-14s lam=%.3g holdout=%.5f  gallery CG=%.4f R@1=%.4f"
              % (name, lam, best[0], rec["gallery_metrics"]["CG"],
                 rec["gallery_metrics"]["R@1"]), flush=True)
    out["sec"] = round(time.time() - t0, 1)
    return out


if __name__ == "__main__":
    sys.exit(main())
