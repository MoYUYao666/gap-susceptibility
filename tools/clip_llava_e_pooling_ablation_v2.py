"""(修正版 v2) 解码器 E 位置聚合消融 —— 前缀感知分桶。
修复: transformers 5.x 'model.' 前缀 + vision/LLM 层同名混淆。
分桶(规范 8/16/8 + 前缀): vis | proj | llm_shallow(0-7) | llm_mid(8-23) | llm_deep(24-31) | llm_other(embed/norm) | lm_head
输出: outputs/llava_e_pooling_ablation_v2.json
"""
import os, sys, json, glob
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
from PIL import Image
from transformers import LlavaForConditionalGeneration, AutoProcessor, BitsAndBytesConfig, AutoTokenizer
from scipy import stats

MDIR = 'models/llava-hf'
DATA = sorted(glob.glob('data/marinelife16k/_small/*.jpg'))[:8]
OUT = 'outputs/llava_e_pooling_ablation_v2.json'

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
                         bnb_4bit_quant_type='nf4', bnb_4bit_use_double_quant=True)
m = LlavaForConditionalGeneration.from_pretrained(MDIR, torch_dtype=torch.bfloat16,
                                                  quantization_config=bnb, device_map='cuda')
proc = AutoProcessor.from_pretrained(MDIR)
tok = AutoTokenizer.from_pretrained(MDIR)
lm = getattr(m, 'language_model', getattr(m, 'model', None))
lm.config.use_cache = False
m.eval()
for p in m.parameters():
    if p.is_floating_point():
        p.requires_grad = True

IMGID = m.config.image_token_index
par = dict(m.named_parameters())


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
POS = ['vis_mean_lang_mean', 'vis_max_lang_mean', 'vis_last_lang_mean', 'vis_mean_lang_max']


def pos_feats(h, ids, mode):
    vis = ids == IMGID
    lang = (ids != IMGID) & (ids != tok.pad_token_id)
    v = h[vis]
    l = h[lang]
    if mode == 'vis_mean_lang_mean':
        return v.mean(0), l.mean(0)
    if mode == 'vis_max_lang_mean':
        return v.max(0).values, l.mean(0)
    if mode == 'vis_last_lang_mean':
        return v[-1], l.mean(0)
    return v.mean(0), l.max(0).values


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


imgs = [Image.open(p) for p in DATA]
q = 'What is in the image? Answer with one word.'
tpl = [proc.apply_chat_template([{'role': 'user', 'content': [{'type': 'image'},
                                                             {'type': 'text', 'text': q}]},
                                 {'role': 'assistant', 'content': [{'type': 'text', 'text': 'a fish.'}]}],
                                add_generation_prompt=False, tokenize=False) for _ in imgs]
enc = proc(text=tpl, images=imgs, return_tensors='pt')
ids = enc['input_ids'].to('cuda')
mask = enc['attention_mask'].to('cuda')
pv = enc['pixel_values'].to('cuda')

res = {}
orderings = {}
for mode in POS:
    gd = {}
    e_acc = 0.0
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
        for nm, prm in par.items():
            if prm.grad is None or gE.get(nm) is None:
                continue
            bb = BLK[nm]
            gd[bb] = gd.get(bb, 0.0) + float((prm.grad.detach() * gE[nm]).sum())
        m.zero_grad()
        e_acc += float(e_val.item())
        del gE
    gd = {k: v / len(imgs) for k, v in gd.items()}
    res[mode] = {'gamma': {k: round(v, 1) for k, v in gd.items()}, 'E': round(e_acc / len(imgs), 2)}
    orderings[mode] = [k for k in sorted(gd, key=lambda k: -abs(gd[k]))]
    print(mode, '->', orderings[mode], flush=True)

keys = sorted(set(k for o in orderings.values() for k in o))
cons = {}
for i in range(len(POS)):
    for j in range(i + 1, len(POS)):
        a = res[POS[i]]['gamma']
        b = res[POS[j]]['gamma']
        ks = [k for k in keys if k in a and k in b]
        rho, p = stats.spearmanr([a[k] for k in ks], [b[k] for k in ks])
        cons['%s_vs_%s' % (POS[i], POS[j])] = {'spearman': round(float(rho), 3), 'p': round(float(p), 4)}

json.dump({'orderings': orderings, 'kendall_consistency': cons, 'gamma': res,
           'bucketing': 'canonical 8/16/8 prefix-aware v2'},
          open(OUT, 'w', encoding='utf-8'), indent=1)
print('DONE ->', OUT, flush=True)

