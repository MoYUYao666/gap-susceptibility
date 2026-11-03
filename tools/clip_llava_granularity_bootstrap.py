"""(完整版) 层粒度消融 + Γ 逐样本 bootstrap + E 样本量敏感性(解码器)。
一次运行产出: 逐层 gdot、逐样本 4 块 gdot(bootstrap)、E 每样本。
输出: outputs/llava_granularity_bootstrap.json
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
DATA = sorted(glob.glob('data/marinelife16k/_small/*.jpg'))[:16]
OUT = 'outputs/llava_granularity_bootstrap.json'
IMGID_KEY = 'image_token_index'

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
                         bnb_4bit_quant_type='nf4', bnb_4bit_use_double_quant=True)
m = LlavaForConditionalGeneration.from_pretrained(MDIR, torch_dtype=torch.bfloat16,
                                                  quantization_config=bnb, device_map='cuda')
proc = AutoProcessor.from_pretrained(MDIR)
tok = AutoTokenizer.from_pretrained(MDIR)
lm = getattr(m, 'language_model', getattr(m, 'model', None))
lm.config.use_cache = False
m.eval()
par = dict(m.named_parameters())
for p in m.parameters():
    if p.is_floating_point():
        p.requires_grad = True

IMGID = proc.tokenizer.convert_tokens_to_ids('<image>')
if IMGID is None or IMGID < 0:
    IMGID = m.config.image_token_index


def blk_of(name):
    if name.startswith('vision_tower'):
        return 'vision_tower'
    if name.startswith('multi_modal_projector'):
        return 'projector'
    if '.layers.' in name:
        for seg in name.split('.'):
            if seg.isdigit():
                li = int(seg)
                return 'llm_shallow' if li < 11 else ('llm_mid' if li < 22 else 'llm_deep')
    return 'llm_other'


BLK = {n: blk_of(n) for n in par}
LAYER = {}
for n in par:
    li = None
    for seg in n.split('.'):
        if seg.isdigit():
            li = int(seg)
            break
    LAYER[n] = li if li is not None else -1

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
    if mode == 'vis_mean_lang_mean':
        return v.mean(0), l.mean(0)
    if mode == 'vis_last_lang_mean':
        return v[-1], l.mean(0)
    if mode == 'vis_mean_lang_max':
        return v.mean(0), l.max(0).values
    return v.max(0).values, l.mean(0)


def E_of(idsb, maskb, pvb, mode):
    out = m(pixel_values=pvb, input_ids=idsb, attention_mask=maskb, output_hidden_states=True)
    h = out.hidden_states[-1].float()[0]
    vf, lf = pos_feats(h, idsb[0], mode)
    return ((vf - lf) ** 2).mean()


def L_of(idsb, maskb, pvb):
    labels = idsb.clone()
    labels[labels == tok.pad_token_id] = -100
    out = m(pixel_values=pvb, input_ids=idsb, attention_mask=maskb, labels=labels)
    return out.loss


per_sample = []
mode = 'vis_mean_lang_mean'
layer_sum = {}
for b in range(len(imgs)):
    ids1 = ids[b:b + 1]
    mask1 = mask[b:b + 1]
    pv1 = pv[b:b + 1]
    m.zero_grad()
    e_val = E_of(ids1, mask1, pv1, mode)
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
        if li >= 0:
            gl[li] = gl.get(li, 0.0) + dot
    m.zero_grad()
    per_sample.append({'E': float(e_val.item()), 'blocks': gb, 'layers': gl})
    for li, v in gl.items():
        layer_sum[li] = layer_sum.get(li, 0.0) + v / len(imgs)
    del gE
    del gb, gl


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

layer_full = {k: v for k, v in layer_sum.items() if k >= 0}
layer_order = sorted(layer_full, key=lambda k: -abs(layer_full[k]))
depths = sorted(layer_full)
spec = stats.spearmanr(depths, [abs(layer_full[d]) for d in depths])

top_freq = Counter(tuple(o[:2]) for o in boot_orders)
agg = defaultdict(float)
for li, v in layer_full.items():
    agg['llm_shallow' if li < 11 else ('llm_mid' if li < 22 else 'llm_deep')] += v
agg_order = order_of(agg)
# 粒度一致性: 仅在"真正由层构成"的 3 块上比较 (排除 llm_other, 它由 lm_head/embed 主导)
llm_blocks = ['llm_shallow', 'llm_mid', 'llm_deep']
consistency = stats.spearmanr([blk_mean[k] for k in llm_blocks], [agg.get(k, 0.0) for k in llm_blocks])
# 层剖面 U 形诊断
depths_arr = np.array(sorted(layer_full))
gabs = np.array([abs(layer_full[d]) for d in depths_arr])
argmax_l = int(depths_arr[int(np.argmax(gabs))])
u_spec = stats.spearmanr(np.abs(depths_arr - argmax_l), gabs)
argmin_l = int(depths_arr[int(np.argmin(gabs))])
middle = int(np.argmin(np.abs(depths_arr - 15.5)))
# 前缀稳定性: n=4/8/16 的层序 Top-3 与全量 Top-3 的一致性 (用逐样本累计)
layer_by_n = {}
for n in (4, 8, 16):
    acc = defaultdict(float)
    for s in per_sample[:n]:
        for li, v in s['layers'].items():
            acc[li] += v / n
    layer_by_n[str(n)] = {'top3': [int(k) for k in sorted(acc, key=lambda k: -abs(acc[k]))[:3]],
                          'argmin': int(min(acc, key=lambda k: abs(acc[k])))}

json.dump({
    'mode': mode, 'n_samples': len(per_sample),
    'E_by_n': e_n,
    'block_mean_gdot': {k: round(v, 2) for k, v in blk_mean.items()},
    'block_order_full': order_of(blk_mean),
    'layer_order_top5': [int(k) for k in layer_order[:5]],
    'layer_gdot_full': {int(k): round(v, 3) for k, v in sorted(layer_full.items())},
    'layer_abs_gdot_depth_spearman': {'rho': round(float(spec.statistic), 3), 'p': round(float(spec.pvalue), 4)},
    'layer_u_shape': {'argmax_layer': argmax_l, 'argmin_layer': argmin_l,
                      'u_spearman_absdepth': round(float(u_spec.statistic), 3),
                      'u_p': round(float(u_spec.pvalue), 4),
                      'note': 'correlation of |layer Gamma| with distance from the argmax layer (positive => inverted-U / peaked profile)'},
    'layer_order_by_n': layer_by_n,
    'agg_block_order': agg_order,
    'granularity_consistency': {'blocks_compared': llm_blocks,
                                'spearman': round(float(consistency.statistic), 3),
                                'p': round(float(consistency.pvalue), 4),
                                'note': 'layer-aggregated sum vs direct per-block Gamma for the three layer-only blocks (llm_other excluded: dominated by lm_head/embeddings)'},
    'bootstrap': {'n_resamples': 500, 'top2_freq': {str(k): round(v / 500, 3) for k, v in top_freq.most_common(4)},
                  'spearman_vs_full_mean': round(float(np.mean(rho_b)), 3),
                  'spearman_vs_full_p5': round(float(np.percentile(rho_b, 5)), 3)},
}, open(OUT, 'w', encoding='utf-8'), indent=1)
print('DONE ->', OUT, flush=True)
print('E_by_n:', e_n, flush=True)
print('block_order:', order_of(blk_mean), flush=True)
print('top2 freq:', top_freq.most_common(4), flush=True)
print('bootstrap rho mean/p5:', np.mean(rho_b), np.percentile(rho_b, 5), flush=True)
print('u_shape argmax/argmin:', argmax_l, argmin_l, 'rho:', u_spec.statistic, flush=True)
print('granularity consistency (3 blocks):', consistency.statistic, flush=True)
