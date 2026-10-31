# -*- coding: utf-8 -*-
r"""p360 -- how much of every CG / DG / R@1 in this project is evaluation sampling noise?

WHY (Lead's top-priority question, 2026-10-12)
    `src/dataset.py:401-425` builds the train/val/test loaders by random-splitting the
    `split="train"` dataset object, so the *evaluation* gallery is read with the train
    transform: `RandomHorizontalFlip(p=0.5)` + `ColorJitter(0.1,0.1,0.1)`.  Measured in
    `tools/_p357_dinov2_norm_probe.py` -> `protocol_facts.same_index_two_reads_max_abs_diff
    = 0.2851`: two reads of the same gallery index are different pictures.

    Consequence: every CG / DG / R@1 in `outputs/` -- including every cell of
    `tab:position_strict` -- is ONE DRAW from a stochastic evaluation, not a deterministic
    quantity.  This script measures the resulting distribution.

    NOTE ON `tools/_p358_gallery_noise.py` (written by another member at the same time):
    that script reports `||mean(normalised image embedding)||` on a 200-pair gallery
    (`max_samples=2000`) with no text tower, which is not the centroid gap, gives no
    Delta-CG and no R@1.  It cannot answer this question; this file can.  Both are kept.

WHAT IT DOES  (CPU only, no training, archived weights only)
    For each (model, arm, seed) it re-evaluates the SAME archived checkpoint on N
    independent augmented draws of the same 500-pair gallery and reports the distribution
    of CG_init / CG_final / Delta-CG / DG / R@1_init / R@1_final.

    In the protocol's own convention the adapter is B=0-initialised, so the step-0 model is
    numerically identical to the pristine backbone; and the text tower receives fixed
    tokens, so text embeddings do not vary across draws.  One draw therefore costs only the
    vision pass(es) the arm actually perturbs:
        text_only            1 vision pass   (vision untouched: I_init == I_final)
        both / vision_only   2 vision passes (pristine vision + adapted vision)

ARMS MEASURED
    clip_b32   : models/clip-vit-base-patch32 -- the paper's own backbone, all three arms at
                 seed 42, LoRA loaded from outputs/strict_freeze/<arm>/seed42/
                 last_checkpoint.pt
    dinov2_het : DINOv2-base + CLIP text + fitted head -- text_only/seed42 from
                 outputs/analysis/dinov2_hetero/

SOURCES are recorded per arm inside the JSON (checkpoint path + archived results.json).

USAGE
    python tools/_p360_gallery_noise.py --threads 6 --draws 12
    python tools/_p360_gallery_noise.py --threads 6 --draws 12 --only clip_b32
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ["CUDA_VISIBLE_DEVICES"] = ""          # CPU only: the GPU is held by the runs

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.chdir(REPO)

OUT_ROOT = REPO / "outputs" / "analysis" / "dinov2_hetero"
PROBE_OUT = OUT_ROOT / "gallery_noise"
CLIP_PATH = "models/clip-vit-base-patch32"
PRISTINE = str(REPO / CLIP_PATH)

RANK = 8
ALPHA = 16
MAX_SAMPLES = 5000


def load_p293():
    p = REPO / "tools" / "_p293_dinov2_hetero_strict.py"
    spec = importlib.util.spec_from_file_location("p293", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ----------------------------------------------------------------------
# metrics (identical formulas to src/trainer.py + src/gap_metrics.py)
# ----------------------------------------------------------------------

def metrics(I, T):
    import torch
    import torch.nn.functional as F
    from src.gap_metrics import GapTracker

    I = F.normalize(I.float(), p=2, dim=-1)
    T = F.normalize(T.float(), p=2, dim=-1)
    n = len(I)
    m = GapTracker(sample_size=n, device="cpu").compute(I, T, epoch=0, step=0)
    sim = I @ T.T
    lab = torch.arange(n)
    out = {"CG": m.centroid_gap, "DG": m.distribution_gap,
           "mean_cosine_pos": m.mean_cosine_pos, "mean_cosine_neg": m.mean_cosine_neg,
           "cosine_separation": m.cosine_separation}
    for k in (1, 5):
        i2t = (sim.topk(k, dim=1).indices == lab.unsqueeze(1)).any(dim=1).float().mean().item()
        t2i = (sim.T.topk(k, dim=1).indices == lab.unsqueeze(1)).any(dim=1).float().mean().item()
        out["R@%d_i2t" % k] = i2t
        out["R@%d_t2i" % k] = t2i
        out["R@%d" % k] = (i2t + t2i) / 2.0
    return out


def describe(xs):
    import torch
    v = torch.tensor([float(x) for x in xs])
    sd = float(v.std(unbiased=True))
    return {"n": len(v), "mean": float(v.mean()), "sd": sd,
            "sd_of_mean_of_5": sd / (5 ** 0.5),
            "min": float(v.min()), "max": float(v.max()),
            "range": float(v.max() - v.min()),
            "values": [float(x) for x in v]}


def build_gallery(p293):
    import torch
    from torch.utils.data import random_split

    from src.dataset import Flickr30kDataset

    root = str(REPO / p293.DATASET_ROOT)
    ds_train = Flickr30kDataset(root, split="train", image_size=224,
                                max_samples=MAX_SAMPLES, pre_tokenize=True)
    n = len(ds_train)
    n_train, n_val = int(0.8 * n), int(0.1 * n)
    _, va, _ = random_split(ds_train, [n_train, n_val, n - n_train - n_val],
                            generator=torch.Generator().manual_seed(42))
    ds_clean = Flickr30kDataset(root, split="val", image_size=224,
                                max_samples=MAX_SAMPLES, pre_tokenize=True)
    return ds_train, ds_clean, list(va.indices)


def aug_loader(ds_clean, val_idx, draw, batch=32):
    """One independent augmented draw of the gallery (per-item seed -> i.i.d. draw)."""
    import torch
    from PIL import Image
    from torch.utils.data import DataLoader, Dataset
    from src.dataset import get_clip_transform

    tf = get_clip_transform(224, is_train=True)
    samples = [ds_clean.samples[i] for i in val_idx]
    image_dir = ds_clean.image_dir

    class _D(Dataset):
        def __len__(self):
            return len(samples)

        def __getitem__(self, i):
            torch.manual_seed(1_000_003 * (draw + 1) + i)
            s = samples[i]
            try:
                img = Image.open(os.path.join(image_dir, s["image"])).convert("RGB")
            except Exception:
                img = Image.new("RGB", (224, 224))
            return tf(img)

    return DataLoader(_D(), batch_size=batch, shuffle=False, num_workers=0)


def as_tensor(x):
    """transformers 5.x: CLIPModel.get_{text,image}_features returns a ModelOutput whose
    `pooler_output` is the projected embedding (verified: tools/_p362_clip_api_check.py,
    transformers 5.16.1).  transformers 4.x returned the tensor directly.  Handle both."""
    import torch
    return x if torch.is_tensor(x) else x.pooler_output


def load_lora_state(model, lora_layers, ckpt_path):
    import torch
    ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    lsd = ck["lora_state_dict"]
    assert set(lsd) == set(lora_layers), (
        "checkpoint layers != injected layers (%d vs %d) for %s"
        % (len(lsd), len(lora_layers), ckpt_path))
    for k, w in lora_layers.items():
        w.lora_A.data.copy_(lsd[k]["A"].float())
        w.lora_B.data.copy_(lsd[k]["B"].float())
    return ck


# ----------------------------------------------------------------------
# CLIP B/32 -- the paper's backbone
# ----------------------------------------------------------------------

def run_clip(args, ds_clean, val_idx, draws, res):
    import torch
    from transformers import CLIPModel
    from src.lora import apply_lora_to_model

    print("\n" + "=" * 78 + "\nCLIP B/32 (the paper's backbone)\n" + "=" * 78, flush=True)
    arms = {"text_only": dict(apply_to_vision=False, apply_to_text=True),
            "both": dict(apply_to_vision=True, apply_to_text=True),
            "vision_only": dict(apply_to_vision=True, apply_to_text=False)}

    ids = torch.stack([ds_clean[i]["input_ids"] for i in val_idx])
    am = torch.stack([ds_clean[i]["attention_mask"] for i in val_idx])

    def text_embeds(model):
        import torch.nn.functional as F
        out = []
        with torch.no_grad():
            for i in range(0, len(ids), 64):
                t = as_tensor(model.get_text_features(input_ids=ids[i:i + 64],
                                                      attention_mask=am[i:i + 64]))
                out.append(F.normalize(t.float(), dim=-1))
        return torch.cat(out)

    def image_embeds(model, loader):
        import torch.nn.functional as F
        out = []
        with torch.no_grad():
            for b in loader:
                out.append(F.normalize(
                    as_tensor(model.get_image_features(pixel_values=b)).float(), dim=-1))
        return torch.cat(out)

    # provenance guard: the features this script re-measures must be the ones the trainer
    # uses (`src/trainer.py` reads outputs.image_embeds / outputs.text_embeds from forward()).
    # (runs inside the arm loop: `model` exists there)

    for arm, flags in arms.items():
        ck_path = REPO / "outputs" / "strict_freeze" / arm / "seed42" / "last_checkpoint.pt"
        if not ck_path.exists():
            print("[skip] %s (no checkpoint)" % ck_path, flush=True)
            continue
        model, lora_layers, _ = apply_lora_to_model(
            CLIPModel.from_pretrained(PRISTINE, local_files_only=True).eval(),
            rank=RANK, alpha=ALPHA, dropout=0.0, target_modules=["q_proj", "v_proj"],
            **flags)
        model.eval()
        ck = load_lora_state(model, lora_layers, ck_path)
        vis_keys = [k for k in lora_layers if k.startswith("vision")]
        txt_keys = [k for k in lora_layers if k.startswith("text")]

        # provenance guard (once): the embeddings re-measured here must be the ones the
        # trainer consumes -- src/trainer.py reads outputs.image_embeds / outputs.text_embeds.
        if "provenance_checks" not in res:
            import torch.nn.functional as F
            with torch.no_grad():
                _b = next(iter(aug_loader(ds_clean, val_idx, 0, batch=8)))
                _out = model(pixel_values=_b, input_ids=ids[:8], attention_mask=am[:8])
                _tf = as_tensor(model.get_text_features(input_ids=ids[:8],
                                                        attention_mask=am[:8]))
                _if = as_tensor(model.get_image_features(pixel_values=_b))
            res["provenance_checks"] = {"clip_features_match_forward": {
                "text_max_abs_diff": float((F.normalize(_tf.float(), dim=-1)
                                            - _out.text_embeds.float()).abs().max()),
                "image_max_abs_diff": float((F.normalize(_if.float(), dim=-1)
                                             - _out.image_embeds.float()).abs().max()),
                "note": "0.0 means the re-measured embeddings are bit-equal to the trainer's",
                "transformers": __import__("transformers").__version__}}

        # text tower: fixed tokens -> compute both states once (no draw dependence)
        for k in txt_keys:
            lora_layers[k].lora_B.data.zero_()
        T_init = text_embeds(model)
        for k in txt_keys:
            lora_layers[k].lora_A.data.copy_(ck["lora_state_dict"][k]["A"].float())
            lora_layers[k].lora_B.data.copy_(ck["lora_state_dict"][k]["B"].float())
        T_final = text_embeds(model)
        for k in txt_keys:
            lora_layers[k].lora_B.data.zero_()

        rec = {"arm": arm, "checkpoint": str(ck_path.relative_to(REPO)),
               "checkpoint_epoch": ck.get("epoch"),
               "n_lora_layers": {"vision": len(vis_keys), "text": len(txt_keys)},
               "archived_results_json": str(
                   (REPO / "outputs" / "strict_freeze" / arm / "seed42"
                    / "results.json").relative_to(REPO)),
               "text_embeds_fixed_across_draws": True,
               "visual_side_perturbed": bool(vis_keys),
               "vision_passes_per_draw": 1 if not vis_keys else 2,
               "draws": {}}
        print("[clip] %s: vis_layers=%d txt_layers=%d epoch=%s"
              % (arm, len(vis_keys), len(txt_keys), ck.get("epoch")), flush=True)

        keys = ["CG_init", "CG_final", "DG_init", "DG_final", "dCG", "dDG",
                "R1_init", "R1_final", "dR1", "R5_init", "R5_final"]
        digs = {k: [] for k in keys}
        for r in range(draws):
            t0 = time.time()
            I_init = image_embeds(model, aug_loader(ds_clean, val_idx, r))
            if vis_keys:
                for k in vis_keys:
                    lora_layers[k].lora_A.data.copy_(
                        ck["lora_state_dict"][k]["A"].float())
                    lora_layers[k].lora_B.data.copy_(
                        ck["lora_state_dict"][k]["B"].float())
                I_final = image_embeds(model, aug_loader(ds_clean, val_idx, r))
                for k in vis_keys:
                    lora_layers[k].lora_B.data.zero_()
            else:
                I_final = I_init
            m0, m1 = metrics(I_init, T_init), metrics(I_final, T_final)
            for key, val in (("CG_init", m0["CG"]), ("CG_final", m1["CG"]),
                             ("DG_init", m0["DG"]), ("DG_final", m1["DG"]),
                             ("dCG", m1["CG"] - m0["CG"]),
                             ("dDG", m1["DG"] - m0["DG"]),
                             ("R1_init", m0["R@1"]), ("R1_final", m1["R@1"]),
                             ("dR1", m1["R@1"] - m0["R@1"]),
                             ("R5_init", m0["R@5"]), ("R5_final", m1["R@5"])):
                digs[key].append(val)
            print("    draw %2d: CG %0.4f->%0.4f (dCG %+.4f)  R@1 %0.4f->%0.4f  "
                  "R@5 %0.3f->%0.3f (%.0fs)"
                  % (r, m0["CG"], m1["CG"], m1["CG"] - m0["CG"], m0["R@1"], m1["R@1"],
                     m0["R@5"], m1["R@5"], time.time() - t0), flush=True)
        for k, v in digs.items():
            rec["draws"][k] = describe(v)
        agg = REPO / "outputs" / "strict_freeze" / arm / "seed42" / "results.json"
        with open(agg, encoding="utf-8") as fh:
            a = json.load(fh)
        rec["archived"] = {
            "delta_CG": a["final_gap"]["centroid_gap"] - a["initial_gap"]["centroid_gap"],
            "delta_DG": (a["final_gap"]["distribution_gap"]
                         - a["initial_gap"]["distribution_gap"]),
            "CG_initial": a["initial_gap"]["centroid_gap"],
            "CG_final": a["final_gap"]["centroid_gap"],
            "R1": a["final_task_metrics"]["R@1"],
            "R5": a["final_task_metrics"]["R@5"]}
        res["arms"]["clip_b32_" + arm] = rec
        print("[clip] %-12s dCG = %+.4f +- %.4f (range %.4f) | R@1_final = %.4f +- %.4f "
              "(range %.4f) | archived dCG %+.4f R@1 %.4f"
              % (arm, rec["draws"]["dCG"]["mean"], rec["draws"]["dCG"]["sd"],
                 rec["draws"]["dCG"]["range"], rec["draws"]["R1_final"]["mean"],
                 rec["draws"]["R1_final"]["sd"], rec["draws"]["R1_final"]["range"],
                 rec["archived"]["delta_CG"], rec["archived"]["R1"]), flush=True)
        with open(PROBE_OUT / "results.json", "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, ensure_ascii=False)


# ----------------------------------------------------------------------
# DINOv2 heterogeneous pairing
# ----------------------------------------------------------------------

def run_dinov2(args, p293, ds_clean, val_idx, draws, res):
    import torch
    import torch.nn.functional as F
    from src.lora import _inject_lora

    print("\n" + "=" * 78 + "\nDINOv2-base + CLIP text + fitted head\n" + "=" * 78,
          flush=True)
    ids = torch.stack([ds_clean[i]["input_ids"] for i in val_idx])
    am = torch.stack([ds_clean[i]["attention_mask"] for i in val_idx])
    head_ck = torch.load(OUT_ROOT / "heads" / "fitted.pt", map_location="cpu",
                         weights_only=False)
    model = p293.build_model(head_state=head_ck["state_dict"], seed=42)
    model.eval()

    def text_embeds():
        out = []
        with torch.no_grad():
            for i in range(0, len(ids), 64):
                t = model.text_model(input_ids=ids[i:i + 64],
                                     attention_mask=am[i:i + 64]).text_embeds
                out.append(F.normalize(t.float(), dim=-1))
        return torch.cat(out)

    def image_embeds(loader):
        out = []
        with torch.no_grad():
            for b in loader:
                v = model.vision_model(pixel_values=b).pooler_output
                out.append(F.normalize(model.vision_projection(v).float(), dim=-1))
        return torch.cat(out)

    lora_layers = {}
    _inject_lora(model.text_model, p293.TARGET_MODULES["text"], RANK, ALPHA, 0.0,
                 lora_layers, "text", False, False)
    ck_path = OUT_ROOT / "fitted" / "text_only" / "seed42" / "last_checkpoint.pt"
    ck = load_lora_state(model, lora_layers, ck_path)

    T_init = text_embeds()
    for k, w in lora_layers.items():
        w.lora_A.data.copy_(ck["lora_state_dict"][k]["A"].float())
        w.lora_B.data.copy_(ck["lora_state_dict"][k]["B"].float())
    T_final = text_embeds()
    for k, w in lora_layers.items():
        w.lora_B.data.zero_()

    rec = {"arm": "text_only", "seed": 42,
           "checkpoint": str(ck_path.relative_to(REPO)),
           "checkpoint_epoch": ck.get("epoch"),
           "head_checkpoint": "outputs/analysis/dinov2_hetero/heads/fitted.pt",
           "archived_results_json":
               "outputs/analysis/dinov2_hetero/fitted/text_only/seed42/results.json",
           "visual_side_perturbed": False, "vision_passes_per_draw": 1,
           "why_one_pass": ("strict freeze + text-side-only LoRA: image embeddings are "
                            "identical at init and final for a fixed draw"),
           "draws": {}}
    keys = ["CG_init", "CG_final", "DG_init", "DG_final", "dCG", "dDG",
            "R1_init", "R1_final", "dR1", "R5_init", "R5_final"]
    digs = {k: [] for k in keys}
    for r in range(draws):
        t0 = time.time()
        I = image_embeds(aug_loader(ds_clean, val_idx, r))
        m0, m1 = metrics(I, T_init), metrics(I, T_final)
        for key, val in (("CG_init", m0["CG"]), ("CG_final", m1["CG"]),
                         ("DG_init", m0["DG"]), ("DG_final", m1["DG"]),
                         ("dCG", m1["CG"] - m0["CG"]), ("dDG", m1["DG"] - m0["DG"]),
                         ("R1_init", m0["R@1"]), ("R1_final", m1["R@1"]),
                         ("dR1", m1["R@1"] - m0["R@1"]),
                         ("R5_init", m0["R@5"]), ("R5_final", m1["R@5"])):
            digs[key].append(val)
        print("    draw %2d: CG %0.4f->%0.4f (dCG %+.4f)  R@1 %0.4f->%0.4f (%.0fs)"
              % (r, m0["CG"], m1["CG"], m1["CG"] - m0["CG"], m0["R@1"], m1["R@1"],
                 time.time() - t0), flush=True)
    for k, v in digs.items():
        rec["draws"][k] = describe(v)
    with open(OUT_ROOT / "fitted" / "text_only" / "seed42" / "results.json",
              encoding="utf-8") as fh:
        a = json.load(fh)
    rec["archived"] = {"delta_CG": a["delta_CG"], "delta_DG": a["delta_DG"],
                       "CG_initial": a["CG_initial"], "CG_final": a["CG_final"],
                       "R1": a["R@1"], "R5": a["R@5"]}
    res["arms"]["dinov2_het_text_only_seed42"] = rec
    print("[dinov2] dCG = %+.4f +- %.4f (range %.4f) | R@1_final = %.4f +- %.4f "
          "(range %.4f) | archived dCG %+.4f R@1 %.4f"
          % (rec["draws"]["dCG"]["mean"], rec["draws"]["dCG"]["sd"],
             rec["draws"]["dCG"]["range"], rec["draws"]["R1_final"]["mean"],
             rec["draws"]["R1_final"]["sd"], rec["draws"]["R1_final"]["range"],
             a["delta_CG"], a["R@1"]), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--draws", type=int, default=12)
    ap.add_argument("--only", default=None, choices=["clip_b32", "dinov2"])
    a = ap.parse_args()

    import torch
    torch.set_num_threads(a.threads)
    p293 = load_p293()
    PROBE_OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ds_train, ds_clean, val_idx = build_gallery(p293)
    print("[gallery] n=%d  (indices identical to _p357: d69098c0074eca13)" % len(val_idx),
          flush=True)

    res = {"script": "tools/_p360_gallery_noise.py", "draws": a.draws,
           "threads": a.threads, "device": "cpu", "torch": torch.__version__,
           "protocol_facts": {
               "gallery_transform_in_use": repr(ds_train.transform),
               "deterministic_transform_available": repr(ds_clean.transform),
               "origin": "src/dataset.py:401-425 -- create_dataloaders random-splits the "
                         "split='train' dataset object, so val/test keep "
                         "RandomHorizontalFlip+ColorJitter",
               "n_pairs": len(val_idx), "chance_R1": 1.0 / len(val_idx)},
           "reported_units": "CG/DG/R@1 exactly as src/trainer.py computes them on val_loader",
           "source_published_means":
               "outputs/analysis/dinov2_hetero/clip_baseline_check.json :: rows",
           "arms": {}, "wall_sec": None}

    if a.only in (None, "clip_b32"):
        run_clip(a, ds_clean, val_idx, a.draws, res)
    if a.only in (None, "dinov2"):
        run_dinov2(a, p293, ds_clean, val_idx, a.draws, res)

    res["wall_sec"] = round(time.time() - t0, 1)
    with open(PROBE_OUT / "results.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)
    print("\n[ok] wrote %s (%.1f min)" % (PROBE_OUT / "results.json",
                                          res["wall_sec"] / 60), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
