# -*- coding: utf-8 -*-
"""
P1 strict-freeze control  (2026-09-18)
=====================================
WHY THIS EXISTS
    src/lora.py:215-236 (apply_lora_to_model) never freezes the backbone: it only
    injects LoRALinear wrappers, each of which freezes its own wrapped Linear.  The
    Adapter and Prefix paths DO freeze first (src/peft_methods.py:107 and :129).
    Consequence: every LoRA run in outputs/ trained whatever else had
    requires_grad=True.  The archive proves it -- outputs/flickr30k/rq2_text_only/
    results.json:44 records n_trainable_params = 145170177 for a CLIP ViT-B/32 whose
    total is ~151M, versus 405888 for the comparable Adapter run and 131290881 for
    rq2_both (FEWER than text-only, the signature of freezing only the replaced
    Linears).  The paper's supplement then claims "text-only has zero vision-side
    updates", which that figure cannot support.

WHAT IT DOES
    Re-runs the same RQ2 configurations with the manipulation the paper claims:
    ONLY the LoRA adapters are trainable.  Nothing under src/ is modified -- the
    freeze is applied after GapAwareTrainer.__init__ has injected the adapters and
    before train() builds the optimizer, which selects parameters by requires_grad
    (src/trainer.py:242-244).

    Per run it records, besides the usual gap/R@1 numbers:
      * n_trainable_params                 (must be ~2*rank*512*#layers, not ~145M)
      * backbone delta-W per encoder       (vision / text / other), measured against
                                           a pristine CLIP reloaded from disk:
                                           nonzero_tensors, max|delta|, Frobenius
      * LoRA update magnitude per encoder  (scaling * B @ A), Frobenius
      * layer-wise effective rank at init and after training, using the SAME
        definition as paper/scripts/noise_sensitivity.py:170-177
        (exp of the entropy of the normalised singular values, mean-pooled over
        tokens, 16 samples -- kept at 16 to stay comparable with
        outputs/effective_rank_tracking.json)

USAGE
    python experiments/strict_freeze_control.py --smoke          # 1 epoch, 1 seed, 512 samples
    python experiments/strict_freeze_control.py                  # full: 3 configs x 5 seeds
    python experiments/strict_freeze_control.py --tags text_only --seeds 42
"""

import argparse
import collections
import json
import os
import sys
import time

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from src.config import ExperimentConfig, LoRAConfig, TrainConfig   # noqa: E402
from src.trainer import GapAwareTrainer                            # noqa: E402
from src.dataset import create_dataloaders                         # noqa: E402

PRISTINE = os.path.join(ROOT, "models", "clip-vit-base-patch32")
OUT_DIR = "outputs/strict_freeze"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# RQ2 configurations of the paper, rank 8 / alpha 16 as published.
CONFIGS = {
    "text_only":   dict(apply_to_vision=False, apply_to_text=True),
    "both":        dict(apply_to_vision=True,  apply_to_text=True),
    "vision_only": dict(apply_to_vision=True,  apply_to_text=False),
}


def set_seed(seed):
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def strict_freeze(trainer):
    """Freeze everything, then re-enable ONLY the LoRA A/B matrices."""
    for p in trainer.model.parameters():
        p.requires_grad = False
    n = 0
    for w in trainer.lora_layers.values():
        for p in (w.lora_A, w.lora_B):
            p.requires_grad = True
            n += p.numel()
    return n


class StrictTrainer(GapAwareTrainer):
    """GapAwareTrainer with the LoRA backbone freeze the library never applied.

    setup_model() is called by train() only when self.model is None
    (src/trainer.py:225-226), so calling it explicitly here is enough to put the
    freeze in place before the optimizer is built (src/trainer.py:242-244).
    """

    strict_n = 0

    def setup_model(self):
        super().setup_model()
        self.strict_n = strict_freeze(self)
        total = sum(p.numel() for p in self.model.parameters())
        print("[strict] trainable=%d (%.4f%% of %d)  lora_layers=%d"
              % (self.strict_n, 100.0 * self.strict_n / total, total,
                 len(self.lora_layers)))
        assert self.strict_n < 2_000_000, \
            "strict freeze failed: %d trainable params" % self.strict_n


@torch.no_grad()
def compute_effective_rank(embeddings):
    """Same definition as paper/scripts/noise_sensitivity.py:170-177."""
    U, S, Vt = torch.linalg.svd(embeddings.float(), full_matrices=False)
    p = S / S.sum()
    p = p[p > 1e-10]
    entropy = -(p * torch.log(p)).sum()
    return torch.exp(entropy).item()


