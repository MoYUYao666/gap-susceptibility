"""Γ measurement cost probe (limitation 10: absolute cost of >7B).

The paper's Γ needs one full-model backward pass at the initialization point (no Hessian). This script measures on a single machine:
  - model load time and VRAM after loading;
  - wall-clock and peak VRAM of a single E forward pass and a single E backward pass (one of the two passes a Γ estimate needs);
  - the cost of one training step (loss forward + backward), as the ratio "Γ measurement vs one training step".
Supports LLaVA and Qwen2-VL (4-bit QLoRA loading, same quantization config as the training scripts),
and adapts to transformers 4.x/5.x (Qwen needs mm_token_type_ids on 5.x).

Usage (cloud):
  python tools/gamma_cost_probe.py --arch qwen  --model-path /root/Qwen2-VL-7B-Instruct --n-samples 4
  python tools/gamma_cost_probe.py --arch llava --model-path /root/llava-1.5-7b-hf     --n-samples 4
Output: outputs/gamma_cost_<arch>_<basename>.json
"""
import argparse
import json
import os
import time

os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')

import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402


def build_batch(arch, processor, seed=42, size=336):
    """Same input as the training scripts: blank/noise image + one instruction; returns (batch_dict, img_tok_id)."""
    rng = np.random.RandomState(seed)
    img = Image.fromarray(rng.randint(0, 255, (size, size, 3), dtype=np.uint8))
    if arch == 'llava':
        text = "USER: Describe this image.\nASSISTANT: a photo."
        toks = processor.tokenizer(text, return_tensors='pt', max_length=1024, truncation=True)
        pv = processor.image_processor(img, return_tensors='pt')['pixel_values']
        img_tok = processor.tokenizer.convert_tokens_to_ids('<image>')
        if img_tok is None or img_tok < 0:
            img_tok = 32000
        img_tokens = torch.full((1, 576), img_tok, dtype=torch.long)
        input_ids = torch.cat([img_tokens, toks['input_ids'][:, 1:]], dim=1)
        att = torch.cat([torch.ones(1, 576, dtype=torch.long), toks['attention_mask'][:, 1:]], dim=1)
        return ({'input_ids': input_ids, 'attention_mask': att, 'pixel_values': pv}, img_tok, 576)
    # qwen
    messages = [{"role": "user", "content": [{"type": "image", "image": img},
                                             {"type": "text", "text": "Describe this image."}]},
                {"role": "assistant", "content": [{"type": "text", "text": "a photo."}]}]
    text = processor.apply_chat_template(messages, add_generation_prompt=False)
    proc = processor(text=[text], images=[img], return_tensors='pt', max_length=1024)
    b = {'input_ids': proc['input_ids'], 'attention_mask': proc['attention_mask'],
         'pixel_values': proc['pixel_values'], 'image_grid_thw': proc['image_grid_thw']}
    mm = proc.get('mm_token_type_ids', None)
    if mm is not None:
        b['mm_token_type_ids'] = mm
    return b, int(proc['input_ids'][0][proc['input_ids'][0] != proc['input_ids'][0][0]].max()), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arch', choices=['llava', 'qwen'], required=True)
    ap.add_argument('--model-path', required=True)
    ap.add_argument('--n-samples', type=int, default=4, help='number of eval samples averaged for the Γ E (the reference protocol uses 4 eval samples)')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    from transformers import (AutoProcessor, AutoTokenizer, BitsAndBytesConfig,
                              LlavaForConditionalGeneration, Qwen2VLForConditionalGeneration)
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                               bnb_4bit_use_double_quant=True)
    cls = LlavaForConditionalGeneration if args.arch == 'llava' else Qwen2VLForConditionalGeneration

    t0 = time.time()
    model = cls.from_pretrained(args.model_path, quantization_config=quant, device_map='auto')
    load_s = time.time() - t0
    processor = (AutoProcessor if args.arch == 'qwen' else AutoProcessor).from_pretrained(args.model_path)
    model.eval()
    vram_loaded = torch.cuda.memory_allocated() / 1e9
    torch.cuda.reset_peak_memory_stats()

    b, img_tok, _ = build_batch(args.arch, processor)
    # 4-bit base model: open the gradient path only for trainable/float parameters (does E need second order? No -- first order suffices)
    for p in model.parameters():
        if p.is_floating_point():
            p.requires_grad = True

    def e_measure():
        out = model(**{k: v.cuda() for k, v in b.items()}, output_hidden_states=True)
        h = out.hidden_states[-1][0]
        ids = b['input_ids'][0].cuda()
        v = ids == img_tok
        pad = processor.tokenizer.pad_token_id
        l = (~v) & (ids != pad)
        hv, hl = h[v].mean(0), h[l].mean(0)
        return ((hv - hl) ** 2).mean()

    # warm up once (to exclude first-time kernel compilation)
    try:
        e_measure()
    except Exception as ex:  # noqa: BLE001
        print('warmup failed:', repr(ex))
    torch.cuda.synchronize(); t1 = time.time()
    vals = []
    for i in range(max(1, args.n_samples)):
        vals.append(float(e_measure().item()))
    torch.cuda.synchronize()
    fwd_s = (time.time() - t1) / max(1, args.n_samples)

    model.zero_grad()
    torch.cuda.synchronize(); t2 = time.time()
    val = e_measure()
    val.backward()
    torch.cuda.synchronize()
    bwd_s = time.time() - t2
    peak_gamma = torch.cuda.max_memory_allocated() / 1e9

    # one training step (loss forward + backward) as the comparison
    labels = b['input_ids'].clone()
    labels[labels == processor.tokenizer.pad_token_id] = -100
    model.zero_grad()
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize(); t3 = time.time()
    out = model(**{k: v.cuda() for k, v in b.items()}, labels=labels.cuda())
    out.loss.backward()
    torch.cuda.synchronize()
    step_s = time.time() - t3
    peak_step = torch.cuda.max_memory_allocated() / 1e9

    res = {'arch': args.arch, 'model_path': args.model_path,
           'n_trainable_float_params': int(sum(p.numel() for p in model.parameters() if p.requires_grad)),
           'load_seconds': round(load_s, 1), 'vram_after_load_gb': round(vram_loaded, 2),
           'E_value': round(float(np.mean(vals)), 3),
           'gamma_forward_seconds': round(fwd_s, 3), 'gamma_backward_seconds': round(bwd_s, 3),
           'gamma_total_seconds': round(fwd_s + bwd_s, 3), 'gamma_peak_vram_gb': round(peak_gamma, 2),
           'train_step_seconds': round(step_s, 3), 'train_step_peak_vram_gb': round(peak_step, 2),
           'gamma_over_train_step_time': round((fwd_s + bwd_s) / max(step_s, 1e-6), 3),
           'gpu': torch.cuda.get_device_name(0), 'torch': torch.__version__,
           'transformers': __import__('transformers').__version__}
    out_path = args.out or os.path.join('outputs', 'gamma_cost_%s_%s.json'
                                        % (args.arch, os.path.basename(args.model_path.rstrip('/\\'))))
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    json.dump(res, open(out_path, 'w', encoding='utf-8'), indent=1)
    print(json.dumps(res, indent=1))
    print('DONE ->', out_path, flush=True)


if __name__ == '__main__':
    main()
