"""Supplementary experiment A: degradation-surgery equivalence check.
Synthetic degradations (turbidity haze I=J*t+A(1-t) / underwater color cast) applied to ocean images,
measure the projection s of the embedding shift onto d̂ → effective λ_eff = s/||g|| → use the exact predictor to obtain τ_pred(λ_eff),
compare with the measured τ(degradation) — testing whether "domain degradation effects can be predicted in closed form".
output: outputs/ocean_degradation.json
"""
import os, sys, json, io, importlib.util
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from datasets import load_dataset

spec = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
ocm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocm)

OUT = 'outputs/ocean_degradation.json'
# degradation settings: (name, type, parameter)
DEGRADES = [
    ('clean', 'none', None),
    ('haze_t0.60', 'haze', 0.60),
    ('haze_t0.30', 'haze', 0.30),
    ('uw_cast', 'uw', None),
]
HZ_A = np.array([0.85, 0.88, 0.84], dtype=np.float32)   # haze background color
UW_GAIN = np.array([0.55, 0.92, 1.06], dtype=np.float32)  # underwater attenuation: red weak, blue strong


def degrade(arr, cfg):
    name, kind, p = cfg
    if kind == 'none':
        return arr
    if kind == 'haze':
        J = arr.astype(np.float32) / 255.0
        I = J * p + HZ_A * (1.0 - p)
        return (np.clip(I, 0, 1) * 255).astype(np.uint8)
    if kind == 'uw':
        J = arr.astype(np.float32) / 255.0
        I = J * UW_GAIN
        # slight green-bias shift
        I = I - np.array([0.12, 0.0, -0.10], dtype=np.float32)
        return (np.clip(I, 0, 1) * 255).astype(np.uint8)
    raise ValueError(kind)


def main():
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    sub = json.load(open('outputs/ocean_subset.json', encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    texts = [ocm.TEMPLATE.format(c) for c in classes]
    imgs = []
    for j in idx:
        b = ds[j]['file_name']
        im = (Image.open(io.BytesIO(b['bytes'])).convert('RGB')
              if isinstance(b, dict) and b.get('bytes')
              else Image.open(b['path']).convert('RGB') if isinstance(b, dict) else b.convert('RGB'))
        imgs.append(im)

    res = {}
    for tag in ['bioclip', 'oceanclip']:
        print('== %s ==' % tag, flush=True)
        m, pre = ocm.load_openclip(tag)
        tok = open_clip_get_tok()
        with torch.no_grad():
            tf = F.normalize(m.encode_text(tok(texts).to('cuda')), dim=-1)
        # frozen baseline: clean embeddings + score order + bias field
        def enc(im_list):
            feats = []
            with torch.no_grad():
                for i in range(0, len(im_list), 32):
                    xs = torch.stack([pre(im) for im in im_list[i:i + 32]]).to('cuda')
                    feats.append(F.normalize(m.encode_image(xs), dim=-1))
            return torch.cat(feats)
        f0 = enc(imgs)
        gap = tf.mean(0) - f0.mean(0)
        gnorm = gap.norm().item()
        dH = (gap / gnorm).cpu().numpy()
        S0 = (f0 @ tf.T).cpu().numpy()
        topk5 = np.argsort(-S0, axis=1)[:, :5]
        m_c = dH @ tf.cpu().numpy().T
        rows = []
        for name, kind, p in DEGRADES:
            deg_imgs = [Image.fromarray(degrade(np.array(im), (name, kind, p))) for im in imgs]
            fd = enc(deg_imgs)
            delta = fd - f0
            shift = delta.mean(0).cpu().numpy()
            s = float(shift @ dH)
            lam_eff = s / gnorm
            # per-image projection dispersion
            per = (delta.cpu().numpy() @ dH)
            s_std = float(np.std(per))
            # measured τ: clean scores as reference, degraded scores as perturbation
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
            # prediction: exact inversion condition at lam_eff (using the clean m_c and margins)
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
            # degraded top1
            top1 = float((Sd.argmax(1) == labels).mean() * 100)
            rows.append({'degrade': name, 'lam_eff': round(lam_eff, 4), 's_std': round(s_std, 4),
                         'tau_meas': round(tau_meas, 4), 'tau_pred': round(tau_pred, 4),
                         'diff': round(abs(tau_meas - tau_pred), 4),
                         'top1': round(top1, 3), 'top1_clean': round(float((S0.argmax(1) == labels).mean() * 100), 3)})
            print('  %-12s lam_eff=%+.3f (sd %.3f) tau_meas=%.4f tau_pred=%.4f diff=%.4f top1=%.2f' %
                  (name, lam_eff, s_std, tau_meas, tau_pred, abs(tau_meas - tau_pred), top1), flush=True)
        res[tag] = {'gap_norm': round(gnorm, 4), 'rows': rows}
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        del m
        torch.cuda.empty_cache()
    print('DONE ->', OUT, flush=True)


def open_clip_get_tok():
    import open_clip
    return open_clip.get_tokenizer('ViT-B-16')


if __name__ == '__main__':
    main()
