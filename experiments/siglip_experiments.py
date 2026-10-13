"""
SigLIP cross-validation experiments — Phase 2
=============================
Verify that the core findings generalize across training paradigms (CLIP contrastive loss → SigLIP sigmoid loss)

Experiment configurations (8):
  S1: SigLIP frozen — initial Gap measurement
  S2: SigLIP full_ft — full fine-tuning catastrophe verification
  S3: SigLIP LoRA rank sweep (rank=4, 8, 16)
  S4: SigLIP LoRA position (text_only, both)
  S5: SigLIP Adapter text_only — new: cross-PEFT verification

Story line: SigLIP uses sigmoid loss for pairwise similarity, fundamentally
different from CLIP InfoNCE. If text_only also holds, the finding does not depend on the training objective.

Usage:
    python siglip_experiments.py --data_dir ./data --max_samples 20000 --epochs 10
"""

import os, sys, json, time, argparse
os.environ["HF_HUB_OFFLINE"] = "1"
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
# src/ must also be on the path: run_one_siglip internally does `from lora import apply_lora_to_model`
# (lora.py lives in src/); with only the repo root on the path that import raises ModuleNotFoundError.
sys.path.insert(0, os.path.join(_ROOT, "src"))

import torch
import torch.nn.functional as F
import numpy as np

from src.config import ExperimentConfig, LoRAConfig, AdapterConfig, TrainConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders


# ============================================================
# Experiment definitions
# ============================================================

SIGLIP_MODEL = "./models/siglip-base-patch16-224"
SIGLIP_IMAGE_SIZE = 224

SIGLIP_EXPERIMENTS = [
    # S1: frozen baseline
    ("s1_siglip_frozen", "frozen", None, None),

    # S3: LoRA rank sweep
    ("s3_siglip_lora_r4", "lora",
     LoRAConfig(rank=4, alpha=8, apply_to_vision=True, apply_to_text=True), None),
    ("s3_siglip_lora_r8", "lora",
     LoRAConfig(rank=8, alpha=16, apply_to_vision=True, apply_to_text=True), None),
    ("s3_siglip_lora_r16", "lora",
     LoRAConfig(rank=16, alpha=32, apply_to_vision=True, apply_to_text=True), None),

    # S4: LoRA position
    ("s4_siglip_lora_text_only", "lora",
     LoRAConfig(rank=8, alpha=16, apply_to_vision=False, apply_to_text=True), None),
    ("s4_siglip_lora_both", "lora",
     LoRAConfig(rank=8, alpha=16, apply_to_vision=True, apply_to_text=True), None),

    # S5: Adapter text_only (cross-PEFT verification)
    ("s5_siglip_adapter_text_only", "adapter", None,
     AdapterConfig(bottleneck_dim=16, apply_to_vision=False, apply_to_text=True)),

    # S6: vision_only (completes the three-arm position map; the CLIP side already has text_only/both/vision_only)
    ("s6_siglip_lora_vision_only", "lora",
     LoRAConfig(rank=8, alpha=16, apply_to_vision=True, apply_to_text=False), None),

    # S7: rank4 + text_only (for the cross-backbone rank sweep; alpha = rank×2, same convention as CLIP)
    # ⚠ the existing s3_siglip_lora_r4 is at the **both position** and was run under the legacy convention, so it **cannot replace** this config.
    ("s7_siglip_lora_r4_text_only", "lora",
     LoRAConfig(rank=4, alpha=8, apply_to_vision=False, apply_to_text=True), None),

    # S8: rank4 + both (for the cross-backbone rank sweep)
    ("s7_siglip_lora_r4_both", "lora",
     LoRAConfig(rank=4, alpha=8, apply_to_vision=True, apply_to_text=True), None),
]


# ============================================================
# SigLIP model loading
# ============================================================

