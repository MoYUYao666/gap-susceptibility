# -*- coding: utf-8 -*-
r"""PR R2.3 / R1.4 -- does the adaptation-position ordering survive on a NON-contrastive backbone?

WHY THIS EXISTS
    The strict-freeze control of `experiments/strict_freeze_control.py` is the experiment on
    which the paper's adaptation-position claim rests.  Every backbone it has been run on is
    either a contrastive dual encoder (CLIP B/32, CLIP B/16, OpenCLIP) or a pairwise-sigmoid /
    domain model (SigLIP, BioCLIP).  PR R2.3 asks for validation on models outside that set.

    `facebook/dinov2-base` is the only non-contrastive vision backbone available locally.  It has
    NO text tower, so it cannot be run through the unmodified control.  This script builds the
    minimal heterogeneous substitute and runs the identical three-arm control on it.

WHAT THE MODEL ACTUALLY IS  (read this before quoting any number)
    DINOv2-base vision tower  +  CLIP ViT-B/32 text tower  +  a shared 512-d projection head.

    This is a HETEROGENEOUS PAIRING, NOT A NATIVE MODEL.  It is not "DINOv2" and it is not
    "a non-contrastive dual encoder", because no such pretrained dual encoder exists here.
    DINOv2 is self-supervised on images alone, so it has no text space to be aligned with; the
    head below is what supplies one.  Two consequences are reported with the results:
      * `--head fitted` : the head is fitted on a split DISJOINT from both training and
        evaluation (train captions 5000..9999), then frozen for every arm; the fitting cost is
        recorded.  Whatever the head itself learns is therefore identical across arms.
      * `--head random` : the head is left at its seeded random initialisation.  This is the
        control for "the fitted head supplied the alignment, not the adapters".

PROTOCOL (identical to the strict-freeze control)
    Flickr30k, 5000 samples, 10 epochs, batch 128, rank 8 / alpha 16, LoRA on q_proj+v_proj.
    Strict freeze: every backbone parameter requires_grad=False; only the LoRA A/B matrices are
    trainable, asserted by identity against the injected layers.  Arms:
      text_only  = LoRA on the CLIP text tower only        (vision tower frozen)
      both       = LoRA on both towers
      vision_only= LoRA on the DINOv2 vision tower only
    CG/DG are computed by the unmodified `src/gap_metrics.GapTracker` on the 1000-pair-capped
    Flickr30k val split, exactly as in the control.

WHY THE HEAD IS FITTED ON A DISJOINT SPLIT
    A randomly initialised 768->512 map between two independently pretrained towers has no
    reason to carry mutual information; measuring the gap before fitting it would measure the
    head, not the backbone.  Fitting it on a disjoint split keeps the head outside the
    train/eval path, so the three arms still differ only in where the adapters sit.

USAGE
    python tools/_p293_dinov2_hetero_strict.py smoke
    python tools/_p293_dinov2_hetero_strict.py head  --head fitted
    python tools/_p293_dinov2_hetero_strict.py run   --head fitted --arm text_only --seed 42
    python tools/_p293_dinov2_hetero_strict.py all   --head fitted --seeds 42 123 456
    python tools/_p293_dinov2_hetero_strict.py all   --head random --seeds 42 123 456
    python tools/_p293_dinov2_hetero_strict.py tables

OUTPUTS
    outputs/analysis/dinov2_hetero/heads/<head>.pt                fitted head weights + fitting log
    outputs/analysis/dinov2_hetero/<head>/<arm>/seed<N>/results.json
    outputs/analysis/dinov2_hetero/<head>/<arm>/seed<N>/gap_history.json
    outputs/analysis/dinov2_hetero/tables.json
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.chdir(REPO)

PY = sys.executable
OUT_ROOT = REPO / "outputs" / "analysis" / "dinov2_hetero"
LOGS = OUT_ROOT / "logs"

VISION_PATH = "models/dinov2-base"
TEXT_PATH = "models/clip-vit-base-patch32"

SHARED_DIM = 512          # CLIP B/32 text-embedding width; both towers project into it
NUM_LAYERS = 12
VISION_HIDDEN = 768
TEXT_HIDDEN = 512

TRAIN_MAX_SAMPLES = 5000  # matches the strict-freeze control
TUNE_START, TUNE_END = 5000, 10000   # disjoint from train [0,5000); includes val/test slices
BATCH = 128
EPOCHS = 10
RANK = 8
ALPHA_MULT = 2
SEEDS = [42, 123, 456]

# Data root as the control resolves it: create_dataloaders builds
# os.path.join(data_dir, "flickr30k"), so data_dir="." -> "./flickr30k", where flickr30k.json
# and flickr30k-images/ actually live in this checkout.  Verified by
# tools/_p293_protocol_check_tmp.py.  Named here so no call site can drift.
DATA_DIR = "."
DATASET_ROOT = os.path.join(DATA_DIR, "flickr30k")
# create_dataloaders caps the DATASET to max_samples BEFORE the 80/10/10 random_split, so the
# evaluation gallery is 0.1 * 5000 = 500 pairs, not 1000; chance R@1 = 0.002.  Recorded in
# every results.json so the retrieval column is interpretable.
EVAL_PAIRS = int(0.1 * TRAIN_MAX_SAMPLES)
CHANCE_R1 = 1.0 / EVAL_PAIRS

# Fixed CLIP logit scale init (ln(1/0.07)); held fixed, not trained -- see report.
LOGIT_SCALE_INIT = 2.659260036932778

ARMS = {
    "text_only":   dict(apply_to_vision=False, apply_to_text=True),
    "both":        dict(apply_to_vision=True,  apply_to_text=True),
    "vision_only": dict(apply_to_vision=True,  apply_to_text=False),
}

# Each tower keeps its OWN native attention-projection names, because the two towers come from
# different codebases: CLIP calls them q_proj/v_proj, DINOv2 calls them query/value.  The
# control's target_modules default is ["q_proj","v_proj"], which silently matches NOTHING on
# DINOv2 -- verified: with the default the vision side gets 0 LoRA layers.  Substituting the
# architecture's own names keeps the manipulation identical in kind (the two projections that
# LoRA is applied to throughout the paper, q and v, at the same rank and alpha); what changes
# is only the module naming convention imposed by the codebase.
TARGET_MODULES = {"vision": ["query", "value"], "text": ["q_proj", "v_proj"]}
# The trainer's LoRAConfig carries a single list; it is not used to inject (injection is done
# here explicitly) and is only read back for the printed config, so give it the union.
TRAINER_TARGET_MODULES = ["q_proj", "v_proj", "query", "value"]

# Head parameters: Linear(768,512) + Linear(512,512)
HEAD_PARAMS = (VISION_HIDDEN * SHARED_DIM + SHARED_DIM) + (SHARED_DIM * SHARED_DIM + SHARED_DIM)


def n_lora_params(apply_to_vision, apply_to_text):
    """Closed-form count of trainable LoRA scalars, used as a cross-check on the assertions."""
    n = 0
    if apply_to_vision:
        n += NUM_LAYERS * 2 * VISION_HIDDEN * RANK * 2   # query, value; A(in,r)+B(r,out)
    if apply_to_text:
        n += NUM_LAYERS * 2 * TEXT_HIDDEN * RANK * 2
    return n


def expected_n_trainable(arm, fitting_head=False):
    """Closed-form trainable count; the head is trainable only while it is itself fitted."""
    return n_lora_params(**ARMS[arm]) + (HEAD_PARAMS if fitting_head else 0)


# ======================================================================
# model
# ======================================================================

def build_model(head_state=None, seed=42):
    """Frozen DINOv2 vision tower + frozen CLIP text tower + shared 512-d head."""
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from transformers import CLIPTextModelWithProjection, Dinov2Model

    class HeteroEncoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.vision_model = Dinov2Model.from_pretrained(VISION_PATH,
                                                            local_files_only=True)
            self.text_model = CLIPTextModelWithProjection.from_pretrained(
                TEXT_PATH, local_files_only=True)
            self.vision_projection = nn.Sequential(
                nn.Linear(VISION_HIDDEN, SHARED_DIM),
                nn.GELU(),
                nn.Linear(SHARED_DIM, SHARED_DIM),
            )
            self.logit_scale = nn.Parameter(torch.tensor(LOGIT_SCALE_INIT))
            self.image_embeds = None
            self.text_embeds = None

        def forward(self, pixel_values=None, input_ids=None, attention_mask=None,
                    return_loss=False, **kw):
            v = self.vision_model(pixel_values=pixel_values).pooler_output
            ie = self.vision_projection(v)
            t = self.text_model(input_ids=input_ids,
                                attention_mask=attention_mask).text_embeds
            ie = F.normalize(ie.float(), dim=-1)
            te = F.normalize(t.float(), dim=-1)
            self.image_embeds, self.text_embeds = ie, te
            return type("Out", (), {"image_embeds": ie, "text_embeds": te,
                                    "loss": None})()

    torch.manual_seed(seed)
    model = HeteroEncoder()
    # The head gets its own seeded init regardless of torch.manual_seed's global state order.
    g = torch.Generator().manual_seed(seed + 90001)
    for lin in (model.vision_projection[0], model.vision_projection[2]):
        nn.init.kaiming_uniform_(lin.weight, a=5 ** 0.5, generator=g)
        nn.init.zeros_(lin.bias)

    if head_state is not None:
        model.vision_projection.load_state_dict(head_state)
    return model


# ======================================================================
# head fitting (disjoint split; frozen for every arm)
# ======================================================================

def fit_head(head, epochs, batch, seed, smoke=False):
    import numpy as np
    import torch
    import torch.nn.functional as F
    from torch.optim import AdamW
    from torch.utils.data import DataLoader, Subset
    from transformers import CLIPTokenizerFast

    from src.dataset import Flickr30kDataset, _collate_fn

    t0 = time.time()
    # Same root the control uses: create_dataloaders(data_dir=".") -> "./flickr30k"
    root = REPO / DATASET_ROOT
    ds = Flickr30kDataset(str(root), split="train", image_size=224,
                          max_samples=None, pre_tokenize=True)
    assert len(ds) > TUNE_END, "tuning split [%d,%d) exceeds corpus (%d)" % (
        TUNE_START, TUNE_END, len(ds))
    tune = Subset(ds, range(TUNE_START, TUNE_END))
    loader = DataLoader(tune, batch_size=batch, shuffle=True, num_workers=0,
                        collate_fn=_collate_fn)
    print("[head] tuning split = train captions [%d, %d)  n=%d  (train uses [0,%d))"
          % (TUNE_START, TUNE_END, len(tune), TRAIN_MAX_SAMPLES), flush=True)

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = build_model(seed=seed).to(dev)
    for p in model.parameters():
        p.requires_grad = False
    for p in model.vision_projection.parameters():
        p.requires_grad = True
    params = [p for p in model.vision_projection.parameters()]
    n_head = sum(p.numel() for p in params)
    opt = AdamW(params, lr=1e-4, weight_decay=0.01)
    model.train()

    for ep in range(1, epochs + 1):
        tot, nb = 0.0, 0
        for b in loader:
            opt.zero_grad(set_to_none=True)
            out = model(pixel_values=b["image"].to(dev),
                        input_ids=b["input_ids"].to(dev),
                        attention_mask=b["attention_mask"].to(dev))
            logits = model.logit_scale.exp() * out.image_embeds @ out.text_embeds.T
            lab = torch.arange(logits.shape[0], device=dev)
            loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
            loss.backward()
            opt.step()
            tot += loss.item()
            nb += 1
        print("[head] epoch %d/%d  train_loss=%.4f" % (ep, epochs, tot / max(nb, 1)),
              flush=True)
        if smoke and ep >= 1:
            break

    # held-out retrieval on the SAME val loader the arms use, to size what the head supplies
    r1 = evaluate_head_retrieval(model, dev)
    state = {k: v.detach().cpu().clone() for k, v in model.vision_projection.state_dict().items()}
    meta = {
        "head": "fitted",
        "tuning_split": "flickr30k train captions [%d, %d)" % (TUNE_START, TUNE_END),
        "tuning_n": len(tune),
        "epochs": epochs,
        "batch": batch,
        "lr": 1e-4,
        "seed": seed,
        "n_head_params": n_head,
        "val_R@1_after_fitting": r1,
        "fit_seconds": round(time.time() - t0, 1),
        "note": ("head fitted on a split disjoint from the arm training data ([0,%d)) and from "
                 "the gap/retrieval evaluation; frozen for every arm" % TRAIN_MAX_SAMPLES),
    }
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "heads").mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": state, "meta": meta}, OUT_ROOT / "heads" / "fitted.pt")
    print("[head] saved -> %s  val R@1 = %.4f  (%.0fs)"
          % (OUT_ROOT / "heads" / "fitted.pt", r1, meta["fit_seconds"]), flush=True)
    return meta


def evaluate_head_retrieval(model, dev):
    import torch
    import torch.nn.functional as F
    from torch.utils.data import DataLoader

    from src.dataset import create_dataloaders

    _, val_loader, _ = create_dataloaders(dataset_name="flickr30k", data_dir=DATA_DIR,
                                          batch_size=BATCH, max_samples=TRAIN_MAX_SAMPLES)
    model.eval()
    I, T = [], []
    with torch.no_grad():
        for b in val_loader:
            out = model(pixel_values=b["image"].to(dev), input_ids=b["input_ids"].to(dev),
                        attention_mask=b["attention_mask"].to(dev))
            I.append(out.image_embeds.cpu())
            T.append(out.text_embeds.cpu())
    I, T = torch.cat(I), torch.cat(T)
    sim = I @ T.T
    lab = torch.arange(len(sim))
    r1 = ((sim.topk(1, dim=1).indices.squeeze(1) == lab).float().mean().item()
          + (sim.T.topk(1, dim=1).indices.squeeze(1) == lab).float().mean().item()) / 2
    return r1


# ======================================================================
# strict-freeze arm run
# ======================================================================

def run_arm(arm, seed, head, epochs, batch, max_samples):
    import torch
    import torch.nn.functional as F

    from src.config import ExperimentConfig, GapConfig, LoRAConfig, TrainConfig
    from src.dataset import create_dataloaders
    from src.gap_metrics import GapTracker
    from src.lora import _inject_lora
    from src.trainer import GapAwareTrainer

    assert arm in ARMS, arm
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(seed)

    head_state = None
    if head == "fitted":
        ck = torch.load(OUT_ROOT / "heads" / "fitted.pt", weights_only=False)
        head_state = ck["state_dict"]
    model = build_model(head_state=head_state, seed=seed)

    # ---- LoRA injection via the SAME primitive the control's shared src/ path uses
    # (src/lora.py::_inject_lora).  Called once per tower with that tower's own projection
    # names -- see TARGET_MODULES for why a single list cannot express this. ----
    lora_layers = {}
    for tower, attr in (("vision", "vision_model"), ("text", "text_model")):
        if not ARMS[arm]["apply_to_%s" % tower]:
            continue
        _inject_lora(getattr(model, attr), TARGET_MODULES[tower], RANK, RANK * ALPHA_MULT,
                     0.0, lora_layers, tower, False, False)
    n_vis_layers = sum(1 for k in lora_layers if k.startswith("vision"))
    n_txt_layers = sum(1 for k in lora_layers if k.startswith("text"))
    print("[lora] layers: vision=%d text=%d  params=%d"
          % (n_vis_layers, n_txt_layers,
             sum(w.lora_A.numel() + w.lora_B.numel() for w in lora_layers.values())),
          flush=True)

    # ---- STRICT FREEZE: everything off, then only the LoRA A/B matrices on ----
    for p in model.parameters():
        p.requires_grad = False
    lora_ids = set()
    for w in lora_layers.values():
        for p in (w.lora_A, w.lora_B):
            p.requires_grad = True
            lora_ids.add(id(p))
    trainable = [p for p in model.parameters() if p.requires_grad]
    n_strict = sum(p.numel() for p in trainable)
    assert all(id(p) in lora_ids for p in trainable), "non-LoRA parameter left trainable"
    assert n_strict == n_lora_params(**ARMS[arm]), \
        "trainable %d != closed form %d" % (n_strict, n_lora_params(**ARMS[arm]))
    # Parameter split by tower, taken from the injected layer dict itself (not by name prefix
    # of the tensor, which differs between towers).
    n_vis = sum(w.lora_A.numel() + w.lora_B.numel()
                for k, w in lora_layers.items() if k.startswith("vision"))
    n_txt = sum(w.lora_A.numel() + w.lora_B.numel()
                for k, w in lora_layers.items() if k.startswith("text"))
    assert n_vis + n_txt == n_strict, "tower split %d+%d != %d" % (n_vis, n_txt, n_strict)
    print("[strict] arm=%s seed=%d  n_trainable=%d (vis=%d txt=%d)  lora_layers=%d"
          % (arm, seed, n_strict, n_vis, n_txt, len(lora_layers)), flush=True)

    # ---- config: dataloaders + trainer scaffolding. Only `model` is overridden; the whole
    # train loop, gap metrics and retrieval metrics come from the unmodified src/ trainer.
    save_dir = OUT_ROOT / head / arm / ("seed%d" % seed)
    cfg = ExperimentConfig(
        name="dinov2het_%s_%s" % (head, arm),
        lora=LoRAConfig(rank=RANK, alpha=RANK * ALPHA_MULT, dropout=0.0,
                        target_modules=["q_proj", "v_proj"], **ARMS[arm]),
        gap=GapConfig(compute_every_n_epochs=1),
        train=TrainConfig(dataset="flickr30k", batch_size=batch, num_epochs=epochs,
                          max_samples=max_samples, save_dir=str(save_dir),
                          clip_model=TEXT_PATH, device=dev),
    )
    train_loader, val_loader, _ = create_dataloaders(
        dataset_name="flickr30k", data_dir=DATA_DIR, batch_size=batch,
        max_samples=max_samples)
    n_pairs = len(val_loader.dataset)
    print("[data] train=%d val=%d (retrieval gallery; chance R@1=%.4f)"
          % (len(train_loader.dataset), n_pairs, 1.0 / n_pairs), flush=True)

    trainer = GapAwareTrainer(cfg)
    trainer.model = model.to(dev)
    trainer.processor = None          # the loader pre-tokenizes; nothing tokenizes at train time
    trainer.lora_layers = lora_layers
    trainer._trainable_params = trainable
    trainer.optimizer = None

    # sanity: the trainer must optimise exactly the LoRA parameters we froze in
    assert set(id(p) for p in trainer._trainable_params) == lora_ids

    t0 = time.time()
    result = trainer.train(train_loader, val_loader)
    elapsed = time.time() - t0

    # ---- what actually moved.  `backbone_delta` covers only PRE-EXISTING weights, so under
    # strict freezing it is 0 by construction -- that is the freeze verification, not the
    # adaptation.  The adaptation lives in the LoRA A/B matrices, which are not part of any
    # reference state_dict and must be measured separately.  Both are recorded.
    #
    # DO NOT zero the LoRA matrices "to make the reference pristine": `ref` is a fresh model with
    # no LoRA attached, while `lora_layers` belongs to the TRAINED `model`, so zeroing them would
    # destroy the very quantity the next block measures (this bug was caught in review before the
    # `both` arm finished; the trained checkpoints were unaffected).
    ref = build_model(head_state=head_state, seed=seed)
    ref_sd = {k: v.float() for k, v in ref.state_dict().items()}
    agg = {}
    for name, p in model.named_parameters():
        key = name.replace(".original.", ".").replace(".original", "")
        if key not in ref_sd:
            continue
        grp = ("vision" if key.startswith("vision_model")
               else "text" if key.startswith("text_model")
               else "head" if key.startswith("vision_projection") else "other")
        d = p.detach().cpu().float() - ref_sd[key]
        a = agg.setdefault(grp, {"tensors": 0, "nonzero_tensors": 0,
                                 "max_abs_delta": 0.0, "sq": 0.0})
        a["tensors"] += 1
        mx = d.abs().max().item()
        a["nonzero_tensors"] += 1 if mx > 0 else 0
        a["max_abs_delta"] = max(a["max_abs_delta"], mx)
        a["sq"] += float(d.norm().item()) ** 2
    deltas = {g: {**v, "frobenius": v["sq"] ** 0.5} for g, v in agg.items()}
    for v in deltas.values():
        v.pop("sq")

    # LoRA update magnitude per tower.  Two aggregates are recorded on purpose, because they are
    # different quantities and a report must not switch between them mid-table:
    #   * `frobenius_of_scaled_update` = sqrt(sum_layers ||scaling*A@B||_F^2)
    #   * `sum_of_per_layer_frobenius` = sum_layers ||scaling*A@B||_F  (not a norm of one matrix)
    lora_norms, lora_sum, lora_max = {}, {}, {}
    for k, w in lora_layers.items():
        grp = "vision" if k.startswith("vision") else "text"
        delta = (w.scaling * (w.lora_A @ w.lora_B)).detach().cpu().float()
        n = float(delta.norm().item())
        lora_norms[grp] = lora_norms.get(grp, 0.0) + n ** 2
        lora_sum[grp] = lora_sum.get(grp, 0.0) + n
        lora_max[grp] = max(lora_max.get(grp, 0.0), float(delta.abs().max().item()))
    lora_norms = {g: v ** 0.5 for g, v in lora_norms.items()}

    cg0 = (result.get("initial_gap") or {}).get("centroid_gap")
    cg1 = (result.get("final_gap") or {}).get("centroid_gap")
    dg0 = (result.get("initial_gap") or {}).get("distribution_gap")
    dg1 = (result.get("final_gap") or {}).get("distribution_gap")
    tm = result.get("final_task_metrics") or {}

    out = {
        "experiment": "dinov2_hetero_strict",
        "heterogeneous_pairing": True,
        "vision_tower": VISION_PATH,
        "text_tower": TEXT_PATH,
        "head": head,
        "arm": arm,
        "seed": seed,
        "strict_freeze": True,
        "n_trainable_params": n_strict,
        "n_trainable_vision_side": n_vis,
        "n_trainable_text_side": n_txt,
        "n_trainable_from_trainer": result.get("n_trainable_params"),
        "rank": RANK, "alpha": RANK * ALPHA_MULT,
        "epochs": epochs, "max_samples": max_samples, "batch_size": batch,
        "image_size": 224,
        "eval_gallery_pairs": n_pairs,
        "chance_R@1": 1.0 / n_pairs,
        "data_dir": DATA_DIR,
        "image_normalisation": "CLIP mean/std (src/dataset.py:19-20), not DINOv2's ImageNet stats",
        "logit_scale": LOGIT_SCALE_INIT,
        "logit_scale_trainable": False,
        "elapsed_sec": round(elapsed, 1),
        "CG_initial": cg0, "CG_final": cg1,
        "DG_initial": dg0, "DG_final": dg1,
        "delta_CG": (cg1 - cg0) if (cg0 is not None and cg1 is not None) else None,
        "delta_DG": (dg1 - dg0) if (dg0 is not None and dg1 is not None) else None,
        "R@1": tm.get("R@1"), "R@1_i2t": tm.get("R@1_i2t"), "R@1_t2i": tm.get("R@1_t2i"),
        "R@5": tm.get("R@5"),
        "backbone_delta": deltas,
        "backbone_delta_note": ("pre-existing weights only; 0 under strict freezing is the freeze "
                                "verification, not a measure of adaptation"),
        "lora_update_norm_frobenius": lora_norms,
        "lora_update_sum_of_layer_frobenius": lora_sum,
        "lora_update_max_abs": lora_max,
        "lora_update_definitions": {
            "lora_update_norm_frobenius": "sqrt(sum_layers ||scaling*A@B||_F^2)",
            "lora_update_sum_of_layer_frobenius": "sum_layers ||scaling*A@B||_F",
        },
        "final_train_loss": result.get("final_train_loss"),
        "final_val_loss": result.get("final_val_loss"),
        "source": {
            "script": "tools/_p293_dinov2_hetero_strict.py",
            "trainer": "src/trainer.py::GapAwareTrainer (unmodified)",
            "gap_metrics": "src/gap_metrics.py::GapTracker (unmodified)",
            "head_checkpoint": ("outputs/analysis/dinov2_hetero/heads/fitted.pt"
                                if head == "fitted" else None),
        },
        "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    save_dir.mkdir(parents=True, exist_ok=True)
    with open(save_dir / "results.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    # gap history, straight from the trainer's tracker
    with open(save_dir / "gap_history.json", "w", encoding="utf-8") as fh:
        json.dump(trainer.gap_tracker.get_history_dict(), fh, indent=2, ensure_ascii=False)

    print("[done] %s/%s seed=%d  dCG=%s  dDG=%s  R@1=%s  vis_nonzero=%s  head_nonzero=%s  %.0fs"
          % (head, arm, seed, out["delta_CG"], out["delta_DG"], out["R@1"],
             deltas.get("vision", {}).get("nonzero_tensors"),
             deltas.get("head", {}).get("nonzero_tensors"), elapsed), flush=True)
    return out


def run_frozen(head, max_samples, batch):
    """Matched frozen baseline: the same constructed model, no training at all."""
    import torch

    from src.dataset import create_dataloaders
    from src.gap_metrics import GapTracker

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    head_state = None
    if head == "fitted":
        head_state = torch.load(OUT_ROOT / "heads" / "fitted.pt",
                                weights_only=False)["state_dict"]
    model = build_model(head_state=head_state, seed=42).to(dev).eval()
    _, val_loader, _ = create_dataloaders(dataset_name="flickr30k", data_dir=DATA_DIR,
                                          batch_size=batch, max_samples=max_samples)
    I, T = [], []
    with torch.no_grad():
        for b in val_loader:
            out = model(pixel_values=b["image"].to(dev), input_ids=b["input_ids"].to(dev),
                        attention_mask=b["attention_mask"].to(dev))
            I.append(out.image_embeds.cpu())
            T.append(out.text_embeds.cpu())
    gt = GapTracker(sample_size=max_samples, device="cpu")
    m = gt.compute(torch.cat(I), torch.cat(T), epoch=0, step=0)
    sim = torch.cat(I) @ torch.cat(T).T
    lab = torch.arange(len(sim))
    r1 = ((sim.topk(1, dim=1).indices.squeeze(1) == lab).float().mean().item()
          + (sim.T.topk(1, dim=1).indices.squeeze(1) == lab).float().mean().item()) / 2
    out = {"experiment": "dinov2_hetero_frozen", "head": head, "n_trainable_params": 0,
           "CG": m.centroid_gap, "DG": m.distribution_gap, "R@1": r1,
           "max_samples": max_samples, "batch_size": batch,
           "vision_tower": VISION_PATH, "text_tower": TEXT_PATH,
           "heterogeneous_pairing": True,
           "source": {"script": "tools/_p293_dinov2_hetero_strict.py"}}
    d = OUT_ROOT / head / "frozen"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "results.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print("[frozen:%s] CG=%.4f DG=%.4f R@1=%.4f" % (head, m.centroid_gap, m.distribution_gap, r1),
          flush=True)
    return out


# ======================================================================
# driver: every arm in its own subprocess (leak isolation), GPU strictly serial
# ======================================================================

def gpu_python_others():
    """Commands of OTHER python processes holding GPU memory.

    All subprocess output is decoded with errors='replace': this machine's console tools emit
    output in the local ANSI codepage, and a strict decode raised UnicodeDecodeError inside
    subprocess's pipe-drain thread (measured 2026-10-12).  The run survived because that thread
    is a daemon, but the failure-tail diagnostic was lost -- so every read is lenient now.
    """
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
             "--format=csv,noheader"], capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace")
    except Exception:
        return []
    rows = []
    for line in (out.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(line)
    return rows


def wait_for_gpu(tag, max_wait=7200, poll=60):
    """Block while another python.exe holds GPU memory. Single-GPU project rule."""
    if os.environ.get("P293_SKIP_GPU_WAIT") == "1":
        print("[gpu] wait disabled by P293_SKIP_GPU_WAIT=1", flush=True)
        return
    t0 = time.time()
    while True:
        rows = gpu_python_others()
        busy = [r for r in rows if "python" in r.lower()]
        if not busy:
            return
        if time.time() - t0 > max_wait:
            raise SystemExit("[gpu] waited %ds for %s, still busy: %s"
                             % (max_wait, tag, busy))
        print("[gpu] %s: %s busy, waiting %ds" % (tag, busy, poll), flush=True)
        time.sleep(poll)


def cmd_all(args):
    LOGS.mkdir(parents=True, exist_ok=True)
    tasks = []
    arms = args.arms or list(ARMS)
    if not args.skip_frozen:
        tasks.append(("frozen", None))
    for arm in arms:
        for seed in args.seeds:
            tasks.append((arm, seed))

    for arm, seed in tasks:
        tag = "frozen" if seed is None else "%s_seed%d" % (arm, seed)
        outfile = (OUT_ROOT / args.head / ("frozen" if seed is None else arm)
                   / ("results.json" if seed is None else "seed%d/results.json" % seed))
        if outfile.exists() and not args.force:
            print("[skip] %s exists" % outfile, flush=True)
            continue
        wait_for_gpu(tag)
        cmd = [PY, str(Path(__file__).resolve()), "run", "--head", args.head,
               "--epochs", str(args.epochs), "--batch", str(args.batch),
               "--max-samples", str(args.max_samples)]
        if seed is None:
            cmd += ["--frozen"]
        else:
            cmd += ["--arm", arm, "--seed", str(seed)]
        log = LOGS / ("%s_%s.log" % (args.head, tag))
        print("[run] %s -> %s" % (" ".join(cmd[1:]), log), flush=True)
        t0 = time.time()
        with open(log, "w", encoding="utf-8") as fh:
            rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT,
                                cwd=str(REPO)).returncode
        print("[run] %s rc=%d  %.0fs" % (tag, rc, time.time() - t0), flush=True)
        if rc != 0:
            print("[run] FAILED %s -- tail of %s:" % (tag, log), flush=True)
            tail = open(log, encoding="utf-8", errors="replace").read().splitlines()[-25:]
            print("\n".join(tail), flush=True)
            if args.stop_on_fail:
                raise SystemExit(1)


def cmd_run(args):
    if args.frozen:
        return run_frozen(args.head, args.max_samples, args.batch)
    return run_arm(args.arm, args.seed, args.head, args.epochs, args.batch, args.max_samples)


def cmd_smoke(args):
    """One-epoch end-to-end check plus a peak-memory probe on the real batch size."""
    import torch
    print("=" * 70)
    print("SMOKE: head fit (1 epoch) then one full-size training step, peak memory reported")
    print("=" * 70)
    m = fit_head(args.head, epochs=1, batch=args.batch, seed=42, smoke=True)
    print("[smoke] head meta:", json.dumps({k: v for k, v in m.items() if k != "note"},
                                           ensure_ascii=False))
    torch.cuda.reset_peak_memory_stats()
    out = run_arm("both", 42, args.head, epochs=1, batch=args.batch, max_samples=512)
    peak = torch.cuda.max_memory_allocated() / 2 ** 20
    reserved = torch.cuda.max_memory_reserved() / 2 ** 20
    print("[smoke] peak_allocated=%.0f MiB  peak_reserved=%.0f MiB" % (peak, reserved), flush=True)
    d = OUT_ROOT / "smoke"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "smoke.json", "w", encoding="utf-8") as fh:
        json.dump({"head_meta": m, "peak_allocated_MiB": peak, "peak_reserved_MiB": reserved,
                   "batch": args.batch, "delta_CG": out["delta_CG"], "delta_DG": out["delta_DG"],
                   "R@1": out["R@1"], "n_trainable_params": out["n_trainable_params"]},
                  fh, indent=2, ensure_ascii=False)
    print("[smoke] wrote", d / "smoke.json", flush=True)


# ======================================================================
# tables (rendered from the archived JSON, never hand-copied)
# ======================================================================

def _load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _sd(xs):
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return None
    mu = sum(xs) / len(xs)
    return (sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


def cmd_tables(args):
    lines = []
    tables = {"generated_by": "tools/_p293_dinov2_hetero_strict.py tables", "heads": {}}
    for head in ("fitted", "random"):
        d = OUT_ROOT / head
        if not d.exists():
            continue
        rows = {}
        for arm in ARMS:
            fs = sorted(d.glob("%s/seed*/results.json" % arm))
            if not fs:
                continue
            runs = [_load(f) for f in fs]
            rows[arm] = {
                "n_seeds": len(runs),
                "seeds": [r["seed"] for r in runs],
                "delta_CG_mean": _mean([r["delta_CG"] for r in runs]),
                "delta_CG_sd": _sd([r["delta_CG"] for r in runs]),
                "delta_DG_mean": _mean([r["delta_DG"] for r in runs]),
                "delta_DG_sd": _sd([r["delta_DG"] for r in runs]),
                "R1_mean": _mean([r["R@1"] for r in runs]),
                "R1_sd": _sd([r["R@1"] for r in runs]),
                "n_trainable_params": runs[0]["n_trainable_params"],
            }
        fr = d / "frozen" / "results.json"
        frozen = _load(fr) if fr.exists() else None
        order = sorted(rows, key=lambda a: rows[a]["delta_CG_mean"])
        tables["heads"][head] = {"arms": rows, "frozen": frozen,
                                 "ordering_by_delta_CG_ascending": order}
        hdr = ("| head | arm | n | dCG (mean+-sd) | dDG (mean+-sd) | R@1 (mean+-sd) | "
               "trainable |")
        lines += ["", "### head = %s" % head, "", hdr,
                  "|---|---|---|---|---|---|---|"]
        if frozen:
            lines.append("| %s | frozen | - | %.4f (init) | %.4f (init) | %.4f | 0 |"
                         % (head, frozen["CG"], frozen["DG"], frozen["R@1"]))
        for arm in ARMS:
            if arm not in rows:
                continue
            r = rows[arm]

            def f(v, s):
                return "n/a" if v is None else ("%.4f +- %.4f" % (v, s) if s is not None
                                                else "%.4f" % v)
            lines.append("| %s | %s | %d | %s | %s | %s | %d |"
                         % (head, arm, r["n_seeds"],
                            f(r["delta_CG_mean"], r["delta_CG_sd"]),
                            f(r["delta_DG_mean"], r["delta_DG_sd"]),
                            f(r["R1_mean"], r["R1_sd"]), r["n_trainable_params"]))
        lines.append("")
        lines.append("ordering by dCG ascending (smallest gap change first): %s"
                     % " < ".join(order))
    tables["rendered_markdown"] = "\n".join(lines)
    with open(OUT_ROOT / "tables.json", "w", encoding="utf-8") as fh:
        json.dump(tables, fh, indent=2, ensure_ascii=False)
    print("\n".join(lines))
    print("\n[ok] wrote", OUT_ROOT / "tables.json")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--head", default="fitted", choices=["fitted", "random"])
        p.add_argument("--epochs", type=int, default=EPOCHS)
        p.add_argument("--batch", type=int, default=BATCH)
        p.add_argument("--max-samples", type=int, default=TRAIN_MAX_SAMPLES)

    for name in ("smoke", "head", "all", "run", "tables"):
        p = sub.add_parser(name)
        common(p)
        if name == "all":
            p.add_argument("--seeds", nargs="*", type=int, default=SEEDS)
            p.add_argument("--arms", nargs="*", default=None)
            p.add_argument("--force", action="store_true")
            p.add_argument("--stop-on-fail", action="store_true")
            p.add_argument("--skip-frozen", action="store_true")
        if name == "run":
            p.add_argument("--arm", required=False, default="text_only", choices=list(ARMS))
            p.add_argument("--seed", type=int, default=42)
            p.add_argument("--frozen", action="store_true")
        if name == "head":
            p.add_argument("--seed", type=int, default=42)

    a = ap.parse_args()
    if a.cmd == "smoke":
        cmd_smoke(a)
    elif a.cmd == "head":
        fit_head("fitted", a.epochs, a.batch, a.seed)
    elif a.cmd == "run":
        cmd_run(a)
    elif a.cmd == "all":
        cmd_all(a)
    elif a.cmd == "tables":
        cmd_tables(a)


if __name__ == "__main__":
    main()
