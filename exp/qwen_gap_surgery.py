"""A1 #1: generalization of gap surgery to a decoder-style VLM (Qwen2-VL) — cloud script, not executed yet.

Does the core A1 signature still hold on a decoder VLM:
  - the collapse curves of top-1 and τ under gap-direction shift surgery (image side / text side);
  - image side vs text side asymmetry (the prediction of bias-field theory: the image side is more fatal);
  - the non-monotonic behavior of CG as a function of λ.
Embedding conventions (a decoder VLM has no CLIP-style dual tower, so define them as follows):
  - image embedding: model.visual(pixel_values) outputs [B, T, D], mean-pool over T then L2-normalize;
  - text embedding: pure-text forward pass (no image), take the last-token hidden_state, L2-normalize;
  - gap: g = mean(class text embeddings) − mean(image embeddings), estimated on 5k ImageNet samples.

⚠️ Model weight rule (CLAUDE.md): always download on the server; uploading after a local download is forbidden.
  Server download (pick one):
    HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_XET=1 python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2-VL-2B-Instruct', local_dir='/root/models/qwen2vl-2b')"
    python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen2-VL-2B-Instruct', local_dir='/root/models/qwen2vl-2b')"

Usage (server):
  python exp/qwen_gap_surgery.py --model /root/models/qwen2vl-2b \
      --parquet-dir data/imagenet_hf --sample 5000 --out outputs/a1_qwen_surgery.json
VRAM: 2B bf16 ≈ 8–10 GB (runs on a single GPU); 7B needs ~24 GB.
Runtime reference: 5k images × (1 frozen + 8λ×2 sides) ≈ 17 forward passes, about 20–40 minutes on an A100.
"""
import argparse
import glob
import json

import numpy as np
import torch
import torch.nn.functional as F
from datasets import Dataset
from scipy import stats
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration


def norm(x):
    return F.normalize(x, dim=-1)


def get_lm(model):
    lm = getattr(model, 'language_model', None)
    if lm is not None:
        return lm
    m = model.model
    lm = getattr(m, 'language_model', None)
    return lm if lm is not None else m   # 4.48: model.model is the language model


def text_embeddings(model, processor, texts, batch=16):
    """Pure-text forward pass (through the language model), last-token hidden state as the text embedding."""
    tok = processor.tokenizer
    lm = get_lm(model)
    outs = []
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            chunk = texts[i:i + batch]
            inp = tok(text=chunk, return_tensors='pt', padding=True).to(model.device)
            o = lm(input_ids=inp['input_ids'],
                   attention_mask=inp['attention_mask'],
                   output_hidden_states=True)
            h = o.hidden_states[-1]                    # [B, L, D]
            last = h[torch.arange(h.shape[0], device=h.device),
                     inp['attention_mask'].sum(1) - 1]
            outs.append(last)
    return torch.cat(outs)


def image_embeddings(model, processor, images):
    """Feed the vision tokens (already through the merger) to the language model, then mean-pool the last-layer hidden state.
    Both embeddings then live in the same LM space, so the zero-shot similarity is meaningful."""
    ip = processor.image_processor
    lm = get_lm(model)
    outs = []
    with torch.no_grad():
        for img in images:
            out = ip(images=img, return_tensors='pt')
            px = out.pixel_values.to(model.device)
            grid = out.image_grid_thw.to(model.device)
            v = model.visual(px, grid_thw=grid)        # [T, D] (already through the merger)
            if hasattr(v, 'last_hidden_state'):
                v = v.last_hidden_state
            elif isinstance(v, tuple):
                v = v[0]
            v = v if v.dim() == 3 else v.unsqueeze(0)  # [1, T, D]
            o = lm(inputs_embeds=v, output_hidden_states=True)
            outs.append(o.hidden_states[-1].mean(dim=1))
    return torch.cat(outs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='Qwen/Qwen2-VL-2B-Instruct')
    ap.add_argument('--local-only', action='store_true',
                    help='read the local cache offline (for servers without network / to avoid HF access)')
    ap.add_argument('--parquet-dir', default='data/imagenet_hf')
    ap.add_argument('--sample', type=int, default=5000)
    ap.add_argument('--lambdas', default='-2,-1,-0.5,0,0.25,0.5,1,2')
    ap.add_argument('--out', default='outputs/a1_qwen_surgery.json')
    args = ap.parse_args()

    parq = sorted(glob.glob(args.parquet_dir + '/*.parquet'))
    assert parq, 'no parquet shards'
    ds_in = Dataset.from_parquet(parq)
    names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
    texts = ['a photo of a %s' % c.replace('_', ' ') for c in names]
    rng = np.random.RandomState(42)
    idx = rng.choice(len(ds_in), args.sample, replace=False)
    sub = ds_in.select(list(idx))
    labels = np.array(sub['label'])
    imgs = list(sub['image'])

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        args.model, torch_dtype=torch.bfloat16,
        local_files_only=args.local_only).eval().cuda()
    processor = AutoProcessor.from_pretrained(args.model, local_files_only=args.local_only)

    with torch.no_grad():
        tf = norm(text_embeddings(model, processor, texts))          # [K, D]
        imf = norm(image_embeddings(model, processor, imgs))         # [N, D]

    g = tf.mean(0) - imf.mean(0)
    gap_norm = g.norm().item()
    d_hat = g / gap_norm

    base_sims = (imf @ tf.T).float().cpu().numpy()
    topk5 = np.argsort(-base_sims, axis=1)[:, :5]
    frozen_top1 = (base_sims.argmax(1) == labels).mean() * 100

    results = []
    for lam in [float(x) for x in args.lambdas.split(',')]:
        rec = {'lambda': lam}
        # image-side shift
        simg = norm(imf + lam * gap_norm * d_hat)
        si = (simg @ tf.T).float().cpu().numpy()
        taus_i = []
        for i in range(args.sample):
            r1 = base_sims[i][topk5[i]]
            r2 = si[i][topk5[i]]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus_i.append(t)
        rec['image_side'] = {'top1': float((si.argmax(1) == labels).mean() * 100),
                             'tau': float(np.mean(taus_i)),
                             'CG': float((tf.mean(0) - simg.mean(0)).norm().item())}
        # text-side shift
        stf = norm(tf + lam * gap_norm * d_hat)
        st = (imf @ stf.T).float().cpu().numpy()
        taus_t = []
        for i in range(args.sample):
            r1 = base_sims[i][topk5[i]]
            r2 = st[i][topk5[i]]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus_t.append(t)
        rec['text_side'] = {'top1': float((st.argmax(1) == labels).mean() * 100),
                            'tau': float(np.mean(taus_t)),
                            'CG': float((stf.mean(0) - imf.mean(0)).norm().item())}
        results.append(rec)
        print('λ=%s: img top1=%.2f τ=%.3f | txt top1=%.2f τ=%.3f' %
              (lam, rec['image_side']['top1'], rec['image_side']['tau'],
               rec['text_side']['top1'], rec['text_side']['tau']), flush=True)

    out = {'model': args.model, 'n_images': args.sample,
           'frozen': {'top1': float(frozen_top1), 'CG': float(g.norm().item())},
           'gap_norm': gap_norm, 'results': results}
    import os as _os
    _os.makedirs(_os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print('saved', args.out, '| frozen top1=%.2f CG=%.4f' % (frozen_top1, gap_norm))


if __name__ == '__main__':
    main()
