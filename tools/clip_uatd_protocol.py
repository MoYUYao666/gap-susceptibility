"""UATD (Xie et al., Scientific Data 2022) full protocol---isomorphic to watertank/riku.
Data: data/second_sonar/UATD/data/{UATD_Training,UATD_Test_1,UATD_Test_2}
Annotations: VOC xml (object names + sonar parameters); 10 classes; 44.8% multi-class images (the most frequent class is taken as the image-level label).
Eval: Test_1+Test_2 (1,600 images); train: Training (7,600 images). Same 10ep FT schedule; same terrestrial control.
Output: outputs/uatd_protocol.json
"""
import os, sys, json, glob, collections
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import xml.etree.ElementTree as ET
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from transformers import CLIPModel, CLIPProcessor

TEMPLATE = 'a photo of a {}'
SEED = 42
EPOCHS = 10
MDIR = 'models/clip-vit-base-patch32'
BASE = 'data/second_sonar/UATD/data'
OUT = 'outputs/uatd_protocol.json'
FT_WEIGHTS = 'outputs/uatd_clip_ft.pt'
FR = 'outputs/ocean_clip_flickrft.pt'

CLASS_ORDER = None  # determined by the training set


def load_split(splits):
    imgs, labels = [], []
    cnt = collections.Counter()
    for s in splits:
        img_dir = os.path.join(BASE, s, 'images')
        lab_dir = os.path.join(BASE, s, 'annotations')
        for fn in sorted(os.listdir(img_dir)):
            if not fn.lower().endswith(('.bmp', '.jpg', '.png')):
                continue
            xf = os.path.join(lab_dir, os.path.splitext(fn)[0] + '.xml')
            if not os.path.exists(xf):
                continue
            try:
                t = ET.parse(xf)
            except Exception:
                continue
            names = [o.findtext('name') for o in t.iter('object')]
            if not names:
                continue
            c = collections.Counter(names).most_common(1)[0][0]
            imgs.append(os.path.join(img_dir, fn))
            labels.append(c)
            cnt[c] += 1
    print('  %s: %d imgs' % ('+'.join(splits), len(imgs)), flush=True)
    print('  class distribution:', dict(cnt.most_common(15)), flush=True)
    return imgs, labels


def load_model():
    m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().eval()
    p = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
    return m, p


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


