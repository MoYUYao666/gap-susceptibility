"""A1 hardening item 5 -- explain (or fail to explain) the systematic offset.

Observations to explain (outputs/a1_rr_summary.json):
  * every real LoRA checkpoint sits 3.3-5.5 accuracy points ABOVE the synthetic tau->top-1 curve
    at matched tau (k = 5),
  * the three archived Flickr30k checkpoints have tau above the synthetic curve's entire range at
    k = 5.

Hypothesis to test: synthetic "gap surgery" is a norm-preserving EXACT TRANSLATION of the image
embedding cluster by a fixed vector, whereas real fine-tuning changes the embedding geometry
(norms, within-class spread, per-class margins). At matched tau the two families therefore need
not coincide.

Design (all on the fixed 5 000-image ImageNet sample, RandomState(42), legacy1001 class list):
  A. geometry table for the frozen model and every reachable checkpoint --
     mean image-embedding norm, mean |x| displacement vs frozen, decomposition of that
     displacement into the component parallel to the gap direction and the orthogonal component,
     the centroid gap CG, the within-class spread, the top-1 margin distribution, and the
     logit_scale.
  B. match the perturbation MAGNITUDE: for every checkpoint, find the synthetic lambda whose
     mean displacement ||delta|| equals the checkpoint's, and read off (tau, top-1) there. Also
     the reverse: interpolate the synthetic curve to each checkpoint's tau and report the excess.
  C. match tau: invert the synthetic tau(lambda) curve for each checkpoint's tau and report the
     synthetic top-1 at that matched tau -> the offset in points.
  D. does the geometry explain the offset? correlate the per-checkpoint excess with each geometry
     delta (Pearson + Spearman over the checkpoints), and report the answer either way.

Nothing is invented: if a checkpoint cannot be loaded it is reported with its error and excluded.
Output: outputs/a1_h_offset.json
Run:    D:\\Anaconda\\envs\\pytorch\\python.exe tools/a1_h_offset.py
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
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
from transformers import CLIPModel, CLIPProcessor
from torch.utils.data import DataLoader
from datasets import Dataset as HFDataset

from a1_h_common import per_image_tau  # noqa: E402
from src.dataset import Flickr30kDataset, _collate_fn  # noqa: E402
from src.lora import apply_lora_to_model  # noqa: E402

MODEL_ID = 'openai/clip-vit-base-patch32'
TEMPLATE = 'a photo of a {}'
N_SAMPLE = 5000
TOPK = 5
PLACEHOLDER_IDX = 1000
BATCH = 128
LAM_GRID = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
SUMMARY_JSON = 'outputs/a1_rr_summary.json'
BASELINE_JSON = 'outputs/a1_h_baseline_metrics.json'
TEMPLATES_JSON = 'outputs/a1_h_templates.json'
OUT = 'outputs/a1_h_offset.json'


def file_sha1(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def summarise(vals):
    """Mean / sample sd / range of a list, ignoring None."""
    a = np.asarray([v for v in vals if v is not None], dtype=float)
    if a.size == 0:
        return {'n': 0}
    return {'n': int(a.size), 'mean': round(float(a.mean()), 4),
            'sd': (None if a.size < 2 else round(float(a.std(ddof=1)), 4)),
            'min': round(float(a.min()), 4), 'max': round(float(a.max()), 4),
            'range': round(float(a.max() - a.min()), 4)}


def corr(x, y):
    """Pearson/Spearman with their p-values, or a note when undefined."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 3 or len(set(x.tolist())) < 2 or len(set(y.tolist())) < 2:
        return {'n': int(len(x)), 'note': 'undefined (constant or too few points)'}
    return {'n': int(len(x)), 'pearson_r': round(float(stats.pearsonr(x, y)[0]), 4),
            'pearson_p': float(stats.pearsonr(x, y)[1]),
            'spearman_r': round(float(stats.spearmanr(x, y)[0]), 4),
            'spearman_p': float(stats.spearmanr(x, y)[1])}


def shard_signature(parq):
    h = hashlib.sha1()
    for p in parq:
        h.update(os.path.basename(p).encode())
        h.update(str(os.path.getsize(p)).encode())
    return h.hexdigest()[:16]


