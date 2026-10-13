"""A2 enhancement ②: cross-domain validation of the top-1 loss bound (ocean version of Theorem 3).
For the 4 model families {bioclip, oceanclip, openclip_tf, siglip} × rare-species 67 classes/1608 images:
  (a) deterministic exact (Theorem 3a, true m): mean( any(λ‖g‖b_1j > d_1j) )     —— cross-checked against the archived predicted_rank1_loss_exact
  (c) correlated-structure Gaussian tight bound (Theorem 3c): r1 = 1 - ∫φ(u)∏Φ(σ_λ u + d_1j/(λ‖g‖σ_m)) du (λ>0; for λ<0 use Φ(c_j - u))
  weak bound: P(top-1 wrong) ≤ 5(1 - τ̄_meas)
  measured loss rate: (top1_0 - top1_λ)/top1_0
Output: outputs/ocean_rank1_bound.json
Run: conda run -n pytorch python tools/clip_ocean_rank1_bound.py
"""
import os, sys, json, io
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from scipy.special import erf, erfc, ndtr
from datasets import load_dataset
from transformers import CLIPModel, CLIPProcessor, SiglipModel, SiglipProcessor
import importlib.util

spec = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
ocm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocm)

TEMPLATE = 'a photo of a {}'
LAMBDAS = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0]
OUT = 'outputs/ocean_rank1_bound.json'
SUB = 'outputs/ocean_subset.json'
U = np.arange(-8.0, 8.0 + 1e-9, 0.02)          # numerical integration grid (same as A1)
PHI = np.exp(-U ** 2 / 2) / np.sqrt(2 * np.pi)  # φ(u)


def corr_bound_exact(d1j, lam, gnorm, sigma_m):
    """Correct implementation of Theorem 3c: r1 = 1 - ∫φ(u) ∏_j Φ(σ_λ u + c_j) du, c_j = d_1j/(|λ|‖g‖σ_m)。"""
    lamg = abs(lam) * gnorm * sigma_m
    c = d1j / lamg
    prod = np.ones_like(U)
    for cj in c:
        if lam > 0:
            prod *= ndtr(U + cj)
        else:
            prod *= ndtr(cj - U)
    return 1.0 - float(np.sum(PHI * prod * 0.02))


def enc_tf(m, p, tag, texts, ds, idx, batch=32):
    if tag == 'siglip':
        ti = p(text=texts, return_tensors='pt', padding='max_length', max_length=64).to('cuda')
        with torch.no_grad():
            tf = m.text_model(**ti).pooler_output
        tf = F.normalize(tf, dim=-1)
    else:
        ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
        with torch.no_grad():
            out = m.text_model(**ti)
            pooled = out[1] if isinstance(out, tuple) else out.pooler_output
            tf = F.normalize(m.text_projection(pooled), dim=-1)
    feats = []
    with torch.no_grad():
        for i in range(0, len(idx), batch):
            b = ds[idx[i:i + batch]]['file_name']
            imgs = []
            for x in b:
                imgs.append(Image.open(io.BytesIO(x['bytes'])) if isinstance(x, dict) and x.get('bytes')
                            else Image.open(x['path']) if isinstance(x, dict) else x)
            inp = p(images=imgs, return_tensors='pt').to('cuda')
            if tag == 'siglip':
                vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                f = m.visual_projection(vp) if hasattr(m, 'visual_projection') else vp
            else:
                vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                f = m.visual_projection(vp) if hasattr(m, 'visual_projection') else vp
            feats.append(F.normalize(f, dim=-1))
    return tf, torch.cat(feats)


