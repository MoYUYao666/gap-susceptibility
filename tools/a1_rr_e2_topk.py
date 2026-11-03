"""A1 revision E2 -- top-k ablation for the order-preservation coefficient tau (answers R2.2).

Reviewer R2.2: the choice of top-5 for the frozen class sets is unjustified; a top-k ablation is
required. This script recomputes, for k in {1,3,5,10,20,50,100}:

  (a) tau under the *same* gap-surgery grid (family T, lambda in GRID),
  (b) tau under the *same* 26-condition perturbation grid used by
      tools/clip_a1_baseline_metrics.py, so that the tau-vs-top1 Spearman correlation
      reported in the paper (tau 0.926) can be recomputed per k,
  (c) the Spearman between the per-lambda tau curve of each k and the reference k=5 curve,
  (d) the "exact predictor" tau_pred(lambda) from the first-order bias-field model
      (Lemma-1 inversion condition, generalised from 10 pairs at k=5 to k(k-1)/2 pairs)
      and the resulting prediction error against the measured tau.

Protocol is byte-compatible with the archived A1 scripts (same model, same 5000-image sample
RandomState(42), same Flickr30k rows 2000..3000 gap direction, same RandomState(7) perturbation
stream, same condition order), so the k=5 row must reproduce outputs/a1_baseline_metrics.json.

Two class-list conventions are evaluated because the parquet shards carry 1001 label names
(the 1000 real ImageNet-1K names plus a trailing placeholder 'none' that no image uses):
  - legacy1001 : matches the archived A1 scripts / the published tau tables
  - clean1000  : drops the placeholder, matches train_class_aligned.imagenet_class_names()

tau is computed with a vectorised but *exactly equivalent* estimator: with continuous similarity
scores there are no ties, so Kendall tau_b equals 1 - 2*(#discordant pairs)/C(k,2). The script
cross-checks this against the archived scipy-based tools/clip_a1_probe2.py::kendall_topk loop and
records the maximum absolute deviation in the JSON.

Output: outputs/a1_rr_e2_topk.json   (no existing JSON is modified)
Run:    D:\\Anaconda\\envs\\pytorch\\python.exe tools/a1_rr_e2_topk.py
"""
import os
import sys
import json
import glob
import time
import hashlib

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
from datasets import Dataset
from transformers import CLIPModel, CLIPProcessor
from torch.utils.data import DataLoader

from src.dataset import Flickr30kDataset, _collate_fn  # noqa: E402

TEMPLATE = 'a photo of a {}'
N = 5000
KS = [1, 3, 5, 10, 20, 50, 100]
GRID = [-2.0, -1.0, -0.5, 0.0, 0.25, 0.5, 1.0, 2.0, 4.0]   # the published T-family surgery grid
OUT = 'outputs/a1_rr_e2_topk.json'
PLACEHOLDER_IDX = 1000          # 'none' in the 1001-name legacy label list
CHUNK = 256


# --------------------------------------------------------------------------- helpers
def shard_signature(parq):
    h = hashlib.sha1()
    for p in parq:
        h.update(os.path.basename(p).encode())
        h.update(str(os.path.getsize(p)).encode())
    return h.hexdigest()[:16]


def linear_cka(X, Y):
    """Identical to tools/clip_a1_baseline_metrics.py::linear_cka."""
    XX = X @ X.T
    YY = Y @ Y.T
    XY = X @ Y.T
    denom = (torch.trace(XX @ XX).item() * torch.trace(YY @ YY).item()) ** 0.5
    return (torch.trace(XY @ XY).item() / denom) if denom > 0 else 0.0


