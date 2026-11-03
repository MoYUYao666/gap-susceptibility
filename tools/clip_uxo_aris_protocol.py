"""(d) 多类声呐集复现——ARIS 3000 UXO 极坐标声呐集(DFKI "An Acoustic and Optical Dataset
for the Perception of Underwater UXO", Zenodo 13778485, BSD-3-Clause)。
类=3 种 UXO(标注 JSON 的 "class" 字段;逐帧框)。协议与 NKSID 完全一致,仅 top-k=k=n_class(3)。
输出: outputs/aris_uxo_protocol.json
"""
import os, sys, json, collections
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageFilter
from scipy import stats
from transformers import CLIPModel, CLIPProcessor

TEMPLATE = 'a photo of a {}'
SEED = 42
EPOCHS = 10
MDIR = 'models/clip-vit-base-patch32'
ROOT = 'data/ctx_uxo/uxo_aris'
OUT = 'outputs/aris_uxo_protocol.json'
FT_WEIGHTS = 'outputs/aris_clip_ft.pt'
CAP = 150          # 每类最多图(类间平衡)
MAXSIDE = 640
DEGS = [('speckle_p20', 'speckle', 0.20), ('speckle_p40', 'speckle', 0.40),
        ('blur_r2', 'blur', 2), ('blur_r5', 'blur', 5), ('shadow_strip', 'shadow', None)]


def sonar_deg(im, kind, arg):
    if kind == 'speckle':
        a = np.asarray(im).astype(np.float32) / 255.0
        noise = np.random.default_rng(42).normal(0, arg, a.shape)
        return Image.fromarray((np.clip(a + a * noise, 0, 1) * 255).astype(np.uint8))
    if kind == 'blur':
        return im.filter(ImageFilter.GaussianBlur(arg))
    if kind == 'shadow':
        a = np.asarray(im).astype(np.float32)
        a[:, int(a.shape[1] * 0.55):] *= 0.45
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return im


def _gblur(im, r):
    from PIL import ImageFilter
    return im.filter(ImageFilter.GaussianBlur(r))


def build_manifest():
    rec = os.path.join(ROOT, 'data_export', 'recordings')
    if not os.path.isdir(rec):
        # 递归定位 recordings 目录
        for root, dirs, files in os.walk(ROOT):
            if os.path.basename(root) == 'recordings' and 'data_export' in root:
                rec = root
                break
    man = []
    for cls_dir in sorted(os.listdir(rec)):
        cd = os.path.join(rec, cls_dir)
        if not os.path.isdir(cd):
            continue
        for rname in sorted(os.listdir(cd)):
            rd = os.path.join(cd, rname)
            pol = os.path.join(rd, 'aris_polar')
            lab = os.path.join(rd, 'labels')
            if not (os.path.isdir(pol) and os.path.isdir(lab)):
                continue
            for f in sorted(os.listdir(lab)):
                if not f.endswith('.json'):
                    continue
                try:
                    d = json.load(open(os.path.join(lab, f), encoding='utf-8'))
                except Exception:
                    continue
                c = d.get('class')
                if not c:
                    continue
                stem = f[:-5]
                png = os.path.join(pol, stem + '.png')
                if os.path.exists(png):
                    man.append((png, c))
    # 每类 CAP,均匀抽样
    byc = collections.defaultdict(list)
    for pth, c in man:
        byc[c].append(pth)
    out = []
    for c, lst in sorted(byc.items()):
        rng = np.random.RandomState(SEED)
        sel = list(rng.permutation(len(lst)))[:CAP]
        for i in sel:
            out.append((lst[i], c))
    print('classes:', {c: len(l) for c, l in sorted(byc.items())}, flush=True)
    return out


def load_model():
    m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().eval()
    p = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
    return m, p


def encode(m, p, imgs, texts=None, cap_batch=32):
    with torch.no_grad():
        tf = None
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
    return tf, base


