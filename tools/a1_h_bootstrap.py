"""A1 hardening item 4 -- bootstrap 95% confidence intervals for tau, and the k-specificity of
the calibration thresholds.

Part A (bootstrap CIs). For every condition with a measurable per-image tau, resample the images
with replacement (>=1000 replicates) and report tau with its percentile 95% CI:
  * the dose-response (gap-surgery) grid of `tools/a1_h_baseline_metrics.py` on the ImageNet 5 000
    -image sample, k = 5,
  * the lambda = 0/0.5/1/2 points of the four benchmarks of `outputs/a1_rr_e3_benchmarks.json`
    (DTD, Food-101, iNat-wild, rare-species) -- the per-image quantities are recomputed here with
    the estimator of `tools/a1_rr_e3_benchmarks.py` so the point estimates reproduce that JSON,
  * the ImageNet 5k / DTD / Food-101 template conditions of `outputs/a1_h_templates.json`,
  * the per-image tau in `outputs/a1_h_baseline_metrics.json` (surgery family, k = 5).
Every point estimate is reported next to the value in the source JSON so agreement is visible.

Part B (k-specificity). The manuscript's tripwire thresholds are calibrated at k = 5. Using the
per-image tau over a k-sweep from `outputs/a1_h_baseline_metrics.json` and the absolute levels in
`outputs/a1_rr_e2_topk.json`, this part quantifies how far the ABSOLUTE tau level moves with k and
what that does to a fixed threshold.

Output: outputs/a1_h_bootstrap.json
Run:    D:\\Anaconda\\envs\\pytorch\\python.exe tools/a1_h_bootstrap.py
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
from PIL import Image
from transformers import CLIPModel, CLIPProcessor
from torch.utils.data import DataLoader

from a1_h_common import per_image_tau, bootstrap_mean  # noqa: E402
from src.dataset import Flickr30kDataset, _collate_fn  # noqa: E402

MODEL_ID = 'openai/clip-vit-base-patch32'
TEMPLATE = 'a photo of a {}'
TOPK = 5
LAMBDAS = [0.0, 0.5, 1.0, 2.0]
N_BOOT = 2000
BOOT_SEED = 20260101
BATCH = 128
BASELINE_JSON = 'outputs/a1_h_baseline_metrics.json'
TEMPLATES_JSON = 'outputs/a1_h_templates.json'
E2_JSON = 'outputs/a1_rr_e2_topk.json'
E3_JSON = 'outputs/a1_rr_e3_benchmarks.json'
OUT = 'outputs/a1_h_bootstrap.json'


def file_sha1(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def shard_signature(parq):
    h = hashlib.sha1()
    for p in parq:
        h.update(os.path.basename(p).encode())
        h.update(str(os.path.getsize(p)).encode())
    return h.hexdigest()[:16]


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# --------------------------------------------------------------------------- benchmark loaders
# verbatim from tools/a1_rr_e3_benchmarks.py so the point estimates are comparable
def _tv_paths_labels(ds):
    paths = None
    for attr in ('_image_files', 'imgs'):
        v = getattr(ds, attr, None)
        if v is not None and len(v) == len(ds):
            paths = [x[0] if isinstance(x, (tuple, list)) else x for x in v]
            break
    labels = None
    for attr in ('_labels', 'labels', 'targets'):
        v = getattr(ds, attr, None)
        if v is not None and len(v) == len(ds):
            labels = [int(x) for x in v]
            break
    if labels is None:
        labels = [int(ds[i][1]) for i in range(len(ds))]
    return paths, labels


def load_dtd():
    import torchvision.datasets as tvds
    ds = tvds.DTD(root='data', split='test', download=False)
    names = list(ds.classes)
    paths, labels = _tv_paths_labels(ds)
    return names, (paths if paths is not None else [ds[i][0] for i in range(len(ds))]), np.array(labels)


def load_food101():
    import torchvision.datasets as tvds
    ds = tvds.Food101(root='data', split='test', download=False)
    names = list(ds.classes)
    paths, labels = _tv_paths_labels(ds)
    return names, (paths if paths is not None else [ds[i][0] for i in range(len(ds))]), np.array(labels)


def load_inat_wild():
    root = 'data/inat_wild'
    dirs = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    names, sources, labels = [], [], []
    for d in dirs:
        files = sorted(f for f in os.listdir(os.path.join(root, d)) if f.lower().endswith('.jpg'))
        if len(files) < 8:
            continue
        ci = len(names)
        names.append(d.replace('_', ' '))
        for f in files:
            sources.append(os.path.join(root, d, f))
            labels.append(ci)
    return names, sources, np.array(labels)


def load_rare_species():
    from datasets import load_dataset
    files = sorted(os.path.join('data/rare-species/data', f)
                   for f in os.listdir('data/rare-species/data'))
    ds = load_dataset('parquet', data_files=files, split='train')
    sci = ds['sciName']
    counts = {}
    for s in sci:
        counts[s] = counts.get(s, 0) + 1
    top = sorted(counts, key=lambda c: (-counts[c], c))[:50]
    top_set = set(top)
    keep = {}
    for i, s in enumerate(sci):
        if s in top_set and len(keep.get(s, [])) < 20:
            keep.setdefault(s, []).append(i)
    names, sources, labels = [], [], []
    for ci, s in enumerate(top):
        names.append(s)
        for i in keep[s]:
            b = ds[i]['file_name']
            if isinstance(b, Image.Image):
                im = b
            elif isinstance(b, dict):
                im = Image.open(b['path']) if b.get('path') else Image.open(__import__('io').BytesIO(b['bytes']))
            else:
                im = Image.open(b)
            sources.append(im.convert('RGB'))
            labels.append(ci)
    return names, sources, np.array(labels)


BENCH_LOADERS = {'dtd': load_dtd, 'food101': load_food101,
                 'inat_wild': load_inat_wild, 'rare_species': load_rare_species}


@torch.no_grad()
def embed_images(model, processor, sources):
    feats = []
    for i in range(0, len(sources), BATCH):
        chunk = sources[i:i + BATCH]
        pil = [(s if isinstance(s, Image.Image) else Image.open(s)).convert('RGB') for s in chunk]
        inp = processor(images=pil, return_tensors='pt').to('cuda')
        vout = model.vision_model(**inp)
        vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        feats.append(F.normalize(model.visual_projection(vp), dim=-1))
    return torch.cat(feats)


@torch.no_grad()
def embed_texts(model, processor, texts):
    ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**ti)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    return F.normalize(model.text_projection(pooled), dim=-1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=OUT)
    ap.add_argument('--n-boot', type=int, default=N_BOOT)
    args = ap.parse_args()
    t0 = time.time()

    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    shard_sig = shard_signature(parq)
    torch.manual_seed(0)
    np.random.seed(0)

    base_json = load(BASELINE_JSON)
    templates_json = load(TEMPLATES_JSON) if os.path.exists(TEMPLATES_JSON) else None
    e2 = load(E2_JSON)
    e3 = load(E3_JSON)

    out = {'meta': {
        'script': 'tools/a1_h_bootstrap.py',
        'purpose': 'item 4 -- bootstrap 95% CIs for tau; k-specificity of the thresholds',
        'script_sha1_self': file_sha1('tools/a1_h_bootstrap.py'),
        'common_sha1': file_sha1('tools/a1_h_common.py'),
        'model': MODEL_ID,
        'n_boot': args.n_boot, 'boot_seed': BOOT_SEED, 'ci_level': 0.95,
        'resampling_unit': 'images, with replacement (tau is a mean of per-image quantities)',
        'topk_for_tau': TOPK,
        'class_list_source': base_json['meta'].get('class_list_source'),
        'class_list_len': base_json['meta'].get('class_list_len'),
        'class_list_len_clean': base_json['meta'].get('class_list_len_clean'),
        'shard_signature': shard_sig,
        'inputs': {p: file_sha1(p) for p in [BASELINE_JSON, TEMPLATES_JSON, E2_JSON, E3_JSON]
                   if os.path.exists(p)},
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
    }}

    # =========================================================== A: bootstraps
    boot = {}

    # --- A1: dose-response grid, ImageNet 5k, from the stored per-image tau (k = 5)
    stored = base_json['per_image_tau_by_condition']['k5']
    src_tau = {c['name']: c.get('tau_k5') for c in base_json['conditions']}
    grid = {}
    for name, arr in stored.items():
        r = bootstrap_mean(arr, n_boot=args.n_boot, seed=BOOT_SEED)
        r['tau_in_source_json'] = src_tau.get(name)
        r['agrees_with_source'] = (None if r['point'] is None or r['tau_in_source_json'] is None
                                   else bool(abs(r['point'] - r['tau_in_source_json']) < 1e-9))
        grid[name] = r
        print('  [grid] %-7s tau=%.4f [%.4f, %.4f]  (se %.4f, n=%d)'
              % (name, r['point'], r['ci_low'], r['ci_high'], r['se'], r['n_images']), flush=True)
    boot['dose_response_grid_imagenet5k_k5'] = {
        'source': BASELINE_JSON, 'note': 'T-family surgery, lambda = 0/0.25/0.5/1/2/4 and the '
                                        'negative-lambda recovery points', 'conditions': grid}

    # --- A2: benchmark conditions, per-image recomputed with the E3 estimator
    model = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True).cuda().eval()
    processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)
    ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
    fi, ft = [], []
    with torch.no_grad():
        loader = DataLoader(torch.utils.data.Subset(ds_f, range(2000, 3000)), batch_size=64,
                            shuffle=False, num_workers=0, collate_fn=_collate_fn)
        for b in loader:
            o = model(pixel_values=b['image'].cuda(), input_ids=b['input_ids'].cuda(),
                      attention_mask=b['attention_mask'].cuda(), return_loss=False)
            fi.append(F.normalize(o.image_embeds, dim=-1))
            ft.append(F.normalize(o.text_embeds, dim=-1))
    g = torch.cat(ft).mean(0) - torch.cat(fi).mean(0)
    gap_norm = float(g.norm().item())
    d_hat = g / g.norm()

    bench_res = {}
    for bkey, loader_fn in BENCH_LOADERS.items():
        e3b = e3['benchmarks'].get(bkey, {})
        if not e3b.get('loaded'):
            bench_res[bkey] = {'loaded': False, 'error': e3b.get('error', 'not loaded in E3 JSON')}
            continue
        names, sources, labels = loader_fn()
        print('  [bench] %s: %d images, %d classes' % (bkey, len(sources), len(names)), flush=True)
        img = embed_images(model, processor, sources)
        tf = embed_texts(model, processor, [TEMPLATE.format(c) for c in names])
        base_np = (img @ tf.T).float().cpu().numpy()
        topk = np.argsort(-base_np, axis=1)[:, :TOPK]
        entry = {'loaded': True, 'n_images': len(sources), 'n_classes': len(names),
                 'class_list_len': len(names), 'gap_norm': round(gap_norm, 6),
                 'frozen_top1': round(float((base_np.argmax(1) == labels).mean() * 100), 4),
                 'conditions': {}}
        for lam in LAMBDAS:
            img2 = img if lam == 0.0 else F.normalize(img + lam * gap_norm * d_hat, dim=-1)
            s_np = (img2 @ tf.T).float().cpu().numpy()
            pi = per_image_tau(base_np, s_np, topk)
            r = bootstrap_mean(pi, n_boot=args.n_boot, seed=BOOT_SEED)
            r['top1'] = round(float((s_np.argmax(1) == labels).mean() * 100), 4)
            e3v = e3b['variants']['flickr30k']['surgery'].get(str(lam), {})
            r['tau_in_e3_json'] = e3v.get('tau')
            r['top1_in_e3_json'] = e3v.get('top1')
            r['tau_agrees_with_e3'] = (None if r['point'] is None or r['tau_in_e3_json'] is None
                                       else bool(abs(r['point'] - r['tau_in_e3_json']) < 1e-5))
            r['top1_agrees_with_e3'] = (None if r['top1_in_e3_json'] is None
                                        else bool(abs(r['top1'] - r['top1_in_e3_json']) < 0.01))
            entry['conditions'][str(lam)] = r
            print('     %-12s lam=%+0.1f tau=%.4f [%.4f, %.4f] top1=%.2f (E3 tau=%s)'
                  % (bkey, lam, r['point'], r['ci_low'], r['ci_high'], r['top1'],
                     r['tau_in_e3_json']), flush=True)
        bench_res[bkey] = entry
        del img, tf
        torch.cuda.empty_cache()
    boot['benchmarks_e3'] = {'source': E3_JSON, 'note': 'gap estimated on Flickr30k rows '
                                                       '2000..3000 (the E3 primary variant)',
                             'gap_norm': round(gap_norm, 6), 'benchmarks': bench_res}

    # --- A3: template conditions, from the stored per-image tau
    if templates_json:
        tpl_res = {}
        for bname, b in templates_json['results'].items():
            tpl_res[bname] = {'n_images': b['n_images'], 'class_list_len': b['class_list_len'],
                              'templates': {}}
            for tkey, tv in b['templates'].items():
                sv = tv['variants']['coupled']['surgery']
                conds = {}
                for lam in LAMBDAS:
                    d = sv[str(lam)]
                    if 'per_image_tau' in d:
                        r = bootstrap_mean(d['per_image_tau'], n_boot=args.n_boot, seed=BOOT_SEED)
                        r['tau_in_source_json'] = d['tau']
                        r['top1'] = d['top1']
                        r['agrees_with_source'] = bool(abs(r['point'] - d['tau']) < 1e-5)
                    else:
                        r = {'point': d['tau'], 'top1': d['top1'], 'n_images': None,
                             'ci_low': None, 'ci_high': None, 'se': None,
                             'note': 'not bootstrapped: per-image tau not stored for lambda=0 '
                                     '(tau=1 by construction)'}
                    conds[str(lam)] = r
                tpl_res[bname]['templates'][tkey] = conds
        boot['templates'] = {'source': TEMPLATES_JSON, 'benchmarks': tpl_res}

    out['bootstrap'] = boot

    # =========================================================== B: k-specificity
    ks = base_json['per_image_tau_k_sweep']['ks']
    ksw = base_json['per_image_tau_k_sweep']['data']
    k_lams = base_json['per_image_tau_k_sweep']['lambdas']
    # absolute E2 levels (independent source: outputs/a1_rr_e2_topk.json)
    e2tab = {}
    for conv in ('legacy1001', 'clean1000'):
        e2tab[conv] = {}
        for k in e2['meta']['ks']:
            ls = str(k)
            tv = e2['conventions'][conv]['tau_vs_lambda_by_k'].get(ls, {}).get('measured', {})
            e2tab[conv][ls] = {lam: tv.get(lam) for lam in ('0.0', '0.25', '0.5', '1.0', '2.0', '4.0')}
    kabs = {}
    for k in ks:
        kabs[str(k)] = {}
        for lam in k_lams:
            arr = ksw[str(k)].get('T%.2g' % lam)
            r = bootstrap_mean(arr, n_boot=args.n_boot, seed=BOOT_SEED) if arr else None
            if r:
                r['n_images_scored'] = int(np.isfinite(np.asarray(arr, dtype=float)).sum())
                r['frac_images_dropped'] = round(
                    1 - r['n_images_scored'] / len(arr), 6) if arr else None
            kabs[str(k)][str(lam)] = r
    # tripwire translation: at which lambda does tau first drop below a given threshold, per k?
    thresholds = [0.8, 0.7, 0.6, 0.5, 0.4]
    trip = {}
    ksorted = sorted([k for k in ks if k >= 2])
    for k in ksorted:
        row = {}
        for thr in thresholds:
            hit = None
            for lam in sorted(k_lams):
                r = kabs[str(k)].get(str(lam))
                if r and r['point'] is not None and r['point'] < thr:
                    hit = float(lam)
                    break
            row['thr_%.1f' % thr] = hit
        trip[str(k)] = {'first_lambda_below': row,
                        'tau_at_lambda0.5': (kabs[str(k)]['0.5'] or {}).get('point'),
                        'tau_at_lambda1.0': (kabs[str(k)]['1.0'] or {}).get('point')}
    shift = {}
    for lam in k_lams:
        vals = {str(k): (kabs[str(k)][str(lam)] or {}).get('point') for k in ksorted}
        ok = {k: v for k, v in vals.items() if v is not None}
        if ok:
            kmax = max(ok, key=lambda kk: ok[kk])
            kmin = min(ok, key=lambda kk: ok[kk])
            shift[str(lam)] = {'tau_by_k': vals, 'max_over_k': ok[kmax], 'argmax_k': int(kmax),
                              'min_over_k': ok[kmin], 'argmin_k': int(kmin),
                              'abs_shift': round(ok[kmax] - ok[kmin], 6)}
    exact = {'spearman_vs_k5_curve': e2['conventions']['legacy1001']['curve_stability_vs_k5'],
             'e2_absolute_levels': e2tab,
             'e2_note': e2['meta']['tau_estimator'],
             'kendall_tau_undefined_at_k1': e2['meta']['kendall_tau_undefined_at_k1']}
    out['k_specificity'] = {
        'note': 'the manuscript tripwire thresholds are calibrated at k = 5; the ABSOLUTE tau '
                'level is a function of k, so a fixed numeric threshold has a different meaning '
                'at every k.',
        'per_k_bootstrap_at_sweep_lambdas': kabs,
        'first_lambda_below_threshold': trip,
        'absolute_level_shift_over_k': shift,
        'e2_absolute_levels_by_k': exact,
        'thresholds_probed': thresholds,
        'sweep_lambdas': k_lams,
    }

    out['meta']['runtime_s'] = round(time.time() - t0, 1)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    print('\n== k-specificity (tau at lambda = 0.5, bootstrap point estimates) ==')
    for k in ksorted:
        r = kabs[str(k)]['0.5']
        print('  k=%-4d tau(0.5)=%s  CI=[%s, %s]' %
              (k, None if not r else round(r['point'], 4),
               None if not r else round(r['ci_low'], 4), None if not r else round(r['ci_high'], 4)))
    print('\nsaved', args.out, '(%.1fs)' % (time.time() - t0))


if __name__ == '__main__':
    main()
