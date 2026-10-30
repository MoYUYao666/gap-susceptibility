# -*- coding: utf-8 -*-
r"""task-9 步骤 2：在 Qwen2-VL-2B 上按论文定义测**逐块 Γ_k**（R3.12 要的完整表）。

## 定义（论文 Definition 1，**内积**而非范数×余弦）

    Γ_k = Σ_{θ ∈ block k} ⟨ ∇_θ E , ∇_θ L_CE ⟩

- `E = mean‖h_vis − h_lang‖²`（最后一层隐状态；§IV-A / Appendix B）
- `L_CE`：交叉熵，**只在 assistant 回复 token 上**（快速且省显存；全序列 CE 会把
  4 样本顶到 17.8 GiB，见 `tools/_p430_gpu_calib.py`）
- 视觉编码器**冻结**（论文协议），故梯度只流经 LoRA 参数

## 为什么用内积而不是 `‖∇E‖·cosφ`

`tools/_p54_gamma_vlm.py` 记的是 `norm_g × cos_phi`，即 `⟨∇E,u⟩ / ‖u‖`。
论文的 Γ 是**内积本身**；两者差一个 `‖u‖` 因子，**块间不可互比**。本脚本用论文定义。

## 产出

`outputs/analysis/p3_alloc_gamma_qwen2vl2b.json`：逐块 Γ_k（多 batch、多 seed）、
每 batch 明细（供稳定性核查）、sign 一致性、以及 rank-1 成本。
"""
from __future__ import annotations

import io
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from _p43x_common import (BLOCKS, alignment_energy, build_model, is_excluded,  # noqa: E402
                          load_alpaca, measure_n_trainable)

OUT = REPO / "outputs" / "analysis" / "p3_alloc_gamma_qwen2vl2b.json"

REFERENCE_RANK = 4          # 与论文 Theory 组同预算的参考配置
N_BATCH = 5                 # 论文 Appendix D：5 prompt 平均
BATCH_SIZE = 4
SEEDS = [42, 101, 202]


def _response_labels(proc, input_ids):
    """把 assistant 回复区间的 token 作为监督目标，其余置 -100。"""
    import torch
    im_start = proc.tokenizer.convert_tokens_to_ids("<|im_start|>")
    assistant = proc.tokenizer.encode("assistant", add_special_tokens=False)
    labels = torch.full_like(input_ids, -100)
    B, L = input_ids.shape
    ids = input_ids.tolist()
    for b in range(B):
        starts = [i for i, v in enumerate(ids[b]) if v == im_start]
        chosen = None
        for s in starts:
            if ids[b][s + 1:s + 1 + len(assistant)] == assistant:
                chosen = s + 1 + len(assistant) + 1   # 跳过 'assistant' 后的换行
        assert chosen is not None, "未找到 assistant 区间"
        labels[b, chosen:] = input_ids[b, chosen:]
    return labels


def task_ce_loss(model, proc, texts, device):
    """只在回复 token 上算 CE（省显存的关键）。"""
    import torch
    import torch.nn.functional as F
    content = [[{"type": "image"}, {"type": "text", "text": t}] for t in texts]
    full = [proc.apply_chat_template(
        [{"role": "user", "content": c},
         {"role": "assistant", "content": "OK"}], tokenize=False) for c in content]
    from PIL import Image
    blank = Image.new("RGB", (28 * 14, 28 * 14), (0, 0, 0))
    inp = proc(text=full, images=[blank] * len(full), return_tensors="pt", padding=True)
    inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in inp.items()}
    out = model(**inp)
    labels = _response_labels(proc, inp["input_ids"])
    logits = out.logits[:, :-1, :].float()
    tgt = labels[:, 1:]
    return F.cross_entropy(logits.reshape(-1, logits.size(-1)), tgt.reshape(-1),
                           ignore_index=-100)


