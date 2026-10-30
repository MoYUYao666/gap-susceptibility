"""P1 保护性实验 · 3-seed 版本（训练随机性稳健性）。
配置与 clip_ocean_peft.py 完全一致（Flickr 1000 对/10ep/lr 1e-4(FT 5e-5)/cosine/对称CE/fp16 autocast），
仅种子遍历 {1,42,99}（seed42 应复现原 ocean_peft.json 数值，作一致性校验）。
输出: outputs/ocean_peft_ms.json
"""
import os, sys, json, io
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from datasets import load_dataset
import open_clip
from peft import LoraConfig, get_peft_model

TEMPLATE = 'a photo of a {}'
EPOCHS = 10
OUT = 'outputs/ocean_peft_ms.json'
SUB = 'outputs/ocean_subset.json'
SEEDS = [1, 42, 99]


def set_seed(s):
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def load_base(tag):
    if tag == 'bioclip':
        m, _, p = open_clip.create_model_and_transforms(
            'ViT-B-16', pretrained='models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin', device='cuda')
    else:
        ck = torch.load('models/oceanclip-0.15b/oceanclip-bio/epoch_50.pt', map_location='cpu')
        m, _, p = open_clip.create_model_and_transforms(
            'ViT-B-16', pretrained='models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin', device='cuda')
        m.load_state_dict(ck['state_dict'], strict=False)
    m.eval()
    return m, p


def build_flickr():
    import json as _j
    img_dir = os.path.join('flickr30k', 'flickr30k-images')
    data = _j.load(open(os.path.join('flickr30k', 'flickr30k.json'), encoding='utf-8'))
    pairs = []
    for it in data:
        fn = it['image']
        if os.path.exists(os.path.join(img_dir, fn)) and it.get('captions'):
            pairs.append((os.path.join(img_dir, fn), it['captions'][0]))
    return pairs


def load_marine():
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    sub = json.load(open(SUB, encoding='utf-8'))
    return ds, sub['classes'], sub['subset_idx']


def eval_marine(m, pre, ds, idx, texts, labels, tok):
    with torch.no_grad():
        tf = F.normalize(m.encode_text(tok(texts).to('cuda')), dim=-1)
        feats = []
        for i in range(0, len(idx), 32):
            b = ds[idx[i:i + 32]]['file_name']
            imgs = []
            for x in b:
                imgs.append(Image.open(io.BytesIO(x['bytes'])) if isinstance(x, dict) and x.get('bytes')
                            else Image.open(x['path']) if isinstance(x, dict) else x)
            xs = torch.stack([pre(im) for im in imgs]).to('cuda')
            with torch.no_grad():
                feats.append(F.normalize(m.encode_image(xs), dim=-1))
        base = torch.cat(feats)
    S = (base @ tf.T).cpu().numpy()
    top1 = float((S.argmax(1) == labels).mean() * 100)
    cg = (base.mean(0) - tf.mean(0)).norm().item()
    return {'top1': round(top1, 3), 'CG': round(cg, 4)}


def train_eval(tag, method, seed, pairs, tok, m, pre, ds, idx, texts, labels):
    set_seed(seed)
    if method == 'lora_text':
        cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                         target_modules=['qkv', 'c_fc', 'c_proj', 'in_proj', 'out_proj'])
        m = get_peft_model(m, cfg)
        for n, p in m.named_parameters():
            if 'visual' in n.split('.'):
                p.requires_grad_(False)
    elif method == 'lora_both':
        cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                         target_modules=['qkv', 'c_fc', 'c_proj', 'in_proj', 'out_proj'])
        m = get_peft_model(m, cfg)
    elif method == 'bitfit':
        for n, p in m.named_parameters():
            p.requires_grad_(False)
        for n, p in m.named_parameters():
            if '.bias' in n:
                p.requires_grad_(True)
    elif method == 'fullft':
        for n, p in m.named_parameters():
            p.requires_grad_(True)
    else:
        raise ValueError(method)
    opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],
                            lr=1e-4 if method != 'fullft' else 5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    tr_paths = [p for p, _ in pairs[:1000]]
    tr_caps = [c for _, c in pairs[:1000]]
    va_paths = [p for p, _ in pairs[2000:2500]]
    va_caps = [c for _, c in pairs[2000:2500]]
    m.train()
    for ep in range(EPOCHS):
        perm = np.random.RandomState(seed + ep).permutation(1000)
        tot = 0.0
        for i in range(0, 1000, 64):
            sel = perm[i:i + 64]
            xs = torch.stack([pre(Image.open(tr_paths[j])) for j in sel]).to('cuda')
            txt = tok([tr_caps[j] for j in sel]).to('cuda')
            opt.zero_grad()
            with torch.cuda.amp.autocast():
                if_ = F.normalize(m.encode_image(xs), dim=-1)
                tf_ = F.normalize(m.encode_text(txt), dim=-1)
                logits = if_ @ tf_.T * m.logit_scale.exp()
                lab = torch.arange(len(sel), device='cuda')
                loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
            loss.backward()
            opt.step()
            tot += loss.item()
        sched.step()
    m.eval()

    def r_at_1(imgs_p, caps_p, bs=64):
        i2t_l, t2i_l = [], []
        with torch.no_grad():
            for i in range(0, len(imgs_p), bs):
                xs = torch.stack([pre(Image.open(p)) for p in imgs_p[i:i + bs]]).to('cuda')
                txt = tok(caps_p[i:i + bs]).to('cuda')
                if_ = F.normalize(m.encode_image(xs), dim=-1)
                tf_ = F.normalize(m.encode_text(txt), dim=-1)
                sims = if_ @ tf_.T
                i2t_l.append((sims.argmax(1) == torch.arange(len(sims), device='cuda')).float().mean().item())
                t2i_l.append((sims.argmax(0) == torch.arange(len(sims), device='cuda')).float().mean().item())
        return float(np.mean(i2t_l)), float(np.mean(t2i_l))
    i2t, t2i = r_at_1(va_paths, va_caps)
    r1 = (i2t + t2i) / 2
    mar = eval_marine(m, pre, ds, idx, texts, labels, tok)
    return {'method': method, 'seed': seed, 'flickr_R1': round(r1, 4), 'flickr_i2t': round(i2t, 4),
            'flickr_t2i': round(t2i, 4), 'marine_top1': mar['top1'], 'marine_CG': mar['CG']}


def main():
    pairs = build_flickr()
    ds, classes, idx = load_marine()
    texts = [TEMPLATE.format(c) for c in classes]
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    tok = open_clip.get_tokenizer('ViT-B-16')
    jobs = [('bioclip', 'lora_text'), ('bioclip', 'fullft'),
            ('oceanclip', 'lora_text'), ('oceanclip', 'lora_both'),
            ('oceanclip', 'bitfit'), ('oceanclip', 'fullft')]
    results = {}
    for tag, method in jobs:
        for seed in SEEDS:
            print('== %s / %s / seed%d ==' % (tag, method, seed), flush=True)
            m, pre = load_base(tag)
            r = train_eval(tag, method, seed, pairs, tok, m, pre, ds, idx, texts, labels)
            results['%s__%s__s%d' % (tag, method, seed)] = r
            json.dump(results, open(OUT, 'w', encoding='utf-8'), indent=1)
            print('  R@1=%.4f marine_top1=%.2f CG=%.4f' % (r['flickr_R1'], r['marine_top1'], r['marine_CG']), flush=True)
            del m
            torch.cuda.empty_cache()
    print('ALL DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