@torch.no_grad()
def encode_images(model, processor, pil_list, batch=BATCH):
    feats = []
    for i in range(0, len(pil_list), batch):
        inp = processor(images=list(pil_list[i:i + batch]), return_tensors='pt').to('cuda')
        vout = model.vision_model(**inp)
        vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        feats.append(F.normalize(model.visual_projection(vp), dim=-1))
    return torch.cat(feats)


@torch.no_grad()
def text_feats(model, processor, texts):
    ti = processor(text=list(texts), return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**ti)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    return F.normalize(model.text_projection(pooled), dim=-1)


def build_lora(vision=True, text=True, rank=8, alpha=16.0):
    m, layers, _ = apply_lora_to_model(
        CLIPModel.from_pretrained(MODEL_ID, local_files_only=True),
        rank=rank, alpha=alpha, apply_to_vision=vision, apply_to_text=text)
    return m, layers


def load_ckpt(model, layers, path):
    ck = torch.load(path, map_location='cpu', weights_only=False)
    sd = ck['lora_state_dict'] if isinstance(ck, dict) and 'lora_state_dict' in ck else ck
    miss = set(sd) - set(layers)
    extra = set(layers) - set(sd)
    if miss or extra:
        raise ValueError('LoRA key mismatch (%d unknown, %d unfilled)' % (len(miss), len(extra)))
    with torch.no_grad():
        for k, w in sd.items():
            layers[k].lora_A.data.copy_(w['A'].to(layers[k].lora_A.dtype))
            layers[k].lora_B.data.copy_(w['B'].to(layers[k].lora_B.dtype))
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=OUT)
    ap.add_argument('--no-vision-ckpt', action='store_true',
                    help='skip checkpoints that cannot be described by the by-name LoRA loader')
    args = ap.parse_args()
    t0 = time.time()

    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    shard_sig = shard_signature(parq)
    torch.manual_seed(0)
    np.random.seed(0)

    processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)
    ds_in = HFDataset.from_parquet(parq)
    legacy_names = [n.split(',')[0].strip().replace('_', ' ') for n in ds_in.features['label'].names]
    assert len(legacy_names) == 1001
    rng = np.random.RandomState(42)
    idx = rng.choice(len(ds_in), N_SAMPLE, replace=False)
    sub = ds_in.select(list(idx))
    pil = list(sub['image'])
    lab = np.array(sub['label'])
    lab_pos = np.array([0 if x == PLACEHOLDER_IDX else x for x in lab])   # placeholder unused

    fm = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True).cuda().eval()
    tf_frozen = text_feats(fm, processor, [TEMPLATE.format(c) for c in legacy_names])
    frozen_img = encode_images(fm, processor, pil)
    frozen_np = (frozen_img @ tf_frozen.T).float().cpu().numpy()
    frozen_topk = np.argsort(-frozen_np, axis=1)[:, :TOPK]
    frozen_top1 = float((frozen_topk[:, 0] == lab).mean() * 100)

    ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
    loader = DataLoader(torch.utils.data.Subset(ds_f, range(2000, 3000)), batch_size=64,
                        shuffle=False, num_workers=0, collate_fn=_collate_fn)
    fi, ft = [], []
    with torch.no_grad():
        for b in loader:
            o = fm(pixel_values=b['image'].cuda(), input_ids=b['input_ids'].cuda(),
                   attention_mask=b['attention_mask'].cuda(), return_loss=False)
            fi.append(F.normalize(o.image_embeds, dim=-1))
            ft.append(F.normalize(o.text_embeds, dim=-1))
    fi, ft = torch.cat(fi), torch.cat(ft)
    gap_vec = ft.mean(0) - fi.mean(0)
    gap_norm = float(gap_vec.norm().item())
    d_hat = gap_vec / gap_vec.norm()
    frozen_cg = (fi.mean(0) - ft.mean(0)).norm().item()

    # frozen geometry
    def geometry(imgf, textf, label_pos, name, model=None):
        """Geometry descriptors for one image-embedding matrix against one text matrix."""
        S = (imgf @ textf.T).float().cpu().numpy()
        topk = np.argsort(-S, axis=1)[:, :TOPK]
        top1 = float((topk[:, 0] == lab).mean() * 100)
        # within-class spread: mean || x - centroid(image label) || over images whose class is
        # represented in the sample (placeholder-labelled images are excluded)
        cent = {}
        for c in np.unique(label_pos):
            m = label_pos == c
            if m.sum() >= 2:
                cent[c] = F.normalize(imgf[m].mean(0), dim=-1)
        spreads = []
        for i in range(len(label_pos)):
            c = label_pos[i]
            if c in cent:
                spreads.append(float(1 - (imgf[i] * cent[c]).sum().item()))
        # top-1 margin: correct-class score minus best other-class score (only where the sample's
        # label is a real ImageNet class)
        correct = S[np.arange(len(S)), lab]
        S_wo = S.copy()
        S_wo[np.arange(len(S)), lab] = -np.inf
        best_other = S_wo.max(1)
        margin = correct - best_other
        pred = topk[:, 0]
        # margin to the best competitor *that is inside this image's own frozen top-5 set* --
        # the quantity tau actually sees
        m5 = np.array([S[i][frozen_topk[i][1]] - S[i][frozen_topk[i][0]] for i in range(len(S))])
        return {
            'name': name, 'top1': round(top1, 4),
            'mean_image_norm': round(float(imgf.norm(dim=-1).mean().item()), 6),
            'std_image_norm': round(float(imgf.norm(dim=-1).std().item()), 6),
            'mean_text_norm': round(float(textf.norm(dim=-1).mean().item()), 6),
            'within_class_spread_mean': round(float(np.mean(spreads)), 6) if spreads else None,
            'margin_top1_mean': round(float(margin.mean()), 6),
            'margin_top1_median': round(float(np.median(margin)), 6),
            'margin_top1_std': round(float(margin.std()), 6),
            'margin_top1_p10': round(float(np.percentile(margin, 10)), 6),
            'margin_top1_p90': round(float(np.percentile(margin, 90)), 6),
            'frac_correct_top1': round(float((pred == lab).mean()), 6),
            'mean_within_top5_margin': round(float(m5.mean()), 6),
            'logit_scale': (None if model is None else round(float(model.logit_scale.exp().item()), 6)),
            '_topk': topk, '_S': S, '_margin': margin, '_pred': pred,
        }

    frozen_geo = geometry(frozen_img, tf_frozen, lab_pos, 'frozen', fm)
    print('frozen geometry: top1=%.2f spread=%.5f margin=%.5f' %
          (frozen_geo['top1'], frozen_geo['within_class_spread_mean'],
           frozen_geo['margin_top1_mean']), flush=True)
    del fi, ft
    torch.cuda.empty_cache()

    # ------------------------------------------------------------------ checkpoints
    summ = json.load(open(SUMMARY_JSON, encoding='utf-8'))
    ckpts = []
    for c in summ['e4']['checkpoints']:
        if 'error' in c or c.get('tau5') is None:
            continue
        tag = c['tag']
        if tag == 'coco_r8_both':
            p = 'outputs/a1_rr_ckpt/coco/epoch10.pt'
        elif tag == 'food101_r8_both':
            p = 'outputs/a1_rr_ckpt/food101/epoch10.pt'
        elif tag == 'dtd_r8_both':
            p = 'outputs/a1_rr_ckpt/dtd/epoch10.pt'
        elif tag == 'flickr30k_ref_r8_both':
            p = 'outputs/a1_rr_ckpt/flickr30k_ref/epoch10.pt'
        elif tag == 'flickr30k_text_only_r8':
            p = 'outputs/imagenet_zs/text_only_r8/best_checkpoint.pt'
            ckpts.append({'tag': tag, 'path': p, 'vision': False, 'text': True,
                          'summary': c, 'dataset': 'flickr30k'})
            continue
        elif tag == 'flickr30k_both_r8':
            p = 'outputs/imagenet_zs/both_r8/best_checkpoint.pt'
        elif tag == 'flickr30k_retrain_both_ep10':
            p = 'outputs/a1_retrain/both/epoch10.pt'
        else:
            continue
        ckpts.append({'tag': tag, 'path': p, 'vision': True, 'text': True,
                      'summary': c, 'dataset': c.get('dataset')})
    # the new seed spread (item 2)
    for ds in ('coco', 'food101', 'dtd'):
        for s in (43, 44):
            p = 'outputs/a1_rr_ckpt/seed%d/%s/epoch10.pt' % (s, ds)
            j = 'outputs/a1_h_seeds_%s_seed%d.json' % (ds, s)
            if os.path.exists(p) and os.path.exists(j):
                d = json.load(open(j, encoding='utf-8'))
                r = d['result']
                ckpts.append({'tag': '%s_r8_both_seed%d' % (ds, s), 'path': p,
                              'vision': True, 'text': True, 'dataset': ds,
                              'summary': {'tag': r['tag'], 'tau5': r['image_only']['legacy1001']['tau_by_k']['5'],
                                          'top1_5k': r['image_only']['legacy1001']['top1_5k'],
                                          'top1_50k': r.get('top1_50k_legacy1001'),
                                          'CG': r['CG_flickr_val'], 'seed': s,
                                          'source_json': j}})

    # ------------------------------------------------------------------ synthetic curve sweep
    def synthetic_row(img2, textf):
        S = (img2 @ textf.T).float().cpu().numpy()
        pi = per_image_tau(frozen_np, S, frozen_topk)
        fin = pi[np.isfinite(pi)]
        return {'tau': float(fin.mean()) if fin.size else None,
                'top1': float((S.argmax(1) == lab).mean() * 100),
                'displacement': float((img2 - frozen_img).norm(dim=-1).mean().item()),
                'n_scored': int(fin.size),
                '_S': S, '_pi': pi}

    syn = {}
    print('\nsynthetic sweep (frozen text tower) ...', flush=True)
    for lam in LAM_GRID:
        img2 = frozen_img if lam == 0 else F.normalize(frozen_img + lam * gap_norm * d_hat, dim=-1)
        r = synthetic_row(img2, tf_frozen)
        syn[str(lam)] = r
        print('  lam=%+0.2f tau=%.4f top1=%6.2f |dx|=%.4f (%.1fs)'
              % (lam, r['tau'], r['top1'], r['displacement'], time.time() - t0), flush=True)

    # ------------------------------------------------------------------ synthetic text-only family
    # Control for the TEXT-only checkpoints: a synthetic model that shares the checkpoint's own
    # (fine-tuned) text tower and keeps the FROZEN image tower. Applying gap surgery to a frozen
    # vision tower changes nothing (dx = 0), so the only meaningful zero-|dx| comparison is this
    # one: it isolates what the text-tower movement alone contributes, and tells us how far the
    # class text embeddings of a fine-tuned checkpoint sit from the frozen ones.
    print('\nsynthetic sweep with the frozen text tower is done; text-only control runs per checkpoint',
          flush=True)

    def syn_interp_tau_at_top1(tau):
        """Interpolate the synthetic tau->top1 curve at a given tau (monotone branch)."""
        pts = sorted([(syn[k]['tau'], syn[k]['top1']) for k in syn if syn[k]['tau'] is not None])
        for i in range(len(pts) - 1):
            t0_, y0 = pts[i]
            t1_, y1 = pts[i + 1]
            if t0_ <= tau <= t1_:
                f = 0.0 if t1_ == t0_ else (tau - t0_) / (t1_ - t0_)
                return y0 + f * (y1 - y0), (t0_, y0), (t1_, y1)
        return None, None, None

    def syn_lambda_for_displacement(d):
        """Synthetic lambda whose mean |dx| equals d (linear interpolation on the sweep)."""
        pts = sorted([(syn[k]['displacement'], float(k)) for k in syn])
        for i in range(len(pts) - 1):
            d0, l0 = pts[i]
            d1, l1 = pts[i + 1]
            if d0 <= d <= d1:
                f = 0.0 if d1 == d0 else (d - d0) / (d1 - d0)
                return l0 + f * (l1 - l0)
        return None

    def syn_refine(target_tau, lo, hi, textf, n_iter=12):
        """Bisect lambda to hit a target tau (tau is monotone decreasing in lambda here)."""
        for _ in range(n_iter):
            mid = 0.5 * (lo + hi)
            img2 = F.normalize(frozen_img + mid * gap_norm * d_hat, dim=-1)
            r = synthetic_row(img2, textf)
            if r['tau'] is None:
                return None
            if r['tau'] > target_tau:
                lo = mid
            else:
                hi = mid
        mid = 0.5 * (lo + hi)
        img2 = F.normalize(frozen_img + mid * gap_norm * d_hat, dim=-1)
        r = synthetic_row(img2, textf)
        r['lambda'] = mid
        r.pop('_S', None)
        r.pop('_pi', None)
        return r

    # ------------------------------------------------------------------ per-checkpoint work
    rows = []
    for entry in ckpts:
        tag = entry['tag']
        print('\n== %s (%s) ==' % (tag, entry['path']), flush=True)
        try:
            m, layers = build_lora(entry['vision'], entry['text'])
            m = load_ckpt(m, layers, entry['path'])
            m = m.cuda().eval()
            imgf = encode_images(m, processor, pil)
            tfc = text_feats(m, processor, [TEMPLATE.format(c) for c in legacy_names])
            geo = geometry(imgf, tfc, lab_pos, tag, m)
            S = geo.pop('_S')
            topk_c = geo.pop('_topk')
            margin_c = geo.pop('_margin')
            pred_c = geo.pop('_pred')

            dx = (imgf - frozen_img)
            mean_dx = float(dx.norm(dim=-1).mean().item())
            # text-tower movement: how far did the class TEXT embeddings move? Needed to judge
            # whether a checkpoint's scores are comparable to a synthetic model built on the
            # FROZEN text tower.
            dtxt = (tfc - tf_frozen)
            mean_dtx = float(dtxt.norm(dim=-1).mean().item())
            # zero-|dx| control: score the frozen image tower against THIS checkpoint's text tower
            S_txt = (frozen_img @ tfc.T).float().cpu().numpy()
            zero_ctrl = {
                'note': 'frozen image tower x this checkpoint\'s text tower -- the only comparison '
                        'available for checkpoints with a frozen vision tower (gap surgery on a '
                        'frozen vision tower is a no-op, dx = 0)',
                'top1': round(float((S_txt.argmax(1) == lab).mean() * 100), 4),
                'tau_vs_frozen': (lambda p: round(float(p[np.isfinite(p)].mean()), 6)
                                  if np.isfinite(p).any() else None)(
                                      per_image_tau(frozen_np, S_txt, frozen_topk)),
                'frozen_image_tower_top1_under_frozen_text': round(frozen_top1, 4),
                'delta_top1_from_frozen': round(
                    float((S_txt.argmax(1) == lab).mean() * 100) - frozen_top1, 4),
            }
            shift_vec = imgf.mean(0) - frozen_img.mean(0)
            shift_norm = float(shift_vec.norm().item())
            cos_shift_gap = float((F.normalize(shift_vec, dim=-1) @ d_hat).item())
            par = float((dx @ d_hat).mean().item())
            perp = float((dx - (dx @ d_hat)[:, None] * d_hat).norm(dim=-1).mean().item())
            ck_cg = (imgf.mean(0) - tfc.mean(0)).norm().item()
            # Flickr30k-val CG of the checkpoint (same definition as the E4 evaluator)
            fi2, ft2 = [], []
            with torch.no_grad():
                for b in loader:
                    o = m(pixel_values=b['image'].cuda(), input_ids=b['input_ids'].cuda(),
                          attention_mask=b['attention_mask'].cuda(), return_loss=False)
                    fi2.append(F.normalize(o.image_embeds, dim=-1))
                    ft2.append(F.normalize(o.text_embeds, dim=-1))
            cg_flickr = float((torch.cat(fi2).mean(0) - torch.cat(ft2).mean(0)).norm().item())

            tau_ck = per_image_tau(frozen_np, S, frozen_topk)
            fin = tau_ck[np.isfinite(tau_ck)]
            tau_ck_mean = float(fin.mean())
            top1_ck = float((S.argmax(1) == lab).mean() * 100)

            # (C) matched tau: synthetic point with the same tau
            syn_pred, lo_pair, hi_pair = syn_interp_tau_at_top1(tau_ck_mean)
            matched = None
            if lo_pair is not None:
                matched = syn_refine(tau_ck_mean, 0.0, 6.0, tf_frozen)
            # (B) matched displacement
            lam_d = syn_lambda_for_displacement(mean_dx)
            matched_disp = None
            if lam_d is not None:
                img2 = F.normalize(frozen_img + lam_d * gap_norm * d_hat, dim=-1)
                rd = synthetic_row(img2, tf_frozen)
                matched_disp = {'lambda': lam_d, 'tau': rd['tau'], 'top1': rd['top1'],
                                'displacement': rd['displacement']}
            # error-set overlap between the checkpoint and the synthetic model at matched tau
            overlap = None
            if matched is not None:
                Ssyn = matched['_S'] if '_S' in matched else None
                if Ssyn is None:
                    img2 = F.normalize(frozen_img + matched['lambda'] * gap_norm * d_hat, dim=-1)
                    Ssyn = (img2 @ tf_frozen.T).float().cpu().numpy()
                pred_s = Ssyn.argmax(1)
                right = lab == pred_c
                overlap = {
                    'frac_correct_ckpt': round(float(right.mean()), 6),
                    'frac_correct_syn': round(float((lab == pred_s).mean()), 6),
                    'both_correct': round(float((right & (lab == pred_s)).mean()), 6),
                    'ckpt_only_correct': round(float((right & (lab != pred_s)).mean()), 6),
                    'syn_only_correct': round(float((~right & (lab == pred_s)).mean()), 6),
                    'both_wrong': round(float((~right & (lab != pred_s)).mean()), 6),
                }
            row = {
                'tag': tag, 'path': entry['path'], 'dataset': entry['dataset'],
                'vision_lora': entry['vision'], 'text_lora': entry['text'],
                'summary_tau5': entry['summary'].get('tau5'),
                'summary_top1_5k': entry['summary'].get('top1_5k'),
                'summary_top1_50k': entry['summary'].get('top1_50k'),
                'summary_CG_flickr': entry['summary'].get('CG'),
                'measured': {
                    'tau5_recomputed': tau_ck_mean,
                    'top1_5k_recomputed': top1_ck,
                    'n_scored': int(fin.size),
                    'peak_top1_class_shift_vs_frozen': round(
                        float((topk_c[:, 0] != frozen_topk[:, 0]).mean()), 6),
                    'top5_set_jaccard_vs_frozen': round(float(np.mean(
                        [len(set(topk_c[i]) & set(frozen_topk[i])) /
                         len(set(topk_c[i]) | set(frozen_topk[i])) for i in range(len(topk_c))])), 6),
                },
                'geometry': geo,
                'geometry_delta_vs_frozen': {
                    'd_within_class_spread': round(
                        (geo['within_class_spread_mean'] or 0)
                        - (frozen_geo['within_class_spread_mean'] or 0), 6),
                    'd_margin_top1_mean': round(geo['margin_top1_mean']
                                                - frozen_geo['margin_top1_mean'], 6),
                    'd_margin_top1_p10': round(geo['margin_top1_p10']
                                               - frozen_geo['margin_top1_p10'], 6),
                    'd_margin_top1_std': round(geo['margin_top1_std']
                                               - frozen_geo['margin_top1_std'], 6),
                    'd_mean_image_norm': round(geo['mean_image_norm']
                                               - frozen_geo['mean_image_norm'], 6),
                    'd_logit_scale': (None if geo['logit_scale'] is None
                                      else round(geo['logit_scale'] - frozen_geo['logit_scale'], 6)),
                },
                'displacement': {
                    'mean_abs_dx': round(mean_dx, 6),
                    'mean_abs_text_dx': round(mean_dtx, 6),
                    'cos_shift_vs_gap_dir': round(cos_shift_gap, 6),
                    'component_parallel_to_gap_dir': round(par, 6),
                    'component_orthogonal_to_gap_dir': round(perp, 6),
                    'frac_orthogonal_of_total': round(perp / (abs(par) + perp + 1e-12), 6),
                    'equivalent_synthetic_lambda': (None if lam_d is None else round(lam_d, 6)),
                },
                'zero_vision_displacement_control': zero_ctrl,
                'cg_imagenet5k_frozen_text': round(ck_cg, 6),
                'cg_flickr_val': round(cg_flickr, 6),
                'matched_tau': ({
                    'target_tau': tau_ck_mean,
                    'synthetic_lambda': matched['lambda'],
                    'synthetic_tau': matched['tau'],
                    'synthetic_top1': matched['top1'],
                    'synthetic_displacement': matched['displacement'],
                    'interp_synthetic_top1_linear': (None if syn_pred is None else round(syn_pred, 4)),
                    'excess_top1': round(top1_ck - matched['top1'], 4),
                    'excess_vs_linear_interp': (None if syn_pred is None
                                                else round(top1_ck - syn_pred, 4)),
                } if matched else None),
                'matched_displacement': matched_disp,
                'error_set_overlap_at_matched_tau': overlap,
            }
            rows.append(row)
            print('  tau=%.4f top1=%.2f |dx|=%.4f cos(shift,gap)=%+.3f par=%+.4f perp=%.4f'
                  % (tau_ck_mean, top1_ck, mean_dx, cos_shift_gap, par, perp), flush=True)
            if matched:
                print('  matched-tau synthetic: lam=%.4f tau=%.4f top1=%.2f -> excess %+.2f points'
                      % (matched['lambda'], matched['tau'], matched['top1'],
                         top1_ck - matched['top1']), flush=True)
            del m, layers, imgf, tfc, S, tau_ck
            torch.cuda.empty_cache()
        except Exception as e:
            import traceback
            rows.append({'tag': tag, 'path': entry['path'], 'ok': False,
                         'error': '%s: %s' % (type(e).__name__, str(e)[:300]),
                         'traceback_tail': traceback.format_exc()[-500:]})
            print('  FAILED: %s' % e, flush=True)
            torch.cuda.empty_cache()

    # ------------------------------------------------------------------ does geometry explain it?
    ok = [r for r in rows if r.get('matched_tau')]
    explain = {'n_checkpoints_with_measurement': len(ok)}
    if len(ok) >= 3:
        exc = np.array([r['matched_tau']['excess_top1'] for r in ok])
        feats = {
            'd_within_class_spread': 'geometry_delta_vs_frozen|d_within_class_spread',
            'd_margin_top1_mean': 'geometry_delta_vs_frozen|d_margin_top1_mean',
            'd_margin_top1_p10': 'geometry_delta_vs_frozen|d_margin_top1_p10',
            'd_margin_top1_std': 'geometry_delta_vs_frozen|d_margin_top1_std',
            'mean_abs_dx': 'displacement|mean_abs_dx',
            'mean_abs_text_dx': 'displacement|mean_abs_text_dx',
            'component_parallel_to_gap_dir': 'displacement|component_parallel_to_gap_dir',
            'component_orthogonal_to_gap_dir': 'displacement|component_orthogonal_to_gap_dir',
            'frac_orthogonal_of_total': 'displacement|frac_orthogonal_of_total',
            'cos_shift_vs_gap_dir': 'displacement|cos_shift_vs_gap_dir',
            'frac_top1_class_shifted': 'measured|peak_top1_class_shift_vs_frozen',
            'cg_flickr_val': 'cg_flickr_val',
        }
        corrs = {}
        for fname, path in feats.items():
            vals = []
            for r in ok:
                cur = r
                for p in path.split('|'):
                    cur = cur.get(p) if isinstance(cur, dict) else None
                    if cur is None:
                        break
                vals.append(cur)
            if any(v is None for v in vals) or len(set(vals)) < 3:
                corrs[fname] = {'n': len(vals), 'note': 'insufficient variation or missing values'}
                continue
            corrs[fname] = {
                'pearson_r': round(float(stats.pearsonr(vals, exc)[0]), 4),
                'pearson_p': float(stats.pearsonr(vals, exc)[1]),
                'spearman_r': round(float(stats.spearmanr(vals, exc)[0]), 4),
                'spearman_p': float(stats.spearmanr(vals, exc)[1]),
                'n': len(vals)}
        explain.update({
            'excess_top1_mean': round(float(exc.mean()), 4),
            'excess_top1_min': round(float(exc.min()), 4),
            'excess_top1_max': round(float(exc.max()), 4),
            'excess_top1_std': round(float(exc.std(ddof=1)), 4),
            'correlation_of_excess_with_geometry': corrs,
            'definition': 'excess_top1 = checkpoint 5k top-1 minus the synthetic (frozen-text) '
                          'top-1 at the SAME tau, lambda found by bisection',
        })
        # --- split by whether the VISION tower was fine-tuned: the excess is only a like-for-like
        # comparison when the checkpoint's image tower moved, because the synthetic family always
        # keeps the frozen text tower and a frozen vision tower makes the surgery a no-op.
        try:
            vchanged = [r for r in ok if r.get('vision_lora')]
            vfrozen = [r for r in ok if not r.get('vision_lora')]
            explain['by_vision_tower'] = {
                'note': 'excess_top1 = checkpoint top-1 minus synthetic top-1 at matched tau. For '
                        'vision-frozen checkpoints the synthetic reference is degenerate (dx = 0), '
                        'so their excess is NOT a like-for-like number; use '
                        'zero_vision_displacement_control instead.',
                'vision_lora_checkspoints': {
                    'n': len(vchanged),
                    'tags': [r['tag'] for r in vchanged],
                    'excess_stats': summarise([r['matched_tau']['excess_top1'] for r in vchanged])},
                'vision_frozen_checkpoints': {
                    'n': len(vfrozen),
                    'tags': [r['tag'] for r in vfrozen],
                    'excess_stats': summarise([r['matched_tau']['excess_top1'] for r in vfrozen]),
                    'zero_dx_control': {r['tag']: r['zero_vision_displacement_control']
                                        for r in vfrozen}},
                'mean_abs_dx_vs_excess_vision_lora_only': corr(
                    [r['displacement']['mean_abs_dx'] for r in vchanged],
                    [r['matched_tau']['excess_top1'] for r in vchanged]),
                'frac_orthogonal_vs_excess_vision_lora_only': corr(
                    [r['displacement']['frac_orthogonal_of_total'] for r in vchanged],
                    [r['matched_tau']['excess_top1'] for r in vchanged]),
                'frac_top1_class_shifted_vs_excess_vision_lora_only': corr(
                    [r['measured']['peak_top1_class_shift_vs_frozen'] for r in vchanged],
                    [r['matched_tau']['excess_top1'] for r in vchanged]),
            }
        except Exception as e:
            explain['by_vision_tower'] = {'error': '%s: %s' % (type(e).__name__, e)}

        # same question within the synthetic family itself (control): does the synthetic excess
        # against its own linear interpolation vary systematically?
        explain['synthetic_selfcheck'] = {
            'note': 'the synthetic family at matched tau has excess 0 by construction; the '
                    'linear-interpolation variant quantifies how much of a small excess could be '
                    'curve curvature rather than mechanism',
            'linear_interp_residuals': {
                r['tag']: r['matched_tau']['excess_vs_linear_interp'] for r in ok}}

    payload = {
        'meta': {
            'script': 'tools/a1_h_offset.py',
            'purpose': 'item 5 -- test whether the real-checkpoint offset above the synthetic '
                       'tau->top-1 curve is explained by embedding-geometry changes',
            'script_sha1_self': file_sha1('tools/a1_h_offset.py'),
            'common_sha1': file_sha1('tools/a1_h_common.py'),
            'model': MODEL_ID, 'template': TEMPLATE,
            'class_list_source': 'data/imagenet_hf parquet label names (legacy1001)',
            'class_list_len': len(legacy_names),
            'placeholder_class_index': PLACEHOLDER_IDX,
            'shard_signature': shard_sig,
            'n_sample_images': N_SAMPLE,
            'topk_for_tau': TOPK,
            'lambda_grid': LAM_GRID,
            'gap': {'source': 'Flickr30k train rows 2000..3000', 'gap_norm': round(gap_norm, 6)},
            'inputs': {p: file_sha1(p) for p in [SUMMARY_JSON, BASELINE_JSON, TEMPLATES_JSON]
                       if os.path.exists(p)},
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'runtime_s': None,
        },
        'frozen': {k: v for k, v in frozen_geo.items() if not k.startswith('_')},
        'frozen_cg_flickr_val': round(frozen_cg, 6),
        'frozen_top1_5k': round(frozen_top1, 4),
        'synthetic_curve': {k: {kk: vv for kk, vv in v.items() if not kk.startswith('_')}
                            for k, v in syn.items()},
        'checkpoints': rows,
        'offset_analysis': explain,
    }
    payload['meta']['runtime_s'] = round(time.time() - t0, 1)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)

    print('\n== offset analysis (%d checkpoints) ==' % len(ok))
    for r in ok:
        mt = r['matched_tau']
        print('  %-30s tau=%.4f top1=%.2f matched_lam=%6.3f syn_top1=%.2f excess=%+.2f (%s)'
              % (r['tag'], r['measured']['tau5_recomputed'], r['measured']['top1_5k_recomputed'],
                 mt['synthetic_lambda'], mt['synthetic_top1'], mt['excess_top1'],
                 r['dataset']))
    if 'excess_top1_mean' in explain:
        print('  excess mean=%.3f sd=%.3f range=[%.3f, %.3f]'
              % (explain['excess_top1_mean'], explain['excess_top1_std'],
                 explain['excess_top1_min'], explain['excess_top1_max']))
        for k, v in explain['correlation_of_excess_with_geometry'].items():
            print('    corr(excess, %-32s) pearson=%s spearman=%s n=%s'
                  % (k, v.get('pearson_r'), v.get('spearman_r'), v.get('n')))
    print('\nsaved', args.out, '(%.1fs)' % (time.time() - t0))


if __name__ == '__main__':
    main()
