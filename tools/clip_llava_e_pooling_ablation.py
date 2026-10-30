"""(合并稿提升) 解码器 E 位置聚合消融: E=mean||h_vis-h_lang||² 的聚合方式
(mean/max/last-token × vis/lang) 是否改变 |Γ| 块排序。
块=vision_tower / projector / llm_shallow(0-10) / llm_mid(11-21) / llm_deep(22-31);
Γ_k=⟨∇_kE, ∇_kL⟩(同批 LM loss); 输出 outputs/llava_e_pooling_ablation.json
"""
import os, sys, json, glob, random
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
import torch.nn.functional as F
from PIL import Image
from transformers import LlavaForConditionalGeneration, AutoProcessor, BitsAndBytesConfig

MDIR = 'models/llava-hf'
DATA = sorted(glob.glob('data/marinelife16k/_small/*.jpg'))
OUT = 'outputs/llava_e_pooling_ablation.json'

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
                         bnb_4bit_quant_type='nf4', bnb_4bit_use_double_quant=True)
m = LlavaForConditionalGeneration.from_pretrained(MDIR, torch_dtype=torch.bfloat16,
                                                  quantization_config=bnb, device_map='cuda')
proc = AutoProcessor.from_pretrained(MDIR)
lm = getattr(m, 'language_model', getattr(m, 'model', None))
lm.config.use_cache = False
m.eval()
for p in m.parameters():
    if p.is_floating_point():
        p.requires_grad = True

IMGID = m.config.image_token_index

par = dict(m.named_parameters())
BLK = {}
for name in par:
    if name.startswith('vision_tower'):
        BLK[name] = 'vision_tower'
    elif name.startswith('multi_modal_projector'):
        BLK[name] = 'projector'
    elif '.layers.' in name:
        try:
            li = int(name.split('.layers.')[0].rsplit('.', 1)[-1])
        except Exception:
            li = 0
        for seg in name.split('.'):
            if seg.isdigit():
                li = int(seg); break
        BLK[name] = 'llm_shallow' if li < 11 else ('llm_mid' if li < 22 else 'llm_deep')
    else:
        BLK[name] = 'llm_other'

POS = ['vis_mean_lang_mean', 'vis_max_lang_mean', 'vis_last_lang_mean', 'vis_mean_lang_max']


def pos_feats(h, ids, mode):
    """h: (B,T,HD); 返回 vis 与 lang 两个 (B,HD) 聚合特征。"""
    B, T = ids.shape
    vis = ids == IMGID
    lang = (ids != IMGID) & (ids != proc.tokenizer.pad_token_id)
    vb, lb = [], []
    for b in range(B):
        v = h[b][vis[b]]; l = h[b][lang[b]]
        if mode == 'vis_mean_lang_mean':
            va, la = v.mean(0), l.mean(0)
        elif mode == 'vis_max_lang_mean':
            va, la = v.max(0).values, l.mean(0)
        elif mode == 'vis_last_lang_mean':
            va, la = v[-1], l.mean(0)
        else:
            va, la = v.mean(0), l.max(0).values
        vb.append(va); lb.append(la)
    return torch.stack(vb), torch.stack(lb)


def E_of(m, ids, mask, pv, mode):
    # 完整前向(视觉注入): 取 LLM 最后一层隐状态
    out = m(pixel_values=pv, input_ids=ids, attention_mask=mask, output_hidden_states=True)
    h = out.hidden_states[-1].float()
    vf, lf = pos_feats(h, ids, mode)
    return ((vf - lf) ** 2).mean()


def L_of(m, ids, mask, pv):
    labels = ids.clone()
    labels[labels == proc.tokenizer.pad_token_id] = -100
    out = m(pixel_values=pv, input_ids=ids, attention_mask=mask, labels=labels)
    return out.loss


def block_gdot(grad_dict):
    gd = {}
    for nm, gr in grad_dict.items():
        if gr is None:
            continue
        b = BLK[nm]
        gd[b] = gd.get(b, 0.0) + float(gr.double().pow(2).sum())
    return gd  # 已平方和(尺度)


def gamma_order(m, ids, mask, pv, mode):
    """逐样本双 backward 累计(8GB 限批=1); 返回平均 gdot 与 E。"""
    B = ids.shape[0]
    gd = {}
    e_acc = 0.0
    for b in range(B):
        ids1 = ids[b:b + 1]
        mask1 = mask[b:b + 1]
        pv1 = pv['pixel_values'][b:b + 1] if 'pixel_values' in pv else pv[b:b + 1]
        m.zero_grad()
        lossE = E_of(m, ids1, mask1, pv1, mode)
        lossE.backward()
        gE = {nm: (prm.grad.detach().clone() if prm.grad is not None else None)
              for nm, prm in par.items()}
        m.zero_grad()
        try:
            lossL = L_of(m, ids1, mask1, pv1)
            lossL.backward()
        except RuntimeError as e2:
            print('L_of skip:', str(e2)[:60], flush=True)
            m.zero_grad()
            continue
        for nm, prm in par.items():
            if prm.grad is None or gE.get(nm) is None:
                continue
            bb = BLK[nm]
            gd[bb] = gd.get(bb, 0.0) + float((prm.grad.detach() * gE[nm]).sum())
        m.zero_grad()
        e_acc += float(lossE.item())
        del gE
    return {k: v / B for k, v in gd.items()}, e_acc / B


imgs = [Image.open(p) for p in DATA[:8]]
with torch.no_grad():
    inp = proc(text=None, images=imgs, return_tensors='pt')
pix = {k: v.to('cuda') for k, v in inp.items() if k in ('pixel_values',)}

from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained(MDIR)
tok.padding_side = 'right'
q = 'What is in the image? Answer with one word.'
tpl = [proc.apply_chat_template([{'role': 'user', 'content': [{'type': 'image'},
                                                            {'type': 'text', 'text': q}]},
                                 {'role': 'assistant', 'content': [{'type': 'text', 'text': 'a fish.'}]}],
                                add_generation_prompt=False, tokenize=False) for _ in imgs]
enc = proc(text=tpl, images=imgs, return_tensors='pt')
ids = enc['input_ids'].to('cuda')
mask = enc['attention_mask'].to('cuda')

res = {}
orderings = {}
for mode in POS:
    gd, e = gamma_order(m, ids, mask, pix, mode)
    res[mode] = {'gamma': {k: round(v, 1) for k, v in gd.items()},
                 'E': round(e, 2)}
    orderings[mode] = [k for k in sorted(gd, key=lambda k: -abs(gd[k]))]
    print(mode, '->', orderings[mode], flush=True)

from scipy import stats
keys = sorted(set(k for o in orderings.values() for k in o))
cons = {}
for i in range(len(POS)):
    for j in range(i + 1, len(POS)):
        a = res[POS[i]]['gamma']; b = res[POS[j]]['gamma']
        ks = [k for k in keys if k in a and k in b]
        rho, p = stats.spearmanr([a[k] for k in ks], [b[k] for k in ks])
        cons['%s_vs_%s' % (POS[i], POS[j])] = {'spearman': round(float(rho), 3), 'p': round(float(p), 4)}
json.dump({'orderings': orderings, 'kendall_consistency': cons, 'gamma': res}, open(OUT, 'w', encoding='utf-8'), indent=1)
print('DONE ->', OUT, flush=True)
