"""Unified verification of the three remaining theory items of A1 (2026-08-22).

① Correlation-structure bound with the empirical distribution F̂_m (removes the Gaussian conservatism gap)
② O orthogonal family: reproduce r_hat of RandomState(7) → σ̃=std(r·t_c) + pointwise prediction τ_O(λ) of Theorem 1 vs measured
③ Theorem 5 class-contraction per-image micro-verification: centroids from the same 5k samples + exact affine ordering → predicted top-1/τ vs measured (70.32/78.58)

All conventions are identical to tools/clip_a1_{margins,full,subspace}.py (seed 42, fifty-thousand-image sampling,
Flickr30k validation subset 2000-3000 for the gap, same CLIP weights). Output outputs/a1_theory_verify.json.
"""
import os
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
import glob
import json
import sys
import pathlib

import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
from scipy.special import erf
from transformers import CLIPModel, CLIPProcessor
from datasets import Dataset
from torch.utils.data import DataLoader

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from src.dataset import Flickr30kDataset, _collate_fn  # noqa: E402

TEMPLATE = 'a photo of a {}'
N = 5000
LAMBDAS = [-2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 4]


def phi(x):
    return 0.5 * (1.0 + erf(x / np.sqrt(2.0)))


def main():
    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    assert parq, 'no parquet shards'
    ds_in = Dataset.from_parquet(parq)
    names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
    texts = [TEMPLATE.format(c.replace('_', ' ')) for c in names]
    rng = np.random.RandomState(42)
    idx = rng.choice(len(ds_in), N, replace=False)
    sub = ds_in.select(list(idx))
    labels = torch.tensor(sub['label'])

    model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32',
                                      local_files_only=True).cuda().eval()
    processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32',
                                              local_files_only=True)

    with torch.no_grad():
        ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
        tout = model.text_model(**ti)
        pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
        tf = F.normalize(model.text_projection(pooled), dim=-1)
        imgs = []
        for i in range(0, N, 64):
            b = sub[i:i + 64]
            inp = processor(images=b['image'], return_tensors='pt').to('cuda')
            vout = model.vision_model(**inp)
            vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            imgs.append(F.normalize(model.visual_projection(vpooled), dim=-1))
        base = torch.cat(imgs)
        base = base / base.norm(dim=-1, keepdim=True)

    # gap direction (same convention as margins/full/subspace)
    ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
    val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
    loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0,
                        collate_fn=_collate_fn)
    fi, ft = [], []
    with torch.no_grad():
        for batch in loader:
            out = model(pixel_values=batch['image'].cuda(),
                        input_ids=batch['input_ids'].cuda(),
                        attention_mask=batch['attention_mask'].cuda(),
                        return_loss=False)
            fi.append(F.normalize(out.image_embeds, dim=-1))
            ft.append(F.normalize(out.text_embeds, dim=-1))
    fi = torch.cat(fi)
    ft = torch.cat(ft)
    gap_vec = ft.mean(0) - fi.mean(0)
    gap_norm = gap_vec.norm().item()
    d_hat = gap_vec / gap_norm

    m = (d_hat @ tf.T).cpu().numpy()           # m_c for the 1000 classes (raw units)
    mean_m = float(np.mean(m))
    m0 = m - mean_m
    sigma_m = float(np.std(m0))
    S = (base @ tf.T).cpu().numpy()            # 5000×1000 frozen scores
    topk5 = np.argsort(-S, axis=1)[:, :5]
    out = {'meta': {'n_images': N, 'gap_norm': gap_norm, 'mean_m': mean_m,
                    'sigma_m': sigma_m, 'sigma_b': float(np.sqrt(2) * sigma_m)}}

    # ============ ① correlation-structure bound with the empirical distribution F̂_m ============
    # condition on m_1 = u (the actual value for this image); competitors are sampled empirically from the 999 other m values
    # λ>0: P_j = F̂_m(u + d/(λ‖g‖)); λ<0: P_j = 1 − F̂_m(u − d/(|λ|‖g‖))
    res_emp = {}
    for l in LAMBDAS:
        losses = []
        for i in range(N):
            k5 = topk5[i]
            c1 = k5[0]
            u = m[c1]
            dc = S[i][c1] - S[i][k5[1:]]              # the 4 d_{1j}
            ps = []
            for t in (u + dc / (l * gap_norm)) if l > 0 else (u - dc / (abs(l) * gap_norm)):
                sgn_keep = 1.0 if l > 0 else -1.0
                # F̂_m(t) over the other classes (excluding class c1)
                others = np.delete(m, c1)
                frac = float(np.mean(others <= t))
                prob = frac if l > 0 else 1.0 - frac
                ps.append(prob)
            losses.append(1.0 - float(np.prod(ps)))
        res_emp[str(l)] = float(np.mean(losses))
    out['predicted_rank1_loss_emp'] = res_emp

    # ============ ② O orthogonal family (verification of Corollary 1) ============
    rng2 = np.random.RandomState(7)
    rv = torch.tensor(rng2.randn(512), dtype=torch.float32)
    rv = rv - (rv @ d_hat.cpu()) * d_hat.cpu()
    r_hat = (rv / rv.norm()).numpy()
    mO = r_hat @ tf.cpu().numpy().T               # m^O_c for the 1000 classes
    sigma_O = float(np.std(mO))
    out['orthogonal'] = {'sigma_mO': sigma_O, 'ratio_sigmaO_over_sigmaM': sigma_O / sigma_m}
    # Theorem 1 operator: same top-5 structure and margins, only the bias field b^O is replaced (vectorized version)
    mO_t = torch.tensor(mO)
    pred_tau_O = {}
    for l in LAMBDAS:
        inv = []
        for i in range(N):
            k5 = topk5[i]
            s5 = S[i][k5]
            dmat = s5[:, None] - s5[None, :]
            bmat = mO_t[k5][None, :] - mO_t[k5][:, None]   # m_i − m_j (we need j−i)
            bmat = -bmat
            upper = np.triu(np.ones((5, 5)), k=1).astype(bool)
            inv.append(int(((l * gap_norm * bmat.numpy()[upper]) > dmat[upper]).sum()))
        pred_tau_O[str(l)] = 1.0 - 2 * float(np.mean(inv)) / 10.0
    out['predicted_tau_orthogonal'] = pred_tau_O
    meas_tau_O = {}
    fr = json.load(open('outputs/a1_full_results.json', encoding='utf-8'))
    for r in fr:
        if r.get('kind') == 'O':
            meas_tau_O[str(r['lambda'])] = r.get('tau_top5')
    out['measured_tau_orthogonal'] = meas_tau_O

    # ============ ③ Theorem 5: per-image micro-verification of class contraction ============
    cents = torch.stack([base[labels == c].mean(0) for c in sorted(set(labels.numpy().tolist()))])
    cents = cents / cents.norm(dim=-1, keepdim=True)
    cidx = torch.tensor([sorted(set(labels.numpy().tolist())).index(int(li)) for li in labels],
                        device='cuda')
    c_own = cents[cidx]
    e = (c_own - base)                           # 5000×512 (not normalized; the ordering is determined by the numerator)
    Delta = (e @ tf.T).cpu().numpy()             # ⟨e, t_c⟩ 5000×1000
    resP = {}
    self_field = []
    for a in [0.25, 0.5]:
        S2 = S + a * Delta
        pred_top1 = float((S2.argmax(1) == labels.numpy()).mean() * 100)
        taus = []
        for i in range(N):
            k5 = topk5[i]
            r1, r2 = S[i][k5], S2[i][k5]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        resP[str(a)] = {'predicted_top1': round(pred_top1, 2),
                        'predicted_tau': round(float(np.mean(taus)), 4)}
        if a == 0.5:
            y = labels.numpy()
            self_field = [float(Delta[i, y[i]]) for i in range(N)]
    out['class_contraction'] = resP
    out['class_contraction']['self_field_mean_a1'] = float(np.mean(self_field))
    out['class_contraction']['self_field_std_a1'] = float(np.std(self_field))
    # compare against the measurements (P rows of a1_subspace_results.json)
    sp = json.load(open('outputs/a1_subspace_results.json', encoding='utf-8'))
    measP = {}
    for r in sp['results']:
        if r['family'] == 'class_contraction':
            measP[str(r['param'])] = {'top1': r['top1'], 'tau': r['tau_top5']}
    out['class_contraction']['measured'] = measP

    with open('outputs/a1_theory_verify.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print('saved outputs/a1_theory_verify.json')
    print(' ① emp-F:', {k: round(v, 4) for k, v in res_emp.items()})
    print(' ② sigma_O=%.4f (ratio %.3f)  pred_tau_O:' % (sigma_O, out['orthogonal']['ratio_sigmaO_over_sigmaM']),
          {k: round(v, 4) for k, v in pred_tau_O.items()})
    print('    meas_tau_O:', {k: v for k, v in meas_tau_O.items()})
    print(' ③ P:', resP, 'vs measured:', measP)


if __name__ == '__main__':
    main()
