"""A3 提升①: 全量 NKSID（2617 图, 无 per-class cap）协议复跑。
与 clip_sonar_protocol.py 完全同协议, 仅: ① manifest 全取 ② SonarCLIP 在全量上重训 10ep(同名调度)
       ③ 输出 outputs/sonar_protocol_full.json ④ FT 权重存 outputs/sonar_clip_ft_full.pt
"""
import os, sys, json, io, collections
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
IMG_ROOT = 'data/NKSID/NKSID'
OUT = 'outputs/sonar_protocol_full.json'
FT_WEIGHTS = 'outputs/sonar_clip_ft_full.pt'
CLASSES = ['big propeller', 'cylinder', 'fishing net', 'floats', 'iron pipeline',
           'small propeller', 'soft pipeline', 'tire']
CLASS_DIR = ['big_propeller', 'cylinder', 'fishing_net', 'floats', 'iron_pipeline',
             'small_propeller', 'soft_pipeline', 'tire']


def build_manifest():
    manifest = []
    for c, d in zip(CLASSES, CLASS_DIR):
        p = os.path.join(IMG_ROOT, d)
        if not os.path.isdir(p):
            p = IMG_ROOT  # tire 直接解压在根目录
        fs = sorted(f for f in os.listdir(p) if f.lower().endswith(('.jpg', '.png')))
        manifest.extend((os.path.join(p, f), c) for f in fs)  # 全量: 不截取
    return manifest


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


def protocol(tag, m, p, manifest, texts, labels, outdict):
    imgs = [Image.open(fp).convert('RGB') for fp, _ in manifest]
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
        print('  %s λ=%+.1f top1=%.2f tau_pred=%.4f tau_meas=%.4f CG=%.4f' %
              (tag, l, top1_l, np.mean(preds), np.mean(taus), cg), flush=True)
    # 文本侧 λ=1
    with torch.no_grad():
        tf2 = F.normalize(tf - 1.0 * gnorm * dH, dim=-1)
    S2 = (base @ tf2.T).cpu().numpy()
    taus2 = []
    for i in range(len(S)):
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
    manifest = build_manifest()
    labels = np.array([CLASSES.index(c) for _, c in manifest])
    print('manifest: %d images' % len(manifest), flush=True)
    texts = [TEMPLATE.format(c) for c in CLASSES]
    out = {'meta': {'dataset': 'NKSID (Bohai Bay, Oculus M750d), FULL 2617', 'n_classes': len(CLASSES),
                    'n_images': len(manifest), 'per_class': dict(collections.Counter(c for _, c in manifest))}}
    m, p = load_model()
    protocol('clip_frozen', m, p, manifest, texts, labels, out)
    # SonarCLIP: 全量重训 10ep(与原 650 子集同调度)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().train()
    data = [(manifest[i][0], manifest[i][1]) for i in range(len(manifest))]
    n = len(data)
    opt = torch.optim.AdamW(m.parameters(), lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    imgs = [Image.open(fp).convert('RGB') for fp, _ in manifest]
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(n)
        tot, cnt = 0.0, 0
        for i in range(0, n, 32):
            sel = perm[i:i + 32]
            xs = torch.stack([p(images=imgs[j])['pixel_values'][0] for j in sel]).to('cuda')
            txt = p(text=[TEMPLATE.format(data[j][1]) for j in sel], return_tensors='pt',
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
        print('  ep%d loss=%.4f' % (ep + 1, tot / cnt), flush=True)
    torch.save(m.state_dict(), FT_WEIGHTS)
    m = m.eval()
    protocol('sonar_ft_full', m, p, manifest, texts, labels, out)
    # 陆地对照: 已有 CLIP+FlickrFT 权重(与子集协议一致, 直接全量评估)
    if os.path.exists('outputs/ocean_clip_flickrft.pt'):
        m2 = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda()
        m2.load_state_dict(torch.load('outputs/ocean_clip_flickrft.pt', map_location='cpu'))
        m2 = m2.cuda().eval()
        protocol('clip_flickrft', m2, p, manifest, texts, labels, out)
        del m2
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
