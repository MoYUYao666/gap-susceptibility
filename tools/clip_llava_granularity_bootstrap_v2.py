"""(fixed v2) Prefix-aware layer granularity + bootstrap + E-n (decoder).
Fix: in transformers 5.x top-level parameters carry the 'model.' prefix and vision/proj share the
same 'layers.N' names as the LLM layers
→ the old version's startswith did not match + bucketed by number. This version: exact prefix attribution.
Bucketing (canonical): vis | proj | llm_shallow(0-7) | llm_mid(8-23) | llm_deep(24-31) | llm_other(embed/norm) | lm_head
Output: outputs/llava_granularity_bootstrap_v2.json
"""
import os, sys, json, glob
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
from PIL import Image
from scipy import stats
from collections import defaultdict, Counter
from transformers import LlavaForConditionalGeneration, AutoProcessor, BitsAndBytesConfig, AutoTokenizer

MDIR = 'models/llava-hf'
BATCH_START = int(sys.argv[1]) if len(sys.argv) > 1 else 0
DATA = sorted(glob.glob('data/marinelife16k/_small/*.jpg'))[BATCH_START:BATCH_START + 16]
OUT = 'outputs/llava_granularity_bootstrap_v2_b%d.json' % BATCH_START
if len(DATA) < 8:
    print('not enough images:', len(DATA)); sys.exit(1)

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
                         bnb_4bit_quant_type='nf4', bnb_4bit_use_double_quant=True)
m = LlavaForConditionalGeneration.from_pretrained(MDIR, torch_dtype=torch.bfloat16,
                                                  quantization_config=bnb, device_map='cuda')
proc = AutoProcessor.from_pretrained(MDIR)
tok = AutoTokenizer.from_pretrained(MDIR)
lm = getattr(m, 'language_model', getattr(m, 'model', None))
m.eval()
par = dict(m.named_parameters())
for p in m.parameters():
    if p.is_floating_point():
        p.requires_grad = True

IMGID = proc.tokenizer.convert_tokens_to_ids('<image>')
if IMGID is None or IMGID < 0:
    IMGID = m.config.image_token_index


def blk_of(name):
    """prefix-aware bucketing (fixed)"""
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


def llm_layer_of(name):
    if name.startswith('model.language_model.layers.'):
        for seg in name.split('.'):
            if seg.isdigit():
                return int(seg)
    return None


BLK = {n: blk_of(n) for n in par}
LAYER = {n: llm_layer_of(n) for n in par}

imgs = [Image.open(p) for p in DATA]
q = 'What is in the image? Answer with one word.'
tpl = [proc.apply_chat_template(
    [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': q}]},
     {'role': 'assistant', 'content': [{'type': 'text', 'text': 'a fish.'}]}],
    add_generation_prompt=False, tokenize=False) for _ in imgs]
enc = proc(text=tpl, images=imgs, return_tensors='pt')
ids = enc['input_ids'].to('cuda')
mask = enc['attention_mask'].to('cuda')
pv = enc['pixel_values'].to('cuda')


def pos_feats(h, idsb, mode='vis_mean_lang_mean'):
    vis = idsb == IMGID
    lang = (idsb != IMGID) & (idsb != tok.pad_token_id)
    v = h[vis]
    l = h[lang]
    return v.mean(0), l.mean(0)


def E_of(idsb, maskb, pvb):
    out = m(pixel_values=pvb, input_ids=idsb, attention_mask=maskb, output_hidden_states=True)
    h = out.hidden_states[-1].float()[0]
    vf, lf = pos_feats(h, idsb[0])
    return ((vf - lf) ** 2).mean()


def L_of(idsb, maskb, pvb):
    labels = idsb.clone()
    labels[labels == tok.pad_token_id] = -100
    out = m(pixel_values=pvb, input_ids=idsb, attention_mask=maskb, labels=labels)
    return out.loss


per_sample = []
layer_sum = {}
for b in range(len(imgs)):
    ids1 = ids[b:b + 1]
    mask1 = mask[b:b + 1]
    pv1 = pv[b:b + 1]
    m.zero_grad()
    e_val = E_of(ids1, mask1, pv1)
    e_val.backward()
    gE = {nm: (prm.grad.detach().clone() if prm.grad is not None else None) for nm, prm in par.items()}
    m.zero_grad()
    l_val = L_of(ids1, mask1, pv1)
    l_val.backward()
    gb = {}
    gl = {}
    for nm, prm in par.items():
        if prm.grad is None or gE.get(nm) is None:
            continue
        dot = float((prm.grad.detach() * gE[nm]).sum())
        gb[BLK[nm]] = gb.get(BLK[nm], 0.0) + dot
        li = LAYER[nm]
        if li is not None:
            gl[li] = gl.get(li, 0.0) + dot
    m.zero_grad()
    per_sample.append({'E': float(e_val.item()), 'blocks': gb, 'layers': gl})
    for li, v in gl.items():
        layer_sum[li] = layer_sum.get(li, 0.0) + v / len(imgs)
    del gE, gb, gl


