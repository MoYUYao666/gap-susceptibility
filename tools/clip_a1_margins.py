"""Supporting theory refinement for A1: pairwise margin extraction + exact τ(λ) prediction (to be run together with #8, not executed).

Purpose (together with docs/theory_tau_bound.md §9-1 and docs/theory_first_order_residual.md):
  1. On 5k samples (RandomState(42), the same sampling as baseline_metrics) compute for the frozen model:
     the top-5 class set, the 10 pairwise margins {d_ij}, and the rank-1 margin d_min^1;
  2. Compute m_c = d̂·t_c (d̂ comes from the gap vector of the Flickr30k validation subset);
  3. **Exact prediction** (without any distributional assumption):
     inversion condition (exact version of Lemma 1) λ‖g‖(m_j − m_i) > d_ij ⟹
        predicted_τ(λ)   = mean_i(1 − 2·inv_i(λ)/10)
        predicted_rank1_loss(λ) = mean_i(1{∃j≠c1: λ‖g‖(m_j − m_c1) > d_c1j})
     plus the Gaussian-model version (the Φ̄ formula) as a comparison;
  4. Compare against the measured τ(λ): the T condition of baseline_metrics (same 5k samples) + a1_full_results (50k).

Output: outputs/a1_margins.json (margin statistics + m statistics + the two prediction curves + the measured curves).
Run: conda run -n pytorch python tools/clip_a1_margins.py  (a few minutes, only forward passes of the frozen model)
"""
import os
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')   # required for Windows + torch
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
from src.dataset import Flickr30kDataset, _collate_fn   # noqa: E402