def protocol(tag, m, p, manifest, texts, labels, outdict, k=None):
    imgs = [Image.open(fp).convert('RGB') for fp, _ in manifest]
    tf, base = encode(m, p, imgs, texts)
    gap = tf.mean(0) - base.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    m_c = (dH.cpu().numpy() @ tf.cpu().numpy().T)
    S0 = (base @ tf.T).cpu().numpy()
    ncls = len(texts)
    k = k or ncls
    topk = np.argsort(-S0, axis=1)[:, :k]
    top1 = float((S0.argmax(1) == labels).mean() * 100)
    npair = k * (k - 1) // 2
    rows = []
    for l in [-1.0, -0.5, 0.0, 0.5, 1.0, 2.0]:
        with torch.no_grad():
            sh = F.normalize(base + l * gnorm * dH, dim=-1)
        S = (sh @ tf.T).cpu().numpy()
        taus, preds = [], []
        for i in range(len(S)):
            kk = topk[i]
            s5 = S0[i][kk]
            d_pairs = s5[:, None] - s5[None, :]
            dm = -(m_c[kk][:, None] - m_c[kk][None, :])
            up = np.triu(np.ones((k, k)), k=1).astype(bool)
            inv = (l * gnorm * dm[up] > d_pairs[up]).sum()
            preds.append(1.0 - 2 * inv / npair)
            r1, r2 = S0[i][kk], S[i][kk]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        rows.append({'lambda': l, 'tau_meas': round(float(np.mean(taus)), 4),
                     'tau_pred': round(float(np.mean(preds)), 4)})
        print('  %s λ=%+.1f tau_pred=%.4f tau_meas=%.4f' %
              (tag, l, np.mean(preds), np.mean(taus)), flush=True)
    with torch.no_grad():
        tf2 = F.normalize(tf - 1.0 * gnorm * dH, dim=-1)
    S2 = (base @ tf2.T).cpu().numpy()
    taus2 = []
    for i in range(len(S0)):
        r1, r2 = S0[i][topk[i]], S2[i][topk[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus2.append(t)
    rows.append({'lambda': 'text1.0', 'tau_meas': round(float(np.mean(taus2)), 4)})
    print('  %s T λ=1 tau=%.4f' % (tag, np.mean(taus2)), flush=True)
    outdict[tag] = {'n_images': len(manifest), 'sigma_m': round(float(np.std(m_c)), 4),
                    'mean_m': round(float(np.mean(m_c)), 4), 'top1_0': round(top1, 3),
                    'gnorm': round(gnorm, 4), 'rows': rows}
    json.dump(outdict, open(OUT, 'w', encoding='utf-8'), indent=1)
    return imgs, tf


def deg_map(m, p, manifest, texts, labels, outdict, tf, tag):
    imgs = [Image.open(fp).convert('RGB') for fp, _ in manifest]
    tf_np = tf.cpu().numpy()
    gnorm_out = outdict[tag]['gnorm']
    dH = None
    base = encode(m, p, imgs)[1]
    gap = tf.mean(0) - base.mean(0)
    dH = (gap / gap.norm()).cpu().numpy()
    S0 = (base @ tf.T).cpu().numpy()
    ncls = len(texts)
    topk = np.argsort(-S0, axis=1)[:, :ncls]
    rows = []
    for name, kind, arg in DEGS:
        deg = [sonar_deg(im, kind, arg) for im in imgs]
        fd = encode(m, p, deg)[1]
        # λ_eff: 平均位移在间隙轴上的投影 / ‖g‖
        delta = (fd - base).cpu().numpy()
        lam_eff = float((delta.mean(0) @ dH) / gnorm_out)
        Sd = (fd @ tf.T).cpu().numpy()
        taus = []
        for i in range(len(S0)):
            kk = topk[i]
            r1, r2 = S0[i][kk], Sd[i][kk]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        rows.append({'degrade': name, 'lambda_eff': round(lam_eff, 4),
                     'tau_meas': round(float(np.mean(taus)), 4)})
        print('  deg %-14s lam_eff=%+.4f tau=%.4f' % (name, lam_eff, np.mean(taus)), flush=True)
    outdict[tag + '_deg'] = rows
    json.dump(outdict, open(OUT, 'w', encoding='utf-8'), indent=1)


def main():
    manifest = build_manifest()
    classes = sorted(set(c for _, c in manifest))
    labels = np.array([classes.index(c) for _, c in manifest])
    texts = [TEMPLATE.format(c) for c in classes]
    out = {'meta': {'dataset': 'DFKI UXO (ARIS 3000 polar sonar frames; Zenodo 13778485; BSD-3)',
                    'n_classes': len(classes), 'classes': classes,
                    'n_images': len(manifest)}}
    m, p = load_model()
    imgs, tf = protocol('clip_frozen', m, p, manifest, texts, labels, out)
    deg_map(m, p, manifest, texts, labels, out, tf, 'clip_frozen')
    # 匹配域微调 10ep(与声呐协议同调度)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().train()
    n = len(manifest)
    opt = torch.optim.AdamW(m.parameters(), lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    imgs = [Image.open(fp).convert('RGB') for fp, _ in manifest]
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(n)
        tot, cnt = 0.0, 0
        for i in range(0, n, 32):
            sel = perm[i:i + 32]
            xs = torch.stack([p(images=imgs[j])['pixel_values'][0] for j in sel]).to('cuda')
            txt = p(text=[TEMPLATE.format(manifest[j][1]) for j in sel], return_tensors='pt',
                    padding=True)['input_ids'].to('cuda')
            opt.zero_grad()
            with torch.cuda.amp.autocast():
                outm = m(pixel_values=xs, input_ids=txt, return_loss=False)
                if_ = F.normalize(outm.image_embeds, dim=-1)
                tf_ = F.normalize(outm.text_embeds, dim=-1)
                logits = if_ @ tf_.T * m.logit_scale.exp()
                lab = torch.arange(len(sel), device='cuda')
                loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
            loss.backward()
            opt.step()
            tot += loss.item(); cnt += 1
        sched.step()
        print('  ep%d loss=%.4f' % (ep + 1, tot / max(cnt, 1)), flush=True)
    torch.save(m.state_dict(), FT_WEIGHTS)
    m = m.cuda().eval()
    _, tf2 = protocol('aris_ft', m, p, manifest, texts, labels, out)
    deg_map(m, p, manifest, texts, labels, out, tf2, 'aris_ft')
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
