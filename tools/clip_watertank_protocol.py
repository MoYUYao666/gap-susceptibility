"""L6-B / batch 3: full replication on the third sonar dataset (mvaldenegro watertank, ARIS 3000, 10 classes).
Protocol identical to clip_sonar_protocol_full.py (frozen -> FT 10ep -> terrestrial control flickrft),
plus degradation subsets (speckle20/blur_r2/shadow).
- Data: data/second_sonar/watertank96.hdf5 (x_train/val/test, y, class_names; 10 classes + background[10])
- Eval set: x_test (10 classes only); train set: x_train (10 classes)
- Frozen backbone: CLIP ViT-B/32 (models/clip-vit-base-patch32), same backbone as the sonar protocol
- Terrestrial control: outputs/ocean_clip_flickrft.pt (same-day dose Flickr30k FT)
Output: outputs/watertank_protocol.json
Run: conda run -n pytorch python tools/clip_watertank_protocol.py
"""
import os, sys, json
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import h5py
import torch
import torch.nn.functional as F
from PIL import Image, ImageFilter
from scipy import stats
from transformers import CLIPModel, CLIPProcessor

TEMPLATE = 'a photo of a {}'
SEED = 42
EPOCHS = 10
MDIR = 'models/clip-vit-base-patch32'
H5 = 'data/second_sonar/watertank96.hdf5'
OUT = 'outputs/watertank_protocol.json'
FT_WEIGHTS = 'outputs/watertank_clip_ft.pt'
FR = 'outputs/ocean_clip_flickrft.pt'
DEGS = [('speckle_p20', 'speckle', 0.20), ('blur_r2', 'blur', 2), ('shadow_strip', 'shadow', None)]


def load_h5():
    f = h5py.File(H5, 'r')
    names = [n.decode() if isinstance(n, bytes) else n for n in f['class_names'][:]]
    x = np.concatenate([f['x_train'][:], f['x_val'][:], f['x_test'][:]], 0)
    y = np.concatenate([f['y_train'][:], f['y_val'][:], f['y_test'][:]], 0)
    n_tr, n_va, n_te = len(f['x_train']), len(f['x_val']), len(f['x_test'])
    # 10 classes (excluding background=10)
    keep = y < 10
    i_tr = np.where((np.arange(len(y)) < n_tr) & keep)[0]
    i_te = np.where((np.arange(len(y)) >= n_tr + n_va) & keep)[0]
    return names[:10], x, y, i_tr, i_te


def to_img(a):
    a = np.squeeze(a)
    if a.max() <= 1.5:
        a = a * 255.0
    a = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(a).convert('RGB')


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
    return topk5, S0, tf, base


def degradation(tag, m, p, imgs, texts, labels, topk5, S0, tf, outdict):
    with torch.no_grad():
        f0f = []
        for i in range(0, len(imgs), 32):
            inp = p(images=imgs[i:i + 32], return_tensors='pt').to('cuda')
            vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
            vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            f0f.append(F.normalize(m.visual_projection(vp), dim=-1))
        f0 = torch.cat(f0f)
    gap = tf.mean(0) - f0.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    rows = []
    for name, kind, arg in DEGS:
        if kind == 'speckle':
            out = []
            for im in imgs:
                a = np.asarray(im).astype(np.float32) / 255.0
                noise = np.random.default_rng(42).normal(0, arg, a.shape).astype(np.float32)
                o = np.clip(a + a * noise, 0, 1)
                out.append(Image.fromarray((o * 255).astype(np.uint8)))
            deg = out
        elif kind == 'blur':
            deg = [im.filter(ImageFilter.GaussianBlur(arg)) for im in imgs]
        else:
            out = []
            for im in imgs:
                a = np.asarray(im).astype(np.float32)
                h, w = a.shape[:2]
                a[:, int(w * 0.55):] *= 0.45
                out.append(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
            deg = out
        with torch.no_grad():
            fd = []
            for i in range(0, len(deg), 32):
                inp = p(images=deg[i:i + 32], return_tensors='pt').to('cuda')
                vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                fd.append(F.normalize(m.visual_projection(vp), dim=-1))
            fd = torch.cat(fd)
        delta = (fd - f0).mean(0).cpu().numpy()
        lam_eff = float(delta @ dH.cpu().numpy()) / gnorm
        Sd = (fd @ tf.T).cpu().numpy()
        taus = []
        for i in range(len(S0)):
            r1, r2 = S0[i][topk5[i]], Sd[i][topk5[i]]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        rows.append({'deg': name, 'lambda_eff': round(lam_eff, 4),
                     'tau_meas': round(float(np.mean(taus)), 4)})
        print('  %s %s λ_eff=%+.4f tau=%.4f' % (tag, name, lam_eff, np.mean(taus)), flush=True)
    outdict['deg_' + tag] = rows
    json.dump(outdict, open(OUT, 'w', encoding='utf-8'), indent=1)


def main():
    names, x, y, i_tr, i_te = load_h5()
    cls_idx_tr = y[i_tr]
    cls_idx_te = y[i_te]
    print('train %d / eval %d / classes %s' % (len(i_tr), len(i_te), names), flush=True)
    imgs_tr = [to_img(x[i]) for i in i_tr]
    imgs_te = [to_img(x[i]) for i in i_te]
    texts = [TEMPLATE.format(c) for c in names]
    m0, p = load_model()
    outd = {'meta': {'dataset': 'mvaldenegro watertank (ARIS 3000)', 'n_eval': len(i_te),
                     'n_train': len(i_tr), 'classes': names}}
    print('== frozen ==', flush=True)
    topk5, S0, tf, base = protocol('frozen', m0, p, imgs_te, texts, cls_idx_te, outd)
    degradation('frozen', m0, p, imgs_te, texts, cls_idx_te, topk5, S0, tf, outd)

    # terrestrial control (flickrft)
    print('== flickrft (terrestrial) ==', flush=True)
    fr = CLIPModel.from_pretrained(MDIR, local_files_only=True)
    fr.load_state_dict(torch.load(FR, map_location='cpu'))
    fr = fr.cuda().eval()
    protocol('flickrft', fr, p, imgs_te, texts, cls_idx_te, outd)

    # domain fine-tuning (watertank FT)
    print('== domain FT ==', flush=True)
    m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().train()
    for pp in m.parameters():
        pp.requires_grad_(True)
    opt = torch.optim.AdamW(m.parameters(), lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    n = len(imgs_tr)
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(n)
        tot, cnt = 0.0, 0
        for i in range(0, n, 32):
            sel = perm[i:i + 32]
            xs = torch.stack([p(images=imgs_tr[j])['pixel_values'][0] for j in sel]).to('cuda')
            caps = [TEMPLATE.format(names[c]) for c in cls_idx_tr[sel]]
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
    topk5t, S0t, tft, baset = protocol('domainft', m, p, imgs_te, texts, cls_idx_te, outd)
    degradation('domainft', m, p, imgs_te, texts, cls_idx_te, topk5t, S0t, tft, outd)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
