"""
Adapter & Prefix Tuning — 复用 lora.py 注入框架
=================================================
"""
import torch
import torch.nn as nn
from typing import Dict, List, Tuple


class AdapterLayer(nn.Module):
    """Bottleneck Adapter: down→GELU→up, 残差连接"""
    def __init__(self, hidden_dim, bottleneck_dim=16):
        super().__init__()
        self.down = nn.Linear(hidden_dim, bottleneck_dim)
        self.act = nn.GELU()
        self.up = nn.Linear(bottleneck_dim, hidden_dim)
        nn.init.kaiming_uniform_(self.down.weight, a=5**0.5)
        nn.init.zeros_(self.up.weight)
    def forward(self, x): return self.up(self.act(self.down(x)))


class AdapterWrapper(nn.Module):
    """原始层 + Adapter 残差"""
    def __init__(self, original, bottleneck_dim, hidden_dim=None):
        super().__init__()
        self.original = original
        if hidden_dim is None:
            hidden_dim = getattr(original, 'out_features', None) or 768
        self.adapter = AdapterLayer(hidden_dim, bottleneck_dim)
    def forward(self, *a, **kw):
        o = self.original(*a, **kw)
        return ((self.adapter(o[0]) + o[0],) + o[1:]) if isinstance(o, tuple) else (self.adapter(o) + o)


class PrefixWrapper(nn.Module):
    """attention 前拼接 prefix tokens"""
    def __init__(self, original, pre_len, hidden_dim):
        super().__init__()
        self.original = original
        self.pre_len = pre_len
        self.prefix = nn.Parameter(torch.randn(pre_len, hidden_dim) * 0.02)
    def forward(self, hs=None, *a, **kw):
        # CLIP 传 hidden_states= 是 keyword 参数，需兼容
        if hs is None:
            hs = kw.pop("hidden_states", None)
        if hs is None:
            raise ValueError("PrefixWrapper: 未找到 hidden_states 输入")
        B = hs.shape[0]
        pfx = self.prefix.unsqueeze(0).expand(B, -1, -1)
        ext = torch.cat([pfx, hs], dim=1)

        # 扩展所有 mask（attention_mask 2D/4D、causal_attention_mask 4D）
        for mask_key in ('attention_mask', 'causal_attention_mask'):
            if mask_key not in kw or kw[mask_key] is None:
                continue
            m = kw[mask_key]
            if m.dim() == 2:
                # 2D: (B, seq) → (B, pre_len+seq)
                kw[mask_key] = torch.cat([
                    torch.ones(B, self.pre_len, device=m.device, dtype=m.dtype), m
                ], dim=1)
            elif m.dim() == 4:
                # 4D: (B, 1, Q, K) → (B, 1, pre_len+Q, pre_len+K)
                # 前缀行: prefix attend 所有; 前缀列: 所有 attend prefix
                m = torch.cat([
                    torch.ones(B, 1, m.shape[2], self.pre_len, device=m.device, dtype=m.dtype),
                    m,
                ], dim=-1)  # 扩展 key 维
                kw[mask_key] = torch.cat([
                    torch.ones(B, 1, self.pre_len, m.shape[-1], device=m.device, dtype=m.dtype),
                    m,
                ], dim=2)  # 扩展 query 维

        return self.original(ext, *a, **kw)


# --- 递归注入（仿照 lora.py _inject_lora 模式）---

def _inject_into(module, target_names, factory_fn, result_dict, prefix):
    """递归遍历，自动穿透 ModuleList"""
    for name, child in list(module.named_children()):
        full = f"{prefix}.{name}"
        if name in target_names:
            wrapper = factory_fn(child, name)
            setattr(module, name, wrapper)
            result_dict[full] = wrapper
        elif isinstance(child, nn.ModuleList):
            for i, item in enumerate(child):
                _inject_into(item, target_names, factory_fn, result_dict, f"{full}.{i}")
        else:
            _inject_into(child, target_names, factory_fn, result_dict, full)


def apply_adapter_to_model(model, bottleneck_dim=16, activation="gelu", dropout=0.0,
                          target_modules=None, apply_to_vision=True, apply_to_text=True):
    # 从 model config 获取 hidden_dim
    vis_dim = model.config.vision_config.hidden_size if hasattr(model, 'config') else 768
    txt_dim = model.config.text_config.hidden_size if hasattr(model, 'config') else 512
    adict = {}
    if apply_to_vision and hasattr(model, 'vision_model'):
        f = lambda c, n: AdapterWrapper(c, bottleneck_dim, vis_dim)
        _inject_into(model.vision_model, {'self_attn', 'mlp'}, f, adict, "vision")
    if apply_to_text and hasattr(model, 'text_model'):
        f = lambda c, n: AdapterWrapper(c, bottleneck_dim, txt_dim)
        _inject_into(model.text_model, {'self_attn', 'mlp'}, f, adict, "text")
    # 冻结所有参数，再只解冻 adapter 子模块
    for p in model.parameters(): p.requires_grad = False
    for w in adict.values():
        for p in w.adapter.parameters(): p.requires_grad = True
    tp = sum(p.numel() for w in adict.values() for p in w.adapter.parameters())
    print(f"✅ Adapter: dim={bottleneck_dim}, {len(adict)} layers, {tp:,} params")
    return model, adict, tp


def apply_prefix_to_model(model, prefix_length=16, hidden_dim=None,
                          apply_to_vision=True, apply_to_text=True, **kw):
    if hidden_dim is None:
        vis_d = model.config.vision_config.hidden_size if hasattr(model, 'config') else 768
        txt_d = model.config.text_config.hidden_size if hasattr(model, 'config') else 512
    else:
        vis_d = txt_d = hidden_dim
    pdict = {}
    if apply_to_vision and hasattr(model, 'vision_model'):
        f = lambda c, n: PrefixWrapper(c, prefix_length, vis_d)
        _inject_into(model.vision_model, {'self_attn'}, f, pdict, "vision")
    if apply_to_text and hasattr(model, 'text_model'):
        f = lambda c, n: PrefixWrapper(c, prefix_length, txt_d)
        _inject_into(model.text_model, {'self_attn'}, f, pdict, "text")
    for p in model.parameters(): p.requires_grad = False
    for w in pdict.values():
        w.prefix.requires_grad = True
    tp = sum(p.numel() for w in pdict.values() for p in w.parameters() if p.requires_grad)
    print(f"✅ Prefix: len={prefix_length}, {len(pdict)} layers, {tp:,} params")
    return model, pdict, tp


def get_peft_params(model, peft_method=None):
    return [p for p in model.parameters() if p.requires_grad]


def count_peft_parameters(model, peft_method):
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"peft_trainable": trainable, "trainable_ratio": trainable / total * 100 if total > 0 else 0}
