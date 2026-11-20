import os
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

class LoRALinear(nn.Module):

    def __init__(self, original: nn.Linear, rank: int=8, alpha: float=16.0, dropout: float=0.0, layer_name: str=''):
        super().__init__()
        assert rank > 0, f'LoRA rank must be positive, got {rank}'
        self.original = original
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        self.layer_name = layer_name
        self.original.weight.requires_grad_(False)
        if self.original.bias is not None:
            self.original.bias.requires_grad_(False)
        in_features = original.in_features
        out_features = original.out_features
        self.lora_A = nn.Parameter(torch.zeros(in_features, rank))
        self.lora_B = nn.Parameter(torch.zeros(rank, out_features))
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)
        self.register_buffer('_frozen', torch.tensor(True))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        result = self.original(x)
        delta = self.dropout(x) @ self.lora_A @ self.lora_B
        result = result + self.scaling * delta
        return result

    def merge_weights(self):
        if self._frozen:
            delta = self.lora_A @ self.lora_B
            self.original.weight.data = self.original.weight.data + self.scaling * delta.T
            self._frozen = torch.tensor(False)

    def unmerge_weights(self):
        if not self._frozen:
            delta = self.lora_A @ self.lora_B
            self.original.weight.data = self.original.weight.data - self.scaling * delta.T
            self._frozen = torch.tensor(True)

    @property
    def delta_weight(self) -> torch.Tensor:
        return self.lora_B.T @ self.lora_A.T

    @property
    def trainable_params(self) -> int:
        return self.lora_A.numel() + self.lora_B.numel()

    @property
    def total_params(self) -> int:
        return self.original.weight.numel() + self.trainable_params

