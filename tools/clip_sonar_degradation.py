"""A3 增强②: 声呐退化压力测试（散斑噪声/模糊/阴影条带）→ 检验离轴边界是否跨模态。
与 A2 退化实验同构: 每图退化后嵌入位移投影 s → λ_eff; τ_meas vs τ_pred(λ_eff) (间隙轴预测器);
输出: outputs/sonar_degradation.json
"""
import os, sys, json
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageFilter
from scipy import stats
from transformers import CLIPModel, CLIPProcessor

TEMPLATE = 'a photo of a {}'
MDIR = 'models/clip-vit-base-patch32'
IMG_ROOT = 'data/NKSID/NKSID'
OUT = 'outputs/sonar_degradation.json'
CLASSES = ['big propeller', 'cylinder', 'fishing net', 'floats', 'iron pipeline',
           'small propeller', 'soft pipeline', 'tire']
CLASS_DIR = ['big_propeller', 'cylinder', 'fishing_net', 'floats', 'iron_pipeline',
             'small_propeller', 'soft_pipeline', 'tire']
CAP = 90
DEGS = [('speckle_p20', 'speckle', 0.20), ('speckle_p40', 'speckle', 0.40),
        ('blur_r2', 'blur', 2), ('shadow_strip', 'shadow', None)]


def manifest():
    m = []
    for c, d in zip(CLASSES, CLASS_DIR):
        p = os.path.join(IMG_ROOT, d)
        if not os.path.isdir(p):
            p = IMG_ROOT
        fs = sorted(f for f in os.listdir(p) if f.lower().endswith(('.jpg', '.png')))[:CAP]
        m.extend((os.path.join(p, f), c) for f in fs)
    return m


def degrade(im, kind, arg):
    if kind == 'speckle':
        a = np.asarray(im).astype(np.float32) / 255.0
        noise = np.random.default_rng(42).normal(0, arg, a.shape).astype(np.float32)
        out = np.clip(a + a * noise, 0, 1)
        return Image.fromarray((out * 255).astype(np.uint8))
    if kind == 'blur':
        return im.filter(ImageFilter.GaussianBlur(arg))
    if kind == 'shadow':
        a = np.asarray(im).astype(np.float32)
        h, w = a.shape[:2]
        a[:, int(w * 0.55):] *= 0.45  # 阴影条带
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return im


def main():
    man = manifest()
    labels = np.array([CLASSES.index(c) for _, c in man])
    texts = [TEMPLATE.format(c) for c in CLASSES]
    m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().eval()
    p = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
    imgs = [Image.open(fp).convert('RGB') for fp, _ in man]

    def enc(lst):
        out = []
        with torch.no_grad():
            for i in range(0, len(lst), 32):
                inp = p(images=lst[i:i + 32], return_tensors='pt').to('cuda')
                vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                out.append(F.normalize(m.visual_projection(vp), dim=-1))
        return torch.cat(out)

    ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
    with torch.no_grad():
        out = m.text_model(**ti)
        pooled = out[1] if isinstance(out, tuple) else out.pooler_output
        tf = F.normalize(m.text_projection(pooled), dim=-1)
    f0 = enc(imgs)
    gap = tf.mean(0) - f0.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    m_c = dH.cpu().numpy() @ tf.cpu().numpy().T
    S0 = (f0 @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    res = {'meta': {'model': 'clip_frozen', 'dataset': 'NKSID', 'n_images': len(imgs)}}
    rows = []
    for name, kind, arg in DEGS:
        deg = [degrade(im, kind, arg) for im in imgs]
        fd = enc(deg)
        delta = fd - f0
        shift = delta.mean(0).cpu().numpy()
        s = float(shift @ dH.cpu().numpy())
        lam_eff = s / gnorm
        Sd = (fd @ tf.T).cpu().numpy()
        taus = []
        for i in range(len(S0)):
            r1, r2 = S0[i][topk5[i]], Sd[i][topk5[i]]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        tau_meas = float(np.mean(taus))
        preds = []
        for i in range(len(S0)):
            k5 = topk5[i]
            s5 = S0[i][k5]
            d_pairs = s5[:, None] - s5[None, :]
            dm = -(m_c[k5][:, None] - m_c[k5][None, :])
            up = np.triu(np.ones((5, 5)), k=1).astype(bool)
            inv = (lam_eff * gnorm * dm[up] > d_pairs[up]).sum()
            preds.append(1.0 - 2 * inv / 10.0)
        tau_pred = float(np.mean(preds))
        top1 = float((Sd.argmax(1) == labels).mean() * 100)
        rows.append({'degrade': name, 'lam_eff': round(lam_eff, 4), 'tau_meas': round(tau_meas, 4),
                     'tau_pred': round(tau_pred, 4), 'diff': round(abs(tau_meas - tau_pred), 4),
                     'top1': round(top1, 3)})
        print('%-14s lam_eff=%+.4f tau_meas=%.4f tau_pred=%.4f diff=%.4f top1=%.2f' %
              (name, lam_eff, tau_meas, tau_pred, abs(tau_meas - tau_pred), top1), flush=True)
    res['rows'] = rows
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
