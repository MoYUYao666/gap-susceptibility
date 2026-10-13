"""(A3) Cross-batch Γ estimation: hierarchical bootstrap (batch × within-batch) gives batch-level confidence intervals and allocation stability for the per-block |Γ|.

Background (limitation 9 in the paper): the existing bootstrap resamples only within a single batch and cannot reflect cross-batch variation.
This script measures the per-block Γ once for each of the N independent sample windows (BATCH_START ∈ {0,16,32,48,64,80}),
with a protocol **fully identical** to the published clip_llava_granularity_bootstrap_v2.py (same template, same E/L definition,
same prefix-aware bucketing, full parametrization), so it can be compared directly with outputs/llava_granularity_bootstrap_v2*.json.

Output:
  1) per-block cross-batch mean / std / 95% t-CI / CV;
  2) hierarchical bootstrap (resample batches first, then resample samples within a batch) → hierarchical 95% CI of |Γ| per block;
  3) ordering stability: block order per batch, argmax/argmin frequency, cross-batch Spearman;
  4) allocation stability: beta*=1/sigma(|Γ|) exponential shares → rank vectors with the same budget as the paper, and their bootstrap agreement rate
     (including the per-parameter-count normalized variant).
Output: outputs/llava_gamma_batches.json
"""
import os
import sys
import json
import glob

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import numpy as np
import torch
from PIL import Image
from scipy import stats
from collections import defaultdict, Counter
from transformers import LlavaForConditionalGeneration, AutoProcessor, AutoTokenizer, BitsAndBytesConfig

MDIR = 'models/llava-hf'
OUT = 'outputs/llava_gamma_batches.json'
STARTS = [0, 16, 32, 48, 64, 80]
N_PER_BATCH = 16
IMGS = sorted(glob.glob('data/marinelife16k/_small/*.jpg'))
Q = 'What is in the image? Answer with one word.'
ANS = 'a fish.'

BLOCKS = ['vis', 'proj', 'llm_shallow', 'llm_mid', 'llm_deep', 'llm_other', 'lm_head']
ALLOC_BLOCKS = ['llm_shallow', 'llm_mid', 'llm_deep']
LAYERS_PER_BLOCK = {'llm_shallow': 8, 'llm_mid': 16, 'llm_deep': 8}
BUDGET_RANKLAYERS = 136  # same budget as the paper's exp/beta* strategy

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
                         bnb_4bit_quant_type='nf4', bnb_4bit_use_double_quant=True)
m = LlavaForConditionalGeneration.from_pretrained(MDIR, torch_dtype=torch.bfloat16,
                                                  quantization_config=bnb, device_map='cuda')
proc = AutoProcessor.from_pretrained(MDIR)
tok = AutoTokenizer.from_pretrained(MDIR)
m.eval()
par = dict(m.named_parameters())
for p in m.parameters():
    if p.is_floating_point():
        p.requires_grad = True
IMGID = proc.tokenizer.convert_tokens_to_ids('<image>')
if IMGID is None or IMGID < 0:
    IMGID = m.config.image_token_index


def blk_of(name):
    if name.startswith('model.vision_tower.'):
        return 'vis'
    if name.startswith('model.multi_modal_projector.'):
        return 'proj'
    if name.startswith('model.language_model.embed_tokens') or name.startswith('model.language_model.norm'):
        return 'llm_other'
    if name.startswith('lm_head'):
        return 'lm_head'
    if name.startswith('model.language_model.layers.'):
        for seg in name.split('.'):
            if seg.isdigit():
                li = int(seg)
                return 'llm_shallow' if li < 8 else ('llm_mid' if li < 24 else 'llm_deep')
    return 'llm_other'


BLK = {n: blk_of(n) for n in par}


def pos_feats(h, idsb):
    vis = idsb == IMGID
    lang = (idsb != IMGID) & (idsb != tok.pad_token_id)
    return h[vis].mean(0), h[lang].mean(0)


def E_of(idsb, maskb, pvb):
    out = m(pixel_values=pvb, input_ids=idsb, attention_mask=maskb, output_hidden_states=True)
    h = out.hidden_states[-1].float()[0]
    vf, lf = pos_feats(h, idsb[0])
    return ((vf - lf) ** 2).mean()


def L_of(idsb, maskb, pvb):
    labels = idsb.clone()
    labels[labels == tok.pad_token_id] = -100
    return m(pixel_values=pvb, input_ids=idsb, attention_mask=maskb, labels=labels).loss


