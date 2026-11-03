"""A1 hardening item 1 -- certify the baseline-metrics row.

`outputs/a1_baseline_metrics.json` holds the row quoted in the manuscript: the Spearman
correlation of tau / linear CKA / mean embedding cosine / Centroid Gap (CG) with top-1 over a
26-condition perturbation grid. An audit found that the archived file is NOT self-consistent: its
tau correlation matches a top-10 computation rather than the top-5 that
`tools/clip_a1_baseline_metrics.py` performs, and its CG / mean-cosine do not reproduce either.

This script re-runs the archived protocol (logic copied verbatim from
`tools/clip_a1_baseline_metrics.py`; the original file is NOT modified) and produces ONE
self-consistent run in which every statistic comes from the same code state, with:

  * per-condition detail (name, family, parameter, top-1, tau@k, CG, CKA, mean cosine),
  * the 26-condition Spearman correlations for tau / CG / CKA / mean cosine,
  * the archived values quoted side by side and an agree/disagree verdict per statistic,
  * a `--tau-k` switch so the SAME code state is run at k = 5 (the manuscript's frozen-top-5
    convention) and at k = 10 (the value the archived file actually stores),
  * a diagnostic sweep over plausible alternative definitions of CG and mean cosine, to test
    whether the archived numbers came from a different (but still admissible) code state,
  * a machine-precision cross-check of the vectorised per-image tau against the archived
    scipy `kendall_topk` estimator,
  * the class bias-field theory check of part B of the archived script.

The per-image tau arrays are stored so that item 4 (bootstrap CIs) reuses them.

Output: outputs/a1_h_baseline_metrics.json
Run:    D:\\Anaconda\\envs\\pytorch\\python.exe tools/a1_h_baseline_metrics.py --tau-k 5 10
"""
import os
import sys
import json
import glob
import time
import hashlib
import argparse
from datetime import datetime, timezone

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from datasets import Dataset
from transformers import CLIPModel, CLIPProcessor
from torch.utils.data import DataLoader
from scipy import stats

from src.dataset import Flickr30kDataset, _collate_fn  # noqa: E402

TEMPLATE = 'a photo of a {}'          # unchanged, archived convention
N = 5000                              # unchanged, archived convention
MODEL_ID = 'openai/clip-vit-base-patch32'
CLASS_ALIGNED_PY = 'tools/train_class_aligned.py'
ARCHIVED = 'outputs/a1_baseline_metrics.json'
OUT = 'outputs/a1_h_baseline_metrics.json'
PLACEHOLDER_IDX = 1000
CROSSCHECK_N = 400                    # images used for the scipy cross-check
SCORE_KEEP = ['base', 'T0.5', 'P0.5']  # conditions whose perturbed scores are stored
PER_IMAGE_KEEP = ['base', 'T0.25', 'T0.5', 'T1', 'T2', 'T4', 'T-0.5', 'T-1', 'P0.5']
K_SWEEP = [2, 3, 5, 10, 20, 50, 100]   # per-image tau stored at these k (item 4: k-specificity)
K_SWEEP_LAMBDAS = [-0.5, 0.5, 1.0, 2.0]


def shard_signature(parq):
    h = hashlib.sha1()
    for p in parq:
        h.update(os.path.basename(p).encode())
        h.update(str(os.path.getsize(p)).encode())
    return h.hexdigest()[:16]