def load_siglip_model(model_name: str = SIGLIP_MODEL):
    """
    Load the SigLIP model

    Key differences between SigLIP and CLIP:
    - SigLIP: sigmoid loss for pairwise similarity
    - CLIP: InfoNCE contrastive loss
    - SigLIP outputs logit_scale and logit_bias
    - Embedding interface compatible: image_embeds / text_embeds (needs verification)
    """
    from transformers import AutoModel, AutoProcessor

    print(f"\n📦 Loading SigLIP model: {model_name}")

    model = AutoModel.from_pretrained(model_name, local_files_only=True)
    processor = AutoProcessor.from_pretrained(model_name, local_files_only=True)

    # Check the output interface
    total_params = sum(p.numel() for p in model.parameters())
    print(f"📊 SigLIP parameter count: {total_params:,}")

    # SigLIP uses VisionTransformer + T5Encoder, output in pooled_* or last_hidden_state
    # Verify how embeddings are extracted
    print(f"   Architecture type: {type(model).__name__}")

    return model, processor


class SigLIPWrapper(torch.nn.Module):
    """
    SigLIP model wrapper — unifies the embedding extraction interface to CLIP style

    SigLIPModel outputs:
    - vision_model_output: BaseModelOutput with last_hidden_state, pooler_output
    - text_model_output: BaseModelOutput with last_hidden_state, pooler_output
    """

    def __init__(self, siglip_model):
        super().__init__()
        self.siglip = siglip_model

    @property
    def logit_scale(self):
        return self.siglip.logit_scale

    @property
    def logit_bias(self):
        return self.siglip.logit_bias

    @property
    def vision_model(self):
        return self.siglip.vision_model

    @property
    def text_model(self):
        return self.siglip.text_model

    def get_image_features(self, pixel_values):
        """Extract image features (compatible with the CLIP interface)"""
        vision_outputs = self.siglip.vision_model(pixel_values=pixel_values)
        # pooler_output: (B, hidden_dim)
        if hasattr(vision_outputs, 'pooler_output') and vision_outputs.pooler_output is not None:
            return vision_outputs.pooler_output
        # fallback: mean of last_hidden_state
        return vision_outputs.last_hidden_state.mean(dim=1)

    def get_text_features(self, input_ids, attention_mask=None):
        """Extract text features (compatible with the CLIP interface)"""
        text_outputs = self.siglip.text_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        # pooler_output: (B, hidden_dim)
        if hasattr(text_outputs, 'pooler_output') and text_outputs.pooler_output is not None:
            return text_outputs.pooler_output
        # fallback: EOS token or mean pooling
        if attention_mask is not None:
            # Take the EOS token (the last non-padding position)
            eos_idx = attention_mask.sum(dim=1) - 1
            return text_outputs.last_hidden_state[
                torch.arange(text_outputs.last_hidden_state.shape[0]), eos_idx
            ]
        return text_outputs.last_hidden_state.mean(dim=1)

    def forward(self, pixel_values=None, input_ids=None, attention_mask=None, **kwargs):
        """
        Unify forward to CLIP style: return image_embeds and text_embeds
        """
        outputs = self.siglip(
            pixel_values=pixel_values,
            input_ids=input_ids,
            attention_mask=attention_mask,
            **kwargs,
        )

        # SigLIP outputs loss, logits_per_image, logits_per_text, etc.
        image_embeds = outputs.image_embeds if hasattr(outputs, 'image_embeds') else None
        text_embeds = outputs.text_embeds if hasattr(outputs, 'text_embeds') else None

        if image_embeds is None:
            image_embeds = self.get_image_features(pixel_values)
        if text_embeds is None:
            text_embeds = self.get_text_features(input_ids, attention_mask)

        # Return a simple object to match CLIP's output format
        return SigLIPOutput(image_embeds, text_embeds, outputs)


class SigLIPOutput:
    """Simulate the CLIPOutput interface"""
    def __init__(self, image_embeds, text_embeds, raw_outputs):
        self.image_embeds = image_embeds
        self.text_embeds = text_embeds
        self.raw_outputs = raw_outputs


# ============================================================
# Run a single experiment
# ============================================================

