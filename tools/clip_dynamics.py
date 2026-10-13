"""A2 extended E2: training dynamics matrix —— per-epoch τ/σ_m/top-1 trajectories.
- CLIP+Sonar10ep (balanced 650) evaluated epoch by epoch on NKSID-650
- CLIP+Flickr10ep (1000 pairs) evaluated epoch by epoch on ImageNet-5k
Monitor semantics: τ(t)=Kendall(frozen initial vs current, frozen top-5 set); σ_m(t)/top1(t) are for the current model.
Output: outputs/dynamics_matrix.json
Run: conda run -n pytorch python tools/clip_dynamics.py
"""
import os, sys, json, io, glob
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from transformers import CLIPModel, CLIPProcessor

OUT = 'outputs/dynamics_matrix.json'
MDIR = 'models/clip-vit-base-patch32'
TEMPLATE = 'a photo of a {}'
SEED = 42
EPOCHS = 10
SONAR_CLASSES = ['big propeller', 'cylinder', 'fishing net', 'floats', 'iron pipeline',
                 'small propeller', 'soft pipeline', 'tire']
SONAR_DIR = ['big_propeller', 'cylinder', 'fishing_net', 'floats', 'iron_pipeline',
             'small_propeller', 'soft_pipeline', 'tire']


def build_sonar(cap=90):
    man = []
    for c, d in zip(SONAR_CLASSES, SONAR_DIR):
        p = os.path.join('data/NKSID/NKSID', d)
        if not os.path.isdir(p):
            p = 'data/NKSID/NKSID'
        fs = sorted(f for f in os.listdir(p) if f.lower().endswith(('.jpg', '.png')))[:cap]
        man.extend((os.path.join(p, f), c) for f in fs)
    return man


def load_imagenet5k():
    from datasets import load_dataset
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/imagenet_hf', f) for f in os.listdir('data/imagenet_hf')
        if f.endswith('.parquet')), split='train')
    names = json.load(open('data/imagenet_1k_names.json', encoding='utf-8'))
    rng = np.random.RandomState(SEED)
    idx = rng.choice(len(ds), size=5000, replace=False)
    imgs, labels = [], []
    for i in idx:
        r = ds[int(i)]
        labels.append(int(r['label']))
        imgs.append(r['image'].convert('RGB') if hasattr(r['image'], 'convert') else r['image'])
    return imgs, np.array(labels), names


def load_flickr(n=1000):
    import json as j
    d = j.load(open('flickr30k/flickr30k.json', encoding='utf-8'))
    rng = np.random.RandomState(SEED)
    sel = [d[int(i)] for i in rng.choice(len(d), size=n, replace=False)]
    pairs = []
    for rec in sel:
        p = os.path.join('flickr30k', 'flickr30k-images', rec['image'])
        pairs.append((Image.open(p).convert('RGB'), rec['captions'][0]))
    return pairs