def file_sha1(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def linear_cka(X, Y):
    """Verbatim from tools/clip_a1_baseline_metrics.py."""
    XX = X @ X.T
    YY = Y @ Y.T
    XY = X @ Y.T
    denom = (torch.trace(XX @ XX).item() * torch.trace(YY @ YY).item()) ** 0.5
    return (torch.trace(XY @ XY).item() / denom) if denom > 0 else 0.0


def kendall_topk_scipy(base_np, cur_np, topk):
    """ARCHIVED estimator, verbatim from tools/clip_a1_probe2.py::kendall_topk."""
    taus = []
    for i in range(len(base_np)):
        r1 = base_np[i][topk[i]]
        r2 = cur_np[i][topk[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    return float(np.mean(taus)) if taus else None


def per_image_tau(base_np, cur_np, topk):
    """Per-image Kendall tau_b over the frozen top-k sets, in double precision.

    Identical estimator to the archived scipy loop (tau_b, tie-corrected); returns `nan` exactly
    where that loop would skip an image (zero variance in either score vector).
    """
    k = topk.shape[1]
    n0 = k * (k - 1) // 2
    r1 = np.take_along_axis(base_np, topk, axis=1).astype(np.float64)
    r2 = np.take_along_axis(cur_np, topk, axis=1).astype(np.float64)
    up = np.triu(np.ones((k, k), dtype=bool), 1)
    a = r1[:, :, None] - r1[:, None, :]
    b = r2[:, :, None] - r2[:, None, :]
    af, bf = a[:, up], b[:, up]
    cmd = np.sign(af * bf).sum(axis=1)
    n1 = (af == 0).sum(axis=1)
    n2 = (bf == 0).sum(axis=1)
    denom = np.sqrt((n0 - n1).astype(float) * (n0 - n2).astype(float))
    with np.errstate(divide='ignore', invalid='ignore'):
        t = np.where(denom > 1e-12, cmd / denom, np.nan)
    # clamp to the valid tau_b range (float32 tie-correction denominator can exceed it marginally)
    return np.clip(t, -1.0, 1.0)


@torch.no_grad()
def encode_val(model, processor, ds, rows=None, batch=64):
    """Flickr30k image+text embeddings with the archived CLIPModel forward."""
    sub = torch.utils.data.Subset(ds, rows) if rows is not None else ds
    loader = DataLoader(sub, batch_size=batch, shuffle=False, num_workers=0, collate_fn=_collate_fn)
    fi, ft = [], []
    for b in loader:
        o = model(pixel_values=b['image'].cuda(), input_ids=b['input_ids'].cuda(),
                  attention_mask=b['attention_mask'].cuda(), return_loss=False)
        fi.append(F.normalize(o.image_embeds, dim=-1))
        ft.append(F.normalize(o.text_embeds, dim=-1))
    return torch.cat(fi), torch.cat(ft)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tau-k', type=int, nargs='+', default=[5, 10],
                    help='k values for the tau statistic (manuscript top-5 convention = 5)')
    ap.add_argument('--out', default=OUT)
    args = ap.parse_args()

    t0 = time.time()
    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    shard_sig = shard_signature(parq)
    torch.manual_seed(0)
    np.random.seed(0)

    model = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True).cuda().eval()
    processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)
    ds_in = Dataset.from_parquet(parq)
    names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
    texts = [TEMPLATE.format(c.replace('_', ' ')) for c in names]

    rng = np.random.RandomState(42)                       # archived sample stream
    idx = rng.choice(len(ds_in), N, replace=False)
    sub = ds_in.select(list(idx))
    labels = torch.tensor(sub['label'])

    ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
    n_flickr_rows = len(ds_f.samples)

    with torch.no_grad():
        ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
        tout = model.text_model(**ti)
        pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
        tf = F.normalize(model.text_projection(pooled), dim=-1)
        imgs = []
        for i in range(0, len(sub), 64):
            b = sub[i:i + 64]
            inp = processor(images=b['image'], return_tensors='pt').to('cuda')
            vout = model.vision_model(**inp)
            vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            imgs.append(F.normalize(model.visual_projection(vpooled), dim=-1))
        base = torch.cat(imgs)

    fi, ft = encode_val(model, processor, ds_f, rows=range(2000, 3000))

    gap_vec = ft.mean(0) - fi.mean(0)
    gap_norm = gap_vec.norm().item()
    d_hat = gap_vec / gap_norm

    base_sims = base @ tf.T
    base_np = base_sims.cpu().numpy()
    cls_ids = torch.tensor(sorted(set(ds_in['label'])))
    cents = F.normalize(torch.stack([base[labels == c].mean(0) for c in cls_ids]), dim=-1)
    lab_map = {int(c): i for i, c in enumerate(cls_ids)}
    topk_by_k = {k: np.argsort(-base_np, axis=1)[:, :k] for k in args.tau_k}

    # ---------------------------------------------------------- alternative metric variants
    cg_val = (fi.mean(0) - ft.mean(0)).norm().item()               # archived code path
    # alternative val block (rows 0..999 instead of 2000..2999): out-of-sample stability of the
    # gap statistic, i.e. how much of a stored-vs-reproduced CG difference could be block choice
    fi_b, ft_b = encode_val(model, processor, ds_f, rows=range(0, 1000))
    cg_block_b = (fi_b.mean(0) - ft_b.mean(0)).norm().item()
    # unnormalised pooled embeddings (a plausible alternative code state for CG / mean cosine)
    fi_raw_img, ft_raw_txt = [], []
    with torch.no_grad():
        vl = DataLoader(torch.utils.data.Subset(ds_f, range(2000, 3000)), batch_size=64,
                        shuffle=False, num_workers=0, collate_fn=_collate_fn)
        for b in vl:
            o = model(pixel_values=b['image'].cuda(), input_ids=b['input_ids'].cuda(),
                      attention_mask=b['attention_mask'].cuda(), return_loss=False)
            fi_raw_img.append(o.image_embeds)
            ft_raw_txt.append(o.text_embeds)
    cg_raw = (torch.cat(fi_raw_img).mean(0) - torch.cat(ft_raw_txt).mean(0)).norm().item()
    del fi_raw_img, ft_raw_txt

    # unfiltered 5 000-image arg-max (the archived script builds `base` from the HF `image` column
    # while `fi` comes from the DataLoader, so img2/mean-pooling orders can differ)
    unf = torch.zeros(N, device='cuda')
    with torch.no_grad():
        for i in range(0, N, 256):
            inp = processor(images=list(sub['image'][i:i + 256]), return_tensors='pt').to('cuda')
            vout = model.vision_model(**inp)
            vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            unf[i:i + 256] = (F.normalize(model.visual_projection(vp), dim=-1) @ tf.T).argmax(1)
    unf_np = unf.cpu().numpy()
    top1_unfiltered = float((unf_np == labels.numpy()).mean() * 100)
    top1_filtered = float((base_sims.argmax(1).cpu() == labels).float().mean().item() * 100)

    cg_variants = {
        'cg_val_2000_3000': round(cg_val, 6),
        'cg_val_0_1000': round(cg_block_b, 6),
        'cg_val_2000_3000_unnormalized_pooled': round(cg_raw, 6),
        'neg_cg_val_2000_3000': round(-cg_val, 6),
        'abs_delta_between_blocks': round(abs(cg_val - cg_block_b), 6),
    }
    mean_cos_variants = {
        'cos_self_5k': round(float((base * base).sum(1).mean().item()), 6),
        'cos_mean5k_vs_meanval_embedding': round(
            float((base.mean(0) * fi.mean(0)).sum().item()), 6),
        'cos_mean5k_vs_mean_text': round(float((base.mean(0) * tf.mean(0)).sum().item()), 6),
    }

    CG_ARCHIVED_HINT = -0.0821
    COS_ARCHIVED_HINT = 0.8715
    cg_variants_reach_archived = sorted(
        [k for k, v in cg_variants.items() if abs(v - CG_ARCHIVED_HINT) <= 2e-3])
    mean_cos_variants_reach_archived = sorted(
        [k for k, v in mean_cos_variants.items() if abs(v - COS_ARCHIVED_HINT) <= 2e-3])

    # ---------------------------------------------------------- evaluation
    stored_scores = {}

    def evaluate(img2):
        S = img2 @ tf.T
        s_np = S.cpu().numpy()
        out = {'top1': float((S.argmax(1).cpu() == labels).float().mean().item() * 100)}
        for k in args.tau_k:
            pi = per_image_tau(base_np, s_np, topk_by_k[k])
            fin = pi[np.isfinite(pi)]
            out['tau_k%d' % k] = float(fin.mean()) if fin.size else None
            out['tau_k%d_per_image' % k] = pi
        out['CG'] = float((img2.mean(0) - ft.mean(0)).norm().item())
        out['cka'] = linear_cka(base, img2)
        out['mean_cos'] = float((base * img2).sum(1).mean().item())
        return out

    conds = []
    img_by_cond = {}
    per_image_out = {('k%d' % k): {} for k in args.tau_k}
    ksw = {k: {} for k in K_SWEEP}
    rng2 = np.random.RandomState(7)                       # archived perturbation stream
    D = base.shape[1]
    Q, _ = torch.linalg.qr(torch.tensor(rng2.randn(D, D), dtype=torch.float32, device='cuda'))

    def push(name, family, param, img2):
        r = evaluate(img2)
        img_by_cond[name] = img2
        conds.append({'name': name, 'family': family, 'param': param,
                      **{k: v for k, v in r.items() if not k.endswith('_per_image')}})
        if name in PER_IMAGE_KEEP:
            for k in args.tau_k:
                arr = r['tau_k%d_per_image' % k]
                per_image_out['k%d' % k][name] = [None if not np.isfinite(x) else float(x)
                                                  for x in arr]
        if name in SCORE_KEEP:
            stored_scores[name] = (img2 @ tf.T).cpu().numpy()
        # item 4: per-image tau over a wider k range, for the k-specificity of thresholds
        if name in ['T%.2g' % x for x in K_SWEEP_LAMBDAS] or name == 'base':
            s_np = (img2 @ tf.T).cpu().numpy()
            for k in K_SWEEP:
                tk = np.argsort(-base_np, axis=1)[:, :k] if k not in topk_by_k else topk_by_k[k]
                arr = per_image_tau(base_np, s_np, tk)
                ksw[k][name] = [None if not np.isfinite(x) else float(x) for x in arr]
        print('%-8s top1=%6.2f  %s  CG=%+.4f cka=%.4f cos=%.4f'
              % (name, r['top1'],
                 ' '.join('tau_k%d=%s' % (k, 'None' if r['tau_k%d' % k] is None
                                          else '%.4f' % r['tau_k%d' % k]) for k in args.tau_k),
                 r['CG'], r['cka'], r['mean_cos']), flush=True)
        return r

    with torch.no_grad():
        r_base = push('base', 'base', None, base)
        r_hat = torch.tensor(rng2.randn(D), dtype=torch.float32, device='cuda')
        r_hat = r_hat - (r_hat @ d_hat) * d_hat
        r_hat = r_hat / r_hat.norm()
        for lam in [-1, -0.5, 0.25, 0.5, 1, 2, 4]:
            push('T%.2g' % lam, 'T', lam, F.normalize(base + lam * gap_norm * d_hat, dim=-1))
            if lam > 0:
                push('O%.2g' % lam, 'O', lam, F.normalize(base + lam * gap_norm * r_hat, dim=-1))
        for a in [0.1, 0.25, 0.5]:
            push('C%.2g' % a, 'C', a, F.normalize((1 - a) * base + a * fi.mean(0), dim=-1))
        for sig in [0.25, 0.5, 1, 2]:
            noise = torch.tensor(rng2.randn(N, D), dtype=torch.float32, device='cuda')
            noise = noise / noise.norm(dim=-1, keepdim=True)
            push('G%.2g' % sig, 'G', sig, F.normalize(base + sig * gap_norm * noise, dim=-1))
        for k in [1, 4, 16, 64]:
            Pk = Q[:, :k] @ Q[:, :k].T
            v = torch.tensor(rng2.randn(D), dtype=torch.float32, device='cuda')
            v = Pk @ v
            v = v / v.norm()
            push('L%d' % k, 'L', k, F.normalize(base + gap_norm * v, dim=-1))
        for a in [0.25, 0.5]:
            c_own = cents[torch.tensor([lab_map[int(x)] for x in labels], device='cuda')]
            push('P%.2g' % a, 'P', a, F.normalize((1 - a) * base + a * c_own, dim=-1))

    top1s = [c['top1'] for c in conds]
    corrs = {}
    for metric in ['CG', 'cka', 'mean_cos'] + ['tau_k%d' % k for k in args.tau_k]:
        vals = [c[metric] for c in conds]
        if any(v is None for v in vals) or len(set(vals)) < 2:
            corrs[metric] = {'spearman_r': None, 'p': None, 'n': len(vals),
                             'note': 'undefined (constant or missing values)'}
            continue
        r, p = stats.spearmanr(top1s, vals)
        corrs[metric] = {'spearman_r': round(float(r), 4), 'p': float(p), 'n': len(vals)}

    # ---------------------------------------------------------- estimator cross-check
    crosscheck = {}
    for nm in SCORE_KEEP:
        for k in args.tau_k:
            tk = topk_by_k[k][:CROSSCHECK_N]
            slow = kendall_topk_scipy(base_np[:CROSSCHECK_N], stored_scores[nm][:CROSSCHECK_N], tk)
            pi = per_image_tau(base_np[:CROSSCHECK_N], stored_scores[nm][:CROSSCHECK_N], tk)
            fast = float(pi[np.isfinite(pi)].mean())
            crosscheck['%s_k%d' % (nm, k)] = {'scipy_archived_estimator': slow, 'vectorised': fast,
                                              'abs_diff': abs(slow - fast),
                                              'n_images': CROSSCHECK_N}

        # ---------------------------------------------------------- alternative CG definitions
        # Decisive test: recompute the 26-condition Spearman correlation with each admissible CG
        # definition. If the archived CG correlation (-0.0821) is reproduced by NONE of them, the
        # archived CG column did not come from a mere definitional difference.
        alt_cg = {
            'CG_val_2000_3000': [float((img_by_cond[c['name']].mean(0) - ft.mean(0)).norm().item())
                                 for c in conds],
            'CG_val_0_1000': [float((img_by_cond[c['name']].mean(0) - ft_b.mean(0)).norm().item())
                              for c in conds],
            'CG_val_2000_3000_unnormalized_pooled': None,   # needs raw pooled feats per condition
        }
        alt_corr = {}
        for nm, vals in alt_cg.items():
            if vals is None:
                alt_corr[nm] = {'note': 'not computed (needs unnormalised pooled embeddings per '
                                        'condition, which the archived protocol never forms)'}
                continue
            r, p = stats.spearmanr(top1s, vals)
            alt_corr[nm] = {'spearman_r': round(float(r), 4), 'p': float(p), 'n': len(vals),
                            'mean_cg': round(float(np.mean(vals)), 6),
                            'matches_archived_-0.0821': bool(abs(float(r) - (-0.0821)) <= 5e-4)}
        mean_cos_alt = {}
        mean_cos_alt['mean_cos_as_implemented'] = {
            'spearman_r': corrs['mean_cos']['spearman_r'], 'p': corrs['mean_cos']['p'],
            'matches_archived_0.8715': bool(abs(corrs['mean_cos']['spearman_r'] - 0.8715) <= 5e-4)}

    # ---------------------------------------------------------- theory check (part B)
    with torch.no_grad():
        shifted = F.normalize(base + gap_norm * d_hat, dim=-1)
    S1 = shifted @ tf.T
    m_c = (d_hat @ tf.T).cpu().numpy()
    actual = (S1 - base_sims).mean(0).cpu().numpy()
    pred = gap_norm * m_c
    r_bias, p_bias = stats.pearsonr(actual, pred)
    theory = {'pearson_actual_vs_predicted': round(float(r_bias), 4), 'p': float(p_bias),
              'std_m_c': round(float(np.std(m_c)), 4), 'gap_norm': round(gap_norm, 4)}

    archived = json.load(open(ARCHIVED, encoding='utf-8')) if os.path.exists(ARCHIVED) else {}
    verdict = []
    for key, arch_key in (('tau_k5', 'tau'), ('tau_k10', 'tau'), ('CG', 'CG'), ('cka', 'cka'),
                          ('mean_cos', 'mean_cos')):
        if key not in corrs or corrs[key]['spearman_r'] is None:
            continue
        a = archived.get('metric_correlations', {}).get(arch_key, {}).get('spearman_r')
        new = corrs[key]['spearman_r']
        verdict.append({'statistic': key, 'new_spearman_r': new, 'archived_spearman_r': a,
                        'abs_diff': (None if a is None else round(abs(new - a), 6)),
                        'agree_at_5e-4': (None if a is None else bool(abs(new - a) <= 5e-4))})

    payload = {
        'meta': {
            'script': 'tools/a1_h_baseline_metrics.py',
            'purpose': 'item 1 -- certify the baseline-metrics row in one self-consistent run',
            'derived_from': 'tools/clip_a1_baseline_metrics.py (protocol copied verbatim; the '
                            'original file is NOT modified)',
            'script_sha1_self': file_sha1('tools/a1_h_baseline_metrics.py'),
            'archived_script_sha1': file_sha1('tools/clip_a1_baseline_metrics.py'),
            'class_list_source': CLASS_ALIGNED_PY,
            'class_list_len': len(names),
            'class_list_len_clean': len(names) - 1,
            'placeholder_class_index': PLACEHOLDER_IDX,
            'shard_signature': shard_sig,
            'model': MODEL_ID,
            'template': TEMPLATE,
            'n_images': N, 'n_conditions': len(conds),
            'tau_k_values': args.tau_k,
            'tau_estimator': "mean Kendall tau_b over the FROZEN top-k class sets (frozen = the "
                             "same run's lambda=0 scores), tie-corrected, scipy-equivalent",
            'gap': {'source': 'Flickr30k train rows 2000..3000', 'gap_norm': round(gap_norm, 6)},
            'perturbation_stream': 'np.random.RandomState(7), identical to the archived script',
            'sample_stream': 'np.random.RandomState(42), identical to the archived script',
            'n_flickr30k_rows_total': int(n_flickr_rows),
            'frozen_top1_5k_filtered': round(top1_filtered, 6),
            'frozen_top1_5k_unfiltered': round(top1_unfiltered, 6),
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'runtime_s': None,
        },
        'conditions': conds,
        'conditions_order': [c['name'] for c in conds],
        'per_image_tau_by_condition': per_image_out,
        'per_image_tau_k_sweep': {
            'note': 'per-image tau at k in %s for the surgery grid points %s; feeds item 4 '
                    '(k-specificity of the calibration thresholds)' % (K_SWEEP, K_SWEEP_LAMBDAS),
            'ks': K_SWEEP, 'lambdas': K_SWEEP_LAMBDAS, 'data': ksw},
        'metric_correlations': corrs,
        'theory_verification': theory,
        'estimator_crosscheck_vs_archived_scipy': crosscheck,
        'archived_comparison': {'archived_file': ARCHIVED, 'archived_values': archived,
                                'verdict_per_statistic': verdict},
        'cg_mean_cos_variants': {
            'note': 'diagnostic sweep: is the archived CG / mean-cosine reachable from some other '
                    'admissible code state? `*_reaches_archived` lists variants within 2e-3.',
            'cg_variants': cg_variants,
            'cg_variants_reaching_archived': cg_variants_reach_archived,
            'mean_cos_variants': mean_cos_variants,
            'mean_cos_variants_reaching_archived': mean_cos_variants_reach_archived,
            'archived_hints': {'CG': CG_ARCHIVED_HINT, 'mean_cos': COS_ARCHIVED_HINT},
            'top1_5k_filtered_vs_unfiltered': {
                'filtered_5000_resampled': round(top1_filtered, 6),
                'unfiltered_5000': round(top1_unfiltered, 6)},
            'alternative_cg_definitions_through_the_correlation': alt_corr,
            'alternative_mean_cos_definitions_through_the_correlation': mean_cos_alt,
        },
    }
    payload['meta']['runtime_s'] = round(time.time() - t0, 1)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)

    print('\n== certified row (single code state, %d conditions) ==' % len(conds))
    for m, v in corrs.items():
        print('  %-8s rho=%s  p=%s' % (m, v['spearman_r'], v['p']))
    print('  theory: pearson(actual,pred)=%.4f std(m_c)=%.4f gap_norm=%.4f'
          % (theory['pearson_actual_vs_predicted'], theory['std_m_c'], theory['gap_norm']))
    print('  CG variants reaching archived -0.0821: %s' % cg_variants_reach_archived)
    print('  cos variants reaching archived 0.8715: %s' % mean_cos_variants_reach_archived)
    print('\n== archived comparison ==')
    for v in verdict:
        print('  %-9s new=%s archived=%s diff=%s agree=%s'
              % (v['statistic'], v['new_spearman_r'], v['archived_spearman_r'], v['abs_diff'],
                 v['agree_at_5e-4']))
    print('\nsaved', args.out, '(%.1fs)' % (time.time() - t0))


if __name__ == '__main__':
    main()