def protocol(tag, m, p, imgs, texts, labels, outdict):
    tf, base = encode(m, p, imgs, texts)
    gap = tf.mean(0) - base.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    m_c = (dH.cpu().numpy() @ tf.cpu().numpy().T)
    S0 = (base @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    top1 = float((S0.argmax(1) == labels).mean() * 100)
    rows = []
    for l in [-1.0, -0.5, 0.0, 0.5, 1.0, 2.0]:
        with torch.no_grad():
            sh = F.normalize(base + l * gnorm * dH, dim=-1)
        S = (sh @ tf.T).cpu().numpy()
        top1_l = float((S.argmax(1) == labels).mean() * 100)
        taus, preds = [], []
        for i in range(len(S)):
            k5 = topk5[i]
            s5 = S0[i][k5]
            d_pairs = s5[:, None] - s5[None, :]
            dm = -(m_c[k5][:, None] - m_c[k5][None, :])
            up = np.triu(np.ones((5, 5)), k=1).astype(bool)
            inv = (l * gnorm * dm[up] > d_pairs[up]).sum()
            preds.append(1.0 - 2 * inv / 10.0)
            r1, r2 = S0[i][k5], S[i][k5]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        cg = (sh.mean(0) - tf.mean(0)).norm().item()
        rows.append({'lambda': l, 'top1': round(top1_l, 3), 'tau_meas': round(float(np.mean(taus)), 4),
                     'tau_pred': round(float(np.mean(preds)), 4), 'CG': round(cg, 4)})
        print('  %s λ=%+.1f top1=%.2f tau_pred=%.4f tau_meas=%.4f' %
              (tag, l, top1_l, np.mean(preds), np.mean(taus)), flush=True)
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
    rows.append({'lambda': 'text1.0', 'tau_meas': round(float(np.mean(taus2)), 4),
                 'CG': round((base.mean(0) - tf2.mean(0)).norm().item(), 4)})
    print('  %s T λ=1 tau=%.4f' % (tag, np.mean(taus2)), flush=True)
    outdict[tag] = {'gap_norm': round(gnorm, 4), 'sigma_m': round(float(np.std(m_c)), 4),
                    'mean_m': round(float(np.mean(m_c)), 4), 'top1_0': round(top1, 3), 'rows': rows}
    json.dump(outdict, open(OUT, 'w', encoding='utf-8'), indent=1)


def main():
    tr, lab_tr0 = load_split(['UATD_Training'])
    te, lab_te0 = load_split(['UATD_Test_1', 'UATD_Test_2'])
    # class set = union of all classes over train+test (sorted by frequency; also covers classes new in test)
    allc = collections.Counter(lab_tr0 + lab_te0)
    names = [c for c, _ in allc.most_common()]
    idx = {c: i for i, c in enumerate(names)}
    labels_tr = np.array([idx[c] for c in lab_tr0])
    labels_te = np.array([idx[c] for c in lab_te0])
    texts = [TEMPLATE.format(c) for c in names]
    open_imgs = [Image.open(fp).convert('RGB') for fp in te]
    open_imgs_tr = [Image.open(fp).convert('RGB') for fp in tr]
    print('eval %d / train %d / classes %s' % (len(open_imgs), len(open_imgs_tr), names), flush=True)
    m0, p = load_model()
    outd = {'meta': {'dataset': 'UATD (Xie et al. 2022, multibeam FLS)', 'n_eval': len(open_imgs),
                     'n_train': len(open_imgs_tr), 'classes': names,
                     'note': 'image-level label = class with most instances (44.8% multi-class images)'}}
    print('== frozen ==', flush=True)
    protocol('frozen', m0, p, open_imgs, texts, labels_te, outd)
    print('== flickrft (terrestrial) ==', flush=True)
    fr = CLIPModel.from_pretrained(MDIR, local_files_only=True)
    fr.load_state_dict(torch.load(FR, map_location='cpu'))
    fr = fr.cuda().eval()
    protocol('flickrft', fr, p, open_imgs, texts, labels_te, outd)
    print('== domain FT ==', flush=True)
    m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().train()
    m.logit_scale.requires_grad_(False)  # fixed temperature: under the same 10ep schedule large samples trigger temperature collapse; fixing it keeps this reproducible
    for pp in m.parameters():
        pp.requires_grad_(True)
    opt = torch.optim.AdamW(m.parameters(), lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    # class-balanced batch sampling: k images per class per batch (fix for symmetric CE degenerating to ln32 due to repeated classes within a batch)
    idx_by_cls = collections.defaultdict(list)
    for j, c in enumerate(labels_tr):
        idx_by_cls[int(c)].append(j)
    K = 3
    per_batch = K * len(names)
    for ep in range(EPOCHS):
        batches = []
        used = np.zeros(len(labels_tr), dtype=bool)
        rng = np.random.RandomState(SEED * 100 + ep)
        while used.sum() < len(labels_tr):
            sel = []
            for ci in range(len(names)):
                pool = np.array(idx_by_cls[ci])
                if len(pool) == 0:
                    continue
                avail = pool[~used[pool]]
                if len(avail) == 0:
                    continue
                picks = rng.choice(avail, size=min(K, len(avail)), replace=False)
                sel.extend(picks.tolist())
            if not sel:
                break
            for s in sel:
                used[s] = True
            batches.append(np.array(sel, dtype=int))
        tot, cnt = 0.0, 0
        for sel in batches:
            xs = torch.stack([p(images=open_imgs_tr[j])['pixel_values'][0] for j in sel]).to('cuda')
            caps = [TEMPLATE.format(names[c]) for c in labels_tr[sel]]
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
        print('  ep%d loss=%.4f' % (ep + 1, tot / cnt), flush=True)
    torch.save(m.state_dict(), FT_WEIGHTS)
    m.eval()
    protocol('domainft', m, p, open_imgs, texts, labels_te, outd)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