@torch.no_grad()
def layer_effective_ranks(model, batch, processor, n_samples=16):
    """Per-layer effective rank over the vision and text encoder stacks."""
    vis, txt = {}, {}
    hooks = []

    def mk(storage, name):
        def hook(module, inp, out):
            h = out[0] if isinstance(out, tuple) else out
            storage[name] = h.detach()
        return hook

    for i, layer in enumerate(model.vision_model.encoder.layers):
        hooks.append(layer.register_forward_hook(mk(vis, "vis_L%d" % i)))
    for i, layer in enumerate(model.text_model.encoder.layers):
        hooks.append(layer.register_forward_hook(mk(txt, "txt_L%d" % i)))

    images = batch["image"][:n_samples].to(DEVICE)
    cap = batch["caption"][:n_samples]
    ti = processor(text=cap, return_tensors="pt", padding=True,
                   truncation=True, max_length=77)
    model(pixel_values=images,
          input_ids=ti["input_ids"].to(DEVICE),
          attention_mask=ti["attention_mask"].to(DEVICE))
    for h in hooks:
        h.remove()

    ranks = {}
    for name, hidden in {**vis, **txt}.items():
        ranks[name] = compute_effective_rank(hidden.mean(dim=1).cpu())
    return ranks


@torch.no_grad()
def backbone_deltas(model):
    """Delta-W against a pristine CLIP.  Names are normalised because LoRA
    injection renames <proj>.weight to <proj>.original.weight."""
    ref = CLIPModel.from_pretrained(PRISTINE, local_files_only=True)
    ref_sd = ref.state_dict()
    agg = collections.defaultdict(
        lambda: {"tensors": 0, "nonzero": 0, "max_abs": 0.0, "sq": 0.0})
    for name, p in model.named_parameters():
        key = name.replace(".original.", ".").replace(".original", "")
        if key not in ref_sd:
            continue
        grp = ("vision" if key.startswith("vision_model")
               else "text" if key.startswith("text_model") else "other")
        d = p.detach().cpu().float() - ref_sd[key].float()
        mx = d.abs().max().item()
        agg[grp]["tensors"] += 1
        agg[grp]["nonzero"] += 1 if mx > 0 else 0
        agg[grp]["max_abs"] = max(agg[grp]["max_abs"], mx)
        agg[grp]["sq"] += float(d.norm().item()) ** 2
    out = {}
    for grp, v in agg.items():
        out[grp] = {"tensors": v["tensors"], "nonzero_tensors": v["nonzero"],
                    "max_abs_delta": v["max_abs"], "frobenius": v["sq"] ** 0.5}
    return out


@torch.no_grad()
def lora_update_norms(lora_layers):
    """Effective weight change contributed by the adapters: scaling * B @ A."""
    agg = collections.defaultdict(float)
    for name, w in lora_layers.items():
        grp = "vision" if name.startswith("vision") else "text"
        delta = (w.scaling * (w.lora_A @ w.lora_B)).detach().cpu().float()
        agg[grp] += float(delta.norm().item()) ** 2
    return {g: v ** 0.5 for g, v in agg.items()}