def main():
    batches = {}
    for start in STARTS:
        files = IMGS[start:start + N_PER_BATCH]
        if len(files) < 8:
            print('skip start=%d (only %d images)' % (start, len(files)), flush=True)
            continue
        imgs = [Image.open(p).convert('RGB') for p in files]
        tpl = [proc.apply_chat_template(
            [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': Q}]},
             {'role': 'assistant', 'content': [{'type': 'text', 'text': ANS}]}],
            add_generation_prompt=False, tokenize=False) for _ in imgs]
        enc = proc(text=tpl, images=imgs, return_tensors='pt')
        ids = enc['input_ids'].cuda()
        mask = enc['attention_mask'].cuda()
        pv = enc['pixel_values'].cuda()
        per = []
        for b in range(len(imgs)):
            ids1, mask1, pv1 = ids[b:b + 1], mask[b:b + 1], pv[b:b + 1]
            m.zero_grad()
            e_val = E_of(ids1, mask1, pv1)
            e_val.backward()
            gE = {n: (p.grad.detach().clone() if p.grad is not None else None) for n, p in par.items()}
            m.zero_grad()
            l_val = L_of(ids1, mask1, pv1)
            l_val.backward()
            gb = defaultdict(float)
            for n, p in par.items():
                if p.grad is None or gE.get(n) is None:
                    continue
                gb[BLK[n]] += float((p.grad.detach() * gE[n]).sum())
            m.zero_grad()
            per.append(dict(gb))
            del gE, gb
        batches[str(start)] = per
        del ids, mask, pv, enc
        torch.cuda.empty_cache()
        means = {b: float(np.mean([s.get(b, 0.0) for s in per])) for b in BLOCKS}
        print('[batch %d] means=%s' % (start, {k: round(v, 1) for k, v in means.items()}), flush=True)

    keys = list(batches)
    nb = len(keys)
    if nb < 2:
        print('need >=2 batches'); sys.exit(1)
    arr = {b: np.array([np.mean([s.get(b, 0.0) for s in batches[k]]) for k in keys]) for b in BLOCKS}
    per_block = {}
    for b in BLOCKS:
        x = arr[b]
        ci = stats.t.interval(0.95, nb - 1, loc=x.mean(), scale=stats.sem(x))
        per_block[b] = {'mean': round(float(x.mean()), 2),
                        'std': round(float(x.std(ddof=1)), 2),
                        'ci95': [round(float(ci[0]), 2), round(float(ci[1]), 2)],
                        'cv_pct': round(float(100 * x.std(ddof=1) / abs(x.mean())), 1) if x.mean() else None}

    rng = np.random.RandomState(0)
    boot = defaultdict(list)
    orders = Counter()
    alloc_boot = Counter()

    def alloc_from(g):
        vals = np.array([abs(g[b]) for b in ALLOC_BLOCKS], dtype=float)
        vals_n = np.array([abs(g[b]) / LAYERS_PER_BLOCK[b] for b in ALLOC_BLOCKS], dtype=float)
        out = {}
        for tag, v in (('raw', vals), ('param_normalized', vals_n)):
            sigma = v.std()
            beta = 1.0 / sigma if sigma > 0 else 0.0
            share = np.exp(-beta * v)
            share = share / share.sum()
            rl = share * BUDGET_RANKLAYERS
            out[tag] = [int(max(1, round(x))) for x in rl]
        return out

    for _ in range(2000):
        bk = [keys[i] for i in rng.randint(0, nb, nb)]
        val = {}
        for b in BLOCKS:
            acc = []
            for k in bk:
                per = batches[k]
                idx = rng.randint(0, len(per), len(per))
                acc.append(np.mean([per[i].get(b, 0.0) for i in idx]))
            val[b] = float(np.mean(acc))
        for b in BLOCKS:
            boot[b].append(val[b])
        orders[tuple(sorted(BLOCKS, key=lambda x: -abs(val[x])))] += 1
        a = alloc_from(val)
        alloc_boot[(tuple(a['raw']), tuple(a['param_normalized']))] += 1

    hier = {b: {'mean': round(float(np.mean(boot[b])), 2),
                'ci95': [round(float(np.percentile(boot[b], 2.5)), 2),
                         round(float(np.percentile(boot[b], 97.5)), 2)]} for b in BLOCKS}
    order_per_batch = {k: sorted(BLOCKS, key=lambda b: -abs(np.mean([s.get(b, 0.0) for s in batches[k]])))
                       for k in keys}
    spear = {}
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1:]:
            v1 = [abs(np.mean([s.get(b, 0.0) for s in batches[k1]])) for b in BLOCKS]
            v2 = [abs(np.mean([s.get(b, 0.0) for s in batches[k2]])) for b in BLOCKS]
            rho, _ = stats.spearmanr(v1, v2)
            spear['%s_vs_%s' % (k1, k2)] = round(float(rho), 3)
    allocs = {k: alloc_from({b: np.mean([s.get(b, 0.0) for s in batches[k]]) for b in BLOCKS}) for k in keys}

    res = {'n_batches': nb, 'batches': keys, 'n_per_batch': N_PER_BATCH, 'blocks': BLOCKS,
           'protocol': 'vis_mean_lang_mean, full-parameterization, prefix-aware v2 (same as granularity v2)',
           'block_cross_batch': per_block, 'block_hierarchical_bootstrap': hier,
           'order_per_batch': order_per_batch,
           'argmax_freq': {b: round(sum(1 for k in keys if order_per_batch[k][0] == b) / nb, 3) for b in BLOCKS},
           'argmin_freq': {b: round(sum(1 for k in keys if order_per_batch[k][-1] == b) / nb, 3) for b in BLOCKS},
           'pairwise_spearman': spear, 'alloc_blocks': ALLOC_BLOCKS,
           'alloc_budget_rank_layers': BUDGET_RANKLAYERS, 'alloc_per_batch': allocs,
           'alloc_bootstrap_top': [{'alloc_raw': list(k[0]), 'alloc_param_normalized': list(k[1]),
                                    'freq': round(v / 2000, 3)} for k, v in alloc_boot.most_common(5)],
           'raw_per_sample_blocks': {k: [{b: round(v, 3) for b, v in s.items()} for s in batches[k]] for k in keys}}
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print(json.dumps({'block_cross_batch': per_block, 'argmax_freq': res['argmax_freq'],
                      'alloc_per_batch': allocs, 'alloc_bootstrap_top': res['alloc_bootstrap_top']},
                     indent=1), flush=True)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
