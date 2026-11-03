# -*- coding: utf-8 -*-
r"""task-9 / E 组（R2.2, R2.4, R3.9, R3.12, R3.21）——步骤 1：架构与预算可行域探针。

## 这一步解决什么

论文 Corollary 2 的分配律是

    rank*_k = C * exp(-beta |Gamma_k|) / sum_j exp(-beta |Gamma_j|)          (Eq. 5)

审稿人 R3.21 的要害是：**"theory 组 r=4，random 组从 {4,16,32,64} 抽"——两组的
rank 分布与有效参数量根本不可比。** 所以本实验的第一件事不是训练，而是把
**参数预算的记账口径**钉死：

- LoRA 的**每 rank 参数成本** `cost_k`（= 该块所有被适配 Linear 的 (in+out) 之和）
  在块间**并不相等**：vision 块的 Linear 维度是 1152/896 量级，LLM 块是 1536/8960 量级；
- 于是"总 rank 相同"**不等于**"可训参数量相同"；
- 论文自己的 uniform `r=4` 配置实际是把 `sum_k rank_k = 4K` 当预算用的——**这是
  rank 记账**，其可训参数量 = `4 * sum_k cost_k`。

**本探针产出**（写 `outputs/analysis/p3_alloc_budget_probe.json`）：

1. Qwen2-VL-2B 的块结构（vision / llm_shallow / llm_mid / llm_deep）与每块的
   被适配模块名、维度、以及 **exact cost_k**；
2. 在候选预算下 **最大可行 rank 配置**：因为 rank_k >= 1 是硬下界，
   `min_cost = sum_k cost_k` 是**任何**分配方案都无法低于的地板 —— 若地板已经
   超过预算，则该预算下"参数对齐"不可实现（R3.21 必须写明这一点）；
3. 最小二乘校验：用探针算出的 cost_k 预测 `n_trainable_params`，与真实
   `get_peft_model` 实测值**逐位断言相等**（容差 0，因为都是整数计数）。

## 用法

    python tools\_p420_arch_probe.py            # 预演，只打印计划
    python tools\_p420_arch_probe.py --apply    # 实跑并落盘
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
MDIR = REPO / "models" / "Qwen2-VL-2B-Instruct"
OUT = REPO / "outputs" / "analysis" / "p3_alloc_budget_probe.json"

# 与论文 Appendix B 的 LLaVA 训练口径一致：LoRA 打在注意力 + MLP 投影上。
ATTN_TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj"]
MLP_TARGETS = ["gate_proj", "up_proj", "down_proj"]
VISION_TARGETS = ["qkv", "proj", "fc1", "fc2"]

# ⚠️ 实测（tools/_p420b_find_conv.py）：`target_modules=["proj", ...]` 的子串匹配会把
# `model.visual.patch_embed.proj`（Conv3d，权重 1280*3*2*14*14）也包成 LoRA。
# 论文的视觉适配指"注意力投影"（patch_embed 不是 attention projection），
# 故显式剔除——否则每 rank 成本记账会混入卷积核，预算断言失效。
EXCLUDE_SUBSTR = ("patch_embed",)

# 论文 Appendix D 的 K=4 分块口径（vision / shallow / mid / deep LLM）。
BLOCKS = ["vision", "llm_shallow", "llm_mid", "llm_deep"]


def classify(module_name: str, layer_idx: int | None, n_layers: int) -> str | None:
    """把 LoRA 模块名映射到论文 Appendix D 的 4 个块。"""
    if ".visual." in module_name or module_name.startswith("visual"):
        return "vision"
    if "language_model" not in module_name:
        return None
    if layer_idx is None:
        return None
    # 32 层 LLaVA 的分法是 1-7 / 8-23 / 24-31（1-indexed）→ 按比例映射到任意深度。
    third_a = round(n_layers * 7 / 32)
    third_b = round(n_layers * 23 / 32)
    if layer_idx < third_a:
        return "llm_shallow"
    if layer_idx < third_b:
        return "llm_mid"
    return "llm_deep"


def layer_index_of(name: str) -> int | None:
    """从 '...language_model.model.layers.17.self_attn.q_proj...' 里取层号。"""
    parts = name.split(".")
    for i, tok in enumerate(parts):
        if tok == "layers" and i + 1 < len(parts) and parts[i + 1].isdigit():
            return int(parts[i + 1])
    return None


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("=== task-9 步骤 1：架构与预算探针（预演）===")
        print(f"  模型 {MDIR}")
        print(f"  块 {BLOCKS}｜targets attn={ATTN_TARGETS} mlp={MLP_TARGETS} vis={VISION_TARGETS}")
        print("  （加 --apply 实跑）")
        return 0

    import torch
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
    from peft import LoraConfig, get_peft_model

    print(f"=== 探针启动（torch {torch.__version__}，cuda={torch.cuda.is_available()}）===",
          flush=True)

    # ---------- 1. 先只用 config 读结构（不加载权重，秒级） ----------
    from transformers import AutoConfig
    cfg = AutoConfig.from_pretrained(str(MDIR))
    n_layers = int(cfg.text_config.num_hidden_layers)
    d_model = int(cfg.text_config.hidden_size)
    print(f"  LLM: {n_layers} 层, d_model={d_model}", flush=True)
    print(f"  vision: depth={getattr(cfg.vision_config, 'depth', None)} "
          f"hidden={getattr(cfg.vision_config, 'hidden_size', None)} "
          f"embed_dim={getattr(cfg.vision_config, 'embed_dim', None)}", flush=True)

    # ---------- 2. 加载模型（bf16，8GB 卡可行）并挂 LoRA，实测每块成本 ----------
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        str(MDIR), torch_dtype=torch.bfloat16, low_cpu_mem_usage=True)
    model.config.use_cache = False
    targets = ATTN_TARGETS + MLP_TARGETS + VISION_TARGETS
    model = get_peft_model(model, LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
        target_modules=targets, task_type=None))

    # 每块：被适配模块数、rank-1 成本、以及逐模块明细
    per_block: dict[str, dict] = {b: {"modules": [], "cost_per_rank": 0} for b in BLOCKS}
    lora_tensors: dict[str, list[str]] = {b: [] for b in BLOCKS}
    for name, mod in model.named_modules():
        if not hasattr(mod, "lora_A"):
            continue  # 只统计挂了 LoRA 的 Linear
        if any(s in name for s in EXCLUDE_SUBSTR):
            continue  # patch_embed.proj 是 Conv3d，非注意力投影
        base = mod.get_base_layer() if hasattr(mod, "get_base_layer") else mod
        if not isinstance(base, torch.nn.Linear):
            print(f"  [warn] 非 Linear 的 LoRA 模块被跳过：{name} ({type(base).__name__})",
                  flush=True)
            continue
        in_f, out_f = int(base.in_features), int(base.out_features)
        blk = classify(name, layer_index_of(name), n_layers)
        if blk is None:
            print(f"  [warn] 未归类模块 {name}", flush=True)
            continue
        per_block[blk]["modules"].append(
            {"name": name, "in_features": in_f, "out_features": out_f,
             "cost_per_rank": in_f + out_f})
        per_block[blk]["cost_per_rank"] += in_f + out_f
    for b in BLOCKS:
        per_block[b]["n_modules"] = len(per_block[b]["modules"])

    # 真实可训参数量 + 归属块（用 lora_A/lora_B 张量名判定，与模块名同源）
    real_trainable = 0                      # 含 patch_embed（peft 实际包了什么）
    real_trainable_scoped = 0               # 仅我们纳入计账的模块
    excluded_params = 0
    real_per_block = {b: 0 for b in BLOCKS}
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        real_trainable += p.numel()
        base_mod_name = name.rsplit(".lora_", 1)[0]
        if any(s in base_mod_name for s in EXCLUDE_SUBSTR):
            excluded_params += p.numel()
            continue
        real_trainable_scoped += p.numel()
        blk = classify(base_mod_name, layer_index_of(base_mod_name), n_layers)
        if blk is not None:
            real_per_block[blk] += p.numel()
            lora_tensors[blk].append(name)

    # 断言：predicted block cost (r=8) == real per-block trainable params
    chk = []
    ok = True
    for b in BLOCKS:
        pred = 8 * per_block[b]["cost_per_rank"]
        real = real_per_block[b]
        good = pred == real
        ok &= good
        chk.append({"block": b, "predicted_8x_cost": pred, "real_trainable": real,
                    "match": good})
        print(f"  {'OK ' if good else 'FAIL'} {b:<12} cost_per_rank={per_block[b]['cost_per_rank']:>7,}"
              f"  8x={pred:>10,}  real={real:>10,}", flush=True)

    print(f"  总可训参数（r=8, 全 target）real={real_trainable:,} "
          f"pred={8 * sum(per_block[b]['cost_per_rank'] for b in BLOCKS):,}", flush=True)
    print(f"  其中 patch_embed(Conv3d, 已剔除) = {excluded_params:,}；"
          f"纳入记账 = {real_trainable_scoped:,}", flush=True)
    if excluded_params == 0:
        print("  [warn] 未发现 patch_embed 被包装——若 peft 版本变化，需复核 EXCLUDE_SUBSTR",
              flush=True)
    if not ok:
        print("  [FATAL] 成本模型与实测不一致 → 不落盘（预算记账不可信）", flush=True)
        return 1

    min_cost = sum(per_block[b]["cost_per_rank"] for b in BLOCKS)
    print(f"  最小可行参数地板 min_cost（所有块 rank=1）= {min_cost:,}", flush=True)

    # ---------- 3. 候选预算表：给出 uniform r 下的真实参数量 ----------
    cost_sum = sum(per_block[b]["cost_per_rank"] for b in BLOCKS)
    budget_table = []
    for r in (1, 2, 3, 4, 6, 8, 12, 16):
        budget_table.append({
            "uniform_rank": r,
            "trainable_params_all_blocks": r * cost_sum,
            "feasible": True,
        })
        print(f"  uniform r={r:<3} → 可训参数 {r * cost_sum:>12,}", flush=True)

    rec = {
        "script": "tools/_p420_arch_probe.py",
        "model": str(MDIR.relative_to(REPO)).replace("\\", "/"),
        "model_dtype": "bfloat16",
        "quantization": None,
        "n_llm_layers": n_layers,
        "llm_hidden_size": d_model,
        "blocks": BLOCKS,
        "block_split_rule": "layers < round(7N/32) -> shallow; < round(23N/32) -> mid; else deep",
        "target_modules": targets,
        "excluded_substr": list(EXCLUDE_SUBSTR),
        "cost_definition": "cost_per_rank_k = sum over adapted Linears in block k of (in_features + out_features)",
        "per_block": {b: {"n_modules": per_block[b]["n_modules"],
                          "cost_per_rank": per_block[b]["cost_per_rank"],
                          "modules": per_block[b]["modules"]} for b in BLOCKS},
        "hard_assert_cost_model": chk,
        "cost_model_verified": bool(ok),
        "min_feasible_params_all_blocks_rank1": min_cost,
        "sum_cost_per_rank": cost_sum,
        "budget_table_uniform": budget_table,
        "n_lora_tensors": {b: len(lora_tensors[b]) for b in BLOCKS},
        "real_trainable_incl_patch_embed": real_trainable,
        "real_trainable_scoped": real_trainable_scoped,
        "excluded_patch_embed_params": excluded_params,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(rec, ensure_ascii=False, indent=1))
    print(f"\n  已写 {OUT.relative_to(REPO)}", flush=True)

    # 打印供人工核对的紧凑表
    print("\n=== 逐块成本表（供 R3.21 预算对齐用）===")
    print(f"{'block':<12}{'n_modules':>10}{'cost/rank':>12}{'share':>9}")
    for b in BLOCKS:
        c = per_block[b]["cost_per_rank"]
        print(f"{b:<12}{per_block[b]['n_modules']:>10}{c:>12,}{c / cost_sum:>8.1%}")
    print(f"{'TOTAL':<12}{sum(per_block[b]['n_modules'] for b in BLOCKS):>10}"
          f"{cost_sum:>12,}{1.0:>8.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
