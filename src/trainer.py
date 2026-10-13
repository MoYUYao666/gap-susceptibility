"""
Trainer — LoRA fine-tuning of CLIP + dynamic monitoring of the modality gap

Core features:
1. Load CLIP + inject LoRA
2. Contrastive training loop (image-text retrieval)
3. Periodically compute/record gap
4. Missing-modality simulation
5. Logging + checkpoint saves
"""

import os
import json
import time
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict
from tqdm import tqdm
import numpy as np

from .config import ExperimentConfig, LoRAConfig, GapConfig, TrainConfig
from .lora import (
    apply_lora_to_model, get_lora_params, get_null_space_loss,
    compute_gap_direction, apply_gap_init_to_layers,
)
from .peft_methods import (
    apply_adapter_to_model, apply_prefix_to_model, get_peft_params,
    count_peft_parameters,
)
from .gap_metrics import GapTracker, GapMetrics
from .missing_modality import MissingModalitySimulator


class GapAwareTrainer:
    """
    Gap-aware trainer

    Usage:
        trainer = GapAwareTrainer(config)
        results = trainer.train(train_loader, val_loader)
    """

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.train_cfg = config.train
        self.lora_cfg = config.lora
        self.gap_cfg = config.gap
        self.peft_method = config.peft_method
        self.adapter_cfg = config.adapter
        self.prefix_cfg = config.prefix

        self.device = self.train_cfg.device
        self.save_dir = self.train_cfg.save_dir
        os.makedirs(self.save_dir, exist_ok=True)

        # Components (lazy initialization)
        self.model = None
        self.processor = None
        self.lora_layers = {}
        self.adapter_layers = {}
        self.prefix_layers = {}
        self.gap_tracker = GapTracker(
            sample_size=self.gap_cfg.sample_size,
            device=self.device,
        )

        # DG* trajectory tracker (for theory paper V1 — Gap Susceptibility)
        from .dg_star_tracker import DGStarTracker
        self.dg_star_tracker = DGStarTracker(
            sample_size=self.gap_cfg.sample_size,
            device=self.device,
        )
        self._record_dg_star = False  # enable via config or explicit call

        self.missing_sim = MissingModalitySimulator.identity()

        # Gradient collection (Phase 4B — gradient alignment analysis)
        self.gradient_snapshots: List[Dict] = []  # stores vis/txt gradient snapshots
        self._collect_gradients = False

        # Training state
        self.current_epoch = 0
        self.global_step = 0
        self.best_val_loss = float('inf')

        # Logs
        self.train_losses = []
        self.val_losses = []
        self.task_metrics = []  # downstream task performance

    # ============================================================
    # Model initialization
    # ============================================================

    def setup_model(self):
        """Load the CLIP model and inject the PEFT method (LoRA / Adapter / Prefix)"""
        from transformers import CLIPModel, CLIPProcessor

        print(f"\n{'='*60}")
        print(f"🚀 Loading CLIP model: {self.train_cfg.clip_model}")
        print(f"   PEFT method: {self.peft_method}")
        print(f"{'='*60}")

        # Load model (offline mode: HF is blocked on domestic networks)
        self.model = CLIPModel.from_pretrained(
            self.train_cfg.clip_model
        )
        self.processor = CLIPProcessor.from_pretrained(
            self.train_cfg.clip_model
        )

        # Count original parameters
        total_params = sum(p.numel() for p in self.model.parameters())
        print(f"📊 Original parameter count: {total_params:,}")

        # ---- Dispatch different injection logic based on peft_method ----
        if self.peft_method == "lora":
            self._setup_lora(total_params)
        elif self.peft_method == "adapter":
            self._setup_adapter(total_params)
        elif self.peft_method == "prefix":
            self._setup_prefix(total_params)
        elif self.peft_method in ("full_ft", "frozen"):
            self._setup_baseline(total_params)
        else:
            raise ValueError(f"Unknown PEFT method: {self.peft_method}")

        # Move to device
        self.model = self.model.to(self.device)
        self.model.train()

        # Print efficiency information
        params_info = count_peft_parameters(self.model, self.peft_method)
        print(f"📊 Trainable parameters: {params_info['peft_trainable']:,} "
              f"({params_info['trainable_ratio']:.2f}%)")

        print(f"✅ Model ready (device: {self.device})")

    def _setup_lora(self, total_params: int):
        """LoRA injection logic (original logic)"""
        if self.lora_cfg is not None and self.lora_cfg.rank > 0:
            self.model, self.lora_layers, trainable = apply_lora_to_model(
                self.model,
                rank=self.lora_cfg.rank,
                alpha=self.lora_cfg.alpha,
                dropout=self.lora_cfg.dropout,
                target_modules=self.lora_cfg.target_modules,
                apply_to_vision=self.lora_cfg.apply_to_vision,
                apply_to_text=self.lora_cfg.apply_to_text,
                use_null_lora=self.lora_cfg.use_null_lora,
                use_gap_init=self.lora_cfg.use_gap_init,
            )
            print(f"📊 Trainable parameter ratio: {trainable/total_params*100:.2f}%")
        else:
            print("🔒 Frozen mode: no LoRA, all parameters frozen")
            for p in self.model.parameters():
                p.requires_grad = False

    def _setup_adapter(self, total_params: int):
        """Adapter injection logic"""
        if self.adapter_cfg is None:
            raise ValueError("peft_method='adapter' but no AdapterConfig provided")

        self.model, self.adapter_layers, trainable = apply_adapter_to_model(
            self.model,
            bottleneck_dim=self.adapter_cfg.bottleneck_dim,
            activation=self.adapter_cfg.activation,
            dropout=self.adapter_cfg.dropout,
            target_modules=self.adapter_cfg.target_modules,
            apply_to_vision=self.adapter_cfg.apply_to_vision,
            apply_to_text=self.adapter_cfg.apply_to_text,
        )
        print(f"📊 Trainable parameter ratio: {trainable/total_params*100:.2f}%")

    def _setup_prefix(self, total_params: int):
        """Prefix Tuning injection logic"""
        if self.prefix_cfg is None:
            raise ValueError("peft_method='prefix' but no PrefixConfig provided")

        self.model, self.prefix_layers, trainable = apply_prefix_to_model(
            self.model,
            prefix_length=self.prefix_cfg.prefix_length,
            apply_to_vision=self.prefix_cfg.apply_to_vision,
            apply_to_text=self.prefix_cfg.apply_to_text,
        )
        print(f"📊 Trainable parameter ratio: {trainable/total_params*100:.2f}%")

    def _setup_baseline(self, total_params: int):
        """Full fine-tuning or frozen"""
        if self.peft_method == "full_ft":
            print("⚠️ Full fine-tuning mode: all parameters trainable")
            for p in self.model.parameters():
                p.requires_grad = True
        else:
            print("🔒 Frozen mode: all parameters frozen")
            for p in self.model.parameters():
                p.requires_grad = False

    # ============================================================
    # Training loop
    # ============================================================

    def train(
        self,
        train_loader,
        val_loader,
        missing_sim: Optional[MissingModalitySimulator] = None,
    ) -> Dict:
        """
        Main training loop

        Args:
            train_loader: training data
            val_loader: validation data
            missing_sim: missing-modality simulator (None = no missing modality)

        Returns:
            Dictionary containing all training results
        """
        if self.model is None:
            self.setup_model()

        # ---- Gap-Init initialization (LoRA only, paper arXiv:2602.01522) ----
        if self.peft_method == "lora" and self.lora_cfg is not None and self.lora_cfg.use_gap_init:
            print("\n🎯 Computing modality Gap direction for LoRA initialization...")
            gap_dir = compute_gap_direction(
                self.model, train_loader,
                device=self.device, n_batches=10,
            )
            apply_gap_init_to_layers(self.lora_layers, gap_dir)
            print("✅ Gap-Init done\n")

        if missing_sim is None:
            missing_sim = MissingModalitySimulator.identity()
        self.missing_sim = missing_sim

        # ---- Optimizer (supports LoRA / Adapter / Prefix / full_ft) ----
        if self.peft_method in ("lora", "adapter", "prefix"):
            self._trainable_params = get_peft_params(self.model, self.peft_method)
        else:
            self._trainable_params = [p for p in self.model.parameters() if p.requires_grad]

        # No trainable parameters (e.g. baseline_frozen) → skip training
        if len(self._trainable_params) == 0:
            print("\n⚠️ No trainable parameters, skipping training, evaluating initial Gap only")
            init_metrics = self._compute_gap_metrics(val_loader, epoch=0, step=0)
            self.gap_tracker.record(init_metrics)
            self._print_gap_metrics(init_metrics)
            self._save_results()
            return self._collect_results()

        optimizer = AdamW(
            self._trainable_params,
            lr=self.train_cfg.learning_rate,
            weight_decay=self.train_cfg.weight_decay,
        )

        # ---- Learning rate scheduler ----
        total_steps = len(train_loader) * self.train_cfg.num_epochs
        if self.train_cfg.scheduler == "cosine":
            scheduler = CosineAnnealingLR(optimizer, T_max=total_steps)
        elif self.train_cfg.scheduler == "linear":
            scheduler = LinearLR(optimizer, start_factor=1.0, end_factor=0.1,
                                total_iters=total_steps)
        else:
            scheduler = None

        # ---- Initial Gap measurement (epoch 0) ----
        print("\n📏 Measuring initial modality gap (epoch 0)...")
        init_metrics = self._compute_gap_metrics(val_loader, epoch=0, step=0)
        self.gap_tracker.record(init_metrics)
        self._print_gap_metrics(init_metrics)

        # ---- Route E: DG-Guided Early Stopping ----
        if self.config.dg_es.enabled:
            self.enable_dg_early_stopping(self.config.dg_es.patience)
            print(f"🛑 DG-ES: patience={self.config.dg_es.patience}")

        # ---- Training loop ----
        print(f"\n{'='*60}")
        print(f"🏋️ Starting training — {self.train_cfg.num_epochs} epochs")
        print(f"   LoRA rank: {self.lora_cfg.rank if self.lora_cfg else 'full FT'}")
        print(f"   Missing mode: {self._missing_mode_str()}")
        print(f"{'='*60}\n")

        # ---- Route C: initialization enhancements ----
        self._init_route_c()

        for epoch in range(1, self.train_cfg.num_epochs + 1):
            self.current_epoch = epoch
            epoch_start = time.time()

            # ---- Route C: per-epoch callbacks ----
            self._apply_alpha_annealing(epoch)
            self._apply_rank_schedule(epoch)

            # Train one epoch
            train_loss = self._train_epoch(train_loader, optimizer, scheduler, epoch)
            self.train_losses.append(train_loss)

            # Validation
            val_loss = self._validate(val_loader)
            self.val_losses.append(val_loss)

            # Compute downstream task performance (Retrieval Recall@K)
            task_metrics = self._compute_retrieval_metrics(val_loader)
            self.task_metrics.append(task_metrics)

            # ---- Route E: DG-Guided Early Stopping ----
            if getattr(self, '_dg_es_enabled', False) and self._should_stop_early():
                print(f"\n🛑 DG-ES: DG rising consecutively, stopping training at epoch {epoch}")
                break

            # Periodically compute Gap
            if epoch % self.gap_cfg.compute_every_n_epochs == 0 or epoch == 1:
                gap_metrics = self._compute_gap_metrics(
                    val_loader, epoch=epoch, step=self.global_step
                )
                self.gap_tracker.record(gap_metrics)

                # Route C: update gap delta for Gap-Reg Loss
                if self.gap_tracker.history:
                    prev = self.gap_tracker.history[-2] if len(self.gap_tracker.history) >= 2 else self.gap_tracker.history[0]
                    cg_prev = prev.centroid_gap
                    cg_curr = gap_metrics.centroid_gap
                    self._current_gap_delta = cg_curr - cg_prev

                # Per-layer Gap
                if self.gap_cfg.compute_per_layer:
                    per_layer = self._compute_per_layer_gap(val_loader, epoch)
                    gap_metrics.per_layer = per_layer

                self._print_gap_metrics(gap_metrics)

                # Record DG* every epoch (for theory ODE fitting V1)
                if self._record_dg_star:
                    dg_star_record = self._compute_dg_star_record(val_loader, epoch)
                    self.dg_star_tracker.record(dg_star_record)

            epoch_time = time.time() - epoch_start

            # Logging
            print(f"Epoch {epoch:3d}/{self.train_cfg.num_epochs} | "
                  f"Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
                  f"R@1: {task_metrics.get('R@1', 0):.3f} | "
                  f"Time: {epoch_time:.1f}s")

            # Save best model
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self._save_checkpoint(epoch, is_best=True)

        # ---- Final save ----
        self._save_results()
        self._save_checkpoint(self.train_cfg.num_epochs, is_best=False)

        return self._collect_results()

    def _train_epoch(self, loader, optimizer, scheduler, epoch: int = 0) -> float:
        """Train one epoch — contrastive learning loss (InfoNCE)"""
        self.model.train()
        total_loss = 0.0
        n_batches = 0
        self.current_epoch = epoch

        pbar = tqdm(loader, desc=f"Epoch {self.current_epoch}", leave=False)

        for batch in pbar:
            # Missing-modality simulation
            batch = self.missing_sim(batch)

            # Process inputs
            images = batch["image"].to(self.device)
            texts = batch["caption"]

            # Prefer pre-tokenized inputs (done in parallel by multiple workers), otherwise tokenize on the fly
            if "input_ids" in batch and "attention_mask" in batch:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
            else:
                text_inputs = self.processor(
                    text=texts, return_tensors="pt", padding=True, truncation=True,
                    max_length=getattr(self, 'max_seq_len', 77),
                )
                input_ids = text_inputs["input_ids"].to(self.device)
                attention_mask = text_inputs.get("attention_mask", torch.ones_like(input_ids)).to(self.device)

            # Apply text mask (part of the missing-modality simulation)
            batch_text = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "pixel_values": None,
            }
            batch_text = self.missing_sim(batch_text)
            input_ids = batch_text["input_ids"]
            attention_mask = batch_text["attention_mask"]

            # Forward pass
            outputs = self.model(
                pixel_values=images,
                input_ids=input_ids,
                attention_mask=attention_mask,
                return_loss=False,
            )

            image_embeds = outputs.image_embeds   # (B, D)
            text_embeds = outputs.text_embeds       # (B, D)

            # Normalize
            image_embeds = F.normalize(image_embeds, p=2, dim=-1)
            text_embeds = F.normalize(text_embeds, p=2, dim=-1)

            # InfoNCE contrastive loss
            logit_scale = self.model.logit_scale.exp()
            logits_per_image = logit_scale * image_embeds @ text_embeds.T   # (B, B)
            logits_per_text = logits_per_image.T

            batch_size = images.shape[0]
            labels = torch.arange(batch_size, device=self.device)

            loss_i = F.cross_entropy(logits_per_image, labels)
            loss_t = F.cross_entropy(logits_per_text, labels)
            loss = (loss_i + loss_t) / 2.0

            # Null-LoRA null-space constraint (LoRA only)
            if self.peft_method == "lora":
                null_loss = get_null_space_loss(self.lora_layers)
                loss = loss + null_loss

            # Route C1: Gap-Regularized Loss
            gap_penalty = self._compute_gap_penalty()
            if gap_penalty > 0:
                loss = loss + gap_penalty

            # Backward pass
            loss = loss / self.train_cfg.gradient_accumulation_steps
            loss.backward()

            # Gradient hook: **must be before zero_grad** (else p.grad is already cleared;
            # measured in tools/_p40_diag_inner_nan.py). Off by default → zero impact.
            if getattr(self, "_capture_train_grad", False):
                # **Must use model.parameters()**: `_trainable_params` is set only in train(), but
                # the caller (experiment A) runs its own loop for the ∇DG* backward pass and never
                # calls train() → it is None → iterates an empty list → no gradient (see tools/_p43).
                # **Keep the None placeholder**: it pairs 1:1 with
                # [p for p in self.model.parameters() if p.requires_grad]
                self._last_train_grad = [
                    (p.grad.detach().clone() if p.grad is not None else None)
                    for p in self.model.parameters() if p.requires_grad
                ]

            if (n_batches + 1) % self.train_cfg.gradient_accumulation_steps == 0:
                torch.nn.utils.clip_grad_norm_(self._trainable_params, max_norm=1.0)
                optimizer.step()
                if scheduler:
                    scheduler.step()
                optimizer.zero_grad()

                # Gradient snapshot collection (Phase 4B)
                self._collect_gradient_snapshot()

            total_loss += loss.item()
            n_batches += 1
            self.global_step += 1

            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        return total_loss / max(n_batches, 1) * self.train_cfg.gradient_accumulation_steps

    # ============================================================
    # Gradient collection (Phase 4B — gradient alignment analysis)
    # ============================================================

    def enable_gradient_collection(self, collect_every_n_steps: int = 50):
        """
        Enable gradient snapshot collection, used for Phase 4B gradient alignment analysis.

        After each optimization step, collect the gradients of the vision and text encoders
        and compute the cosine similarity between them to detect conflicts.

        Args:
            collect_every_n_steps: collect gradients every this many steps
        """
        self._collect_gradients = True
        self._grad_collect_interval = collect_every_n_steps

    def _collect_gradient_snapshot(self):
        """Collect the gradient snapshot of the current step"""
        if not self._collect_gradients:
            return
        if self.global_step % self._grad_collect_interval != 0:
            return

        snapshot = {"step": self.global_step, "epoch": self.current_epoch}

        # Collect vision encoder gradients
        vis_grads = []
        for name, param in self.model.named_parameters():
            if param.grad is None:
                continue
            if "vision_model" in name and param.requires_grad:
                vis_grads.append(param.grad.detach().flatten())
            elif "text_model" in name and param.requires_grad:
                # text is handled uniformly below
                pass

        # Collect text encoder gradients
        txt_grads = []
        for name, param in self.model.named_parameters():
            if param.grad is None:
                continue
            if "text_model" in name and param.requires_grad:
                txt_grads.append(param.grad.detach().flatten())

        if vis_grads and txt_grads:
            vis_flat = torch.cat(vis_grads)
            txt_flat = torch.cat(txt_grads)

            snapshot["vis_grad_norm"] = vis_flat.norm().item()
            snapshot["txt_grad_norm"] = txt_flat.norm().item()
            snapshot["grad_cosine"] = F.cosine_similarity(
                vis_flat.unsqueeze(0), txt_flat.unsqueeze(0)
            ).item()
            snapshot["grad_conflict"] = snapshot["grad_cosine"] < 0

            self.gradient_snapshots.append(snapshot)

    def get_gradient_snapshots(self) -> List[Dict]:
        """Return all gradient snapshots"""
        return self.gradient_snapshots

    @torch.no_grad()
    def _validate(self, loader) -> float:
        """Validation — compute the contrastive loss"""
        self.model.eval()
        total_loss = 0.0
        n_batches = 0

        for batch in loader:
            images = batch["image"].to(self.device)
            texts = batch["caption"]

            if "input_ids" in batch and "attention_mask" in batch:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
            else:
                text_inputs = self.processor(
                    text=texts, return_tensors="pt", padding=True, truncation=True,
                    max_length=getattr(self, 'max_seq_len', 77),
                )
                input_ids = text_inputs["input_ids"].to(self.device)
                attention_mask = text_inputs.get("attention_mask", torch.ones_like(input_ids)).to(self.device)

            outputs = self.model(
                pixel_values=images,
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

            image_embeds = F.normalize(outputs.image_embeds, p=2, dim=-1)
            text_embeds = F.normalize(outputs.text_embeds, p=2, dim=-1)

            logit_scale = self.model.logit_scale.exp()
            logits = logit_scale * image_embeds @ text_embeds.T
            batch_size = images.shape[0]
            labels = torch.arange(batch_size, device=self.device)

            loss = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2.0
            total_loss += loss.item()
            n_batches += 1

        self.model.train()
        return total_loss / max(n_batches, 1)

    # ============================================================
    # Gap metrics
    # ============================================================

    @torch.no_grad()
    def _compute_gap_metrics(self, loader, epoch: int, step: int) -> GapMetrics:
        """Compute modality gap metrics"""
        self.model.eval()

        all_image_embeds = []
        all_text_embeds = []

        n_samples = 0
        max_samples = self.gap_cfg.sample_size

        for batch in loader:
            if n_samples >= max_samples:
                break

            images = batch["image"].to(self.device)
            texts = batch["caption"]

            if "input_ids" in batch and "attention_mask" in batch:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
            else:
                text_inputs = self.processor(
                    text=texts, return_tensors="pt", padding=True, truncation=True,
                    max_length=getattr(self, 'max_seq_len', 77),
                )
                input_ids = text_inputs["input_ids"].to(self.device)
                attention_mask = text_inputs.get("attention_mask", torch.ones_like(input_ids)).to(self.device)

            outputs = self.model(
                pixel_values=images,
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

            all_image_embeds.append(outputs.image_embeds.cpu())
            all_text_embeds.append(outputs.text_embeds.cpu())

            n_samples += images.shape[0]

        image_embeds = torch.cat(all_image_embeds, dim=0)[:max_samples]
        text_embeds = torch.cat(all_text_embeds, dim=0)[:max_samples]

        metrics = self.gap_tracker.compute(
            image_embeds.to(self.device),
            text_embeds.to(self.device),
            epoch=epoch,
            step=step,
        )

        self.model.train()
        return metrics

    def enable_dg_star_tracking(self):
        """Enable per-epoch DG* recording for theory paper V1 (Gap Susceptibility)."""
        self._record_dg_star = True

    @torch.no_grad()
    def _compute_dg_star_record(self, loader, epoch: int):
        """
        Compute DG* on validation data.
        Returns a DGStarRecord (from dg_star_tracker module).
        Reuses the embedding extraction logic from _compute_gap_metrics.
        """
        self.model.eval()

        all_image_embeds = []
        all_text_embeds = []

        n_samples = 0
        max_samples = self.gap_cfg.sample_size

        for batch in loader:
            if n_samples >= max_samples:
                break

            images = batch["image"].to(self.device)
            texts = batch["caption"]

            if "input_ids" in batch and "attention_mask" in batch:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
            else:
                text_inputs = self.processor(
                    text=texts, return_tensors="pt", padding=True, truncation=True,
                    max_length=getattr(self, 'max_seq_len', 77),
                )
                input_ids = text_inputs["input_ids"].to(self.device)
                attention_mask = text_inputs.get("attention_mask", torch.ones_like(input_ids)).to(self.device)

            outputs = self.model(
                pixel_values=images,
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

            all_image_embeds.append(outputs.image_embeds.cpu())
            all_text_embeds.append(outputs.text_embeds.cpu())

            n_samples += images.shape[0]

        image_embeds = torch.cat(all_image_embeds, dim=0)[:max_samples]
        text_embeds = torch.cat(all_text_embeds, dim=0)[:max_samples]

        record = self.dg_star_tracker.compute(
            image_embeds.to(self.device),
            text_embeds.to(self.device),
            epoch=epoch,
        )

        self.model.train()
        return record

    @torch.no_grad()
    def _compute_per_layer_gap(self, loader, epoch: int) -> Dict[str, GapMetrics]:
        """Compute the gap layer by layer — requires the model to export intermediate layer outputs"""
        # The CLIP model obtains the outputs of each layer via output_hidden_states=True
        self.model.eval()

        # Simplified here: only the final outputs of vision encoder and text encoder are computed
        # Deep per-layer analysis requires hooks or model changes, to be done in a later version
        per_layer = {}

        # Vision encoder: get the outputs of the last 3 transformer blocks
        # Implemented by registering hooks
        vision_outputs = {}
        text_outputs = {}

        def make_hook(name, storage):
            def hook(module, input, output):
                # output is usually a tuple of (hidden_states, ...)
                if isinstance(output, tuple):
                    storage[name] = output[0].detach()
                else:
                    storage[name] = output.detach()
            return hook

        hooks = []

        # Register hooks for the vision encoder (take the first and the last layer)
        if hasattr(self.model.vision_model, 'encoder') and hasattr(self.model.vision_model.encoder, 'layers'):
            layers = self.model.vision_model.encoder.layers
            for idx in [0, len(layers)//2, len(layers)-1]:
                name = f"vis_layer_{idx}"
                hooks.append(layers[idx].register_forward_hook(make_hook(name, vision_outputs)))

        if hasattr(self.model, 'text_model') and self.model.text_model is not None:
            if hasattr(self.model.text_model, 'encoder') and hasattr(self.model.text_model.encoder, 'layers'):
                layers = self.model.text_model.encoder.layers
                for idx in [0, len(layers)//2, len(layers)-1]:
                    name = f"txt_layer_{idx}"
                    hooks.append(layers[idx].register_forward_hook(make_hook(name, text_outputs)))

        # One forward pass
        for batch in loader:
            images = batch["image"].to(self.device)[:32]  # sample
            texts = batch["caption"][:32]

            if "input_ids" in batch and "attention_mask" in batch:
                input_ids = batch["input_ids"][:32].to(self.device)
                attention_mask = batch["attention_mask"][:32].to(self.device)
            else:
                text_inputs = self.processor(
                    text=texts, return_tensors="pt", padding=True, truncation=True,
                    max_length=getattr(self, 'max_seq_len', 77),
                )
                input_ids = text_inputs["input_ids"].to(self.device)
                attention_mask = text_inputs.get("attention_mask", torch.ones_like(input_ids)).to(self.device)
            self.model(
                pixel_values=images,
                input_ids=input_ids,
                attention_mask=attention_mask,
            )
            break

        # Remove hooks
        for h in hooks:
            h.remove()

        # Compute the gap of each layer (vision and text middle layers differ in dim, so skip)
        for vis_key in vision_outputs:
            layer_idx = vis_key.replace("vis_", "")
            txt_key = vis_key.replace("vis", "txt")
            if txt_key in text_outputs:
                vis_emb = vision_outputs[vis_key].mean(dim=1)
                txt_emb = text_outputs[txt_key].mean(dim=1)
                # Dimension match check: ViT hidden=768, Text hidden=512
                if vis_emb.shape[-1] != txt_emb.shape[-1]:
                    continue
                per_layer[f"layer_{layer_idx}"] = self.gap_tracker.compute(
                    vis_emb, txt_emb, epoch=epoch,
                )

        self.model.train()
        return per_layer

    # ============================================================
    # Downstream task evaluation
    # ============================================================

    @torch.no_grad()
    def _compute_retrieval_metrics(self, loader, k_values: List[int] = [1, 5, 10]) -> Dict[str, float]:
        """Compute image→text and text→image Recall@K"""
        self.model.eval()

        all_image_embeds = []
        all_text_embeds = []

        for batch in loader:
            images = batch["image"].to(self.device)
            texts = batch["caption"]

            if "input_ids" in batch and "attention_mask" in batch:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
            else:
                text_inputs = self.processor(
                    text=texts, return_tensors="pt", padding=True, truncation=True,
                    max_length=getattr(self, 'max_seq_len', 77),
                )
                input_ids = text_inputs["input_ids"].to(self.device)
                attention_mask = text_inputs.get("attention_mask", torch.ones_like(input_ids)).to(self.device)

            outputs = self.model(
                pixel_values=images,
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

            all_image_embeds.append(F.normalize(outputs.image_embeds, p=2, dim=-1).cpu())
            all_text_embeds.append(F.normalize(outputs.text_embeds, p=2, dim=-1).cpu())

        image_embeds = torch.cat(all_image_embeds, dim=0)
        text_embeds = torch.cat(all_text_embeds, dim=0)

        # Similarity matrix
        sim_matrix = image_embeds @ text_embeds.T  # (N, N)

        metrics = {}
        for k in k_values:
            # Image → Text
            _, indices_i2t = sim_matrix.topk(k, dim=1)
            correct_i2t = (indices_i2t == torch.arange(len(sim_matrix)).unsqueeze(1)).any(dim=1)
            metrics[f"R@{k}_i2t"] = correct_i2t.float().mean().item()

            # Text → Image
            _, indices_t2i = sim_matrix.T.topk(k, dim=1)
            correct_t2i = (indices_t2i == torch.arange(len(sim_matrix)).unsqueeze(1)).any(dim=1)
            metrics[f"R@{k}_t2i"] = correct_t2i.float().mean().item()

            # Average
            metrics[f"R@{k}"] = (metrics[f"R@{k}_i2t"] + metrics[f"R@{k}_t2i"]) / 2.0

        self.model.train()
        return metrics

    # ============================================================
    # Save & load
    # ============================================================

    # ============================================================
    # Route C: enhanced training strategies
    # ============================================================

    def _init_route_c(self):
        """Initialize Route C enhancements"""
        self._rank_schedule_applied = set()
        self._current_gap_delta = None  # used for Gap-Reg Loss

    def _apply_alpha_annealing(self, epoch: int):
        """α Annealing (Route C4): per-epoch exponential decay"""
        cfg = self.config.alpha_schedule
        if not cfg.enabled or self.peft_method != "lora":
            return
        new_alpha = cfg.alpha_max * math.exp(-cfg.decay * (epoch - 1))
        new_alpha = max(new_alpha, cfg.alpha_min)
        for layer in self.lora_layers.values():
            layer.scaling = new_alpha / max(layer.rank, 1)
        if epoch == 1:
            print(f"   🔥 α Annealing: α_max={cfg.alpha_max}, α_min={cfg.alpha_min}, decay={cfg.decay}")

    def _apply_rank_schedule(self, epoch: int):
        """Dynamic Rank Scheduler (Route C2): reduce rank every epoch"""
        cfg = self.config.rank_schedule
        if not cfg.enabled or self.peft_method != "lora":
            return
        for trigger_epoch, new_rank in cfg.schedule:
            if epoch == trigger_epoch and new_rank not in self._rank_schedule_applied:
                self._rank_schedule_applied.add(new_rank)
                print(f"   📉 Rank Schedule: epoch {epoch} → rank {new_rank}")

    def enable_dg_early_stopping(self, patience: int = 2):
        """Enable DG-Guided Early Stopping (Route E)"""
        self._dg_es_enabled = True
        self._dg_es_patience = patience
        self._dg_consecutive_rises = 0
        self._dg_prev = None

    def _should_stop_early(self) -> bool:
        """Check whether DG has been rising consecutively"""
        if not self.gap_tracker.history:
            return False
        # Take the latest DG from gap_tracker
        latest = self.gap_tracker.history[-1]
        if not hasattr(latest, 'distribution_gap'):
            return False
        dg = latest.distribution_gap
        if self._dg_prev is not None and dg > self._dg_prev:
            self._dg_consecutive_rises += 1
        elif self._dg_prev is not None:
            self._dg_consecutive_rises = 0
        self._dg_prev = dg
        return self._dg_consecutive_rises >= self._dg_es_patience

    def _compute_gap_penalty(self) -> float:
        """Compute the gap regularization penalty term (Route C1)"""
        cfg = self.config.gap_reg
        if not cfg.enabled or self._current_gap_delta is None:
            return 0.0
        penalty = max(0, self._current_gap_delta)
        return cfg.lambda_reg * penalty

    def _save_checkpoint(self, epoch: int, is_best: bool = False):
        """Save checkpoint (LoRA weights only, without the frozen full model)"""
        checkpoint = {
            "epoch": epoch,
            "config_name": self.config.name,
            "lora_state_dict": {
                k: {"A": v.lora_A.data.clone(), "B": v.lora_B.data.clone()}
                for k, v in self.lora_layers.items()
            },
            "gap_history": [asdict(m) for m in self.gap_tracker.history],
            "train_losses": self.train_losses,
            "val_losses": self.val_losses,
            "task_metrics": self.task_metrics,
        }

        os.makedirs(self.save_dir, exist_ok=True)
        path = os.path.join(self.save_dir,
                           f"{'best' if is_best else 'last'}_checkpoint.pt")
        torch.save(checkpoint, path)

    def _save_results(self):
        """Save final results (JSON)"""
        results = self._collect_results()

        path = os.path.join(self.save_dir, "results.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Save DG* trajectory for theory paper V1
        if self._record_dg_star and len(self.dg_star_tracker.history) > 0:
            dg_star_path = os.path.join(self.save_dir, "dg_star_history.json")
            dg_star_dict = self.dg_star_tracker.get_history_dict()
            with open(dg_star_path, 'w', encoding='utf-8') as f:
                json.dump(dg_star_dict, f, indent=2)

        print(f"📁 Results saved: {path}")

        # Save gap history (for later analysis)
        gap_path = os.path.join(self.save_dir, "gap_history.json")
        gap_dict = self.gap_tracker.get_history_dict()
        with open(gap_path, 'w', encoding='utf-8') as f:
            json.dump(gap_dict, f, indent=2)

    def _collect_results(self) -> Dict:
        """Collect training results"""
        return {
            "experiment": self.config.name,
            "lora_rank": self.lora_cfg.rank if self.lora_cfg else None,
            "final_train_loss": self.train_losses[-1] if self.train_losses else None,
            "final_val_loss": self.val_losses[-1] if self.val_losses else None,
            "best_val_loss": self.best_val_loss,
            "final_task_metrics": self.task_metrics[-1] if self.task_metrics else None,
            "initial_gap": asdict(self.gap_tracker.history[0]) if self.gap_tracker.history else None,
            "final_gap": asdict(self.gap_tracker.history[-1]) if len(self.gap_tracker.history) > 1 else None,
            "n_trainable_params": sum(
                p.numel() for p in self.model.parameters() if p.requires_grad
            ),
        }

    # ============================================================
    # Helpers
    # ============================================================

    def _print_gap_metrics(self, metrics: GapMetrics):
        """Print gap metrics"""
        print(f"  📏 Gap — Centroid: {metrics.centroid_gap:.4f} | "
              f"Dist(W₂): {metrics.distribution_gap:.4f} | "
              f"Separation: {metrics.cosine_separation:.3f} | "
              f"Cos⁺: {metrics.mean_cosine_pos:.3f}")

    def _missing_mode_str(self) -> str:
        if self.missing_sim is None:
            return "no missing"
        parts = []
        if self.missing_sim.complete_missing:
            parts.append(f"complete missing({self.missing_sim.complete_missing})")
        if self.missing_sim.image_drop_ratio > 0:
            parts.append(f"image drop {self.missing_sim.image_drop_ratio:.0%}")
        if self.missing_sim.text_mask_ratio > 0:
            parts.append(f"text mask {self.missing_sim.text_mask_ratio:.0%}")
        return ", ".join(parts) if parts else "no missing"