def run_one_siglip(args, name, peft_method, lora_cfg, adapter_cfg, strict_freeze=False, seed=None):
    """Run a single SigLIP experiment

    strict_freeze: strictly freeze the base, training only the LoRA A/B matrices.
    Must be passed by the caller (no closure over main's locals — this function is at module level).

    seed: random seed for this run. The script never set one before, so all archived runs used the
    TrainConfig default 42 (the split has its own hardcoded manual_seed(42), the same for all runs).
    This sets torch/numpy/random seeds so a strict-freeze run is comparable to archived runs.
    """
    print(f"\n{'='*60}")
    print(f"🔬 SigLIP: {name}")
    print(f"   PEFT: {peft_method}")
    print(f"{'='*60}")

    # Explicit seeding (never set before; the data split hardcodes manual_seed(42) in dataset.py)
    if seed is not None:
        import random as _random
        import numpy as _np
        _random.seed(seed)
        _np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        print(f"🌱 seed = {seed}")

    config = ExperimentConfig(
        name=name,
        peft_method=peft_method,
        lora=lora_cfg if lora_cfg else LoRAConfig(rank=0),
        adapter=adapter_cfg,
        train=TrainConfig(
            dataset=args.dataset,
            clip_model=SIGLIP_MODEL,
            device="cuda" if torch.cuda.is_available() else "cpu",
            batch_size=args.batch_size,
            num_epochs=args.epochs if peft_method != "frozen" else 1,
            max_samples=args.max_samples,
            save_dir=f"{args.outputs_dir}/{name}",
            gradient_accumulation_steps=4 if peft_method == "full_ft" else 1,
            seed=seed if seed is not None else 42,
        ),
    )

    train_loader, val_loader, test_loader = create_dataloaders(
        dataset_name=args.dataset,
        data_dir=args.data_dir,
        batch_size=config.train.batch_size,
        max_samples=config.train.max_samples,
        pre_tokenize=False,  # SigLIP needs its own tokenizer, not CLIP's
    )

    # Load the SigLIP model (located locally in models/)
    siglip_model, siglip_processor = load_siglip_model(SIGLIP_MODEL)
    wrapped_model = SigLIPWrapper(siglip_model)

    # Create the trainer and monkey-patch setup_model
    trainer = GapAwareTrainer(config)

    original_setup = trainer.setup_model
    def siglip_setup():
        trainer.model = wrapped_model.to(trainer.device)
        trainer.processor = siglip_processor  # used for trainer tokenization

        total_params = sum(p.numel() for p in trainer.model.parameters())
        print(f"📊 SigLIP parameter count: {total_params:,}")

        if peft_method == "lora" and lora_cfg is not None and lora_cfg.rank > 0:
            from lora import apply_lora_to_model
            trainer.model, trainer.lora_layers, trainable = apply_lora_to_model(
                trainer.model,
                rank=lora_cfg.rank,
                alpha=lora_cfg.alpha,
                dropout=lora_cfg.dropout,
                target_modules=lora_cfg.target_modules,
                apply_to_vision=lora_cfg.apply_to_vision,
                apply_to_text=lora_cfg.apply_to_text,
            )
            print(f"📊 Trainable parameter ratio: {trainable/total_params*100:.2f}%")
            # [Strict freeze] src/lora.py's apply_lora_to_model never freezes the base, so the optimizer
            # sees the whole model. With --strict-freeze the base is frozen here, before optimizer
            # construction, and only the LoRA A/B matrices are unfrozen, exactly as
            # experiments/strict_freeze_control.py's strict_freeze() does.
            if strict_freeze:
                for p in trainer.model.parameters():
                    p.requires_grad = False
                strict_n = 0
                for w in trainer.lora_layers.values():
                    for p in (w.lora_A, w.lora_B):
                        p.requires_grad = True
                        strict_n += p.numel()
                n_vis_updated = 0  # count of trainable parameters on the vision side
                n_non_lora_trainable = 0  # still trainable after freezing but not a LoRA matrix param (should be 0)
                lora_param_ids = set()
                for w in trainer.lora_layers.values():
                    lora_param_ids.add(id(w.lora_A)); lora_param_ids.add(id(w.lora_B))
                for name, p in trainer.model.named_parameters():
                    if p.requires_grad:
                        if 'vision_model' in name:
                            n_vis_updated += p.numel()
                        if id(p) not in lora_param_ids:
                            n_non_lora_trainable += p.numel()
                print(f"🔒 Strict freeze: trainable {strict_n:,} "
                      f"({100.0*strict_n/total_params:.4f}% of {total_params:,}); "
                      f"vision-side trainable params = {n_vis_updated:,}"
                      f" (apply_to_vision={lora_cfg.apply_to_vision})")
                # Correct invariant: the trainable params come **only** from the LoRA A/B matrices.
                # Note: with apply_to_vision=True the vision side **already has** LoRA params (the base
                # is still frozen), so one cannot assert "vision-side trainable = 0" — the earlier version
                # of the assertion was written that way and blocked the whole both arm before training.
                assert n_non_lora_trainable == 0, \
                    f"strict freeze failed: {n_non_lora_trainable:,} non-LoRA params are still trainable"
                assert strict_n < 2_000_000, \
                    f"strict freeze failed: trainable params {strict_n:,} (should be < 2e6)"
                if not lora_cfg.apply_to_vision:
                    assert n_vis_updated == 0, \
                        f"the text-only arm should have no vision-side trainable params, measured {n_vis_updated:,}"
                trainable = strict_n
        elif peft_method == "adapter" and adapter_cfg is not None:
            from peft_methods import apply_adapter_to_model
            trainer.model, trainer.adapter_layers, trainable = apply_adapter_to_model(
                trainer.model,
                bottleneck_dim=adapter_cfg.bottleneck_dim,
                activation=adapter_cfg.activation,
                apply_to_vision=adapter_cfg.apply_to_vision,
                apply_to_text=adapter_cfg.apply_to_text,
            )
        elif peft_method == "full_ft":
            print("⚠️ Full fine-tuning mode")
            for p in trainer.model.parameters():
                p.requires_grad = True
        else:
            print("🔒 Frozen mode")
            for p in trainer.model.parameters():
                p.requires_grad = False

        trainer.model = trainer.model.to(trainer.device)
        trainer.model.train()
        print(f"✅ SigLIP model ready (device: {trainer.device})")

    trainer.setup_model = siglip_setup
    trainer.max_seq_len = 64  # SigLIP max sequence length

    # If using gradient collection, enable it on the full_ft and lora text_only key experiments
    if args.collect_gradients and peft_method in ("lora", "full_ft"):
        trainer.enable_gradient_collection(collect_every_n_steps=50)

    result = trainer.train(train_loader, val_loader)

    test_metrics = trainer._compute_retrieval_metrics(test_loader)
    result["test_metrics"] = test_metrics

    # Save gradient snapshots
    if args.collect_gradients and trainer.gradient_snapshots:
        grad_path = f"{args.outputs_dir}/{name}/gradient_snapshots.json"
        os.makedirs(os.path.dirname(grad_path), exist_ok=True)
        with open(grad_path, 'w') as f:
            json.dump(trainer.gradient_snapshots, f, indent=2)

    # Save results
    save_path = f"{args.outputs_dir}/{name}/results.json"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