def kendall_topk_scipy(base_np, cur_np, topk):
    """ARCHIVED estimator (tools/clip_a1_probe2.py::kendall_topk) -- used only as a cross-check."""
    taus = []
    for i in range(len(base_np)):
        r1 = base_np[i][topk[i]]
        r2 = cur_np[i][topk[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    if not taus:
        return None
    return float(np.mean(taus))


def kendall_topk_notie(base_np, cur_np, topk):
    """Vectorised tau WITHOUT tie correction (1 - 2D/C(k,2)) -- diagnostic only."""
    n, k = topk.shape
    if k < 2:
        return None
    P = k * (k - 1) // 2
    r1 = np.take_along_axis(base_np, topk, axis=1).astype(np.float64)
    r2 = np.take_along_axis(cur_np, topk, axis=1).astype(np.float64)
    up = np.triu(np.ones((k, k), dtype=bool), 1)
    out = np.empty(n)
    for s in range(0, n, CHUNK):
        e = min(n, s + CHUNK)
        a = r1[s:e, :, None] - r1[s:e, None, :]
        b = r2[s:e, :, None] - r2[s:e, None, :]
        disc = ((a[:, up] * b[:, up]) < 0).sum(axis=1)
        out[s:e] = 1.0 - 2.0 * disc / P
    return float(out.mean())


def kendall_topk(base_np, cur_np, topk):
    """Vectorised mean Kendall tau_b over the frozen top-k sets -- matches scipy exactly.

    Per image: tau_b = (C - D) / sqrt((n0 - n1)(n0 - n2)) with n0 = C(k,2) and n1/n2 the numbers
    of pairs tied in the frozen / perturbed score vector. The archived estimator
    (tools/clip_a1_probe2.py::kendall_topk) calls scipy.stats.kendalltau, i.e. tau_b, so the tie
    correction is kept here; the cross-check in the JSON verifies machine-precision agreement.
    Returns (mean_tau or None, fraction_of_images_with_a_tie).
    """
    n, k = topk.shape
    if k < 2:
        return None, 0.0
    n0 = k * (k - 1) // 2
    r1 = np.take_along_axis(base_np, topk, axis=1).astype(np.float64)
    r2 = np.take_along_axis(cur_np, topk, axis=1).astype(np.float64)
    up = np.triu(np.ones((k, k), dtype=bool), 1)
    out = np.empty(n)
    tied = 0
    for s in range(0, n, CHUNK):
        e = min(n, s + CHUNK)
        a = r1[s:e, :, None] - r1[s:e, None, :]
        b = r2[s:e, :, None] - r2[s:e, None, :]
        af = a[:, up]
        bf = b[:, up]
        cmd = np.sign(af * bf).sum(axis=1)          # C - D (tied pairs contribute 0)
        n1 = (af == 0).sum(axis=1)
        n2 = (bf == 0).sum(axis=1)
        denom = np.sqrt((n0 - n1).astype(float) * (n0 - n2).astype(float))
        with np.errstate(divide='ignore', invalid='ignore'):
            t = np.where(denom > 0, cmd / denom, np.nan)
        out[s:e] = t
        tied += int(((n1 > 0) | (n2 > 0)).sum())
    finite = out[np.isfinite(out)]
    if finite.size == 0:
        return None, tied / n
    return float(finite.mean()), tied / n


def top1_agreement(base_np, cur_np):
    """Diagnostic (NOT tau): fraction of images whose arg-max class is unchanged."""
    return float((base_np.argmax(1) == cur_np.argmax(1)).mean())


def predicted_tau_table(base_np, idxk, m, gap_norm, lams):
    """First-order bias-field prediction of tau on the frozen top-k sets, for every lambda.

    Perturbed score model: s_c' = s_c + lam*||g||*m_c (Section 4 of the manuscript).
    A pair (a,b) with a ranked above b under the frozen model is inverted iff
        lam*||g||*(m_b - m_a) > s_a - s_b .
    tau_i = 1 - 2 * (#inverted pairs) / C(k,2); returned value is the mean over images.
    Exactly the estimator of tools/clip_a1_margins.py, generalised from k=5 to arbitrary k.
    """
    n, k = idxk.shape
    if k < 2:
        return {lam: None for lam in lams}
    P = k * (k - 1) // 2
    S = np.take_along_axis(base_np, idxk, axis=1).astype(np.float64)
    M = m[idxk].astype(np.float64)
    up = np.triu(np.ones((k, k), dtype=bool), 1)
    acc = {lam: 0.0 for lam in lams}
    for s in range(0, n, CHUNK):
        e = min(n, s + CHUNK)
        d = S[s:e, :, None] - S[s:e, None, :]          # d_ab = s_a - s_b (a above b)
        b = M[s:e, None, :] - M[s:e, :, None]          # b_ab = m_b - m_a
        d_flat = d[:, up]
        b_flat = b[:, up]
        for lam in lams:
            inv = (lam * gap_norm * b_flat > d_flat).sum(axis=1)
            acc[lam] += float((1.0 - 2.0 * inv / P).sum())
    return {lam: acc[lam] / n for lam in lams}


# --------------------------------------------------------------------------- main
def main():
    t_start = time.time()
    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    assert parq, 'no parquet shards under data/imagenet_hf'
    ds_in = Dataset.from_parquet(parq)
    names_all = list(ds_in.features['label'].names)
    legacy_names = [n.split(',')[0].strip().replace('_', ' ') for n in names_all]
    clean_names = [n for i, n in enumerate(legacy_names) if i != PLACEHOLDER_IDX]
    assert len(legacy_names) == 1001 and len(clean_names) == 1000, 'unexpected class list'
    print('class lists: legacy1001=%d clean1000=%d (placeholder at %d = %r)'
          % (len(legacy_names), len(clean_names), PLACEHOLDER_IDX, legacy_names[PLACEHOLDER_IDX]),
          flush=True)

    rng = np.random.RandomState(42)
    idx = rng.choice(len(ds_in), N, replace=False)
    sub = ds_in.select(list(idx))
    labels = torch.tensor(sub['label'])
    assert labels.max().item() < 1000, 'placeholder class unexpectedly used by an image'

    model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32',
                                      local_files_only=True).cuda().eval()
    processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32',
                                              local_files_only=True)

    def text_mat(names):
        with torch.no_grad():
            texts = [TEMPLATE.format(c) for c in names]
            ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
            tout = model.text_model(**ti)
            pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
            return F.normalize(model.text_projection(pooled), dim=-1).detach()

    tf_legacy = text_mat(legacy_names)
    tf_clean = text_mat(clean_names)

    with torch.no_grad():
        imgs = []
        for i in range(0, N, 64):
            b = sub[i:i + 64]
            inp = processor(images=b['image'], return_tensors='pt').to('cuda')
            vout = model.vision_model(**inp)
            vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            imgs.append(F.normalize(model.visual_projection(vpooled), dim=-1))
        base = torch.cat(imgs)
        print('image features: %s  (%.1fs)' % (tuple(base.shape), time.time() - t_start), flush=True)

        # ---- gap direction: Flickr30k rows 2000..3000, identical to the archived scripts ----
        ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
        val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
        loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0,
                            collate_fn=_collate_fn)
        fi, ft = [], []
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
    d_hat = (gap_vec / gap_norm).detach()
    frozen_cg = (fi.mean(0) - ft.mean(0)).norm().item()
    print('gap_norm = %.6f  frozen CG = %.6f  (paper: 0.8154 / 0.82)' % (gap_norm, frozen_cg),
          flush=True)

    # ------------------------------------------------------------------ conditions
    # Replicates tools/clip_a1_baseline_metrics.py: same RNG, same order, same 26 conditions.
    rng2 = np.random.RandomState(7)
    D = base.shape[1]
    Q, _ = torch.linalg.qr(torch.tensor(rng2.randn(D, D), dtype=torch.float32, device='cuda'))
    cls_ids = torch.tensor(sorted(set(ds_in['label'])))          # 0..999, always
    cents = torch.stack([base[labels == c].mean(0) for c in cls_ids])
    cents = F.normalize(cents, dim=-1)
    lab_map = {int(c): i for i, c in enumerate(cls_ids)}
    mu_i = fi.mean(0)

    conds = []

    def push(name, family, param, img2, fi2):
        conds.append({'name': name, 'family': family, 'param': param, 'img': img2, 'fi': fi2})

    with torch.no_grad():
        push('base', 'base', None, base, fi)
        r_hat = torch.tensor(rng2.randn(D), dtype=torch.float32, device='cuda')
        r_hat = r_hat - (r_hat @ d_hat) * d_hat
        r_hat = r_hat / r_hat.norm()
        for lam in [-1, -0.5, 0.25, 0.5, 1, 2, 4]:
            push('T%.2g' % lam, 'T', lam,
                 F.normalize(base + lam * gap_norm * d_hat, dim=-1),
                 F.normalize(fi + lam * gap_norm * d_hat, dim=-1))
            if lam > 0:
                push('O%.2g' % lam, 'O', lam,
                     F.normalize(base + lam * gap_norm * r_hat, dim=-1),
                     F.normalize(fi + lam * gap_norm * r_hat, dim=-1))
        for a in [0.1, 0.25, 0.5]:
            push('C%.2g' % a, 'C', a,
                 F.normalize((1 - a) * base + a * mu_i, dim=-1),
                 F.normalize((1 - a) * fi + a * mu_i, dim=-1))
        for sig in [0.25, 0.5, 1, 2]:
            noise = torch.tensor(rng2.randn(N, D), dtype=torch.float32, device='cuda')
            noise = noise / noise.norm(dim=-1, keepdim=True)
            push('G%.2g' % sig, 'G', sig, F.normalize(base + sig * gap_norm * noise, dim=-1), fi)
        for kk in [1, 4, 16, 64]:
            Pk = Q[:, :kk] @ Q[:, :kk].T
            v = torch.tensor(rng2.randn(D), dtype=torch.float32, device='cuda')
            v = Pk @ v
            v = v / v.norm()
            push('L%d' % kk, 'L', kk, F.normalize(base + gap_norm * v, dim=-1), fi)
        for a in [0.25, 0.5]:
            c_own = cents[torch.tensor([lab_map[int(x)] for x in labels], device='cuda')]
            push('P%.2g' % a, 'P', a, F.normalize((1 - a) * base + a * c_own, dim=-1), fi)
    assert len(conds) == 26, 'expected the archived 26-condition grid, got %d' % len(conds)
    # The published 26-condition comparison grid of tools/clip_a1_baseline_metrics.py has no
    # lambda=-2 (the 50k phase diagram of clip_a1_full.py does). Add it as an extra condition so
    # the tau(lambda) curve covers the full published surgery grid, but keep the tau-vs-top1
    # Spearman correlation restricted to the 26 archived conditions so it stays comparable to the
    # published 0.926. Adding it consumes no RNG, so the other conditions are bit-identical.
    with torch.no_grad():
        push('T-2', 'T', -2.0, F.normalize(base - 2 * gap_norm * d_hat, dim=-1),
             F.normalize(fi - 2 * gap_norm * d_hat, dim=-1))
    GRID26 = {c['name'] for c in conds if c['name'] != 'T-2'}
    print('built %d conditions (%d of them in the archived 26-condition grid) (%.1fs)'
          % (len(conds), len(GRID26), time.time() - t_start), flush=True)

    # -------------------------- convention-independent condition metrics ------------------
    cond_shared = []
    for c in conds:
        with torch.no_grad():
            S = (c['img'] @ tf_legacy.T)
            cg = (c['fi'].mean(0) - ft.mean(0)).norm().item()
            cka = linear_cka(base, c['img'])
            mean_cos = (base * c['img']).sum(1).mean().item()
            top1_legacy = (S.argmax(1).cpu() == labels).float().mean().item() * 100
            S2 = (c['img'] @ tf_clean.T)
            top1_clean = (S2.argmax(1).cpu() == labels).float().mean().item() * 100
        cond_shared.append({'name': c['name'], 'family': c['family'], 'param': c['param'],
                            'CG': round(cg, 6), 'cka': round(cka, 6),
                            'mean_cos': round(mean_cos, 6),
                            'top1_legacy1001': round(top1_legacy, 4),
                            'top1_clean1000': round(top1_clean, 4)})
    print('shared metrics done (%.1fs)' % (time.time() - t_start), flush=True)

    def top1_of(conv, name):
        key = 'top1_legacy1001' if conv == 'legacy1001' else 'top1_clean1000'
        return next(m[key] for m in cond_shared if m['name'] == name)

    out = {
        'meta': {
            'script': 'tools/a1_rr_e2_topk.py',
            'experiment': 'E2 top-k ablation (reviewer R2.2)',
            'model': 'openai/clip-vit-base-patch32 (frozen)',
            'n_images': N, 'sample_seed': 42,
            'ks': KS, 'surgery_grid': GRID, 'n_conditions': len(conds),
            'condition_names': [c['name'] for c in conds],
            'grid26_names': sorted(GRID26),
            'note_extra_condition': "T-2 is added for the tau(lambda) curve only (the archived "
                                    "26-condition comparison grid starts at lambda=-1); the "
                                    "tau-vs-top1 Spearman uses the 26 archived conditions.",
            'gap_source': 'Flickr30k train rows 2000..3000 (same as archived A1 scripts)',
            'perturbation_rng': 'numpy RandomState(7), same stream/order as clip_a1_baseline_metrics.py',
            'class_list_conventions': {'legacy1001': len(legacy_names), 'clean1000': len(clean_names)},
            'placeholder_class_index': PLACEHOLDER_IDX,
            'shards': len(parq), 'shard_sig': shard_signature(parq),
            'gap_norm': gap_norm, 'frozen_CG': frozen_cg,
            'paper_reference': {'gap_norm': 0.8154, 'frozen_CG_50k': 0.8153,
                                'spearman_tau_top1_k5_26cond': 0.9262,
                                'tau_at_5k_sample_lambda0_top1': 'a1_tau_trajectory.json frozen top1=59.1'},
            'tau_estimator': 'vectorised Kendall tau_b on the frozen top-k sets; no ties are '
                             'possible with continuous scores, so 1-2*D/C(k,2) is exact. '
                             'Cross-checked against the archived scipy loop (see '
                             'estimator_crosscheck in each convention block).',
            'kendall_tau_undefined_at_k1':
                'Kendall tau needs >= 2 ranks; at k=1 the frozen set has zero variance, so the '
                'archived kendall_topk() skips every image and tau is undefined (null). '
                'top1_agreement_diagnostic is reported for that row instead.',
        },
        'conditions_shared': cond_shared,
        'conventions': {},
    }

    for conv, tmat in (('legacy1001', tf_legacy), ('clean1000', tf_clean)):
        print('\n===== convention %s (%d classes) =====' % (conv, tmat.shape[0]), flush=True)
        with torch.no_grad():
            base_np = (base @ tmat.T).float().cpu().numpy()
            cur_np = {c['name']: (c['img'] @ tmat.T).float().cpu().numpy() for c in conds}
            m = (d_hat @ tmat.T).cpu().numpy()      # per-class mean-text alignment
        idx_by_k = {k: np.argsort(-base_np, axis=1)[:, :k] for k in KS}
        print('  score matrices + top-k index tables done (%.1fs)' % (time.time() - t_start),
              flush=True)

        # estimator cross-check on a 500-image slice against the archived scipy implementation
        cross = {}
        for k in (3, 5, 20):
            tk = idx_by_k[k][:500]
            tau_tie, tied = kendall_topk(base_np[:500], cur_np['T1'][:500], tk)
            tau_notie = kendall_topk_notie(base_np[:500], cur_np['T1'][:500], tk)
            slow = kendall_topk_scipy(base_np[:500], cur_np['T1'][:500], tk)
            cross[str(k)] = {'tie_aware': round(tau_tie, 9), 'no_tie_formula': round(tau_notie, 9),
                             'archived_scipy': round(slow, 9),
                             'abs_diff_tie_aware_vs_scipy': abs(tau_tie - slow),
                             'abs_diff_notie_vs_scipy': abs(tau_notie - slow),
                             'frac_images_with_ties': round(tied, 6)}
        print('  estimator cross-check (T=1, first 500 images): %s' % cross, flush=True)

        # ---- T-family tau(lambda) per k: measured + exact predictor ----
        t_rows = {}
        for k in KS:
            idxk = idx_by_k[k]
            meas = {}
            tied_frac = {}
            for lam in GRID:
                nm = 'base' if lam == 0.0 else 'T%.2g' % lam
                tau_v, tied = kendall_topk(base_np, cur_np[nm], idxk)
                meas[str(lam)] = tau_v
                tied_frac[str(lam)] = round(tied, 6)
            pred = predicted_tau_table(base_np, idxk, m, gap_norm, GRID)
            pred = {str(l): pred[l] for l in GRID}
            frac_ph = (float(np.mean([PLACEHOLDER_IDX in idxk[i] for i in range(N)]))
                       if conv == 'legacy1001' else 0.0)
            t_rows[k] = {'measured': meas, 'predicted_exact': pred,
                         'frac_images_with_ties': tied_frac,
                         'frac_images_with_placeholder_in_topk': round(frac_ph, 6)}
            print('  k=%-4d tau(lambda) = %s' %
                  (k, {a: ('n/a' if meas[str(a)] is None else round(meas[str(a)], 4)) for a in GRID}),
                  flush=True)

        # ---- per-k tau over the full 26-condition grid + correlations ----
        per_k = {}
        for k in KS:
            idxk = idx_by_k[k]
            taus, ties = {}, {}
            for c in conds:
                tv, td = kendall_topk(base_np, cur_np[c['name']], idxk)
                taus[c['name']] = tv
                ties[c['name']] = round(td, 6)
            agree = {c['name']: round(top1_agreement(base_np, cur_np[c['name']]), 6) for c in conds}
            ok = [c['name'] for c in conds if taus[c['name']] is not None and c['name'] in GRID26]
            tau_vec = [taus[n] for n in ok]
            t1_vec = [top1_of(conv, n) for n in ok]
            if len(set(tau_vec)) > 1:
                r_tau, p_tau = stats.spearmanr(tau_vec, t1_vec)
                r_tau, p_tau = float(r_tau), float(p_tau)
            else:
                r_tau, p_tau = float('nan'), float('nan')
            met = {}
            for metric in ['CG', 'cka', 'mean_cos']:
                v = [next(mm[metric] for mm in cond_shared if mm['name'] == n) for n in ok]
                rr, pp = stats.spearmanr(v, t1_vec)
                met[metric] = {'spearman_r': round(float(rr), 4), 'p': float(pp)}
            t_names = [n for n in ok if n == 'base' or n.startswith('T')]
            tt = [taus[n] for n in t_names]
            t1t = [top1_of(conv, n) for n in t_names]
            if len(set(tt)) > 1:
                r_t, p_t = stats.spearmanr(tt, t1t)
                r_t, p_t = float(r_t), float(p_t)
            else:
                r_t, p_t = float('nan'), float('nan')
            per_k[k] = {
                'tau': {n: (None if taus[n] is None else round(taus[n], 6)) for n in taus},
                'frac_images_with_ties': ties,
                'top1_agreement_diagnostic': agree,
                'n_conditions_scored': len(ok),
                'spearman_tau_vs_top1_all26': {'r': round(r_tau, 4), 'p': p_tau},
                'spearman_tau_vs_top1_Tfamily': {'r': round(r_t, 4), 'p': p_t},
                'spearman_other_metrics_vs_top1': met,
            }
            print('  k=%-4d spearman(tau,top1): all26=%.4f  T-family=%.4f'
                  % (k, r_tau, r_t), flush=True)

        # ---- curve stability vs reference k=5 ----
        ref = [t_rows[5]['measured'][str(a)] for a in GRID]
        curve_cmp = {}
        for k in KS:
            cur = [t_rows[k]['measured'][str(a)] for a in GRID]
            if k == 1 or any(v is None for v in cur):
                curve_cmp[k] = {'spearman_vs_k5': None,
                                'note': 'undefined for k=1 (Kendall tau degenerate)'}
                continue
            rr, pp = stats.spearmanr(cur, ref)
            curve_cmp[k] = {
                'spearman_vs_k5': round(float(rr), 6), 'p': float(pp),
                'max_abs_diff_vs_k5': round(float(np.max(np.abs(np.array(cur) - np.array(ref)))), 6),
                'mean_abs_diff_vs_k5': round(float(np.mean(np.abs(np.array(cur) - np.array(ref)))), 6)}

        # ---- exact-predictor error on the T grid ----
        pred_err = {}
        for k in KS:
            meas = [t_rows[k]['measured'][str(a)] for a in GRID]
            pred = [t_rows[k]['predicted_exact'][str(a)] for a in GRID]
            if k == 1 or any(v is None for v in meas) or any(v is None for v in pred):
                pred_err[k] = {'note': 'Kendall tau undefined at k=1; predictor not comparable',
                               'mae_all_lambda': None, 'max_abs_err_all_lambda': None,
                               'mae_lambda_0.5_1_2': None, 'pearson_pred_vs_meas': None}
                continue
            meas_a = np.array(meas, dtype=float)
            pred_a = np.array(pred, dtype=float)
            sub_idx = [i for i, a in enumerate(GRID) if a in (0.5, 1.0, 2.0)]
            pred_err[k] = {
                'mae_all_lambda': round(float(np.mean(np.abs(pred_a - meas_a))), 6),
                'max_abs_err_all_lambda': round(float(np.max(np.abs(pred_a - meas_a))), 6),
                'mae_lambda_0.5_1_2': round(float(np.mean(np.abs(pred_a[sub_idx] - meas_a[sub_idx]))), 6),
                'pearson_pred_vs_meas': round(float(stats.pearsonr(pred_a, meas_a)[0]), 6),
            }
            print('  k=%-4d pred MAE(all lam)=%.4f  MAE(lam in .5/1/2)=%.4f  pearson=%.4f'
                  % (k, pred_err[k]['mae_all_lambda'], pred_err[k]['mae_lambda_0.5_1_2'],
                     pred_err[k]['pearson_pred_vs_meas']), flush=True)

        out['conventions'][conv] = {
            'n_classes': int(tmat.shape[0]),
            'estimator_crosscheck_vs_archived_scipy': cross,
            'tau_vs_lambda_by_k': {str(k): t_rows[k] for k in KS},
            'per_k': {str(k): per_k[k] for k in KS},
            'curve_stability_vs_k5': {str(k): curve_cmp[k] for k in KS},
            'exact_predictor_error': {str(k): pred_err[k] for k in KS},
            'm_stats': {'mean': float(m.mean()), 'std': float(m.std()),
                        'q10': float(np.percentile(m, 10)), 'q90': float(np.percentile(m, 90))},
        }
        json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('  [checkpoint] wrote %s (%.1fs)' % (OUT, time.time() - t_start), flush=True)

    # ------------------------------------------------------------------ compact table
    for conv in ('legacy1001', 'clean1000'):
        L = out['conventions'][conv]
        print('\n================= E2 compact table (%s) =================' % conv)
        print(' k    tau(0) tau(0.5) tau(1)  tau(2) rho(tau,top1)26 T-only predMAE')
        for k in KS:
            t = L['tau_vs_lambda_by_k'][str(k)]['measured']

            def f(a):
                return '  n/a ' if t[str(a)] is None else '%6.3f' % t[str(a)]
            pe = L['exact_predictor_error'][str(k)]['mae_all_lambda']
            print('%-4d %s %s %s %s   %12.4f  %6.4f  %s'
                  % (k, f(0.0), f(0.5), f(1.0), f(2.0),
                     L['per_k'][str(k)]['spearman_tau_vs_top1_all26']['r'],
                     L['per_k'][str(k)]['spearman_tau_vs_top1_Tfamily']['r'],
                     ' n/a ' if pe is None else '%.4f' % pe))
    out['meta']['runtime_s'] = round(time.time() - t_start, 1)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nALL DONE -> %s  (%.1fs)' % (OUT, time.time() - t_start), flush=True)


if __name__ == '__main__':
    main()