def grad_dot_per_block(model, gE: dict, params, n_layers: int):
    """用已存的 ∇E 与当前 `.grad`（任务梯度）做逐块内积。"""
    import torch
    acc = defaultdict(float)
    for name, p in params:
        if p.grad is None or gE.get(name) is None:
            continue
        base = name.rsplit(".lora_", 1)[0]
        if is_excluded(base):
            continue
        from _p43x_common import block_of
        blk = block_of(base, n_layers)
        if blk is None:
            continue
        acc[blk] += float((p.grad.detach().float() * gE[name]).sum())
    return {b: acc[b] for b in BLOCKS}


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("=== Γ 测量（预演）===")
        print(f"  模型 Qwen2-VL-2B｜块 {BLOCKS}｜参考 rank {REFERENCE_RANK}")
        print(f"  {N_BATCH} batch × {BATCH_SIZE} 样本 × {len(SEEDS)} seed")
        print("  Γ_k = Σ_θ∈k ⟨∇E, ∇L_CE⟩（论文 Definition 1，内积）")
        print("  （加 --apply 实跑）")
        return 0

    import torch
    from transformers import AutoProcessor

    dev = "cuda"
    proc = AutoProcessor.from_pretrained(str(REPO / "models" / "Qwen2-VL-2B-Instruct"))
    samples = load_alpaca(N_BATCH * BATCH_SIZE, seed=0)
    all_texts = [s["instruction"] for s in samples]

    per_seed = {}
    for seed in SEEDS:
        torch.manual_seed(seed)
        torch.cuda.empty_cache()
        t0 = time.time()
        ranks = {b: REFERENCE_RANK for b in BLOCKS}
        model, n_tr, per_blk_params, _, n_layers = build_model(ranks)
        model = model.to(dev)
        params = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
        print(f"\n=== seed {seed}｜记账可训 {n_tr:,}｜逐块 {per_blk_params} ===", flush=True)

        rows = []
        for bi in range(N_BATCH):
            texts = all_texts[bi * BATCH_SIZE:(bi + 1) * BATCH_SIZE]
            # --- 1) ∇E ---
            model.eval()
            model.zero_grad(set_to_none=True)
            content = [[{"type": "image"}, {"type": "text", "text": t}] for t in texts]
            chats = [proc.apply_chat_template([{"role": "user", "content": c}],
                                              tokenize=False, add_generation_prompt=True)
                     for c in content]
            from PIL import Image
            blank = Image.new("RGB", (28 * 14, 28 * 14), (0, 0, 0))
            inp = proc(text=chats, images=[blank] * len(chats),
                       return_tensors="pt", padding=True)
            inp = {k: (v.to(dev) if hasattr(v, "to") else v) for k, v in inp.items()}
            out = model(**inp, output_hidden_states=True)
            hid = out.hidden_states[-1].float()
            tok = inp["input_ids"]
            vis_mask = ((tok >= 151652) & (tok <= 151656)).unsqueeze(-1).float()
            n_vis = vis_mask.sum(1).clamp(min=1)
            h_vis = (hid * vis_mask).sum(1) / n_vis
            lang_mask = (1.0 - vis_mask) * inp["attention_mask"].unsqueeze(-1).float()
            n_lang = lang_mask.sum(1).clamp(min=1)
            h_lang = (hid * lang_mask).sum(1) / n_lang
            E = ((h_vis - h_lang) ** 2).sum(-1).mean()
            E.backward()
            gE = {n: (p.grad.detach().clone() if p.grad is not None else None)
                  for n, p in params}
            e_val = float(E)

            # --- 2) ∇L ---
            model.zero_grad(set_to_none=True)
            model.train()
            loss = task_ce_loss(model, proc, texts, dev)
            loss.backward()
            g = grad_dot_per_block(model, gE, params, n_layers)
            rows.append({"batch": bi, "E_mean": e_val, "CE": float(loss), **g})
            print(f"    b{bi}: E={e_val:9.2f} CE={float(loss):8.4f} | "
                  + " ".join(f"{b}={g[b]:+.4e}" for b in BLOCKS), flush=True)
            model.zero_grad(set_to_none=True)
            del out, hid, inp, gE
            torch.cuda.empty_cache()

        mean = {b: sum(r[b] for r in rows) / len(rows) for b in BLOCKS}
        sd = {b: (sum((r[b] - mean[b]) ** 2 for r in rows) / max(len(rows) - 1, 1)) ** 0.5
              for b in BLOCKS}
        signs = {b: [1 if r[b] > 0 else -1 for r in rows] for b in BLOCKS}
        per_seed[seed] = {"rows": rows, "mean": mean, "sd": sd,
                          "sign_consistent": {b: len(set(signs[b])) == 1 for b in BLOCKS},
                          "signs": signs, "n_trainable": n_tr,
                          "per_block_params": per_blk_params,
                          "elapsed_sec": round(time.time() - t0, 1)}
        print(f"  seed {seed} 均值: " + " ".join(f"{b}={mean[b]:+.4e}" for b in BLOCKS),
              flush=True)
        del model
        torch.cuda.empty_cache()

    # 跨 seed 汇总（论文 Appendix D 用的是单次测量；这里给 seed 间离散度做健壮性）
    grand = {}
    for b in BLOCKS:
        vals = [per_seed[s]["mean"][b] for s in SEEDS]
        grand[b] = {"mean": sum(vals) / len(vals), "sd_across_seeds":
                    (sum((v - sum(vals) / len(vals)) ** 2 for v in vals)
                     / max(len(vals) - 1, 1)) ** 0.5, "per_seed": vals}

    rec = {
        "script": "tools/_p432_gamma_blocks.py",
        "model": "models/Qwen2-VL-2B-Instruct",
        "dtype": "bfloat16",
        "quantization": None,
        "blocks": BLOCKS,
        "gamma_definition": "Gamma_k = sum_{theta in block k} <grad_E, grad_CE>  (inner product, paper Def. 1)",
        "E_definition": "E = mean || h_vis - h_lang ||^2, last hidden state, mean-pooled over token positions",
        "CE_definition": "cross-entropy restricted to assistant response tokens",
        "reference_rank": REFERENCE_RANK,
        "n_batch": N_BATCH, "batch_size": BATCH_SIZE, "seeds": SEEDS,
        "alpaca_source": "paper3/train-00000-of-00001-a09b74b3ef9c3b56.parquet (52002 rows)",
        "texts": all_texts,
        "per_seed": per_seed,
        "gamma_across_seeds": grand,
        "gamma_final": {b: grand[b]["mean"] for b in BLOCKS},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(rec, ensure_ascii=False, indent=1))
    print(f"\n=== 落盘 {OUT.relative_to(REPO)} ===")
    for b in BLOCKS:
        print(f"  {b:<12} Γ = {grand[b]['mean']:+.6e}  (跨 seed sd {grand[b]['sd_across_seeds']:.3e})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
