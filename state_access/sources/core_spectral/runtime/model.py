"""Small, explicit PEFT controls for offline Hugging Face CLIP.

Prompt controls are not CoOp/MaPLe reproductions. No legacy project LoRA code.
"""
import contextlib
import math
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from transformers import CLIPModel

MODES = ('lora_text', 'lora_both')


def seed_cpu(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def feature_tensor(output):
    """Handle transformers 5 projected pooler outputs and older tensor APIs."""
    value = output if isinstance(output, torch.Tensor) else output.pooler_output
    if value.ndim != 2 or not torch.isfinite(value).all():
        raise ValueError('Features must be a finite rank-two tensor')
    return value


def normalized(output):
    value = feature_tensor(output).float()
    if (value.norm(dim=-1) <= 0).any():
        raise ValueError('Zero feature vector')
    return F.normalize(value, dim=-1)


class LoRALinear(nn.Module):
    """No-dropout LoRA, alpha/rank=2, with an exactly zero initial delta."""
    def __init__(self, base, rank):
        super().__init__()
        self.base = base
        self.rank = rank
        self.scale = 2.0
        self.enabled = True
        self.lora_A = nn.Parameter(torch.empty(rank, base.in_features))
        self.lora_B = nn.Parameter(torch.zeros(base.out_features, rank))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))

    def forward(self, x):
        value = self.base(x)
        if self.enabled:
            value = value + F.linear(F.linear(x, self.lora_A), self.lora_B) * self.scale
        return value


class AdaptedCLIP(nn.Module):
    def __init__(self, clip, mode):
        super().__init__()
        if mode not in MODES:
            raise ValueError(f'Unknown mode: {mode}')
        self.clip = clip
        self.mode = mode
        self.prompt_enabled = True
        self.hook_handles = []
        for parameter in clip.parameters():
            parameter.requires_grad_(False)
        if mode.startswith('lora_'):
            towers = [clip.text_model]
            if mode != 'lora_text':
                towers.append(clip.vision_model)
            for tower in towers:
                layers = tower.encoder.layers
                if len(layers) != 12:
                    raise ValueError('All adaptation towers must have exactly twelve layers')
                indices = range(12)
                rank = 8
                if mode == 'lora_early':
                    indices, rank = range(6), 8
                elif mode == 'lora_late':
                    indices, rank = range(6, 12), 8
                for index in indices:
                    attention = layers[index].self_attn
                    for name in ('q_proj', 'k_proj', 'v_proj'):
                        setattr(attention, name, LoRALinear(getattr(attention, name), rank))
        else:
            self.text_context = nn.Parameter(torch.empty(4, clip.config.text_config.hidden_size))
            nn.init.normal_(self.text_context, std=0.02)
            self.hook_handles.append(clip.text_model.embeddings.token_embedding.register_forward_hook(
                self._text_hook))
            if mode == 'dual_context':
                self.visual_context = nn.Parameter(torch.empty(4, clip.config.vision_config.hidden_size))
                nn.init.normal_(self.visual_context, std=0.02)
                self.hook_handles.append(clip.vision_model.embeddings.register_forward_hook(self._vision_hook))

    def _text_hook(self, module, inputs, output):
        if not self.prompt_enabled:
            return output
        if output.shape[1] < 7:
            raise ValueError('Text context requires BOS + four prefix tokens + text + EOS')
        return torch.cat((output[:, :1], self.text_context.to(output.dtype).unsqueeze(0).expand(
            output.shape[0], -1, -1), output[:, 5:]), dim=1)

    def _vision_hook(self, module, inputs, output):
        if not self.prompt_enabled:
            return output
        return torch.cat((output, self.visual_context.to(output.dtype).unsqueeze(0).expand(
            output.shape[0], -1, -1)), dim=1)

    @contextlib.contextmanager
    def prompts_disabled(self):
        old = self.prompt_enabled
        self.prompt_enabled = False
        try:
            yield
        finally:
            self.prompt_enabled = old

    @contextlib.contextmanager
    def frozen_baseline(self):
        adapters = [module for module in self.modules() if isinstance(module, LoRALinear)]
        old = [module.enabled for module in adapters]
        with self.prompts_disabled():
            for module in adapters:
                module.enabled = False
            try:
                yield
            finally:
                for module, enabled in zip(adapters, old):
                    module.enabled = enabled

    def image_features(self, pixels):
        return normalized(self.clip.get_image_features(pixel_values=pixels, return_dict=True))

    def text_features(self, text):
        return normalized(self.clip.get_text_features(**text, return_dict=True))

    def features(self, pixels, text):
        return self.image_features(pixels), self.text_features(text)

    def forward(self, pixels, text):
        images, texts = self.features(pixels, text)
        scores = images @ texts.T
        if not torch.isfinite(scores).all():
            raise FloatingPointError('Nonfinite training scores')
        return scores


def build_model(model_path, mode, seed):
    path = Path(model_path)
    if not path.is_dir():
        raise FileNotFoundError(f'Local model directory missing: {path}')
    seed_cpu(seed)
    safe = (path / 'model.safetensors').is_file() or (path / 'model.safetensors.index.json').is_file()
    if not safe and not ((path / 'pytorch_model.bin').is_file() or
                         (path / 'pytorch_model.bin.index.json').is_file()):
        raise FileNotFoundError('No local model weights')
    clip = CLIPModel.from_pretrained(path, local_files_only=True, use_safetensors=safe, weights_only=True,
                                      attn_implementation='eager', dtype=torch.float32)
    return AdaptedCLIP(clip, mode)


def get_trainable_state(model):
    return {key: value.detach().cpu().clone() for key, value in model.named_parameters()
            if value.requires_grad}


def trainable_manifest(model):
    return {key: {'shape': list(value.shape), 'dtype': str(value.dtype)}
            for key, value in model.named_parameters() if value.requires_grad}


def restore_trainable(model, state):
    current = {key: value for key, value in model.named_parameters() if value.requires_grad}
    if set(current) != set(state):
        raise ValueError('Trainable key manifest mismatch')
    for key, parameter in current.items():
        value = state[key]
        if value.shape != parameter.shape or value.dtype != parameter.dtype or not torch.isfinite(value).all():
            raise ValueError(f'Invalid trainable tensor: {key}')
    with torch.no_grad():
        for key, parameter in current.items():
            parameter.copy_(state[key].to(parameter.device))
