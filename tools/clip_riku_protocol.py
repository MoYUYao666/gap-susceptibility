"""riku-1825 FLS 数据集增量协议(与 clip_watertank_protocol.py 同构,仅数据装载不同)。
数据: Roboflow 导出,11 类 YOLO(mine + 10 debris); Train 1627 / val 202 / test 206;
全分辨率原图((438,658)/(500,605)/(416,416))——与 watertank 96×96 图块互为补充,加深
"分辨率/裁剪不变性"证据;mine 类(sonar7 来源)为类集增量。
图像级标签: 每图取标注实例数最多的类(多标注图占比将在输出中报告);无标注图剔除。
输出: outputs/riku_protocol.json
"""
import os, sys, json, glob, collections
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import yaml
import torch
import torch.nn.functional as F
from PIL import Image, ImageFilter
from scipy import stats
from transformers import CLIPModel, CLIPProcessor

TEMPLATE = 'a photo of a {}'
SEED = 42
EPOCHS = 10
MDIR = 'models/clip-vit-base-patch32'
ROOT = 'data/second_sonar/riku1825/Dataset'
OUT = 'outputs/riku_protocol.json'
FT_WEIGHTS = 'outputs/riku_clip_ft.pt'
FR = 'outputs/ocean_clip_flickrft.pt'
DEGS = [('speckle_p20', 'speckle', 0.20), ('blur_r2', 'blur', 2), ('shadow_strip', 'shadow', None)]


def load_riku(split):
    """返回 (imgs, labels, class_names)。每图取实例数最多类。"""
    cfg = yaml.safe_load(open(os.path.join(ROOT, 'data.yaml'), encoding='utf-8'))
    names = [str(n) for n in cfg['names'].values()] if isinstance(cfg['names'], dict) else list(cfg['names'])
    img_dir = os.path.join(ROOT, 'images', split)
    lab_dir = os.path.join(ROOT, 'labels', split)
    imgs, labels, multi, none = [], [], 0, 0
    for fn in sorted(os.listdir(img_dir)):
        if not fn.lower().endswith(('.jpg', '.png')):
            continue
        tf = os.path.join(lab_dir, os.path.splitext(fn)[0] + '.txt')
        if not os.path.exists(tf):
            none += 1
            continue
        cls = collections.Counter()
        for line in open(tf):
            cls[int(line.split()[0])] += 1
        if not cls:
            none += 1
            continue
        if len(cls) > 1:
            multi += 1
        best = max(cls, key=cls.get)
        imgs.append(os.path.join(img_dir, fn))
        labels.append(best)
    print('  %s: %d imgs (multi-class %d, 无标注 %d)' % (split, len(imgs), multi, none), flush=True)
    return imgs, np.array(labels), names, multi, none


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
    imgs_te, lab_te, names, multi, none = load_riku('test')
    imgs_tr, lab_tr, _, _, _ = load_riku('train')
    labels_te = lab_te
    texts = [TEMPLATE.format(c) for c in names]
    open_imgs = [Image.open(fp).convert('RGB') for fp in imgs_te]
    open_imgs_tr = [Image.open(fp).convert('RGB') for fp in imgs_tr]
    print('eval %d imgs / %d classes' % (len(open_imgs), len(names)), flush=True)
    m0, p = load_model()
    outd = {'meta': {'dataset': 'riku-1825 (Roboflow: ARIS3k full-res + sonar7 mine; 11 classes)',
                     'n_eval': len(open_imgs), 'n_train': len(open_imgs_tr),
                     'multi_class_in_eval': multi, 'no_label_in_eval': none, 'classes': names}}
    print('== frozen ==', flush=True)
    protocol('frozen', m0, p, open_imgs, texts, labels_te, outd)
    print('== flickrft (terrestrial) ==', flush=True)
    fr = CLIPModel.from_pretrained(MDIR, local_files_only=True)
    fr.load_state_dict(torch.load(FR, map_location='cpu'))
    fr = fr.cuda().eval()
    protocol('flickrft', fr, p, open_imgs, texts, labels_te, outd)
    print('== domain FT ==', flush=True)
    m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().train()
    for pp in m.parameters():
        pp.requires_grad_(True)
    opt = torch.optim.AdamW(m.parameters(), lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    n = len(open_imgs_tr)
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(n)
        tot, cnt = 0.0, 0
        for i in range(0, n, 32):
            sel = perm[i:i + 32]
            xs = torch.stack([p(images=open_imgs_tr[j])['pixel_values'][0] for j in sel]).to('cuda')
            caps = [TEMPLATE.format(names[c]) for c in lab_tr[sel]]
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