# ============================================================
# Main function
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default=".",
                       help="data root directory")
    parser.add_argument("--outputs_dir", type=str, default="./outputs/siglip")
    parser.add_argument("--dataset", type=str, default="flickr30k")
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--max_samples", type=int, default=20000)
    parser.add_argument("--skip_full_ft", action="store_true",
                       help="skip full fine-tuning (saves time/VRAM)")
    parser.add_argument("--collect_gradients", action="store_true",
                       help="enable gradient alignment analysis collection")
    parser.add_argument("--strict-freeze", action="store_true",
                       help="strictly freeze the base, training only the LoRA A/B matrices (same convention as strict_freeze_control.py); "
                            "this is the only way to make text-only vs both differ purely in 'adapter injection site'")
    parser.add_argument("--seed", type=int, default=None,
                       help="random seed; if omitted, the TrainConfig default 42 is used (consistent with archived runs)")
    parser.add_argument("--only", type=str, default=None,
                       help="only run experiments whose name matches this substring (comma-separated for several)")
    args = parser.parse_args()
    strict_freeze = args.strict_freeze

    # Check whether the SigLIP model is already cached
    from transformers.utils.hub import cached_file
    try:
        cached_file(SIGLIP_MODEL, "config.json")
        print(f"✅ SigLIP model already cached: {SIGLIP_MODEL}")
    except Exception:
        print(f"⚠️ SigLIP model not cached, will try to download: {SIGLIP_MODEL}")
        print("   If the network is restricted, download it in another environment first and copy it into models/")

    total_start = time.time()
    results = {}

    for name, peft_method, lora_cfg, adapter_cfg in SIGLIP_EXPERIMENTS:
        if args.skip_full_ft and "full_ft" in name:
            print(f"⏭ Skipping {name} (full fine-tuning)")
            continue
        if args.only and not any(s.strip() and s.strip() in name for s in args.only.split(",")):
            print(f"⏭ Skipping {name} (--only did not select it)")
            continue

        # Skip if already completed
        save_path = f"{args.outputs_dir}/{name}/results.json"
        if os.path.exists(save_path):
            print(f"⏭ Skipping {name} (already done)")
            with open(save_path, 'r') as f:
                results[name] = json.load(f)
            continue

        start = time.time()
        result = run_one_siglip(args, name, peft_method, lora_cfg, adapter_cfg, strict_freeze, args.seed)
        results[name] = result
        elapsed = time.time() - start

        r1 = result.get("test_metrics", {}).get("R@1", "N/A")
        cg_delta = None
        if result.get("initial_gap") and result.get("final_gap"):
            cg_delta = result["final_gap"]["centroid_gap"] - result["initial_gap"]["centroid_gap"]
        cg_str = f"{cg_delta:+.4f}" if cg_delta is not None else "N/A"
        print(f"   ✅ {name}: R@1={r1}, CG Δ={cg_str}, time={elapsed:.0f}s")

    total = time.time() - total_start
    print(f"\n🎉 SigLIP experiments complete! Total elapsed: {total/60:.0f} minutes")

    # ---- Summary verification ----
    print("\n" + "=" * 60)
    print("📊 SigLIP core finding verification")
    print("=" * 60)

    for name, result in results.items():
        cg_init = result.get("initial_gap", {}).get("centroid_gap")
        cg_final = result.get("final_gap", {}).get("centroid_gap")
        if cg_init and cg_final:
            delta = cg_final - cg_init
            r1 = result.get("test_metrics", {}).get("R@1", "N/A")
            # Do not use "gap down = good" as a success criterion: this project's core finding is that
            # "lower gap ≠ better retrieval" (on OpenCLIP the both arm has a bigger gap yet stronger retrieval).
            arrow = "↓" if delta < 0 else ("=" if delta == 0 else "↑")
            print(f"   [gap {arrow}] {name:<40s} CG Δ={delta:+.4f}  R@1={r1}  (run completed)")

    # Save summary
    summary = {}
    for name, result in results.items():
        summary[name] = {
            "initial_cg": result.get("initial_gap", {}).get("centroid_gap"),
            "final_cg": result.get("final_gap", {}).get("centroid_gap"),
            "R@1": result.get("test_metrics", {}).get("R@1"),
            "train_loss": result.get("final_train_loss"),
        }

    os.makedirs(args.outputs_dir, exist_ok=True)
    with open(f"{args.outputs_dir}/siglip_summary.json", 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n📁 Summary: {args.outputs_dir}/siglip_summary.json")


if __name__ == "__main__":
    main()