def order_of(gd):
    return [k for k in sorted(gd, key=lambda k: -abs(gd[k]))]


blk_mean = {}
for k in set(k for s in per_sample for k in s['blocks']):
    blk_mean[k] = sum(s['blocks'].get(k, 0.0) for s in per_sample) / len(per_sample)

es = np.array([s['E'] for s in per_sample])
e_n = {str(n): {'mean': round(float(es[:n].mean()), 3), 'std': round(float(es[:n].std()), 3)} for n in (4, 8, 16)}

rng = np.random.RandomState(7)
full_keys = list(blk_mean)
base = [blk_mean[k] for k in full_keys]
boot_orders = []
rho_b = []
for _ in range(500):
    idx = rng.randint(0, len(per_sample), size=len(per_sample))
    gv = {}
    for i in idx:
        for k, v in per_sample[i]['blocks'].items():
            gv[k] = gv.get(k, 0.0) + v
    boot_orders.append(order_of(gv))
    rho, _ = stats.spearmanr(base, [gv.get(k, 0.0) for k in full_keys])
    rho_b.append(float(rho))
rho_b = np.array(rho_b)

layer_full = {k: v for k, v in layer_sum.items() if k is not None}
layer_order = sorted(layer_full, key=lambda k: -abs(layer_full[k]))
depths = sorted(layer_full)
spec = stats.spearmanr(depths, [abs(layer_full[d]) for d in depths])
top_freq = Counter(tuple(o[:2]) for o in boot_orders)
argmax_l = int(depths[int(np.argmax([abs(layer_full[d]) for d in depths]))])
argmin_l = int(depths[int(np.argmin([abs(layer_full[d]) for d in depths]))])
u_spec = stats.spearmanr(np.abs(np.array(depths) - argmax_l), [abs(layer_full[d]) for d in depths])

layer_by_n = {}
for n in (4, 8, 16):
    acc = defaultdict(float)
    for s in per_sample[:n]:
        for li, v in s['layers'].items():
            acc[li] += v / n
    layer_by_n[str(n)] = {'top3': [int(k) for k in sorted(acc, key=lambda k: -abs(acc[k]))[:3]],
                          'argmin': int(min(acc, key=lambda k: abs(acc[k])))}

json.dump({
    'mode': 'vis_mean_lang_mean', 'n_samples': len(per_sample), 'bucketing': 'canonical 8/16/8, prefix-aware v2',
    'E_by_n': e_n,
    'block_mean_gdot': {k: round(v, 2) for k, v in blk_mean.items()},
    'block_order_full': order_of(blk_mean),
    'llm_layer_gdot_full': {int(k): round(v, 3) for k, v in sorted(layer_full.items())},
    'layer_order_top5': [int(k) for k in layer_order[:5]],
    'layer_abs_gdot_depth_spearman': {'rho': round(float(spec.statistic), 3), 'p': round(float(spec.pvalue), 4)},
    'layer_profile': {'argmax_layer': argmax_l, 'argmin_layer': argmin_l,
                      'u_spearman_absdepth': round(float(u_spec.statistic), 3),
                      'u_p': round(float(u_spec.pvalue), 4),
                      'llm_shallow_mean(0-7)': round(float(np.mean([abs(layer_full[d]) for d in range(8)])), 3),
                      'llm_mid_mean(8-23)': round(float(np.mean([abs(layer_full[d]) for d in range(8, 24)])), 3),
                      'llm_deep_mean(24-31)': round(float(np.mean([abs(layer_full[d]) for d in range(24, 32)])), 3)},
    'layer_order_by_n': layer_by_n,
    'bootstrap': {'n_resamples': 500, 'top2_freq': {str(k): round(v / 500, 3) for k, v in top_freq.most_common(5)},
                  'spearman_vs_full_mean': round(float(np.mean(rho_b)), 3),
                  'spearman_vs_full_p5': round(float(np.percentile(rho_b, 5)), 3)},
}, open(OUT, 'w', encoding='utf-8'), indent=1)
print('DONE ->', OUT, flush=True)
print('E_by_n:', e_n, flush=True)
print('block_order:', order_of(blk_mean), flush=True)
print('block_mean:', {k: round(v, 2) for k, v in blk_mean.items()}, flush=True)
print('top2 freq:', top_freq.most_common(5), flush=True)
print('profile argmax/argmin/means:', argmax_l, argmin_l, flush=True)
print('spearman_vs_full mean/p5:', np.mean(rho_b), np.percentile(rho_b, 5), flush=True)

