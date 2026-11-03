"""补强实验 ⑥: CLIP 族 2×2 判别——CLIP ViT-B-32 基座 × {Flickr FT, Marine FT}（10ep 匹配规模）。
检验 σ_m 压平的域特异性是否跨模型族成立（当前仅在 bioclip 基座上验证过）。
输出: outputs/ocean_clip_flickrft.pt / ocean_clip_marineft.pt + ocean_clip2x2.json
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
from transformers import CLIPModel, CLIPProcessor

TEMPLATE = 'a photo of a {}'
SEED = 42
EPOCHS = 10
SUB = 'outputs/ocean_subset.json'
MDIR = 'models/clip-vit-base-patch32'
OUT_FT = 'outputs/ocean_clip_flickrft.pt'
OUT_MT = 'outputs/ocean_clip_marineft.pt'
OUT = 'outputs/ocean_clip2x2.json'


def set_seed(s):
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def load_model():
    m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().train()
    return m


def train_contrastive(m, p, xs, txts, opt):
    out = m(pixel_values=xs, input_ids=txts, return_loss=False)
    if_ = F.normalize(out.image_embeds, dim=-1)
    tf_ = F.normalize(out.text_embeds, dim=-1)
    logits = if_ @ tf_.T * m.logit_scale.exp()
    lab = torch.arange(len(xs), device='cuda')
    return (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2


def load_ds():
    return load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')


def flickr_pairs():
    import json as _j
    img_dir = os.path.join('flickr30k', 'flickr30k-images')
    data = _j.load(open(os.path.join('flickr30k', 'flickr30k.json'), encoding='utf-8'))
    out = []
    for it in data:
        fn = it['image']
        if os.path.exists(os.path.join(img_dir, fn)) and it.get('captions'):
            out.append((os.path.join(img_dir, fn), it['captions'][0]))
    return out


def marine_imgs(ds, idx):
    imgs = []
    for j in idx:
        b = ds[j]['file_name']
        imgs.append(Image.open(io.BytesIO(b['bytes'])) if isinstance(b, dict) and b.get('bytes')
                    else Image.open(b['path']) if isinstance(b, dict) else b)
    return imgs


def measure(m, p, ds, idx, classes, labels):
    texts = [TEMPLATE.format(c) for c in classes]
    ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
    with torch.no_grad():
        tout = m.text_model(**ti)
        tf = F.normalize(m.text_projection(tout[1]), dim=-1)
        feats = []
        for i in range(0, len(idx), 32):
            inp = p(images=marine_imgs(ds, idx[i:i + 32]), return_tensors='pt').to('cuda')
            vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
            feats.append(F.normalize(m.visual_projection(vout[1]), dim=-1))
        base = torch.cat(feats)
    gap = tf.mean(0) - base.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    m_c = (dH @ tf.T).cpu().numpy()
    S0 = (base @ tf.T).cpu().numpy()
    top1_0 = float((S0.argmax(1) == labels).mean() * 100)
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    with torch.no_grad():
        sh = F.normalize(base + gnorm * dH, dim=-1)
    S1 = (sh @ tf.T).cpu().numpy()
    top1_1 = float((S1.argmax(1) == labels).mean() * 100)
    taus = []
    for i in range(len(S0)):
        r1, r2 = S0[i][topk5[i]], S1[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    return {'gap_norm': round(gnorm, 4), 'sigma_m': round(float(np.std(m_c)), 4),
            'mean_m': round(float(np.mean(m_c)), 4),
            'top1_0': round(top1_0, 3), 'top1_l1': round(top1_1, 3), 'tau_l1': round(float(np.mean(taus)), 4)}


def run(m, p, mode, ds, idx, classes, labels):
    set_seed(SEED)
    if mode == 'flickr':
        pairs = flickr_pairs()[:1000]
        data = [(Image.open(pp), cc) for pp, cc in pairs]
    else:
        imgs = marine_imgs(ds, idx)
        caps = [TEMPLATE.format(classes[c]) for c in labels]
        data = [(im, c) for im, c in zip(imgs, caps)]
    n = len(data)
    opt = torch.optim.AdamW(m.parameters(), lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    m.train()
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(n)
        tot = 0.0
        cnt = 0
        for i in range(0, n, 32):
            sel = perm[i:i + 32]
            xs = torch.stack([p(images=data[j][0])['pixel_values'][0] for j in sel]).to('cuda')
            txt = p(text=[data[j][1] for j in sel], return_tensors='pt', padding=True)['input_ids'].to('cuda')
            opt.zero_grad()
            with torch.cuda.amp.autocast():
                loss = train_contrastive(m, p, xs, txt, opt)
            loss.backward()
            opt.step()
            tot += loss.item()
            cnt += 1
        sched.step()
        print('  %s ep%d loss=%.4f' % (mode, ep, tot / cnt), flush=True)
    return m.eval()


def main():
    ds = load_ds()
    sub = json.load(open(SUB, encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    results = {}
    print('== clip flickrft ==', flush=True)
    m = load_model()
    p = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
    m = run(m, p, 'flickr', ds, idx, classes, labels)
    torch.save(m.state_dict(), OUT_FT)
    results['clip_flickrft'] = measure(m, p, ds, idx, classes, labels)
    print(json.dumps(results['clip_flickrft'], indent=1), flush=True)
    json.dump(results, open(OUT, 'w', encoding='utf-8'), indent=1)
    del m
    torch.cuda.empty_cache()
    print('== clip marineft ==', flush=True)
    m = load_model()
    m = run(m, p, 'marine', ds, idx, classes, labels)
    torch.save(m.state_dict(), OUT_MT)
    results['clip_marineft'] = measure(m, p, ds, idx, classes, labels)
    json.dump(results, open(OUT, 'w', encoding='utf-8'), indent=1)
    print(json.dumps(results['clip_marineft'], indent=1), flush=True)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