TEMPLATE = 'a photo of a {}'
N = 5000
LAMBDAS = [-2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 4]


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

    # gap direction (Flickr30k validation subset, same convention as baseline_metrics)
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

    m = (d_hat @ tf.T).cpu().numpy()          # per-class m_c
    S = (base @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S, axis=1)[:, :5]     # frozen top-5 (descending)

    # per-image margin extraction
    margins, rank1_margins, inv_exact, inv_gauss, r1_loss_exact, r1_loss_gauss = (
        [], [], {l: [] for l in LAMBDAS}, {l: [] for l in LAMBDAS},
        {l: [] for l in LAMBDAS}, {l: [] for l in LAMBDAS})
    all_d, all_b = [], []          # independence check: all paired (margin, bias difference) samples
    sigma_b = float(np.sqrt(2) * np.std(m))
    for i in range(N):
        k5 = topk5[i]
        s5 = S[i][k5]
        d_pairs = s5[:, None] - s5[None, :]           # d_ij = s_i − s_j
        dm = m[k5][:, None] - m[k5][None, :]          # b_ij = m_i − m_j (to be used as j−i with the sign flipped)
        dm = -dm                                      # b_ij = m_j − m_i
        upper = np.triu(np.ones((5, 5)), k=1).astype(bool)
        d_flat = d_pairs[upper]                       # the 10 margins (i above j)
        b_flat = dm[upper]
        margins.append(d_flat)
        all_d.append(d_flat)
        all_b.append(b_flat)
        rank1_margins.append(d_pairs[0, 1:])          # the 4 rank-1 margins
        for l in LAMBDAS:
            inv = (l * gap_norm * b_flat > d_flat).sum()
            inv_exact[l].append(1.0 - 2 * inv / 10.0)
            r1_loss_exact[l].append(float((l * gap_norm * dm[0, 1:] > d_pairs[0, 1:]).any()))
            # Gaussian-model version (the Φ̄ formula, theory_tau_bound §4)
            u = d_flat / (abs(l) * gap_norm * sigma_b + 1e-12)
            p_g = stats.norm.sf(u)
            inv_gauss[l].append(1.0 - 2 * np.mean(p_g))
            u1 = d_pairs[0, 1:] / (abs(l) * gap_norm * sigma_b + 1e-12)
            r1_loss_gauss[l].append(float(np.mean(stats.norm.sf(u1))))

    # ------------------- top-1 bound with correlation structure (derivation completed 2026-08-22) -------------------
    # exact definition: given m_1 = mean_m + σ_m u, the competitors are conditionally independent:
    #   λ>0: P(c1 survives | u) = ∏_j Φ(u + c_j),   c_j = d_{1j}/(λ‖g‖σ_m)
    #   λ<0: P(c1 survives | u) = ∏_j Φ(−u − c_j)
    # r1_loss_corr(λ) = 1 − E_u[∏_j Φ(±(u+c_j))]   (Gaussian working model; numerical quadrature)
    mean_m = float(np.mean(m))
    m0 = m - mean_m
    sigma_m = float(np.std(m0))
    ugrid = np.arange(-8.0, 8.0 + 1e-9, 0.02)
    wphi = (1.0 / np.sqrt(2 * np.pi)) * np.exp(-0.5 * ugrid ** 2) * 0.02
    r1_corr = {l: [] for l in LAMBDAS}
    for i in range(N):
        k5 = topk5[i]
        dm4 = m0[k5[1:]] - m0[k5[0]]             # m_j − m_1 (the 4 competitors)
        d4 = S[i][k5[0]] - S[i][k5[1:]]          # d_{1j}
        for l in LAMBDAS:
            cj = d4 / (abs(l) * gap_norm * sigma_m + 1e-12)
            sgn = 1.0 if l > 0 else -1.0
            # P(survive | u) = ∏_j Φ(sgn·u + c_j) (λ>0: Z_j ≤ u + c_j; λ<0: Z_j ≥ u − c_j)
            arg = sgn * ugrid[:, None] + cj[None, :]
            phi = 0.5 * (1.0 + erf(arg / np.sqrt(2.0)))
            surv = np.prod(phi, axis=1)
            r1_corr[l].append(1.0 - float(np.sum(wphi * surv)))
    r1_corr_out = {str(l): float(np.mean(r1_corr[l])) for l in LAMBDAS}

    d_all = np.concatenate(margins)
    r1_all = np.concatenate(rank1_margins)
    pred_exact = {str(l): float(np.mean(inv_exact[l])) for l in LAMBDAS}
    pred_gauss = {str(l): float(np.mean(inv_gauss[l])) for l in LAMBDAS}
    r1_exact = {str(l): float(np.mean(r1_loss_exact[l])) for l in LAMBDAS}
    r1_gauss = {str(l): float(np.mean(r1_loss_gauss[l])) for l in LAMBDAS}

    # independence check: pairwise correlation between the margin d_ij and the bias difference b_ij
    d_cat = np.concatenate(all_d)
    b_cat = np.concatenate(all_b)
    r_dm, p_dm = stats.pearsonr(d_cat, b_cat)
    rho_dm, p_rho = stats.spearmanr(d_cat, b_cat)
    indep = {'pearson_d_b': float(r_dm), 'pearson_p': float(p_dm),
             'spearman_d_b': float(rho_dm), 'spearman_p': float(p_rho),
             'n_pairs': int(len(d_cat))}
    print('margin/bias independence: pearson=%.4f (p=%.3g) spearman=%.4f (p=%.3g) n=%d' %
          (r_dm, p_dm, rho_dm, p_rho, len(d_cat)), flush=True)

    # measured reference: the T condition of baseline_metrics (same 5k samples) + a1_full_results (50k)
    # measured τ(λ) on the same samples (image-side T shift) — closes the gap between "5k prediction vs 50k measurement"
    measured_5k = {}
    with torch.no_grad():
        for l in LAMBDAS:
            shifted = F.normalize(base + l * gap_norm * d_hat, dim=-1)
            Sl = (shifted @ tf.T).float().cpu().numpy()
            top1 = float((Sl.argmax(1) == labels.numpy()).mean() * 100)
            taus = []
            for i in range(N):
                k5 = topk5[i]
                r1, r2 = S[i][k5], Sl[i][k5]
                if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                    continue
                t, _ = stats.kendalltau(r1, r2)
                if np.isfinite(t):
                    taus.append(t)
            measured_5k[str(l)] = {'top1': top1, 'tau': float(np.mean(taus))}
            print('measured 5k λ=%g: top1=%.2f tau=%.4f' % (l, top1, measured_5k[str(l)]['tau']),
                  flush=True)
    measured_50k = {}
    if os.path.exists('outputs/a1_full_results.json'):
        fr = json.load(open('outputs/a1_full_results.json', encoding='utf-8'))
        for r in fr:
            if r.get('kind') == 'T':
                measured_50k[str(r['lambda'])] = {'top1': r.get('top1'),
                                                  'tau': r.get('tau_top5')}

    out = {
        'meta': {'n_images': N, 'sample_seed': 42, 'gap_norm': gap_norm,
                 'std_m': float(np.std(m)), 'sigma_b': sigma_b, 'mean_m': mean_m},
        'margin_bias_independence': indep,
        'margins': {'mean': float(d_all.mean()), 'std': float(d_all.std()),
                    'q10': float(np.percentile(d_all, 10)), 'q50': float(np.percentile(d_all, 50)),
                    'q90': float(np.percentile(d_all, 90)),
                    'rank1_mean': float(r1_all.mean()), 'rank1_q10': float(np.percentile(r1_all, 10))},
        'm_values': [float(v) for v in m],   # 1000 classes m_c (raw units, for plots)
        'pair_samples': {'d': [float(v) for v in d_all], 'b': [float(v) for v in b_cat]},  # 50000 pairs (d, b)
        'predicted_tau_exact': pred_exact, 'predicted_tau_gauss': pred_gauss,
        'predicted_rank1_loss_exact': r1_exact, 'predicted_rank1_loss_gauss': r1_gauss,
        'predicted_rank1_loss_corr': r1_corr_out,
        'measured_tau_5k': measured_5k, 'measured_tau_50k': measured_50k,
    }
    with open('outputs/a1_margins.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print('saved outputs/a1_margins.json')
    print('margin stats: mean=%.4f q50=%.4f q10=%.4f | rank1_mean=%.4f' %
          (out['margins']['mean'], out['margins']['q50'], out['margins']['q10'],
           out['margins']['rank1_mean']))
    for l in [0.25, 0.5, 1, 2, 4]:
        print('λ=%g: τ_exact=%.3f τ_gauss=%.3f | r1_loss_exact=%.3f | τ_5k_meas=%s' %
              (l, pred_exact[str(l)], pred_gauss[str(l)], r1_exact[str(l)],
               measured_5k.get(str(l), {}).get('tau', '—')))


if __name__ == '__main__':
    main()
