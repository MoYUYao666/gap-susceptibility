# -*- coding: utf-8 -*-
r"""task-9 公共管线：Qwen2-VL-2B + 逐块 LoRA 分配（P3 E 组补实验，R2.2/R2.4/R3.9/R3.12/R3.21）。

**为什么要有这个模块**：Γ 测量、分配规划、训练三件事必须共用**同一套**块定义、
同一个成本模型、同一套对齐能量口径，否则"同预算对比"就成了空话。
三处各写一份是 bug 的温床（本仓库已有多次此类事故）。

## 口径（全部可追溯）

| 项 | 定义 | 出处 |
|---|---|---|
| 块 | `vision` / `llm_shallow` / `llm_mid` / `llm_deep` | 论文 Appendix D（$K=4$） |
| 层切分 | `layers < round(7N/32)` → shallow；`< round(23N/32)` → mid；其余 deep | 论文 Appendix D「layers 1–7 / 8–23 / 24–31」按比例映射 |
| 目标模块 | attn `q/k/v/o_proj` + mlp `gate/up/down_proj` + vision `qkv/proj/fc1/fc2` | Appendix B 训练口径 |
| 剔除 | `patch_embed`（`Conv3d`，`proj` 子串误伤） | `tools/_p420b_find_conv.py` 实测 |
| 成本 | `cost_k = Σ_{Linear∈k} (in_features + out_features)`，即 LoRA 每 rank 参数量 | `tools/_p420_arch_probe.py` 已逐位断言 |
| 对齐能量 | `E = mean‖h_vis − h_lang‖²`，最后一层隐状态 | 论文 §IV-A / Appendix B |
| Γ | `Γ_k = Σ_{θ∈k} ⟨∇_θE, ∇_θL_CE⟩` | 论文 Definition 1 |

**注意**：论文把 `Γ_k` 定义为**内积**；`tools/_p54_gamma_vlm.py` 用的是
`‖∇E‖·cosφ`（= 内积 / ‖u‖），**两者不等价**。本管线用内积（论文定义）。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

REPO = Path(__file__).resolve().parents[1]
MDIR = REPO / "models" / "Qwen2-VL-2B-Instruct"
ALPACA = REPO / "paper3" / "train-00000-of-00001-a09b74b3ef9c3b56.parquet"

BLOCKS = ["vision", "llm_shallow", "llm_mid", "llm_deep"]

ATTN_TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj"]
MLP_TARGETS = ["gate_proj", "up_proj", "down_proj"]
VISION_TARGETS = ["qkv", "proj", "fc1", "fc2"]
ALL_TARGETS = ATTN_TARGETS + MLP_TARGETS + VISION_TARGETS
EXCLUDE_SUBSTR = ("patch_embed",)

# Qwen2-VL 图像 token 区间（与 tools/_p47_qwen_train.py 一致）
VIS_TOKEN_LO, VIS_TOKEN_HI = 151652, 151656

# 视觉 token 占位数（Qwen2-VL: 每图 28×28 patch / merge 2 → 每 4 patch 合成 1 token）
N_VIS_PLACEHOLDERS = 28 * 28 // 4


# --------------------------------------------------------------------------- #
# 块划分
# --------------------------------------------------------------------------- #
def _layer_index(name: str) -> int | None:
    parts = name.split(".")
    for i, tok in enumerate(parts):
        if tok == "layers" and i + 1 < len(parts) and parts[i + 1].isdigit():
            return int(parts[i + 1])
    return None


def block_of(name: str, n_layers: int) -> str | None:
    """模块名 → 论文 Appendix D 的 4 块之一（None = 不属于任何块，如 lm_head）。"""
    if ".visual." in name:
        return "vision"
    if "language_model" not in name:
        return None
    li = _layer_index(name)
    if li is None:
        return None
    a = round(n_layers * 7 / 32)
    b = round(n_layers * 23 / 32)
    if li < a:
        return "llm_shallow"
    if li < b:
        return "llm_mid"
    return "llm_deep"


def is_excluded(name: str) -> bool:
    return any(s in name for s in EXCLUDE_SUBSTR)


# --------------------------------------------------------------------------- #
# 模型构造
# --------------------------------------------------------------------------- #
def build_model(block_ranks: dict[str, int], device: str = "cuda",
                lora_dropout: float = 0.0, lora_alpha_mult: float = 2.0,
                grad_checkpointing: bool = False):
    """按**逐块 rank** 挂 LoRA（peft 原生支持 `rank_pattern`）。

    返回 `(model, n_trainable_scoped, per_block_params, adapter_names)`。
    注意 `rank_pattern` 的键是**正则**，这里用 `^...$` 锚定的全限定名，
    并在挂完后**实测**每块可训参数量（不信任 pattern 一定匹配上）。
    """
    import torch
    from transformers import Qwen2VLForConditionalGeneration
    from peft import LoraConfig, get_peft_model

    m = Qwen2VLForConditionalGeneration.from_pretrained(
        str(MDIR), torch_dtype=torch.bfloat16, low_cpu_mem_usage=True)
    m.config.use_cache = False
    if grad_checkpointing:
        # 必须**先**开再挂 LoRA（顺序与 peft 的文档一致），否则 adapter 不在
        # checkpoint 段内、显存不降。
        # 实测动机：batch=2、无 checkpointing 时峰值 **10.28 GiB / 7.78 s每步**
        # （`outputs/analysis/p3_alloc_gpu_calib.json :: _first_round`），8 GB 卡不可用。
        # ⚠️ 但 `use_reentrant=True`（旧默认）下 `output_hidden_states=True` 会返回
        # None，而本项目的对齐能量 E 必须用最后一层隐状态 → 故显式走
        # **non-reentrant** 路径。
        m.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False})
        m.enable_input_require_grads()

    # 先把每个待适配 Linear 的全限定名按块收集起来
    n_layers = int(m.config.text_config.num_hidden_layers)
    per_block_names: dict[str, list[str]] = {b: [] for b in BLOCKS}
    for name, mod in m.named_modules():
        if not isinstance(mod, torch.nn.Linear):
            continue
        leaf = name.split(".")[-1]
        if leaf not in ALL_TARGETS or is_excluded(name):
            continue
        blk = block_of(name, n_layers)
        if blk is None:
            continue
        per_block_names[blk].append(name)

    # rank_pattern：键为模块全限定名（peft 用 re.search），值 = 该块 rank
    rank_pattern = {}
    for blk, names in per_block_names.items():
        r = int(block_ranks[blk])
        for n in names:
            rank_pattern[re.escape(n) + "$"] = r

    base_r = int(round(sum(block_ranks[b] for b in BLOCKS) / len(BLOCKS)))
    cfg = LoraConfig(
        r=max(base_r, 1),
        lora_alpha=max(int(round(lora_alpha_mult * max(base_r, 1))), 1),
        lora_dropout=lora_dropout,
        bias="none",
        target_modules=list(ALL_TARGETS),
        # ⚠️ **必须**排除 patch_embed：`target_modules` 的子串匹配会把
        # `model.visual.patch_embed.proj`（Conv3d）也包成 LoRA。实测（CPU 模式）
        # rank=1 时它给 `n_all` 多出 2,456 参数（rank=8 时 19,648），
        # 会让"实测可训参数量 == 预算"的断言**假失败**，也会污染 R3.21 的记账。
        # peft 的 `exclude_modules` 用 `re.fullmatch` 匹配**完整模块名**
        # （源码 `tuners/tuners_utils.py::check_target_module_exists`），
        # 所以这里给**正则**而不是裸子串。
        exclude_modules=r".*patch_embed.*",
        rank_pattern=rank_pattern,
    )
    m = get_peft_model(m, cfg)

    # 严格冻结：只放开 LoRA A/B；同时实测每块参数量
    per_block_params = {b: 0 for b in BLOCKS}
    n_scoped = 0
    adapter_names = {b: [] for b in BLOCKS}
    for name, p in m.named_parameters():
        is_lora = ("lora_A" in name) or ("lora_B" in name)
        p.requires_grad = bool(is_lora)
    for name, p in m.named_parameters():
        if not p.requires_grad:
            continue
        base_mod = name.rsplit(".lora_", 1)[0]
        if is_excluded(base_mod):
            continue
        blk = block_of(base_mod, n_layers)
        if blk is None:
            continue
        per_block_params[blk] += p.numel()
        n_scoped += p.numel()
        adapter_names[blk].append(name)

    # 断言：实测每块参数量 == rank_k * cost_k（成本模型自证）
    mismatch = []
    for b in BLOCKS:
        if len(adapter_names[b]) == 0 and block_ranks[b] > 0:
            mismatch.append(f"{b}: 0 modules matched (rank_pattern 未命中)")
    if mismatch:
        raise RuntimeError("LoRA rank_pattern 未命中：" + "; ".join(mismatch))
    return m, n_scoped, per_block_params, adapter_names, n_layers


def measure_n_trainable(model) -> int:
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))


# --------------------------------------------------------------------------- #
# 数据
# --------------------------------------------------------------------------- #
def load_alpaca(n: int, seed: int = 0):
    """从**归档 parquet** 取 n 条 Alpaca 指令（论文协议：52,002 样本池）。

    用 `input` 字段非空的行优先（更接近 instruction-following），
    再按固定 seed 取前 n 条——**顺序可复现**，且把取到的原文写进归档。
    """
    import pandas as pd
    df = pd.read_parquet(ALPACA)
    df = df[df["input"].fillna("").str.strip() == ""].reset_index(drop=True)
    assert len(df) >= n, f"Alpaca 可用行 {len(df)} < {n}"
    return df.iloc[:n][["instruction", "output", "text"]].to_dict("records")


# --------------------------------------------------------------------------- #
# 前向：对齐能量 E 与任务损失 L
# --------------------------------------------------------------------------- #
def make_inputs(proc, texts, device):
    """把纯文本样本做成 Qwen2-VL 的多模态输入（空白图像，论文协议）。"""
    import torch
    from PIL import Image

    content = [[{"type": "image"}, {"type": "text", "text": t}] for t in texts]
    chats = [proc.apply_chat_template([{"role": "user", "content": c}],
                                      tokenize=False, add_generation_prompt=True)
             for c in content]
    blank = Image.new("RGB", (28 * 14, 28 * 14), (0, 0, 0))
    inp = proc(text=chats, images=[blank] * len(chats),
               return_tensors="pt", padding=True)
    return {k: (v.to(device) if hasattr(v, "to") else v) for k, v in inp.items()}


def alignment_energy(model, proc, texts, device):
    """E = mean‖h_vis − h_lang‖²（最后一层隐状态，视觉/语言 token 位置均值池化）。

    与 `tools/_p47_qwen_train.py:pooled_features` 完全同口径（未归一化版本，
    因为论文的 E 是隐状态欧氏距离的平方，不是归一化后的）。
    """
    import torch
    inp = make_inputs(proc, texts, device)
    with torch.no_grad():
        out = model(**inp, output_hidden_states=True)
    hid = out.hidden_states[-1].float()
    tok = inp["input_ids"]
    vis_mask = ((tok >= VIS_TOKEN_LO) & (tok <= VIS_TOKEN_HI)).unsqueeze(-1).float()
    n_vis = vis_mask.sum(1).clamp(min=1)
    h_vis = (hid * vis_mask).sum(1) / n_vis
    lang_mask = (1.0 - vis_mask) * inp["attention_mask"].unsqueeze(-1).float()
    n_lang = lang_mask.sum(1).clamp(min=1)
    h_lang = (hid * lang_mask).sum(1) / n_lang
    per_sample = ((h_vis - h_lang) ** 2).sum(-1)
    return float(per_sample.mean()), per_sample.detach().cpu().tolist()


def per_sample_energy(model, proc, texts, device):
    return alignment_energy(model, proc, texts, device)
