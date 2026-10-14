"""
训练器 — LoRA微调CLIP + 模态差距动态监测

核心功能:
1. 加载CLIP模型 + 注入LoRA层
2. 对比学习训练循环（图像-文本检索任务）
3. 定期计算并记录模态差距指标
4. 缺失模态模拟实验
5. 日志记录 + 中间检查点保存
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
    Gap感知训练器

    用法:
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

        # 组件（延迟初始化）
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

        # 梯度收集（Phase 4B — 梯度对齐分析）
        self.gradient_snapshots: List[Dict] = []  # 存储 vis/txt 梯度快照
        self._collect_gradients = False

        # 训练状态
        self.current_epoch = 0
        self.global_step = 0
        self.best_val_loss = float('inf')

        # 日志
        self.train_losses = []
        self.val_losses = []
        self.task_metrics = []  # 下游任务性能

    # ============================================================
    # 模型初始化
    # ============================================================

    def setup_model(self):
        """加载CLIP模型并注入PEFT方法（LoRA / Adapter / Prefix）"""
        from transformers import CLIPModel, CLIPProcessor

        print(f"\n{'='*60}")
        print(f"🚀 加载 CLIP 模型: {self.train_cfg.clip_model}")
        print(f"   PEFT 方法: {self.peft_method}")
        print(f"{'='*60}")

        # 加载模型 (离线模式: 国内网络HF被墙)
        self.model = CLIPModel.from_pretrained(
            self.train_cfg.clip_model
        )
        self.processor = CLIPProcessor.from_pretrained(
            self.train_cfg.clip_model
        )

        # 统计原始参数
        total_params = sum(p.numel() for p in self.model.parameters())
        print(f"📊 原始参数量: {total_params:,}")

        # ---- 根据 peft_method 调度不同的注入逻辑 ----
        if self.peft_method == "lora":
            self._setup_lora(total_params)
        elif self.peft_method == "adapter":
            self._setup_adapter(total_params)
        elif self.peft_method == "prefix":
            self._setup_prefix(total_params)
        elif self.peft_method in ("full_ft", "frozen"):
            self._setup_baseline(total_params)
        else:
            raise ValueError(f"未知 PEFT 方法: {self.peft_method}")

        # 移至设备
        self.model = self.model.to(self.device)
        self.model.train()

        # 打印效率信息
        params_info = count_peft_parameters(self.model, self.peft_method)
        print(f"📊 可训练参数: {params_info['peft_trainable']:,} "
              f"({params_info['trainable_ratio']:.2f}%)")

        print(f"✅ 模型准备完成 (设备: {self.device})")

    def _setup_lora(self, total_params: int):
        """LoRA 注入逻辑（原有逻辑）"""
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
            print(f"📊 可训练参数占比: {trainable/total_params*100:.2f}%")
        else:
            print("🔒 冻结模式: 无LoRA, 所有参数冻结")
            for p in self.model.parameters():
                p.requires_grad = False

    def _setup_adapter(self, total_params: int):
        """Adapter 注入逻辑"""
        if self.adapter_cfg is None:
            raise ValueError("peft_method='adapter' 但未提供 AdapterConfig")

        self.model, self.adapter_layers, trainable = apply_adapter_to_model(
            self.model,
            bottleneck_dim=self.adapter_cfg.bottleneck_dim,
            activation=self.adapter_cfg.activation,
            dropout=self.adapter_cfg.dropout,
            target_modules=self.adapter_cfg.target_modules,
            apply_to_vision=self.adapter_cfg.apply_to_vision,
            apply_to_text=self.adapter_cfg.apply_to_text,
        )
        print(f"📊 可训练参数占比: {trainable/total_params*100:.2f}%")

    def _setup_prefix(self, total_params: int):
        """Prefix Tuning 注入逻辑"""
        if self.prefix_cfg is None:
            raise ValueError("peft_method='prefix' 但未提供 PrefixConfig")

        self.model, self.prefix_layers, trainable = apply_prefix_to_model(
            self.model,
            prefix_length=self.prefix_cfg.prefix_length,
            apply_to_vision=self.prefix_cfg.apply_to_vision,
            apply_to_text=self.prefix_cfg.apply_to_text,
        )
        print(f"📊 可训练参数占比: {trainable/total_params*100:.2f}%")

    def _setup_baseline(self, total_params: int):
        """全量微调 或 冻结"""
        if self.peft_method == "full_ft":
            print("⚠️ 全量微调模式: 所有参数可训练")
            for p in self.model.parameters():
                p.requires_grad = True
        else:
            print("🔒 冻结模式: 所有参数冻结")
            for p in self.model.parameters():
                p.requires_grad = False

    # ============================================================
    # 训练循环
    # ============================================================

    def train(
        self,
        train_loader,
        val_loader,
        missing_sim: Optional[MissingModalitySimulator] = None,
    ) -> Dict:
        """
        主训练循环

        Args:
            train_loader: 训练数据
            val_loader: 验证数据
            missing_sim: 缺失模态模拟器（None=无缺失）

        Returns:
            包含所有训练结果的字典
        """
        if self.model is None:
            self.setup_model()

        # ---- Gap-Init 初始化（仅 LoRA，论文 arXiv:2602.01522） ----
        if self.peft_method == "lora" and self.lora_cfg is not None and self.lora_cfg.use_gap_init:
            print("\n🎯 计算模态Gap方向用于 LoRA 初始化...")
            gap_dir = compute_gap_direction(
                self.model, train_loader,
                device=self.device, n_batches=10,
            )
            apply_gap_init_to_layers(self.lora_layers, gap_dir)
            print("✅ Gap-Init 完成\n")

        if missing_sim is None:
            missing_sim = MissingModalitySimulator.identity()
        self.missing_sim = missing_sim

        # ---- 优化器（支持 LoRA / Adapter / Prefix / full_ft） ----
        if self.peft_method in ("lora", "adapter", "prefix"):
            self._trainable_params = get_peft_params(self.model, self.peft_method)
        else:
            self._trainable_params = [p for p in self.model.parameters() if p.requires_grad]

        # 无可训练参数（如 baseline_frozen）→ 跳过训练
        if len(self._trainable_params) == 0:
            print("\n⚠️ 无可训练参数，跳过训练，仅评估初始Gap")
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

        # ---- 学习率调度器 ----
        total_steps = len(train_loader) * self.train_cfg.num_epochs
        if self.train_cfg.scheduler == "cosine":
            scheduler = CosineAnnealingLR(optimizer, T_max=total_steps)
        elif self.train_cfg.scheduler == "linear":
            scheduler = LinearLR(optimizer, start_factor=1.0, end_factor=0.1,
                                total_iters=total_steps)
        else:
            scheduler = None

        # ---- 初始Gap测量（epoch 0） ----
        print("\n📏 测量初始模态差距 (epoch 0)...")
        init_metrics = self._compute_gap_metrics(val_loader, epoch=0, step=0)
        self.gap_tracker.record(init_metrics)
        self._print_gap_metrics(init_metrics)

        # ---- Route E: DG-Guided Early Stopping ----
        if self.config.dg_es.enabled:
            self.enable_dg_early_stopping(self.config.dg_es.patience)
            print(f"🛑 DG-ES: patience={self.config.dg_es.patience}")

        # ---- 训练循环 ----
        print(f"\n{'='*60}")
        print(f"🏋️ 开始训练 — {self.train_cfg.num_epochs} epochs")
        print(f"   LoRA rank: {self.lora_cfg.rank if self.lora_cfg else 'full FT'}")
        print(f"   缺失模式: {self._missing_mode_str()}")
        print(f"{'='*60}\n")

        # ---- Route C: 初始化增强 ----
        self._init_route_c()

        for epoch in range(1, self.train_cfg.num_epochs + 1):
            self.current_epoch = epoch
            epoch_start = time.time()

            # ---- Route C: per-epoch 回调 ----
            self._apply_alpha_annealing(epoch)
            self._apply_rank_schedule(epoch)

            # 训练一个epoch
            train_loss = self._train_epoch(train_loader, optimizer, scheduler, epoch)
            self.train_losses.append(train_loss)

            # 验证
            val_loss = self._validate(val_loader)
            self.val_losses.append(val_loss)

            # 计算下游任务性能（Retrieval Recall@K）
            task_metrics = self._compute_retrieval_metrics(val_loader)
            self.task_metrics.append(task_metrics)

            # ---- Route E: DG-Guided Early Stopping ----
            if getattr(self, '_dg_es_enabled', False) and self._should_stop_early():
                print(f"\n🛑 DG-ES: DG 连续上升, epoch {epoch} 停止训练")
                break

            # 定期计算 Gap
            if epoch % self.gap_cfg.compute_every_n_epochs == 0 or epoch == 1:
                gap_metrics = self._compute_gap_metrics(
                    val_loader, epoch=epoch, step=self.global_step
                )
                self.gap_tracker.record(gap_metrics)

                # Route C: 更新 gap delta 用于 Gap-Reg Loss
                if self.gap_tracker.history:
                    prev = self.gap_tracker.history[-2] if len(self.gap_tracker.history) >= 2 else self.gap_tracker.history[0]
                    cg_prev = prev.centroid_gap
                    cg_curr = gap_metrics.centroid_gap
                    self._current_gap_delta = cg_curr - cg_prev

                # 逐层Gap
                if self.gap_cfg.compute_per_layer:
                    per_layer = self._compute_per_layer_gap(val_loader, epoch)
                    gap_metrics.per_layer = per_layer

                self._print_gap_metrics(gap_metrics)

                # Record DG* every epoch (for theory ODE fitting V1)
                if self._record_dg_star:
                    dg_star_record = self._compute_dg_star_record(val_loader, epoch)
                    self.dg_star_tracker.record(dg_star_record)

            epoch_time = time.time() - epoch_start

            # 日志
            print(f"Epoch {epoch:3d}/{self.train_cfg.num_epochs} | "
                  f"Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
                  f"R@1: {task_metrics.get('R@1', 0):.3f} | "
                  f"Time: {epoch_time:.1f}s")

            # 保存最佳模型
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self._save_checkpoint(epoch, is_best=True)

        # ---- 最终保存 ----
        self._save_results()
        self._save_checkpoint(self.train_cfg.num_epochs, is_best=False)

        return self._collect_results()

    def _train_epoch(self, loader, optimizer, scheduler, epoch: int = 0) -> float:
        """训练一个epoch — 对比学习损失 (InfoNCE)"""
        self.model.train()
        total_loss = 0.0
        n_batches = 0
        self.current_epoch = epoch

        pbar = tqdm(loader, desc=f"Epoch {self.current_epoch}", leave=False)

        for batch in pbar:
            # 缺失模态模拟
            batch = self.missing_sim(batch)

            # 处理输入
            images = batch["image"].to(self.device)
            texts = batch["caption"]

            # 优先用预 tokenize（多 worker 并行完成），否则实时 tokenize
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

            # 应用文本mask（缺失模态模拟的一部分）
            batch_text = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "pixel_values": None,
            }
            batch_text = self.missing_sim(batch_text)
            input_ids = batch_text["input_ids"]
            attention_mask = batch_text["attention_mask"]

            # 前向传播
            outputs = self.model(
                pixel_values=images,
                input_ids=input_ids,
                attention_mask=attention_mask,
                return_loss=False,
            )

            image_embeds = outputs.image_embeds   # (B, D)
            text_embeds = outputs.text_embeds       # (B, D)

            # 归一化
            image_embeds = F.normalize(image_embeds, p=2, dim=-1)
            text_embeds = F.normalize(text_embeds, p=2, dim=-1)

            # InfoNCE 对比损失
            logit_scale = self.model.logit_scale.exp()
            logits_per_image = logit_scale * image_embeds @ text_embeds.T   # (B, B)
            logits_per_text = logits_per_image.T

            batch_size = images.shape[0]
            labels = torch.arange(batch_size, device=self.device)

            loss_i = F.cross_entropy(logits_per_image, labels)
            loss_t = F.cross_entropy(logits_per_text, labels)
            loss = (loss_i + loss_t) / 2.0

            # Null-LoRA 零空间约束（仅 LoRA）
            if self.peft_method == "lora":
                null_loss = get_null_space_loss(self.lora_layers)
                loss = loss + null_loss

            # Route C1: Gap-Regularized Loss
            gap_penalty = self._compute_gap_penalty()
            if gap_penalty > 0:
                loss = loss + gap_penalty

            # 反向传播
            loss = loss / self.train_cfg.gradient_accumulation_steps
            loss.backward()

            # 梯度取值钩子：**必须在 zero_grad 之前**（否则 p.grad 已被清空，见
            # tools/_p40_diag_inner_nan.py 的实测）。默认关闭 → 对既有实验零影响。
            if getattr(self, "_capture_train_grad", False):
                # **必须用 model.parameters()**：`_trainable_params` 只在 train() 里设置，
                # 而调用方（实验 A）为插 ∇DG* 反向而自走循环、从未调用 train()
                # → 该属性为 None → 遍历空列表 → 取不到任何梯度（实测，见 tools/_p43）。
                # **保留 None 占位**：与 [p for p in model.parameters() if p.requires_grad]
                # 一一对应，便于与 ∇DG* 按位置配对（实测两者非零个数不同：398 vs 397）。
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

                # 梯度快照收集（Phase 4B）
                self._collect_gradient_snapshot()

            total_loss += loss.item()
            n_batches += 1
            self.global_step += 1

            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        return total_loss / max(n_batches, 1) * self.train_cfg.gradient_accumulation_steps

    # ============================================================
    # 梯度收集（Phase 4B — 梯度对齐分析）
    # ============================================================

    def enable_gradient_collection(self, collect_every_n_steps: int = 50):
        """
        启用梯度快照收集，用于 Phase 4B 梯度对齐分析。

        在每个优化步骤后，收集视觉和文本编码器的梯度，
        计算它们之间的余弦相似度以检测冲突。

        Args:
            collect_every_n_steps: 每隔多少步收集一次梯度
        """
        self._collect_gradients = True
        self._grad_collect_interval = collect_every_n_steps

    def _collect_gradient_snapshot(self):
        """收集当前步骤的梯度快照"""
        if not self._collect_gradients:
            return
        if self.global_step % self._grad_collect_interval != 0:
            return

        snapshot = {"step": self.global_step, "epoch": self.current_epoch}

        # 收集视觉编码器梯度
        vis_grads = []
        for name, param in self.model.named_parameters():
            if param.grad is None:
                continue
            if "vision_model" in name and param.requires_grad:
                vis_grads.append(param.grad.detach().flatten())
            elif "text_model" in name and param.requires_grad:
                # 后面统一处理 text
                pass

        # 收集文本编码器梯度
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
        """返回所有梯度快照"""
        return self.gradient_snapshots

    @torch.no_grad()
    def _validate(self, loader) -> float:
        """验证 — 计算对比损失"""
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
    # Gap 度量
    # ============================================================

    @torch.no_grad()
    def _compute_gap_metrics(self, loader, epoch: int, step: int) -> GapMetrics:
        """计算模态差距指标"""
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
        """逐层计算 gap — 需要模型导出中间层输出"""
        # CLIP 模型通过 output_hidden_states=True 获取各层输出
        self.model.eval()

        # 由于CLIP模型结构，这里简化：只计算vision encoder和text encoder的最终输出
        # 深层逐层分析需要hook或模型修改，在后继版本中实现
        per_layer = {}

        # Vision encoder: 获取最后3个transformer block的输出
        # 通过注册hook实现
        vision_outputs = {}
        text_outputs = {}

        def make_hook(name, storage):
            def hook(module, input, output):
                # output通常是 (hidden_states, ...) 的tuple
                if isinstance(output, tuple):
                    storage[name] = output[0].detach()
                else:
                    storage[name] = output.detach()
            return hook

        hooks = []

        # 注册vision编码器的hook（取第一层和最后一层）
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

        # 前向传播一次
        for batch in loader:
            images = batch["image"].to(self.device)[:32]  # 采样
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

        # 移除hooks
        for h in hooks:
            h.remove()

        # 计算各层的gap（vision和text中间层维度不同，跳过不匹配的层）
        for vis_key in vision_outputs:
            layer_idx = vis_key.replace("vis_", "")
            txt_key = vis_key.replace("vis", "txt")
            if txt_key in text_outputs:
                vis_emb = vision_outputs[vis_key].mean(dim=1)
                txt_emb = text_outputs[txt_key].mean(dim=1)
                # 维度匹配检查: ViT hidden=768, Text hidden=512
                if vis_emb.shape[-1] != txt_emb.shape[-1]:
                    continue
                per_layer[f"layer_{layer_idx}"] = self.gap_tracker.compute(
                    vis_emb, txt_emb, epoch=epoch,
                )

        self.model.train()
        return per_layer

    # ============================================================
    # 下游任务评估
    # ============================================================

    @torch.no_grad()
    def _compute_retrieval_metrics(self, loader, k_values: List[int] = [1, 5, 10]) -> Dict[str, float]:
        """Retrieval Recall@K over unique images, using explicit image-caption ownership.

        The loader yields one row per caption, so an image with five captions appears five times.
        Treating row i's caption as row i's positive is therefore wrong once the loader is
        flattened: it scores each row against a single caption out of the several that belong to its
        image. This evaluates the conventional protocol instead - a hit if any caption belonging to
        the image is retrieved in the top k - for both image-to-text and text-to-image.
        """
        self.model.eval()

        all_image_embeds = []
        all_text_embeds = []
        owners = []

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

            # image identity: image_path when the dataset provides it, otherwise the batch index
            if "image_path" in batch:
                owners.extend([str(x) for x in batch["image_path"]])
            else:
                owners.extend([f"__idx{len(owners) + j}" for j in range(images.shape[0])])

        row_image_embeds = torch.cat(all_image_embeds, dim=0)
        text_embeds = torch.cat(all_text_embeds, dim=0)

        # collapse to one row per unique image, keeping every caption as its own column
        order = []
        first_row = {}
        for j, key in enumerate(owners):
            if key not in first_row:
                first_row[key] = j
                order.append(key)
        image_embeds = row_image_embeds[[first_row[k] for k in order]]
        owner_index = {k: i for i, k in enumerate(order)}
        col_owner = torch.tensor([owner_index[k] for k in owners], dtype=torch.long)
        n_img, n_cap = image_embeds.shape[0], text_embeds.shape[0]

        kmax = min(max(k_values), max(n_img, n_cap))
        # process the similarity matrix in row chunks so a 40k-image gallery never materialises at once
        chunk = max(1, int(2_000_000 // max(n_img, 1)))

        metrics = {}
        # image -> text: for each image, is any caption of its own in the top k?
        hits_i2t = {k: torch.zeros(n_img, dtype=torch.bool) for k in k_values}
        for s in range(0, n_cap, chunk):
            sim = image_embeds @ text_embeds[s:s + chunk].T          # (n_img, chunk)
            width = sim.shape[1]
            top = sim.topk(min(kmax, width), dim=1).indices
            own = col_owner[s:s + chunk]
            img_ids = torch.arange(n_img)
            for k in k_values:
                if k <= kmax:
                    kk = min(k, width)
                    hits_i2t[k] |= (own[top[:, :kk]] == img_ids.unsqueeze(1)).any(dim=1)
            del sim, top

        # text -> image: for each caption, is its own image in the top k?
        hits_t2i = {k: torch.zeros(n_cap, dtype=torch.bool) for k in k_values}
        tchunk = max(1, int(2_000_000 // max(n_img, 1)))
        for s in range(0, n_cap, tchunk):
            sim = text_embeds[s:s + tchunk] @ image_embeds.T         # (tchunk, n_img)
            top = sim.topk(min(kmax, sim.shape[1]), dim=1).indices
            own = col_owner[s:s + tchunk]
            for k in k_values:
                if k <= kmax:
                    hits_t2i[k][s:s + tchunk] = (top[:, :k] == own.unsqueeze(1)).any(dim=1)
            del sim, top

        for k in k_values:
            a = hits_i2t[k].float().mean().item()
            b = hits_t2i[k].float().mean().item()
            metrics[f"R@{k}_i2t"] = a
            metrics[f"R@{k}_t2i"] = b
            metrics[f"R@{k}"] = (a + b) / 2.0
        metrics["n_unique_images"] = float(n_img)
        metrics["n_captions"] = float(n_cap)

        self.model.train()
        return metrics

    # ============================================================
    # 保存 & 加载
    # ============================================================

    # ============================================================
    # Route C: 增强训练策略
    # ============================================================

    def _init_route_c(self):
        """初始化 Route C 增强"""
        self._rank_schedule_applied = set()
        self._current_gap_delta = None  # 用于 Gap-Reg Loss

    def _apply_alpha_annealing(self, epoch: int):
        """α Annealing (Route C4): per-epoch 指数衰减"""
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
        """Dynamic Rank Scheduler (Route C2): per-epoch 降低 rank"""
        cfg = self.config.rank_schedule
        if not cfg.enabled or self.peft_method != "lora":
            return
        for trigger_epoch, new_rank in cfg.schedule:
            if epoch == trigger_epoch and new_rank not in self._rank_schedule_applied:
                self._rank_schedule_applied.add(new_rank)
                print(f"   📉 Rank Schedule: epoch {epoch} → rank {new_rank}")

    def enable_dg_early_stopping(self, patience: int = 2):
        """启用 DG-Guided Early Stopping (Route E)"""
        self._dg_es_enabled = True
        self._dg_es_patience = patience
        self._dg_consecutive_rises = 0
        self._dg_prev = None

    def _should_stop_early(self) -> bool:
        """检查 DG 是否连续上升"""
        if not self.gap_tracker.history:
            return False
        # 从 gap_tracker 取最新 DG
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
        """计算 gap 正则化惩罚项 (Route C1)"""
        cfg = self.config.gap_reg
        if not cfg.enabled or self._current_gap_delta is None:
            return 0.0
        penalty = max(0, self._current_gap_delta)
        return cfg.lambda_reg * penalty

    def _save_checkpoint(self, epoch: int, is_best: bool = False):
        """Save the trained state.

        The earlier version stored only the adapters, on the assumption that everything else was
        frozen. That assumption did not hold: apply_lora_to_model left the rest of the adapted tower
        trainable, so a run could move 145 million parameters while its checkpoint kept 196
        thousand of them, and the fine-tuned model could not be restored from its own checkpoint.
        Saving every parameter with requires_grad covers both cases.
        """
        trainable = {name: param.detach().cpu().clone()
                     for name, param in self.model.named_parameters() if param.requires_grad}
        checkpoint = {
            "epoch": epoch,
            "config_name": self.config.name,
            "trainable_state_dict": trainable,
            "trainable_param_names": sorted(trainable),
            "n_trainable_params": int(sum(p.numel() for p in trainable.values())),
            # kept so earlier analysis scripts that read lora_state_dict keep working
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
        """保存最终结果（JSON）"""
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

        print(f"📁 结果已保存: {path}")

        # 保存 gap 历史（便于后续分析）
        gap_path = os.path.join(self.save_dir, "gap_history.json")
        gap_dict = self.gap_tracker.get_history_dict()
        with open(gap_path, 'w', encoding='utf-8') as f:
            json.dump(gap_dict, f, indent=2)

    def _collect_results(self) -> Dict:
        """收集训练结果"""
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
    # 辅助
    # ============================================================

    def _print_gap_metrics(self, metrics: GapMetrics):
        """打印gap指标"""
        print(f"  📏 Gap — Centroid: {metrics.centroid_gap:.4f} | "
              f"Dist(W₂): {metrics.distribution_gap:.4f} | "
              f"Separation: {metrics.cosine_separation:.3f} | "
              f"Cos⁺: {metrics.mean_cosine_pos:.3f}")

    def _missing_mode_str(self) -> str:
        if self.missing_sim is None:
            return "无缺失"
        parts = []
        if self.missing_sim.complete_missing:
            parts.append(f"完整缺失({self.missing_sim.complete_missing})")
        if self.missing_sim.image_drop_ratio > 0:
            parts.append(f"图像丢弃{self.missing_sim.image_drop_ratio:.0%}")
        if self.missing_sim.text_mask_ratio > 0:
            parts.append(f"文本mask{self.missing_sim.text_mask_ratio:.0%}")
        return ", ".join(parts) if parts else "无缺失"
