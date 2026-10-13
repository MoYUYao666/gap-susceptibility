"""Shipboard class (FathomNet ROV deployment video-frame subset) trajectory — isomorphic to L5 (CLIP ViT-B/32, 10ep matched schedule).
Evaluation set: data/fathomnet8 (8 concepts × 30 images); τ/σ_m/top1 per epoch; land control = flickrft.
Output: outputs/dynamics_fathomnet.json
"""
import os, sys, json
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from transformers import CLIPModel, CLIPProcessor

TEMPLATE = 'a photo of a {}'
SEED = 42
EPOCHS = 10
MDIR = 'models/clip-vit-base-patch32'
ROOT = 'data/fathomnet8'
OUT = 'outputs/dynamics_fathomnet.json'
FR = 'outputs/ocean_clip_flickrft.pt'


def load_set(cap=24):
    dirs = ['55-gallon drum', 'Actinopterygii', 'Decapoda', 'crab', 'sea star', 'urchin']
    imgs, labels = [], []
    for ci, c in enumerate(dirs):
        d = os.path.join(ROOT, c)
        fs = []
        seen = set()
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith(('.png', '.jpg')):
                uid = fn.split('.')[0]
                if uid not in seen:
                    seen.add(uid)
                    fs.append(os.path.join(d, fn))
        fs = fs[:cap]
        imgs.extend(fs)
        labels.extend([ci] * len(fs))
    return imgs, np.array(labels), dirs


def encode(m, p, imgs, texts=None, cap_batch=32):
    with torch.no_grad():
        if texts is not None:
            ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
            out = m.text_model(**ti)
            pooled = out[1] if isinstance(out, tuple) else out.pooler_output
            tf = F.normalize(m.text_projection(pooled), dim=-1)
        feats = []
        for i in range(0, len(imgs), cap_batch):
            inp = p(images=imgs[i:i + cap_batch], return_tensors='pt').to('cuda')
            vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
            vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            feats.append(F.normalize(m.visual_projection(vp), dim=-1))
        base = torch.cat(feats)
    return (tf if texts is not None else None), base


def eval_now(m, p, imgs, texts, labels, S0, topk5):
    tf, base = encode(m, p, imgs, texts)
    S = (base @ tf.T).cpu().numpy()
    top1 = float((S.argmax(1) == labels).mean() * 100)
    taus = []
    for i in range(len(S)):
        r1, r2 = S0[i][topk5[i]], S[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    gap = (tf.mean(0) - base.mean(0)).cpu().numpy()
    gnorm = np.linalg.norm(gap) + 1e-12
    m_c = (gap / gnorm) @ tf.cpu().numpy().T
    return {'top1': round(top1, 3), 'tau': round(float(np.mean(taus)), 4),
            'sigma_m': round(float(np.std(m_c)), 4)}


def summarize(m, p, imgs, texts, labels, tag):
    tf, base = encode(m, p, imgs, texts)
    gap = tf.mean(0) - base.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    m_c = (dH.cpu().numpy() @ tf.cpu().numpy().T)
    S0 = (base @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    top1 = float((S0.argmax(1) == labels).mean() * 100)
    taus = []
    for i in range(len(S0)):
        r1, r2 = S0[i][topk5[i]], S0[i][topk5[i]]
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    with torch.no_grad():
        tf2 = F.normalize(tf - 1.0 * gnorm * dH, dim=-1)
    S2 = (base @ tf2.T).cpu().numpy()
    taus2 = []
    for i in range(len(S0)):
        r1, r2 = S0[i][topk5[i]], S2[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus2.append(t)
    # image-side λ=1
    with torch.no_grad():
        sh = F.normalize(base + 1.0 * gnorm * dH, dim=-1)
    S1 = (sh @ tf.T).cpu().numpy()
    taus1 = []
    for i in range(len(S0)):
        r1, r2 = S0[i][topk5[i]], S1[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus1.append(t)
    return {'sigma_m': round(float(np.std(m_c)), 4), 'top1_0': round(top1, 3),
            'tau_l1': round(float(np.mean(taus1)), 4), 'tau_text1': round(float(np.mean(taus2)), 4)}


def main():
    imgs_paths, labels, classes = load_set()
    imgs = [Image.open(fp).convert('RGB') for fp in imgs_paths]
    texts = [TEMPLATE.format(c) for c in classes]
    print('class set:', classes, '| n =', len(imgs), flush=True)
    m, p = load = CLIPModel.from_pretrained(MDIR, local_files_only=True), CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
    m0 = m.cuda().eval()
    tf0, base0 = encode(m0, p, imgs, texts)
    S0 = (base0 @ tf0.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    res = {'meta': {'dataset': 'FathomNet ROV subset (8 concepts x 30)', 'n': len(imgs), 'classes': classes}}
    res['frozen_info'] = summarize(m0, p, imgs, texts, labels, 'frozen')
    print('frozen:', res['frozen_info'], flush=True)
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)

    # land control
    fr = CLIPModel.from_pretrained(MDIR, local_files_only=True)
    fr.load_state_dict(torch.load(FR, map_location='cpu'))
    fr = fr.cuda().eval()
    res['flickrft_info'] = summarize(fr, p, imgs, texts, labels, 'flickrft')
    print('flickrft:', res['flickrft_info'], flush=True)
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)

    # domain-FT trajectory
    mt = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().train()
    mt.logit_scale.requires_grad_(False)
    for pp in mt.parameters():
        pp.requires_grad_(True)
    opt = torch.optim.AdamW(mt.parameters(), lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    n = len(imgs)
    traj = []
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(n)
        tot, cnt = 0.0, 0
        for i in range(0, n, 32):
            sel = perm[i:i + 32]
            xs = torch.stack([p(images=imgs[j])['pixel_values'][0] for j in sel]).to('cuda')
            caps = [TEMPLATE.format(classes[c]) for c in labels[sel]]
            ti = p(text=caps, return_tensors='pt', padding=True)['input_ids'].to('cuda')
            opt.zero_grad()
            with torch.cuda.amp.autocast():
                outm = mt(pixel_values=xs, input_ids=ti, return_loss=False)
                if_ = F.normalize(outm.image_embeds, dim=-1)
                tf_ = F.normalize(outm.text_embeds, dim=-1)
                logits = if_ @ tf_.T * mt.logit_scale.exp()
                lab = torch.arange(len(sel), device='cuda')
                loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
            loss.backward()
            opt.step()
            tot += loss.item(); cnt += 1
        sched.step()
        mt.eval()
        st = eval_now(mt, p, imgs, texts, labels, S0, topk5)
        st = {'epoch': ep + 1, 'loss': round(tot / cnt, 4), **st}
        traj.append(st)
        print('  ep%d loss=%.4f tau=%.4f top1=%.2f sigma_m=%.4f' %
              (ep + 1, st['loss'], st['tau'], st['top1'], st['sigma_m']), flush=True)
        mt.train()
    res['traj'] = traj
    res['domainft_info'] = summarize(mt.eval(), p, imgs, texts, labels, 'domainft')
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
