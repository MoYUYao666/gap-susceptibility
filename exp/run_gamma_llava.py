"""Gamma per-block measurement — restore Paper 3 appendix Gamma table (real values)

Usage: python exp/run_gamma_llava.py --ranks 4,8,16,32,64 --batches 3 --model-path /path/to/llava-hf
Output: gamma_llava_results.json

Inputs built like run_training.py: 576 image tokens + text tokens (manual concat).
"""
import os, sys, json, torch, gc, argparse
import numpy as np
from PIL import Image

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from compute_gamma_llava import compute_gamma_llava

parser = argparse.ArgumentParser()
parser.add_argument('--rank', type=int, default=8, help='single rank (--ranks takes priority)')
parser.add_argument('--ranks', type=str, default=None,
                    help='multiple ranks comma-separated, e.g. 4,8,16,32,64 (recommended)')
parser.add_argument('--batches', type=int, default=3,
                    help='average over N batches to reduce gradient noise (3-5 recommended)')
parser.add_argument('--num-samples', type=int, default=4)
parser.add_argument('--output', type=str, default='gamma_llava_results.json')
parser.add_argument('--model-path', type=str, default=None,
                    help='local model dir (recommended); online if not set')
args = parser.parse_args()

def log(msg): print(msg, flush=True)

PROMPTS = [
    'USER: What is shown in this image?\nASSISTANT:',
    'USER: Describe this image.\nASSISTANT:',
    'USER: What can you see?\nASSISTANT:',
    'USER: Is there anything interesting?\nASSISTANT:',
    'USER: What colors are present?\nASSISTANT:',
]

def run_one(model, processor, pixel_vals, img_tok_id, rank, n_batches):
    """Gamma for one rank, averaged over n_batches."""
    from peft import LoraConfig, get_peft_model, TaskType
    peft_cfg = LoraConfig(r=rank, lora_alpha=rank * 2,
                          target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'],
                          lora_dropout=0.1, bias='none', task_type=TaskType.CAUSAL_LM)
    model_lora = get_peft_model(model, peft_cfg)

    gamma_sum, gE_sum, gu_sum, cos_sum = {}, {}, {}, {}
    E_val, CE_val = 0.0, 0.0
    for bi in range(n_batches):
        text = PROMPTS[bi % len(PROMPTS)]
        toks = processor.tokenizer(text, return_tensors='pt', max_length=1024, truncation=True)
        img_tokens = torch.full((1, 576), img_tok_id, dtype=torch.long)
        input_ids = torch.cat([img_tokens, toks['input_ids'][:, 1:]], dim=1).to(model.device)
        vis_mask = torch.zeros_like(input_ids, dtype=torch.bool)
        vis_mask[:, :576] = True
        lang_mask = torch.ones_like(input_ids, dtype=torch.bool)
        lang_mask[:, :576] = False
        lang_mask = lang_mask & (input_ids != processor.tokenizer.pad_token_id)
        label_ids = input_ids.clone()

        result = compute_gamma_llava(
            model_lora, input_ids, pixel_vals, vis_mask, lang_mask, label_ids,
            fine_grained=True,
        )
        for k, v in result['gamma'].items():
            gamma_sum[k] = gamma_sum.get(k, 0.0) + v
            gE_sum[k] = gE_sum.get(k, 0.0) + result['norm_grad_E'][k]
            gu_sum[k] = gu_sum.get(k, 0.0) + result['norm_u'][k]
            cos_sum[k] = cos_sum.get(k, 0.0) + result['cos_phi'][k]
        E_val += result.get('E', 0.0)
        CE_val += result.get('CE_loss', 0.0)
        log(f'    batch {bi + 1}/{n_batches} done')

    n = n_batches
    gamma = {k: v / n for k, v in gamma_sum.items()}
    gE = {k: v / n for k, v in gE_sum.items()}
    gu = {k: v / n for k, v in gu_sum.items()}
    cos = {k: v / n for k, v in cos_sum.items()}
    return {
        'per_block': gamma,
        'norm_grad_E': gE,
        'norm_u': gu,
        'cos_phi': cos,
        'sign': {k: ('+' if v > 0 else '-') for k, v in gamma.items()},
        'E_mean': E_val / n,
        'CE_loss_mean': CE_val / n,
    }


def main():
    from transformers import AutoProcessor, LlavaForConditionalGeneration, BitsAndBytesConfig

    if args.ranks:
        ranks = [int(r) for r in args.ranks.split(',')]
    else:
        ranks = [args.rank]

    log('[1] Loading LLaVA-1.5-7B (4-bit)...')
    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model_path = args.model_path or 'llava-hf/llava-1.5-7b-hf'
    model = LlavaForConditionalGeneration.from_pretrained(
        model_path,
        quantization_config=quant,
        device_map='auto',
        torch_dtype=torch.float16,
        _fast_init=False,
    )
    processor = AutoProcessor.from_pretrained(model_path, use_fast=False)
    processor.patch_size = 14
    processor.image_processor.patch_size = 14
    log(f'  Model loaded. VRAM: {torch.cuda.memory_allocated() / 1e9:.1f} GB')

    blank_img = Image.fromarray(np.zeros((336, 336, 3), dtype=np.uint8))
    pixel_vals = processor.image_processor(blank_img, return_tensors='pt')['pixel_values']
    pixel_vals = pixel_vals.to(model.device, dtype=torch.float16)
    img_tok_id = model.config.image_token_index
    if not isinstance(img_tok_id, int):
        img_tok_id = img_tok_id.item()

    all_results = {}
    for rank in ranks:
        log(f'\n[rank {rank}] Computing Gamma ({args.batches} batches avg)...')
        result = run_one(model, processor, pixel_vals, img_tok_id, rank, args.batches)
        all_results[f'r{rank}'] = result
        log(f'  Gamma: { {k: round(v, 2) for k, v in result["per_block"].items()} }')

    out = {
        'results_by_rank': all_results,
        'config': {'ranks': ranks, 'batches': args.batches, 'model': model_path},
    }
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    log(f'\nSaved: {args.output}')


if __name__ == '__main__':
    main()
