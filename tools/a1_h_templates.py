"""A1 hardening item 3 -- prompt-template sensitivity of the zero-shot / surgery protocol.

The manuscript's zero-shot numbers all use the single template `a photo of a {}`. This script
re-runs the key protocol (frozen top-1 and tau at lambda = 0, 0.5, 1, 2 under gap surgery) under
five templates, on ImageNet (the fixed 5 000-image sample, RandomState(42)) and on the two
benchmarks DTD and Food-101 from outputs/a1_rr_e3_benchmarks.json.

Templates (the first is the manuscript default):
    t0  'a photo of a {}'          <- manuscript default
    t1  'a photo of the {}'
    t2  'a photo of a {} in the wild'
    t3  '{}'
    t4  'a close-up photo of a {}'

Two gap variants per template, because the template enters the gap estimate too:
    coupled : g = mean(text(classes of the benchmark? no) ...) -- concretely, g is estimated on
              Flickr30k rows 2000..3000 with THIS template's text encoder (protocol-identical to
              the manuscript, only the template changes).
    fixed_t0: g is always the t0 gap, so only the evaluation template changes.

IMPORTANT (stated in the report): tau is computed on **frozen top-5 class sets derived per
template** -- i.e. the frozen ranking under template t defines the class set, and the perturbed
ranking under the SAME template is compared to it. tau values are therefore template-internal
and only comparable within a column.

Output: outputs/a1_h_templates.json
Run:    D:\\Anaconda\\envs\\pytorch\\python.exe tools/a1_h_templates.py
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
from PIL import Image
from scipy import stats
from transformers import CLIPModel, CLIPProcessor
from torch.utils.data import DataLoader

from src.dataset import Flickr30kDataset, _collate_fn  # noqa: E402

MODEL_ID = 'openai/clip-vit-base-patch32'
N_IMNET = 5000
PLACEHOLDER_IDX = 1000
LAMBDAS = [0.0, 0.5, 1.0, 2.0]
PER_IMAGE_LAMBDAS = [0.5, 1.0, 2.0]   # per-image tau stored for these (feeds item 4 bootstraps)
TOPK = 5
BATCH = 128
OUT = 'outputs/a1_h_templates.json'

TEMPLATES = {
    't0_photo_of_a': 'a photo of a {}',
    't1_photo_of_the': 'a photo of the {}',
    't2_in_the_wild': 'a photo of a {} in the wild',
    't3_bare_class': '{}',
    't4_close_up': 'a close-up photo of a {}',
}
DEFAULT_TEMPLATE = 't0_photo_of_a'
BENCHMARKS = ['imagenet5k', 'dtd', 'food101']


# ------------------------------------------------------------------ helpers
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


def per_image_tau(base_np, cur_np, topk):
    """Per-image Kendall tau_b over the given (already frozen) top-k index set."""
    k = topk.shape[1]
    if k < 2:
        return None
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
    return np.clip(t, -1.0, 1.0)


@torch.no_grad()
def embed_texts(model, processor, texts):
    ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**ti)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    return F.normalize(model.text_projection(pooled), dim=-1)


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
    sources = paths if paths is not None else [ds[i][0] for i in range(len(ds))]
    return names, sources, np.array(labels)


def load_food101():
    import torchvision.datasets as tvds
    ds = tvds.Food101(root='data', split='test', download=False)
    names = list(ds.classes)
    paths, labels = _tv_paths_labels(ds)
    sources = paths if paths is not None else [ds[i][0] for i in range(len(ds))]
    return names, sources, np.array(labels)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=OUT)
    ap.add_argument('--benchmarks', default=','.join(BENCHMARKS))
    args = ap.parse_args()
    t0 = time.time()

    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    shard_sig = shard_signature(parq)
    torch.manual_seed(0)
    np.random.seed(0)

    model = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True).cuda().eval()
    processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)

    from datasets import Dataset as HFDataset
    ds_in = HFDataset.from_parquet(parq)
    imnet_names = [n.split(',')[0].strip().replace('_', ' ') for n in ds_in.features['label'].names]
    rng = np.random.RandomState(42)
    idx = rng.choice(len(ds_in), N_IMNET, replace=False)
    sub = ds_in.select(list(idx))
    imnet_labels = np.array(sub['label'])
    imnet_imgs = list(sub['image'])

    ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
    val_loader = DataLoader(torch.utils.data.Subset(ds_f, range(2000, 3000)), batch_size=64,
                            shuffle=False, num_workers=0, collate_fn=_collate_fn)

    # ---------------- benchmark image embeddings (template-independent) ----------------
    bench = {}
    print('embedding ImageNet 5k sample ...', flush=True)
    bench['imagenet5k'] = {'class_names': imnet_names, 'labels': imnet_labels,
                           'img': embed_images(model, processor, imnet_imgs),
                           'n_images': len(imnet_imgs)}
    want = [b for b in args.benchmarks.split(',') if b != 'imagenet5k']
    for b in want:
        names, sources, labels = {'dtd': load_dtd, 'food101': load_food101}[b]()
        print('embedding %s (%d images, %d classes) ...' % (b, len(sources), len(names)), flush=True)
        bench[b] = {'class_names': [n.replace('_', ' ') for n in names], 'labels': np.array(labels),
                    'img': embed_images(model, processor, sources), 'n_images': len(sources)}

    # ---------------- per-template frozen text matrix, and the (template, gap) combinations ----
    # NOTE: build the full (benchmark x template) text table FIRST, then loop for the gaps -- the
    # gap loop needs the Flickr30k loader and must not be responsible for filling this table.
    for bname, b in bench.items():
        b['text'] = {}
    with torch.no_grad():
        for tkey, tpl in TEMPLATES.items():
            for bname, b in bench.items():
                b['text'][tkey] = embed_texts(
                    model, processor, [tpl.format(c) for c in b['class_names']])
            print('  text table built for template %-18s (%d benchmarks)'
                  % (tkey, len(bench)), flush=True)

    gaps = {}
    with torch.no_grad():
        for tkey, tpl in TEMPLATES.items():
            # Flickr30k text embeddings under this template -> gap direction
            fi, ft = [], []
            for batch in val_loader:
                o = model(pixel_values=batch['image'].cuda(), input_ids=batch['input_ids'].cuda(),
                          attention_mask=batch['attention_mask'].cuda(), return_loss=False)
                fi.append(F.normalize(o.image_embeds, dim=-1))
                ft.append(F.normalize(o.text_embeds, dim=-1))
            g = torch.cat(ft).mean(0) - torch.cat(fi).mean(0)
            gaps[tkey] = {'vec': g, 'norm': float(g.norm().item()),
                          'd_hat': g / g.norm()}
            print('  template %-18s gap_norm=%.4f' % (tkey, gaps[tkey]['norm']), flush=True)

    # ---------------- protocol ----------------
    def cross_template_tau(b, rows):
        """How much does the frozen ranking itself move between templates?

        For every template t, the t0 frozen ranking is compared to t's frozen ranking on
        (a) t0's own frozen top-5 set and (b) t's own frozen top-5 set. Because the pair
        (t0, t) is scored with a pair-specific reference, this is a measure of template drift in
        the class-relative ranking, not of surgery.
        """
        ref_key = DEFAULT_TEMPLATE
        img = b['img']
        base_np = (img @ b['text'][ref_key].T).float().cpu().numpy()
        topk_fixed = np.argsort(-base_np, axis=1)[:, :TOPK]
        out = {}
        for tkey in TEMPLATES:
            cur_np = (img @ b['text'][tkey].T).float().cpu().numpy()
            pi_fixed = per_image_tau(base_np, cur_np, topk_fixed)
            f1 = pi_fixed[np.isfinite(pi_fixed)]
            own = np.argsort(-cur_np, axis=1)[:, :TOPK]
            pi_own = per_image_tau(base_np, cur_np, own)
            f2 = pi_own[np.isfinite(pi_own)]
            out[tkey] = {
                'tau_vs_t0_on_t0_top5': round(float(f1.mean()), 6) if f1.size else None,
                'tau_vs_t0_on_own_top5': round(float(f2.mean()), 6) if f2.size else None,
                'top5_set_jaccard_vs_t0': round(float(np.mean(
                    [len(set(topk_fixed[i]) & set(own[i])) / len(set(topk_fixed[i]) | set(own[i]))
                     for i in range(len(topk_fixed))])), 6)}
        return out

    results = {}
    for bname, b in bench.items():
        base_img = b['img']
        rows = {}
        for tkey in TEMPLATES:
            tf = b['text'][tkey]
            base_np = (base_img @ tf.T).float().cpu().numpy()
            topk = np.argsort(-base_np, axis=1)[:, :TOPK]
            lab = b['labels']
            frozen_top1 = float((base_np.argmax(1) == lab).mean() * 100)
            row = {'frozen_top1': round(frozen_top1, 4), 'variants': {}}
            for gkey, gsrc in (('coupled', tkey), ('fixed_t0', DEFAULT_TEMPLATE)):
                d_hat = gaps[gsrc]['d_hat']
                gn = gaps[gsrc]['norm']
                surgery = {}
                for lam in LAMBDAS:
                    img2 = base_img if lam == 0.0 else F.normalize(base_img + lam * gn * d_hat,
                                                                   dim=-1)
                    s_np = (img2 @ tf.T).float().cpu().numpy()
                    pi = per_image_tau(base_np, s_np, topk)
                    fin = pi[np.isfinite(pi)]
                    surgery[str(lam)] = {
                        'top1': round(float((s_np.argmax(1) == lab).mean() * 100), 4),
                        'tau': round(float(fin.mean()), 6) if fin.size else None,
                        'n_images_scored': int(fin.size),
                        'frac_images_with_tie': round(float(1 - fin.size / len(pi)), 6)}
                    if lam in PER_IMAGE_LAMBDAS and gkey == 'coupled':
                        surgery[str(lam)]['per_image_tau'] = [
                            None if not np.isfinite(x) else round(float(x), 8) for x in pi]
                row['variants'][gkey] = {'gap_source_template': gsrc,
                                         'gap_norm': round(gn, 6), 'surgery': surgery}
            rows[tkey] = row
            print('%-11s %-18s frozen_top1=%6.2f | coupled tau %s | top1 %s' %
                  (bname, tkey, frozen_top1,
                   [rows[tkey]['variants']['coupled']['surgery'][str(l)]['tau'] for l in LAMBDAS],
                   [rows[tkey]['variants']['coupled']['surgery'][str(l)]['top1'] for l in LAMBDAS]),
                  flush=True)
        results[bname] = {'n_images': b['n_images'], 'n_classes': len(b['class_names']),
                          'class_list_len': len(b['class_names']), 'templates': rows,
                          'cross_template_tau': cross_template_tau(b, rows)}

    # ---------------- template-stability summary ----------------
    stability = {}
    for bname, r in results.items():
        s = {}
        for gkey in ('coupled', 'fixed_t0'):
            for lam in LAMBDAS:
                taus = []
                t1s = []
                for tkey in TEMPLATES:
                    sv = r['templates'][tkey]['variants'][gkey]['surgery'][str(lam)]
                    if sv['tau'] is not None:
                        taus.append(sv['tau'])
                    t1s.append(sv['top1'])
                if not taus:
                    continue
                s['%s|lam%+.1f' % (gkey, lam)] = {
                    'tau_min': min(taus), 'tau_max': max(taus),
                    'tau_mean': float(np.mean(taus)), 'tau_spread': max(taus) - min(taus),
                    'tau_std': float(np.std(taus)),
                    'top1_min': min(t1s), 'top1_max': max(t1s),
                    'top1_spread': max(t1s) - min(t1s),
                    'n_templates_used': len(taus)}
        # is the tau(lambda) collapse signature present under every template?
        collapse = {}
        for tkey in TEMPLATES:
            v = r['templates'][tkey]['variants']['coupled']['surgery']
            collapse[tkey] = {'tau_0': v['0.0']['tau'], 'tau_2': v['2.0']['tau'],
                              'monotone_decreasing': bool(
                                  all(v[str(LAMBDAS[i])]['tau'] is not None and
                                      v[str(LAMBDAS[i + 1])]['tau'] is not None and
                                      v[str(LAMBDAS[i])]['tau'] >= v[str(LAMBDAS[i + 1])]['tau']
                                      for i in range(len(LAMBDAS) - 1))),
                              'top1_0': v['0.0']['top1'], 'top1_2': v['2.0']['top1']}
        stability[bname] = {'spread_per_lambda': s, 'collapse_per_template': collapse}

    payload = {
        'meta': {
            'script': 'tools/a1_h_templates.py',
            'purpose': 'item 3 -- prompt-template sensitivity of the freezing/surgery protocol',
            'script_sha1_self': file_sha1('tools/a1_h_templates.py'),
            'model': MODEL_ID,
            'templates': TEMPLATES,
            'default_template': DEFAULT_TEMPLATE,
            'benchmarks': list(bench.keys()),
            'class_list_len': {b: len(bench[b]['class_names']) for b in bench},
            'class_list_source': {'imagenet5k': 'data/imagenet_hf parquet label names (legacy1001)',
                                  'dtd': 'torchvision DTD test classes',
                                  'food101': 'torchvision Food101 test classes'},
            'placeholder_class_index': PLACEHOLDER_IDX,
            'shard_signature': shard_sig,
            'n_imagenet_images': N_IMNET,
            'lambdas': LAMBDAS, 'topk_for_tau': TOPK,
            'tau_convention': 'tau on the frozen top-5 class set DERIVED PER TEMPLATE: the top-5 '
                              'indices come from that template\'s own frozen scores, so tau is '
                              'template-internal and only comparable within a template column',
            'gap_variants': {'coupled': 'gap estimated on Flickr30k rows 2000..3000 with this '
                                        'template\'s text tower',
                             'fixed_t0': 'gap estimated with the t0 template, evaluation template '
                                         'varies'},
            'sample_stream': 'np.random.RandomState(42) for the 5 000-image ImageNet sample',
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'runtime_s': None,
        },
        'results': results,
        'stability': stability,
    }
    payload['meta']['runtime_s'] = round(time.time() - t0, 1)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)

    print('\n== template stability (tau spread across the 5 templates) ==')
    for bname, s in stability.items():
        for gkey in ('coupled', 'fixed_t0'):
            for lam in LAMBDAS:
                k = '%s|lam%+.1f' % (gkey, lam)
                if k in s['spread_per_lambda']:
                    v = s['spread_per_lambda'][k]
                    print('  %-11s %-22s tau %.4f..%.4f (spread %.4f) | top1 %.2f..%.2f (spread %.2f)'
                          % (bname, k, v['tau_min'], v['tau_max'], v['tau_spread'],
                             v['top1_min'], v['top1_max'], v['top1_spread']))
    print('\nsaved', args.out, '(%.1fs)' % (time.time() - t0))


if __name__ == '__main__':
    main()
