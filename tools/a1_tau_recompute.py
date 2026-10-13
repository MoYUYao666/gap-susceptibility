"""Recompute τ for all class-aligned checkpoints (τ only; 50k/val_loss untouched).

Background: the S0 in frozen_refs.pt no longer matches the sub_indices images in the current
data/imagenet_hf, so all τ from the 2026-09-14 batch were noise (even a zero-LoRA-delta base
model gave τ=−0.087). Recomputed with the fixed reference, written to tau_recomputed_ep{N}.json.

Usage:
  python tools/a1_tau_recompute.py                 # use the sub_indices bundled in the cache
  python tools/a1_tau_recompute.py --remap         # use sub_indices_orig_order.json (restore row order)
  python tools/a1_tau_recompute.py --only 0,123    # run only the listed seeds
"""
import os
import sys
import json
import glob
import argparse
import importlib.util

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
from transformers import CLIPModel, CLIPProcessor
from datasets import Dataset as HFDataset
from src.lora import apply_lora_to_model

SAVE_ROOT = 'outputs/a1_class_aligned'
N_TAU = 5000

ap = argparse.ArgumentParser()
ap.add_argument('--remap', action='store_true', help='index from sub_indices_orig_order.json')
ap.add_argument('--only', type=str, default='', help='comma-separated seed whitelist')
ap.add_argument('--lam', type=str, default='', help='comma-separated λ whitelist')
ap.add_argument('--epochs', type=str, default='10', help='comma-separated epochs; seed42/λ=0 additionally auto-adds 1,2,3,5')
args = ap.parse_args()

ck0 = torch.load(os.path.join(SAVE_ROOT, 'frozen_refs.pt'), weights_only=False)
tf = ck0['tf'].cuda()
S0 = ck0['S0']
topk5 = ck0['topk5']
sub_indices = list(ck0['sub_indices'])
src = 'cache'
if args.remap:
    rp = os.path.join(SAVE_ROOT, 'sub_indices_orig_order.json')
    with open(rp) as f:
        sub_indices = json.load(f)['sub_indices']
    src = rp
print('sub_indices source: %s (n=%d)' % (src, len(sub_indices)), flush=True)

parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
ds_in = HFDataset.from_parquet(parq)
sub = ds_in.select(sub_indices)
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32',
                                          local_files_only=True)

# Pre-decode 5000 images (reused by every checkpoint, same path as the factory compute_tau)
print('Pre-decoding %d images ...' % N_TAU, flush=True)
try:
    px = []
    for i in range(0, N_TAU, 64):
        px.append(processor(images=sub[i:i + 64]['image'],
                            return_tensors='pt')['pixel_values'])
    print('  cached in memory (%.2f GB)' % (sum(p.numel() for p in px) * 4 / 2 ** 30), flush=True)
except MemoryError:
    px = None
    print('  out of memory, falling back to per-checkpoint re-decoding', flush=True)


def tau_only(model):
    imgs = []
    with torch.no_grad():
        if px is not None:
            for p in px:
                vout = model.vision_model(pixel_values=p.cuda())
                vpool = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                imgs.append(F.normalize(model.visual_projection(vpool), dim=-1))
        else:
            for i in range(0, N_TAU, 64):
                inp = processor(images=sub[i:i + 64]['image'],
                                return_tensors='pt').to('cuda')
                vout = model.vision_model(**inp)
                vpool = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                imgs.append(F.normalize(model.visual_projection(vpool), dim=-1))
        cur = torch.cat(imgs)
    Sc = (cur @ tf.T).float().cpu().numpy()
    per = []
    for i in range(N_TAU):
        k5 = topk5[i]
        r1, r2 = S0[i][k5], Sc[i][k5]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            per.append(t)
    return float(np.mean(per)), float(np.std(per)), len(per)


lam_wl = set(args.lam.split(',')) if args.lam else None
seed_wl = set(args.only.split(',')) if args.only else None
summary = []
dose = [(0.0, 42), (0.05, 42), (0.1, 42), (0.25, 42), (0.5, 42), (1.0, 42),
        (0.0, 123), (0.1, 123), (0.5, 123), (1.0, 123),
        (0.0, 456), (0.1, 456), (0.5, 456), (1.0, 456)]
for lam, seed in dose:
    if seed_wl and str(seed) not in seed_wl:
        continue
    if lam_wl and ('%g' % lam) not in lam_wl:
        continue
    eps = [10]
    if lam == 0.0 and seed == 42:
        eps = [1, 2, 3, 5, 10]
    for ep in eps:
        d = os.path.join(SAVE_ROOT, 'lr%s' % lam, 'seed%d' % seed)
        cp = os.path.join(d, 'epoch%d.pt' % ep)
        out_p = os.path.join(d, 'tau_recomputed_ep%d.json' % ep)
        if os.path.exists(out_p):
            print('  τ result already exists, skipping %s' % out_p, flush=True)
            continue
        if not os.path.exists(cp):
            print('  skipping (no weights) %s' % cp, flush=True)
            continue
        m = CLIPModel.from_pretrained('openai/clip-vit-base-patch32',
                                      local_files_only=True)
        m, layers, _ = apply_lora_to_model(m, rank=8, alpha=16.0,
                                           apply_to_vision=True, apply_to_text=True)
        m = m.cuda()
        sd = torch.load(cp, weights_only=False)['lora_state_dict']
        for k, v in layers.items():
            v.lora_A.data.copy_(sd[k]['A'].to(v.lora_A.device, v.lora_A.dtype))
            v.lora_B.data.copy_(sd[k]['B'].to(v.lora_B.device, v.lora_B.dtype))
        m.eval()
        mean, sdv, n = tau_only(m)
        rec = {'lambda_reg': lam, 'seed': seed, 'epoch': ep,
               'tau_final': mean, 'tau_sd_across_samples': sdv, 'n_samples': n,
               'sub_indices_source': src}
        with open(out_p, 'w', encoding='utf-8') as f:
            json.dump(rec, f, indent=1, ensure_ascii=False)
        summary.append(rec)
        print('λ=%-5g seed=%-4d ep=%-2d  τ=%.4f  (per-sample sd=%.4f, n=%d)'
              % (lam, seed, ep, mean, sdv, n), flush=True)
        del m
        torch.cuda.empty_cache()

with open(os.path.join(SAVE_ROOT, 'tau_recomputed_summary.json'), 'w',
          encoding='utf-8') as f:
    json.dump({'sub_indices_source': src, 'records': summary}, f,
              indent=1, ensure_ascii=False)
print()
print('wrote %s/tau_recomputed_summary.json (%d records)' % (SAVE_ROOT, len(summary)))
