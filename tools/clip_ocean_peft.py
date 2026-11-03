"""P1 保护性实验（海洋版）：目标域微调后，海洋零样本是否被 PEFT 保护？
结构忠实 Paper 1：在 Flickr30k（陆地检索任务）上微调，探针 = 任务 R@1（Flickr val）+
零样本保持（海洋 rare-species 子集 top-1 / τ / CG，d̂ 同 phase-1a 协议）。
方法: LoRA-text / LoRA-both / BitFit / FullFT（Adapter 略，peft 0.19 对 open_clip 适配不完整，报告中披露）
模型: oceanclip（主角）x 4 方法 + bioclip（对照）x {LoRA-text, FullFT}
数据: Flickr30k train[0:1000] 训练, train[2000:2500] 验证;  10 epoch, lr 1e-4 (FullFT 5e-5), cosine, fp32
输出: outputs/ocean_peft.json
"""
import os, sys, json, io
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from datasets import load_dataset
import open_clip
from peft import LoraConfig, get_peft_model

TEMPLATE = 'a photo of a {}'
SEED = 42
OUT = 'outputs/ocean_peft.json'
EPOCHS = 10
SUB = 'outputs/ocean_subset.json'
FISH_CLASSES = ['Actinopterygii', 'Chondrichthyes', 'Coelacanthi']


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
    return m, p


def build_flickr():
    """Flickr30k: flickr30k-images/*.jpg + flickr30k.json [{'image','captions':[...]}] → (路径, caption)。"""
    import json as _j
    img_dir = os.path.join('flickr30k', 'flickr30k-images')
    data = _j.load(open(os.path.join('flickr30k', 'flickr30k.json'), encoding='utf-8'))
    pairs = []
    for it in data:
        fn = it['image']
        if not os.path.exists(os.path.join(img_dir, fn)):
            continue
        caps = it.get('captions') or []
        if caps:
            pairs.append((os.path.join(img_dir, fn), caps[0]))
    return pairs


def load_marine():
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    sub = json.load(open(SUB, encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    texts = [TEMPLATE.format(c) for c in classes]
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    return ds, idx, classes, texts, labels


def encode_imgs(m, pre, paths_batch):
    imgs = [pre(Image.open(pt)) for pt in paths_batch]
    xs = torch.stack(imgs).to('cuda')
    with torch.no_grad():
        return F.normalize(m.encode_image(xs), dim=-1)


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
    # τ: 需要"手术后"对照才有意义; 此处记录冻结 τ 定义上的替代: 与 base 一致的 triv 1.0, 直接记 CG
    cg = (base.mean(0) - tf.mean(0)).norm().item()
    return {'top1': round(top1, 3), 'CG': round(cg, 4)}


def train_eval(tag, method, pairs, tok, m, pre, ds, idx, texts, labels, marine_imgs):
    set_seed(SEED)
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

    opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=1e-4 if method != 'fullft' else 5e-5,
                            weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    tr_paths = [p for p, _ in pairs[:1000]]
    tr_caps = [c for _, c in pairs[:1000]]
    va_paths = [p for p, _ in pairs[2000:2500]]
    va_caps = [c for _, c in pairs[2000:2500]]

    m.train()
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(1000)
        total = 0.0
        for i in range(0, 1000, 64):
            sel = perm[i:i + 64]
            xs = torch.stack([pre(Image.open(tr_paths[j])) for j in sel]).to('cuda')
            txt = tok([tr_caps[j] for j in sel]).to('cuda')
            opt.zero_grad()
            with torch.cuda.amp.autocast():  # fp16 前向
                if_ = m.encode_image(xs)
                tf_ = m.encode_text(txt)
                if_ = F.normalize(if_, dim=-1)
                tf_ = F.normalize(tf_, dim=-1)
                scale = m.logit_scale.exp()
                logits = if_ @ tf_.T * scale
                lab = torch.arange(len(sel), device='cuda')
                loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
            loss.backward()
            opt.step()
            total += loss.item()
        sched.step()
        print('  [%s/%s] ep%d loss=%.4f' % (tag, method, ep, total / max(1, len(range(0, 1000, 64)))), flush=True)

    # 任务 R@1（val 500）
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
    print('  [%s/%s] Flickr R@1=%.4f | marine top1=%.2f CG=%.4f' % (tag, method, r1, mar['top1'], mar['CG']), flush=True)
    return {'method': method, 'flickr_R1': round(r1, 4), 'flickr_i2t': round(i2t, 4), 'flickr_t2i': round(t2i, 4),
            'marine_top1': mar['top1'], 'marine_CG': mar['CG']}


def main():
    pairs = build_flickr()
    print('Flickr pairs:', len(pairs), flush=True)
    ds, idx, classes, texts, labels = load_marine()
    tok = open_clip.get_tokenizer('ViT-B-16')
    results = {}
    jobs = [('bioclip', 'lora_text'), ('bioclip', 'fullft'),
            ('oceanclip', 'lora_text'), ('oceanclip', 'lora_both'),
            ('oceanclip', 'bitfit'), ('oceanclip', 'fullft')]
    for tag, method in jobs:
        print('== %s / %s ==' % (tag, method), flush=True)
        m, pre = load_base(tag)
        r = train_eval(tag, method, pairs, tok, m, pre, ds, idx, texts, labels, None)
        results['%s__%s' % (tag, method)] = r
        json.dump(results, open(OUT, 'w', encoding='utf-8'), indent=1)
        del m
        torch.cuda.empty_cache()
    print('ALL DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