def run_model(tag, tf, base, labels_c, m_c, gnorm, d_hat):
    S = (base @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S, axis=1)[:, :5]
    sig = float(np.std(m_c))
    rows = {}
    per_img = {l: [] for l in LAMBDAS}  # store (d1j, b1j) per image
    for i in range(len(S)):
        k5 = topk5[i]
        s5 = S[i][k5]
        d_pairs = s5[:, None] - s5[None, :]
        dm = -(m_c[k5][:, None] - m_c[k5][None, :])
        per_img[i] = (d_pairs[0, 1:], dm[0, 1:])
    # recompute the measured (τ, top1) to align with the archived convention
    measured = {}
    for l in LAMBDAS:
        with torch.no_grad():
            sh = F.normalize(base + l * gnorm * d_hat, dim=-1)
        Sl = (sh @ tf.T).cpu().numpy()
        top1 = float((Sl.argmax(1) == labels_c).mean() * 100)
        taus = []
        for i in range(len(S)):
            r1, r2 = S[i][topk5[i]], Sl[i][topk5[i]]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        measured[str(l)] = {'top1': round(top1, 3), 'tau': round(float(np.mean(taus)), 4)}
    top1_0 = measured['0.0']['top1']
    for l in LAMBDAS:
        d1j_all = np.concatenate([per_img[i][0] for i in range(len(S))])
        # (a) exact
        ex = []
        for i in range(len(S)):
            d1, b1 = per_img[i]
            ex.append(float((l * gnorm * b1 > d1).any()))
        # (c) correlated-structure bound: computed per image then averaged
        cc = [corr_bound_exact(per_img[i][0], l, gnorm, sig) for i in range(len(S))]
        cc = np.array([x for x in cc if np.isfinite(x)])
        meas_keep_loss = (top1_0 - measured[str(l)]['top1']) / top1_0 if top1_0 > 0 else np.nan
        weak = 5.0 * (1.0 - measured[str(l)]['tau']) if l != 0.0 else np.nan
        rows[str(l)] = {'exact': round(float(np.mean(ex)), 4),
                        'corr_gauss': round(float(np.nanmean(cc)), 4) if len(cc) else np.nan,
                        'weak_bound': round(weak, 4),
                        'meas_keep_loss': round(float(meas_keep_loss), 4),
                        'tau_meas': measured[str(l)]['tau'],
                        'top1_meas': measured[str(l)]['top1']}
        print('  %s λ=%+.2f exact=%.4f corr=%.4f weak=%.4f meas_loss=%.4f (top1 %.2f)' %
              (tag, l, rows[str(l)]['exact'], rows[str(l)]['corr_gauss'], weak, meas_keep_loss,
               measured[str(l)]['top1']), flush=True)
    return {'sigma_m': round(sig, 4), 'gap_norm': round(gnorm, 4), 'rows': rows}


def main():
    ds = ocm.load_ds()
    sub = json.load(open(SUB, encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    texts = [TEMPLATE.format(c) for c in classes]
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    res = {}
    # open_clip family (bioclip / oceanclip)
    for tag in ['bioclip', 'oceanclip']:
        print('== %s ==' % tag, flush=True)
        tf, base = ocm.embed(tag, ds, idx, texts)
        gap = tf.mean(0) - base.mean(0)
        gnorm = gap.norm().item()
        dH = gap / gnorm
        m_c = (dH @ tf.T).cpu().numpy()
        res[tag] = run_model(tag, tf, base, labels, m_c, gnorm, dH)
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        del tf, base
        torch.cuda.empty_cache()
    # transformers family (openclip_tf / siglip)
    for tag, mdir in [('openclip_tf', 'models/openclip'), ('siglip', 'models/siglip-base-patch16-224')]:
        print('== %s ==' % tag, flush=True)
        if tag == 'siglip':
            m = SiglipModel.from_pretrained(mdir, local_files_only=True).cuda().eval()
            p = SiglipProcessor.from_pretrained(mdir, local_files_only=True)
        else:
            m = CLIPModel.from_pretrained(mdir, local_files_only=True).cuda().eval()
            p = CLIPProcessor.from_pretrained(mdir, local_files_only=True)
        tf, base = enc_tf(m, p, tag, texts, ds, idx)
        gap = tf.mean(0) - base.mean(0)
        gnorm = gap.norm().item()
        dH = gap / gnorm
        m_c = (dH @ tf.T).cpu().numpy()
        res[tag] = run_model(tag, tf, base, labels, m_c, gnorm, dH)
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        del m, tf, base
        torch.cuda.empty_cache()
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