class GapInitLoRALinear(LoRALinear):

    def __init__(self, *args, gap_direction: Optional[torch.Tensor]=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.gap_direction = gap_direction
        self._gap_init_applied = False

    def apply_gap_init(self, gap_direction: torch.Tensor):
        if self._gap_init_applied:
            return
        self.gap_direction = gap_direction.to(self.lora_A.device)
        g = self.gap_direction / (self.gap_direction.norm() + 1e-08)
        with torch.no_grad():
            scale = math.sqrt(self.lora_A.shape[1])
            self.lora_A[:, 0] = g[:self.lora_A.shape[0]] * scale
        self._gap_init_applied = True

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if not self._gap_init_applied and self.gap_direction is not None:
            self.apply_gap_init(self.gap_direction)
        return super().forward(x)

class NullLoRALinear(LoRALinear):

    def __init__(self, *args, null_constraint_weight: float=0.01, **kwargs):
        super().__init__(*args, **kwargs)
        self.null_constraint_weight = null_constraint_weight

    def null_space_loss(self) -> torch.Tensor:
        W0 = self.original.weight
        delta_W = self.delta_weight
        violation = torch.norm(W0.T @ delta_W, p='fro')
        return self.null_constraint_weight * violation ** 2

def apply_lora_to_model(model: nn.Module, rank: int=8, alpha: float=16.0, dropout: float=0.0, target_modules: Optional[List[str]]=None, apply_to_vision: bool=True, apply_to_text: bool=True, use_null_lora: bool=False, use_gap_init: bool=False) -> Tuple[nn.Module, Dict[str, LoRALinear], int]:
    if target_modules is None:
        target_modules = ['q_proj', 'v_proj']
    lora_layers = {}
    total_trainable = 0
    if apply_to_vision and hasattr(model, 'vision_model'):
        _inject_lora(model.vision_model, target_modules, rank, alpha, dropout, lora_layers, 'vision', use_null_lora, use_gap_init)
    if apply_to_text and hasattr(model, 'text_model'):
        _inject_lora(model.text_model, target_modules, rank, alpha, dropout, lora_layers, 'text', use_null_lora, use_gap_init)
    total_trainable = sum((l.trainable_params for l in lora_layers.values()))
    frozen = 0
    for name, param in model.named_parameters():
        if 'lora_' in name:
            param.requires_grad_(True)
        else:
            if param.requires_grad:
                frozen += 1
            param.requires_grad_(False)
    still_trainable = sum((p.numel() for p in model.parameters() if p.requires_grad))
    print(f'LoRA runtime diagnostic{rank}LoRA runtime diagnostic{alpha}')
    print(f'   {len(lora_layers)}LoRA runtime diagnostic{total_trainable:,}LoRA runtime diagnostic')
    print(f"LoRA runtime diagnostic{sum((1 for k in lora_layers if k.startswith('vision')))}LoRA runtime diagnostic")
    print(f"LoRA runtime diagnostic{sum((1 for k in lora_layers if k.startswith('text')))}LoRA runtime diagnostic")
    print(f'LoRA runtime diagnostic{frozen}')
    print(f'LoRA runtime diagnostic{still_trainable:,} (LoRA only)')
    if still_trainable != total_trainable:
        raise RuntimeError(f'LoRA scope check failed: {still_trainable:,} parameters are trainable but the adapters hold {total_trainable:,}. Only LoRA parameters may remain trainable.')
    return (model, lora_layers, total_trainable)

def _inject_lora(encoder: nn.Module, target_modules: List[str], rank: int, alpha: float, dropout: float, lora_layers: Dict[str, LoRALinear], prefix: str, use_null_lora: bool, use_gap_init: bool=False):
    if use_null_lora and use_gap_init:
        raise ValueError('LoRA runtime diagnostic')
    if use_gap_init:
        lora_cls = GapInitLoRALinear
    elif use_null_lora:
        lora_cls = NullLoRALinear
    else:
        lora_cls = LoRALinear
    for name, module in encoder.named_modules():
        for target in target_modules:
            if name.endswith(f'.{target}') and isinstance(module, nn.Linear):
                full_name = f'{prefix}.{name}'
                lora_module = lora_cls(original=module, rank=rank, alpha=alpha, dropout=dropout, layer_name=full_name)
                parent_name, child_name = _split_name(name)
                parent = encoder.get_submodule(parent_name) if parent_name else encoder
                setattr(parent, child_name, lora_module)
                lora_layers[full_name] = lora_module

def _split_name(name: str) -> Tuple[str, str]:
    parts = name.rsplit('.', 1)
    if len(parts) == 2:
        return (parts[0], parts[1])
    return ('', parts[0])

def get_lora_params(model: nn.Module) -> List[nn.Parameter]:
    params = []
    for name, param in model.named_parameters():
        if 'lora_A' in name or 'lora_B' in name:
            params.append(param)
    return params

def compute_lora_sparsity(lora_layers: Dict[str, LoRALinear]) -> Dict[str, float]:
    result = {}
    for name, layer in lora_layers.items():
        ratio = layer.trainable_params / layer.total_params
        result[name] = ratio
    return result

def get_null_space_loss(lora_layers: Dict[str, LoRALinear]) -> torch.Tensor:
    loss = torch.tensor(0.0)
    for layer in lora_layers.values():
        if isinstance(layer, NullLoRALinear):
            loss = loss + layer.null_space_loss()
    return loss

@torch.no_grad()
def compute_gap_direction(model, dataloader, device: str='mps', n_batches: int=10) -> torch.Tensor:
    from transformers import CLIPProcessor
    model.eval()
    processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
    all_image_embeds = []
    all_text_embeds = []
    for i, batch in enumerate(dataloader):
        if i >= n_batches:
            break
        images = batch['image'].to(device)
        texts = batch['caption']
        text_inputs = processor(text=texts, return_tensors='pt', padding=True, truncation=True, max_length=int(os.environ.get('PEFT_MAX_SEQ_LEN', '77')))
        input_ids = text_inputs['input_ids'].to(device)
        attention_mask = text_inputs['attention_mask'].to(device)
        outputs = model(pixel_values=images, input_ids=input_ids, attention_mask=attention_mask)
        all_image_embeds.append(outputs.image_embeds.cpu())
        all_text_embeds.append(outputs.text_embeds.cpu())
    image_embeds = torch.cat(all_image_embeds, dim=0)
    text_embeds = torch.cat(all_text_embeds, dim=0)
    image_embeds = F.normalize(image_embeds, p=2, dim=-1)
    text_embeds = F.normalize(text_embeds, p=2, dim=-1)
    mu_I = image_embeds.mean(dim=0)
    mu_T = text_embeds.mean(dim=0)
    gap_direction = mu_I - mu_T
    gap_direction = gap_direction / (gap_direction.norm() + 1e-08)
    print(f'LoRA runtime diagnostic{len(image_embeds)} samples)')
    print(f'LoRA runtime diagnostic{(mu_I - mu_T).norm().item():.4f}')
    print(f'LoRA runtime diagnostic{gap_direction.norm().item():.4f}')
    return gap_direction

def apply_gap_init_to_layers(lora_layers: Dict[str, LoRALinear], gap_direction: torch.Tensor):
    applied = 0
    for name, layer in lora_layers.items():
        if isinstance(layer, GapInitLoRALinear):
            in_features = layer.lora_A.shape[0]
            if len(gap_direction) >= in_features:
                sub_gap = gap_direction[:in_features]
            else:
                continue
            layer.apply_gap_init(sub_gap)
            applied += 1
    print(f'LoRA runtime diagnostic{applied}/{len(lora_layers)}LoRA runtime diagnostic')