def eval_stats(m, p, imgs, texts, labels, f0, topk5, gnorm=None, dH=None, m_c=None):
    """Return top1/tau/sigma_m of the current model on the eval set. f0/topk5 come from the frozen initial model."""
    with torch.no_grad():
        fi = []
        for i in range(0, len(imgs), 48):
            inp = p(images=imgs[i:i + 48], return_tensors='pt').to('cuda')
            vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
            vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            fi.append(F.normalize(m.visual_projection(vp), dim=-1))
        fi = torch.cat(fi)
        ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
        out = m.text_model(**ti)
        pooled = out[1] if isinstance(out, tuple) else out.pooler_output
        tf = F.normalize(m.text_projection(pooled), dim=-1)
    S = (fi @ tf.T).cpu().numpy()
    S0 = (f0 @ tf.T).cpu().numpy()  # frozen scores (recomputed, with current text?) —— frozen baseline f0 = initial vision, text = initial
    top1 = float((S.argmax(1) == labels).mean() * 100)
    taus = []
    for i in range(len(S)):
        r1, r2 = S0[i][topk5[i]], S[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    gap = tf.mean(0) - fi.mean(0)
    gnorm = gap.norm().item()
    dH = (gap / gnorm).cpu().numpy()
    m_c = dH @ tf.cpu().numpy().T
    return {'top1': round(top1, 3), 'tau': round(float(np.mean(taus)), 4),
            'sigma_m': round(float(np.std(m_c)), 4), 'gnorm': round(gnorm, 4)}


def train_traj(tag, man, texts, labels, eval_info):
    """Train 10ep, evaluate after each epoch. man=(path,class) or a list of PIL images."""
    m0 = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().eval()
    p = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
    # frozen baseline
    f0_imgs = eval_info['f0_imgs']
    f0 = []
    with torch.no_grad():
        for i in range(0, len(f0_imgs), 48):
            inp = p(images=f0_imgs[i:i + 48], return_tensors='pt').to('cuda')
            vout = m0.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
            vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            f0.append(F.normalize(m0.visual_projection(vp), dim=-1))
        f0 = torch.cat(f0)
        ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
        out = m0.text_model(**ti)
        pooled = out[1] if isinstance(out, tuple) else out.pooler_output
        tf0 = F.normalize(m0.text_projection(pooled), dim=-1)
    S0 = (f0 @ tf0.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]

    m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().train()
    if tag == 'sonar':
        imgs_tr = [Image.open(fp).convert('RGB') for fp, _ in man]
        pairs = [(imgs_tr[i], man[i][1]) for i in range(len(man))]
    else:
        pairs = man  # [(PIL, caption)]
    opt = torch.optim.AdamW(m.parameters(), lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    rows = []
    n = len(pairs)
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(n)
        tot, cnt = 0.0, 0
        for i in range(0, n, 32):
            sel = perm[i:i + 32]
            xs = torch.stack([p(images=pairs[j][0])['pixel_values'][0] for j in sel]).to('cuda')
            caps = []
            for j in sel:
                txt = pairs[j][1] if tag == 'sonar' else pairs[j][1]
                caps.append(TEMPLATE.format(txt) if tag == 'sonar' else txt)
            ti = p(text=caps, return_tensors='pt', padding=True)['input_ids'].to('cuda')
            opt.zero_grad()
            with torch.cuda.amp.autocast():
                outm = m(pixel_values=xs, input_ids=ti, return_loss=False)
                if_ = F.normalize(outm.image_embeds, dim=-1)
                tf_ = F.normalize(outm.text_embeds, dim=-1)
                logits = if_ @ tf_.T * m.logit_scale.exp()
                lab = torch.arange(len(sel), device='cuda')
                loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
            loss.backward()
            opt.step()
            tot += loss.item(); cnt += 1
        sched.step()
        m.eval()
        st = eval_stats(m, p, eval_info['f0_imgs'], texts, labels, f0, topk5)
        st['epoch'] = ep + 1
        st['loss'] = round(tot / cnt, 4)
        rows.append(st)
        print('  %s ep%d loss=%.4f tau=%.4f top1=%.2f sigma_m=%.4f' %
              (tag, ep + 1, st['loss'], st['tau'], st['top1'], st['sigma_m']), flush=True)
        m.train()
    return rows


def main():
    res = {}
    # 1) Sonar
    man = build_sonar()
    labels = np.array([SONAR_CLASSES.index(c) for _, c in man])
    texts = [TEMPLATE.format(c) for c in SONAR_CLASSES]
    simgs = [Image.open(fp).convert('RGB') for fp, _ in man]
    print('== CLIP+Sonar ==', flush=True)
    res['clip_sonar'] = train_traj('sonar', man, texts, labels,
                                   {'f0_imgs': simgs})
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    torch.cuda.empty_cache()
    # 2) Flickr (1000 pairs) → ImageNet-5k evaluation
    print('== CLIP+Flickr ==', flush=True)
    pairs = load_flickr(1000)
    i5, lab5, names5 = load_imagenet5k()
    texts5 = [TEMPLATE.format(c) for c in names5]
    res['clip_flickr'] = train_traj('flickr', pairs, texts5, lab5, {'f0_imgs': i5})
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
