"""CLIP→Qwen zero-shot transfer validation — validates Corollary 4 (the allocation prediction)

Background: Qwen validated only C3 (no phase transition), not C4 (the Γ allocation prediction).
This experiment:
1. measure per-block Γ on Qwen2-VL (the Qwen version of modality groups)
2. exponential allocation (β using the CLIP prior 0.137)
3. Counterfactual validation (theory vs random vs violation, calling run_training_qwen.py)

Output: qwen_transfer_results.json
"""
import os, sys, json, torch, gc, subprocess, argparse
import numpy as np

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

parser = argparse.ArgumentParser()
parser.add_argument('--budget', type=int, default=64)
parser.add_argument('--seeds', type=int, default=5)
parser.add_argument('--model-path', type=str, default='/root/qwen2vl',
                    help='local Qwen2-VL directory (downloaded from ModelScope)')
args = parser.parse_args()

BETA_CLIP = 0.137  # Paper 2: the β learned by CLIP


def get_qwen_modality_groups(model, fine_grained=True):
    """Qwen2-VL parameter partition: visual / merger / llm_shallow / llm_mid / llm_deep / head.

    Qwen2-VL structure:
      model.visual           → vision tower (CLIP-ViT-like)
      model.merger           → vision-language MLP
      model.language_model   → Qwen2 LLM (28 layers for 7B)
    """
    groups = {}

    vis = [p for n, p in model.visual.named_parameters() if p.requires_grad]
    if vis:
        groups['vis'] = vis

    # Qwen2-VL: vision-language fusion is visual.patch_merger (in LLaVA it is model.merger)
    merger = [p for n, p in model.visual.patch_merger.named_parameters() if p.requires_grad]
    if merger:
        groups['merger'] = merger

    llm = model.language_model
    num_layers = len(llm.model.layers)
    if fine_grained:
        groups['llm_shallow'] = []
        groups['llm_mid'] = []
        groups['llm_deep'] = []
        for i, layer in enumerate(llm.model.layers):
            target = ('llm_shallow' if i <= num_layers // 4 else
                      'llm_mid' if i <= 3 * num_layers // 4 else
                      'llm_deep')
            for n, p in layer.named_parameters():
                if p.requires_grad:
                    groups[target].append(p)
    else:
        groups['llm'] = [p for n, p in llm.named_parameters()
                         if p.requires_grad and 'lm_head' not in n]
    # drop empty groups
    return {k: v for k, v in groups.items() if v}


def compute_gamma_qwen(model, input_ids, pixel_values, image_grid_thw,
                       vis_mask, lang_mask, label_ids, fine_grained=True):
    """Γ_k = ⟨∇_{M_k}E, u_{M_k}⟩ for Qwen2-VL (two backward passes)."""
    # Pass 1: ∇E
    outputs = model(input_ids=input_ids, pixel_values=pixel_values,
                    image_grid_thw=image_grid_thw,
                    output_hidden_states=True)
    hidden = outputs.hidden_states[-1]

    # E = mean ||h_vis - h_lang||^2 (consistent with the alignment energy of Paper 3)
    h_vis = hidden[vis_mask]
    h_lang = hidden[lang_mask]
    E = torch.mean(torch.sum((h_vis.mean(0) - h_lang.mean(0)) ** 2))
    E.backward(retain_graph=True)

    grad_E = {p: p.grad.detach().clone() for n, p in model.named_parameters()
              if p.requires_grad and p.grad is not None}
    model.zero_grad()

    # Pass 2: u = ∇L_task
    outputs = model(input_ids=input_ids, pixel_values=pixel_values,
                    image_grid_thw=image_grid_thw, labels=label_ids)
    loss = outputs.loss
    loss.backward()
    grad_u = {p: p.grad.detach().clone() for n, p in model.named_parameters()
              if p.requires_grad and p.grad is not None}
    model.zero_grad()

    # aggregate by block
    groups = get_qwen_modality_groups(model, fine_grained=fine_grained)
    gamma, norm_grad_E, norm_u, cos_phi, sign = {}, {}, {}, {}, {}
    for block, params in groups.items():
        gE = torch.cat([grad_E[p].flatten() for p in params if p in grad_E])
        u = torch.cat([grad_u[p].flatten() for p in params if p in grad_u])
        if gE.numel() == 0:
            continue
        g = float(torch.dot(gE, u))
        gamma[block] = g
        nE = float(torch.norm(gE))
        nu = float(torch.norm(u))
        norm_grad_E[block] = nE
        norm_u[block] = nu
        cos_phi[block] = g / (nE * nu) if nE * nu > 0 else 0.0
        sign[block] = '+' if g > 0 else '-'
    return {'gamma': gamma, 'norm_grad_E': norm_grad_E, 'norm_u': norm_u,
            'cos_phi': cos_phi, 'sign': sign}