def run_one(tag, seed, epochs, max_samples, batch_size):
    set_seed(seed)
    save_dir = "%s/%s/seed%d" % (OUT_DIR, tag, seed)
    cfg = ExperimentConfig(
        name="strict_%s" % tag,
        lora=LoRAConfig(rank=8, alpha=16, **CONFIGS[tag]),
        train=TrainConfig(dataset="flickr30k", batch_size=batch_size,
                          num_epochs=epochs, max_samples=max_samples,
                          save_dir=save_dir),
    )
    train_loader, val_loader, _ = create_dataloaders(
        dataset_name="flickr30k", data_dir=".", batch_size=batch_size,
        max_samples=max_samples)

    trainer = StrictTrainer(cfg)
    trainer.setup_model()          # loads CLIP, injects LoRA, then strict-freezes
    n_strict = trainer.strict_n

    first = next(iter(val_loader))
    ranks_init = layer_effective_ranks(trainer.model, first, trainer.processor)

    t0 = time.time()
    result = trainer.train(train_loader, val_loader)
    elapsed = time.time() - t0

    trainer.model.eval()
    ranks_final = layer_effective_ranks(trainer.model, first, trainer.processor)
    deltas = backbone_deltas(trainer.model)
    lora_norms = lora_update_norms(trainer.lora_layers)

    out = {
        "experiment": "strict_%s" % tag,
        "seed": seed,
        "strict_freeze": True,
        "n_trainable_params": n_strict,
        "n_trainable_reported_by_trainer": result.get("n_trainable_params"),
        "epochs": epochs,
        "max_samples": max_samples,
        "batch_size": batch_size,
        "elapsed_sec": round(elapsed, 1),
        "initial_gap": result.get("initial_gap"),
        "final_gap": result.get("final_gap"),
        "final_task_metrics": result.get("final_task_metrics"),
        "final_train_loss": result.get("final_train_loss"),
        "final_val_loss": result.get("final_val_loss"),
        "backbone_delta": deltas,
        "lora_update_norm": lora_norms,
        "effective_rank_init": ranks_init,
        "effective_rank_final": ranks_final,
    }
    os.makedirs(save_dir, exist_ok=True)
    with open(os.path.join(save_dir, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    cg0 = (result.get("initial_gap") or {}).get("centroid_gap")
    cg1 = (result.get("final_gap") or {}).get("centroid_gap")
    r1 = (result.get("final_task_metrics") or {}).get("R@1")
    print("[done] %s seed=%d cg %.4f -> %.4f  R@1=%s  vis_nonzero=%s  %.0fs"
          % (tag, seed, cg0 or -1, cg1 or -1, r1,
             deltas.get("vision", {}).get("nonzero_tensors"), elapsed))
    return out


def run_frozen(max_samples, batch_size):
    """Matched frozen reference: pristine CLIP, no training, gap + layer ranks.

    Note: for LoRA, B is initialised to zero, so the adapter-injected model is
    numerically identical to the pristine one at step 0.  Each strict run's
    effective_rank_init is therefore the same frozen reference; this function
    only records it once, explicitly, and confirms backbone_delta == 0.
    """
    from transformers import CLIPModel, CLIPProcessor  # noqa: F401  (module-level import used)
    _, val_loader, _ = create_dataloaders(
        dataset_name="flickr30k", data_dir=".", batch_size=batch_size,
        max_samples=max_samples)
    model = CLIPModel.from_pretrained(PRISTINE, local_files_only=True).to(DEVICE)
    proc = CLIPProcessor.from_pretrained(PRISTINE, local_files_only=True)
    model.eval()
    first = next(iter(val_loader))
    ranks = layer_effective_ranks(model, first, proc)
    out = {"experiment": "strict_frozen", "n_trainable_params": 0,
           "max_samples": max_samples, "batch_size": batch_size,
           "effective_rank_final": ranks,
           "backbone_delta": backbone_deltas(model)}
    os.makedirs("%s/frozen" % OUT_DIR, exist_ok=True)
    with open("%s/frozen/results.json" % OUT_DIR, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print("[frozen] vis_L0=%.4f txt_L0=%.4f  vision_nonzero_tensors=%s"
          % (ranks.get("vis_L0", -1), ranks.get("txt_L0", -1),
             out["backbone_delta"].get("vision", {}).get("nonzero_tensors")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", nargs="*", default=list(CONFIGS))
    ap.add_argument("--seeds", nargs="*", type=int,
                    default=[42, 123, 456, 789, 1024])
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--max-samples", type=int, default=5000)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--skip-frozen", action="store_true")
    a = ap.parse_args()
    global OUT_DIR
    if a.smoke:
        a.epochs, a.max_samples, a.seeds = 1, 512, [42]
        # Keep smoke artefacts out of the full-protocol tree: otherwise the
        # "already done" skip check silently accepts a 1-epoch run as finished.
        OUT_DIR = "outputs/strict_freeze_smoke"

    print("device=%s out=%s epochs=%d max_samples=%d batch=%d tags=%s seeds=%s"
          % (DEVICE, OUT_DIR, a.epochs, a.max_samples, a.batch_size, a.tags, a.seeds))
    t0 = time.time()
    if not a.skip_frozen:
        run_frozen(a.max_samples, a.batch_size)
    for tag in a.tags:
        for seed in a.seeds:
            path = "%s/%s/seed%d/results.json" % (OUT_DIR, tag, seed)
            if os.path.exists(path) and not a.smoke:
                print("[skip] %s seed=%d already done" % (tag, seed))
                continue
            run_one(tag, seed, a.epochs, a.max_samples, a.batch_size)
    print("total %.1f min" % ((time.time() - t0) / 60.0))


if __name__ == "__main__":
    main()
