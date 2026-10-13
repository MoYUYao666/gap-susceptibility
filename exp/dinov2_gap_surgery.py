"""A1 #7: DINOv2 negative control — gap surgery for a non-contrastive vision model (cloud script, not executed).

Question: is the “signature” of τ dose-response + non-monotonic CG specific to CLIP contrastive training, or generic to classification geometry?
Protocol (DINOv2 has no text tower, so we do a vision-only adaptation):
  - class representation = class centroid prototypes (mean over 5k samples by true labels, L2-normalized; self-referential but consistent across λ);
  - frozen score s_c = x_i · c_c (nearest-centroid classification), top-5 set and τ definition as in A1;
  - surgery: x' = norm(x + λ‖g‖ d̂), d̂ = normalize(mean(prototypes) − mean(images)) (the “prototype-image gap” direction),
    plus an orthogonal direction and a random direction as two controls;
  - metrics: τ(λ), top1(λ) (nearest-centroid), CG(λ) = ‖mean(prototypes) − mean(x')‖.
Decision:
  - if monotonic τ collapse + non-monotonic CG + direction dependence all appear → the signature is unrelated to contrastive training (strengthens the generality of A1);
  - if not → the signature is specific to CLIP-like models (delimits the boundary of the A1 claim). Both outcomes are valuable.

⚠️ Model weight rule (CLAUDE.md): download on the server; local download-then-upload is forbidden.
  HF mirror: HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_XET=1 python -c "from huggingface_hub import snapshot_download; snapshot_download('facebook/dinov2-base', local_dir='/autodl-fs/data/models/dinov2-base')"
  ModelScope: python -c "from modelscope import snapshot_download; snapshot_download('tiansz/dinov2-base', local_dir='/autodl-fs/data/models/dinov2-base')"  # or the corresponding official mirror name

Usage (on the server):
  python dinov2_gap_surgery.py --model /autodl-fs/data/models/dinov2-base --local-only \
      --parquet-dir /autodl-fs/data/imagenet_hf/data --sample 5000 \
      --out /autodl-fs/data/a1_dinov2_surgery.json
Estimated: dinov2-base on a 4080, 5000 images × 10 λ ≈ 15–25 minutes.
"""
import argparse
import glob
import json
import os

import numpy as np
import torch
import torch.nn.functional as F
from datasets import Dataset as HFDataset
from scipy import stats
from transformers import AutoModel, AutoImageProcessor

LAMBDAS = [-2, -1, -0.5, 0.25, 0.5, 1, 2, 4]


def norm(x):
    return F.normalize(x, dim=-1)


def encode(model, processor, images, batch=32):
    outs = []
    with torch.no_grad():
        for i in range(0, len(images), batch):
            inp = processor(images=images[i:i + batch], return_tensors='pt').to(model.device)
            o = model(**inp)
            h = o.last_hidden_state if hasattr(o, 'last_hidden_state') else o[0]
            outs.append(norm(h[:, 0]))          # [CLS] token
    return torch.cat(outs)


def tau_top1(scores_np, labels, frozen_scores_np, topk5, n):
    top1 = (scores_np.argmax(1) == labels).mean() * 100
    taus = []
    for i in range(n):
        k5 = topk5[i]
        r1, r2 = frozen_scores_np[i][k5], scores_np[i][k5]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    return float(top1), float(np.mean(taus))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='facebook/dinov2-base')
    ap.add_argument('--local-only', action='store_true')
    ap.add_argument('--parquet-dir', default='data/imagenet_hf')
    ap.add_argument('--sample', type=int, default=5000)
    ap.add_argument('--out', default='outputs/a1_dinov2_surgery.json')
    args = ap.parse_args()

    parq = sorted(glob.glob(args.parquet_dir + '/*.parquet'))
    assert parq, 'no parquet shards'
    ds_in = HFDataset.from_parquet(parq)
    rng = np.random.RandomState(42)
    idx = rng.choice(len(ds_in), args.sample, replace=False)
    sub = ds_in.select(list(idx))
    labels = np.array(sub['label'])
    imgs = list(sub['image'])

    model = AutoModel.from_pretrained(args.model, local_files_only=args.local_only).eval().cuda()
    processor = AutoImageProcessor.from_pretrained(args.model, local_files_only=args.local_only)

    x = encode(model, processor, imgs)                       # [N, D] normalized
    cls_ids = sorted(set(labels.tolist()))
    protos = torch.stack([x[labels == c].mean(0) for c in cls_ids])
    protos = norm(protos)                                    # [K, D]

    g = protos.mean(0) - x.mean(0)
    gap_norm = g.norm().item()
    d_hat = g / gap_norm

    S0 = (x @ protos.T).float().cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    frozen_top1 = (S0.argmax(1) == labels).mean() * 100

    # orthogonal and random control directions
    D = x.shape[1]
    rng2 = np.random.RandomState(7)
    r_vec = torch.tensor(rng2.randn(D), dtype=torch.float32, device=x.device)
    r_vec = r_vec - (r_vec @ d_hat) * d_hat
    r_vec = r_vec / r_vec.norm()

    results = []
    for lam in LAMBDAS:
        rec = {'lambda': lam}
        for name, direction in [('gap', d_hat), ('orthogonal', r_vec)]:
            xs = norm(x + lam * gap_norm * direction)
            S = (xs @ protos.T).float().cpu().numpy()
            t1, tau = tau_top1(S, labels, S0, topk5, args.sample)
            cg = (protos.mean(0) - xs.mean(0)).norm().item()
            rec[name] = {'top1': t1, 'tau': tau, 'CG': cg}
        results.append(rec)
        print('λ=%s: gap top1=%.2f τ=%.3f CG=%.3f | orth top1=%.2f τ=%.3f' %
              (lam, rec['gap']['top1'], rec['gap']['tau'], rec['gap']['CG'],
               rec['orthogonal']['top1'], rec['orthogonal']['tau']), flush=True)

    out = {'model': args.model, 'n_images': args.sample,
           'frozen': {'top1': float(frozen_top1), 'CG': float(gap_norm)},
           'gap_norm': gap_norm, 'results': results,
           'protocol': 'vision-only; class prototypes as reference; [CLS] embeddings'}
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print('saved', args.out, '| frozen top1=%.2f CG=%.4f' % (frozen_top1, gap_norm))


if __name__ == '__main__':
    main()