def main():
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration, GPTQConfig
    import os as _os

    is_gptq = _os.path.exists(_os.path.join(args.model_path, "quantize_config.json"))
    if is_gptq:
        print("[1] Loading Qwen2-VL-7B (GPTQ 4-bit)...", flush=True)
        quant = GPTQConfig(bits=4, disable_exllama=True)
        model = Qwen2VLForConditionalGeneration.from_pretrained(
            args.model_path,
            quantization_config=quant,
            device_map="auto",
            torch_dtype=torch.float16,
        )
    else:
        print("[1] Loading Qwen2-VL-7B (float16, no quantization)...", flush=True)
        model = Qwen2VLForConditionalGeneration.from_pretrained(
            args.model_path,
            device_map="auto",
            torch_dtype=torch.float16,
        )
    processor = AutoProcessor.from_pretrained(args.model_path)

    print("[2] Computing per-block Γ...", flush=True)
    blank = torch.zeros(1, 3, 336, 336)
    prompt = "<|im_start|>user\n<|vision_start|><|image_pad|><|vision_end|>What is shown?\n<|im_end|>\n<|im_start|>assistant\n"
    text = [processor.apply_chat_template(
        [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": "What is shown?"}]}],
        tokenize=False, add_generation_prompt=True)]
    inputs = processor(text=text, images=blank, return_tensors="pt")
    input_ids = inputs['input_ids'].to(model.device)
    pixel_values = inputs['pixel_values'].to(model.device, dtype=torch.float16)
    image_grid_thw = inputs['image_grid_thw'].to(model.device)

    # vis/lang masks: <|image_pad|> positions
    pad_id = processor.tokenizer.convert_tokens_to_ids("<|image_pad|>")
    vis_mask = (input_ids == pad_id)
    lang_mask = (input_ids != pad_id) & (input_ids != processor.tokenizer.pad_token_id)
    label_ids = input_ids.clone()

    result = compute_gamma_qwen(model, input_ids, pixel_values, image_grid_thw,
                                vis_mask, lang_mask, label_ids, fine_grained=True)
    g = result['gamma']
    print(f"  Γ per block: { {k: round(v,4) for k,v in g.items()} }")

    print("[3] Exponential allocation (β from CLIP = 0.137)...", flush=True)
    abs_g = {k: abs(v) for k, v in g.items()}
    denom = sum(np.exp(-BETA_CLIP * v) for v in abs_g.values())
    allocation = {k: args.budget * np.exp(-BETA_CLIP * v) / denom
                  for k, v in abs_g.items()}
    print(f"  Allocation: { {k: round(v,1) for k,v in allocation.items()} }")

    print("[4] Counterfactual: run_training_qwen.py must be run separately", flush=True)
    # theory rank = the smallest rank in the allocation (or r=4 as predicted by CLIP)
    theory_rank = min(allocation.values())
    counterfactual = {
        "theory_rank": round(theory_rank),
        "random_ranks": [4, 16, 32, 64],
        "violation_ranks": [16, 32],
        "commands": [
            "python scripts/run_training_qwen.py --rank 4 --epochs 3 --seed 42   # theory",
            "python scripts/run_training_qwen.py --rank 16 --epochs 3 --seed 42  # violation",
            "python scripts/run_training_qwen.py --rank 32 --epochs 3 --seed 42  # violation",
        ],
        "note": "run 3 seeds per rank (42/123/456), collect E(t) then compute ΔE",
    }

    out = {
        "gamma_per_block": {k: float(v) for k, v in g.items()},
        "norm_grad_E": result['norm_grad_E'],
        "cos_phi": result['cos_phi'],
        "allocation": {k: float(v) for k, v in allocation.items()},
        "counterfactual": counterfactual,
        "config": {"budget": args.budget, "seeds": args.seeds,
                   "beta_source": "CLIP", "beta": BETA_CLIP},
    }
    with open("qwen_transfer_results.json", 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print("Saved: qwen_transfer_results.json")


if __name__ == '__main__':
    main()
