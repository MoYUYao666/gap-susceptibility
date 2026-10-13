"""Ocean-domain Theorem 5 / bias-field test + exact τ(λ) prediction + class-count sweep.
Ported from tools/clip_a1_margins.py (A1, ImageNet protocol); subset/conventions same as clip_ocean_gap_surgery.py.

Output outputs/ocean_margins.json:
  per_model:
    m_values(67), sigma_m, mean_m, margin_bias_independence(pearson/spearman),
    margins statistics, predicted_tau_exact / predicted_rank1_loss_exact per λ,
    measured {top1, tau} per λ (same as phase 1a), bias-field test: per_class_pearson[λ] (measured per-class shift vs λ‖g‖m_c)
  nsweep (oceanclip & bioclip): N∈{20,40,67} → gap_norm, τ/predicted, top1@λ∈{0.5,1} retention rate
Run: conda run -n pytorch python tools/clip_ocean_margins.py
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
from datasets import load_dataset
import open_clip

TEMPLATE = 'a photo of a {}'
LAMBDAS = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0]
OUT = 'outputs/ocean_margins.json'
SUB = 'outputs/ocean_subset.json'
FISH_CLASSES = ['Actinopterygii', 'Chondrichthyes', 'Coelacanthi']


def load_ds():
    files = sorted(os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data'))
    return load_dataset('parquet', data_files=files, split='train')


def load_openclip(tag):
    if tag == 'bioclip':
        m, _, p = open_clip.create_model_and_transforms(
            'ViT-B-16', pretrained='models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin', device='cuda')
    else:
        ck = torch.load('models/oceanclip-0.15b/oceanclip-bio/epoch_50.pt', map_location='cpu')
        m, _, p = open_clip.create_model_and_transforms(
            'ViT-B-16', pretrained='models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin', device='cuda')
        m.load_state_dict(ck['state_dict'], strict=False)
    m.eval()
    return m, p


def embed(tag, ds, idx, texts, batch=32):
    m, pre = load_openclip(tag)
    tok = open_clip.get_tokenizer('ViT-B-16')
    with torch.no_grad():
        tf = m.encode_text(tok(texts).to('cuda'))
    tf = F.normalize(tf, dim=-1)
    feats = []
    with torch.no_grad():
        for i in range(0, len(idx), batch):
            imgs = []
            for j in idx[i:i + batch]:
                b = ds[j]['file_name']
                if isinstance(b, dict):
                    b = Image.open(io.BytesIO(b['bytes'])) if b.get('bytes') else Image.open(b['path'])
                imgs.append(b)
            xs = torch.stack([pre(im) for im in imgs]).to('cuda')
            feats.append(F.normalize(m.encode_image(xs), dim=-1))
    return tf, torch.cat(feats)


def analyze(tf, base, labels_c, m, gap_norm, d_hat):
    """Full analysis for a given class set / image set (margins prediction + measurement)."""
    S = (base @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S, axis=1)[:, :5]
    margins, all_d, all_b, rank1 = [], [], [], []
    inv_exact = {l: [] for l in LAMBDAS}
    r1_exact = {l: [] for l in LAMBDAS}
    for i in range(len(S)):
        k5 = topk5[i]
        s5 = S[i][k5]
        d_pairs = s5[:, None] - s5[None, :]
        dm = m[k5][:, None] - m[k5][None, :]
        dm = -dm
        upper = np.triu(np.ones((5, 5)), k=1).astype(bool)
        d_flat = d_pairs[upper]
        b_flat = dm[upper]
        margins.append(d_flat)
        all_d.append(d_flat)
        all_b.append(b_flat)
        rank1.append(d_pairs[0, 1:])
        for l in LAMBDAS:
            inv = (l * gap_norm * b_flat > d_flat).sum()
            inv_exact[l].append(1.0 - 2 * inv / 10.0)
            r1_exact[l].append(float((l * gap_norm * dm[0, 1:] > d_pairs[0, 1:]).any()))
    d_all = np.concatenate(all_d)
    r1_all = np.concatenate(rank1)
    r_dm, p_dm = stats.pearsonr(d_all, np.concatenate(all_b))
    rho_dm, p_rho = stats.spearmanr(d_all, np.concatenate(all_b))
    # measured (image-side translation, same as phase 1a)
    measured, class_pearson = {}, {}
    for l in LAMBDAS:
        with torch.no_grad():
            sh = F.normalize(base + l * gap_norm * d_hat, dim=-1)
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
        measured[str(l)] = {'top1': top1, 'tau': float(np.mean(taus))}
        # bias-field test: measured per-class shift vs λ‖g‖m_c
        disp = []
        for c in range(len(m)):
            idxc = np.where(labels_c == c)[0]
            if len(idxc) == 0:
                continue
            disp.append(float(np.mean(Sl[idxc, c] - S[idxc, c])))
        pred = [l * gap_norm * float(m[c]) for c in range(len(m))]
        # only for classes that are non-empty in the measurement
        keep = np.array([len(np.where(labels_c == c)[0]) > 0 for c in range(len(m))])
        if keep.sum() >= 6:
            r_p, p_p = stats.pearsonr(np.array(disp)[keep], np.array(pred)[keep])
            class_pearson[str(l)] = {'pearson': float(r_p), 'p': float(p_p), 'n': int(keep.sum())}
    out = {
        'gap_norm': float(gap_norm),
        'm_values': [float(v) for v in m],
        'sigma_m': float(np.std(m - m.mean())), 'mean_m': float(np.mean(m)),
        'margin_bias_independence': {'pearson_d_b': float(r_dm), 'pearson_p': float(p_dm),
                                     'spearman_d_b': float(rho_dm), 'spearman_p': float(p_rho)},
        'margins': {'mean': float(d_all.mean()), 'std': float(d_all.std()),
                    'q50': float(np.percentile(d_all, 50)), 'q10': float(np.percentile(d_all, 10)),
                    'rank1_mean': float(r1_all.mean()), 'rank1_q10': float(np.percentile(r1_all, 10))},
        'predicted_tau_exact': {str(l): float(np.mean(inv_exact[l])) for l in LAMBDAS},
        'predicted_rank1_loss_exact': {str(l): float(np.mean(r1_exact[l])) for l in LAMBDAS},
        'measured': measured,
        'bias_field_pearson': class_pearson,
    }
    return out


def main():
    ds = load_ds()
    sub = json.load(open(SUB, encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    texts = [TEMPLATE.format(c) for c in classes]
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])

    result = {}
    for tag in ['bioclip', 'oceanclip']:
        print('== %s ==' % tag, flush=True)
        tf, base = embed(tag, ds, idx, texts)
        mu_i = base.mean(0)
        mu_t = tf.mean(0)
        gap_vec = mu_t - mu_i
        gap_norm = gap_vec.norm().item()
        d_hat = gap_vec / gap_norm
        m = (d_hat @ tf.T).cpu().numpy()
        result[tag] = analyze(tf, base, labels, m, gap_norm, d_hat)
        json.dump(result, open(OUT, 'w', encoding='utf-8'), indent=1)
    # class-count sweep (oceanclip & bioclip)
    counts = {c: sub['class_counts'][c] for c in classes}
    order = sorted(classes, key=lambda c: (-counts[c], c))
    nsweep = {}
    for tag in ['bioclip', 'oceanclip']:
        nsweep[tag] = {}
        for N in [20, 40, 67]:
            cs = order[:N]
            keep = np.where(np.isin(labels, [classes.index(c) for c in cs]))[0]
            idxN = [int(idx[i]) for i in keep]
            labsN = labels[keep]
            textsN = [TEMPLATE.format(c) for c in cs]
            tfN, baseN = embed(tag, ds, idxN, textsN)
            gap = (tfN.mean(0) - baseN.mean(0))
            gnorm = gap.norm().item()
            dH = gap / gnorm
            mN = (dH @ tfN.T).cpu().numpy()
            res = analyze(tfN, baseN, labsN, mN, gnorm, dH)
            nsweep[tag][str(N)] = {'gap_norm': res['gap_norm'], 'n_classes': N, 'n_images': int(len(idxN)),
                                   'tau_meas_1': res['measured']['1.0']['tau'],
                                   'tau_pred_1': res['predicted_tau_exact']['1.0'],
                                   'top1_0': res['measured']['0.0']['top1'],
                                   'top1_1': res['measured']['1.0']['top1'],
                                   'sigma_m': res['sigma_m'], 'mean_m': res['mean_m']}
            print('  %s N=%d: gap=%.4f tau_pred1=%.3f tau_meas1=%.3f top1 0→1: %.2f→%.2f sigma_m=%.4f'
                  % (tag, N, gnorm, res['predicted_tau_exact']['1.0'], res['measured']['1.0']['tau'],
                     res['measured']['0.0']['top1'], res['measured']['1.0']['top1'], res['sigma_m']), flush=True)
        json.dump(nsweep, open('outputs/ocean_nsweep.json', 'w', encoding='utf-8'), indent=1)
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
