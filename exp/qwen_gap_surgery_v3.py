"""A1 #1 v3: first-token logprob zero-shot + weight/representation-space surgery (cloud, not executed).

Diagnostic conclusions (qwen_v2_diag):
  - h_p (the last-layer hidden state of image + classification prompt) carries good information: the greedy next token gives
    reasonable words such as 'bird/dog/mount/mitt/en/...' for 8/8 images;
  - the continuation scoring of v2 has a structural bug (feeding the last-layer hidden state back into the LM as an input embedding → garbage logits).
v3 therefore switches to fully validated components:
  1. Zero-shot score = the **first-token logit** of h_p through lm_head:
        score_c = (h_p · w_{c}), w_c = the row of the lm_head weight matrix corresponding to the first token of class name c;
  2. the surgery is in h space / weight space and **preserves the asymmetric structure of A1**:
        image side  h_p' = norm(h_p + λ‖g‖ d̂)  → score_c = h_p'·w_c   (per-class bias field)
        text side  w_c'  = norm(w_c + λ‖g‖ d̂)  → score_c = h_p·w_c'   (per-image scaling, first-order zero reordering)
  3. τ: on the frozen top-5 class set, the Kendall coefficient between the frozen and perturbed score rankings (same definition as A1);
  4. CG and the gap direction follow the h-space text representation (text_h) and h_p.

Known limitations (honest disclosure): first-token scoring ignores the subsequent tokens of multi-token class names,
so classes sharing the first word such as "tiger cat/shark" tie — top-1 will be lower than under the full logprob protocol,
but this suffices to give a dose-response curve and the τ structure.

Usage (server):
  python qwen_gap_surgery_v3.py --model /autodl-fs/data/models/qwen2vl-2b --local-only \
      --parquet-dir /autodl-fs/data/imagenet_hf/data --sample 64 \
      --out /autodl-fs/data/a1_qwen_v3_smoke.json
  Full run: --sample 5000 (about 1–1.5 hours).
"""
import argparse
import glob
import json
import os

import numpy as np
import torch
import torch.nn.functional as F
from datasets import Dataset
from scipy import stats
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

PREFIX = 'What is shown in this image? Answer with the object name only.'


def norm(x):
    return F.normalize(x, dim=-1)


def get_lm(model):
    lm = getattr(model, 'language_model', None)
    if lm is not None:
        return lm
    m = model.model
    lm = getattr(m, 'language_model', None)
    return lm if lm is not None else m


def text_h(model, processor, texts, batch=16):
    """Text representation: last-layer hidden state of the LM's last token."""
    tok = processor.tokenizer
    lm = get_lm(model)
    outs = []
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            inp = tok(text=texts[i:i + batch], return_tensors='pt', padding=True).to(model.device)
            o = lm(input_ids=inp['input_ids'], attention_mask=inp['attention_mask'],
                   output_hidden_states=True)
            h = o.hidden_states[-1]
            last = h[torch.arange(h.shape[0], device=h.device),
                     inp['attention_mask'].sum(1) - 1]
            outs.append(last)
    return torch.cat(outs)


def img_h_p(model, processor, img):
    """Image representation: full forward pass over image + PREFIX, take the last-layer hidden state of the last real token."""
    if max(img.size) > 640:           # safety downscale: 640 cap, attention-safe (≤2116 patches)
        img = img.copy()
        img.thumbnail((640, 640))
    msgs = [{'role': 'user', 'content': [
        {'type': 'image'},
        {'type': 'text', 'text': PREFIX},
    ]}]
    prompt = processor.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
    inp = processor(images=img, text=prompt, return_tensors='pt').to(model.device)
    with torch.no_grad():
        o = model(**inp, output_hidden_states=True)
    h = o.hidden_states[-1]
    p = int(inp['attention_mask'].sum() - 1)
    return h[0, p]


def first_token_ids(tokenizer, names):
    ids = []
    for c in names:
        t = tokenizer(c, add_special_tokens=False).input_ids
        ids.append(t[0] if t else tokenizer.pad_token_id)
    return torch.tensor(ids)


def scores_from_h(h_p, W_first, vocab_logits=False):
    """score_c = h_p · w_c (raw logit, the ranking is the class ranking). W_first: [K, D]."""
    return (h_p[None, :] @ W_first.T)[0]          # [K]


def top1_tau(scores_np, labels, frozen_scores_np, topk5, n):
    top1 = (scores_np.argmax(1) == labels).mean() * 100
    taus = []
    for i in range(n):
        k5 = topk5[i]
        r1 = frozen_scores_np[i][k5]
        r2 = scores_np[i][k5]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    return float(top1), float(np.mean(taus))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='Qwen/Qwen2-VL-2B-Instruct')
    ap.add_argument('--local-only', action='store_true')
    ap.add_argument('--parquet-dir', default='data/imagenet_hf')
    ap.add_argument('--sample', type=int, default=5000)
    ap.add_argument('--lambdas', default='-2,-1,-0.5,0.25,0.5,1,2')
    ap.add_argument('--out', default='outputs/a1_qwen_surgery.json')
    args = ap.parse_args()

    parq = sorted(glob.glob(args.parquet_dir + '/*.parquet'))
    assert parq, 'no parquet shards'
    ds_in = Dataset.from_parquet(parq)
    names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
    rng = np.random.RandomState(42)
    idx = rng.choice(len(ds_in), args.sample, replace=False)
    sub = ds_in.select(list(idx))
    labels = np.array(sub['label'])
    imgs = list(sub['image'])

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        args.model, torch_dtype=torch.bfloat16,
        local_files_only=args.local_only).eval().cuda()
    processor = AutoProcessor.from_pretrained(args.model, local_files_only=args.local_only)
    tok = processor.tokenizer

    ft_ids = first_token_ids(tok, names).to(model.device)      # [K]
    W = model.lm_head.weight.detach().float()                  # [V, D] (detached, float32 to ease perturbation)
    W_first = W[ft_ids]                                        # [K, D]

    t_h = norm(text_h(model, processor, names))                # [K, D]
    print('text_h done', tuple(t_h.shape), flush=True)

    hps, f_scores, skipped = [], [], []
    with torch.no_grad():
        for i, img in enumerate(imgs):
            try:
                hp = img_h_p(model, processor, img).float()
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                skipped.append(i)
                print('OOM skip image %d (total skipped %d)' % (i, len(skipped)), flush=True)
                hp = torch.zeros_like(hps[-1]) if hps else torch.zeros(1536, device=model.device)
            hps.append(hp)
            f_scores.append(scores_from_h(hp, W_first).cpu().numpy())
            if (i + 1) % 100 == 0:
                print('frozen pass %d/%d' % (i + 1, args.sample), flush=True)
    hps = torch.stack(hps)                                     # [N, D] float32
    hps = norm(hps)
    frozen_scores = np.stack(f_scores)                         # [N, K]

    g = t_h.mean(0) - hps.mean(0)
    gap_norm = g.norm().item()
    d_hat = g / gap_norm

    topk5 = np.argsort(-frozen_scores, axis=1)[:, :5]
    frozen_top1 = (frozen_scores.argmax(1) == labels).mean() * 100

    results = []
    for lam in [float(x) for x in args.lambdas.split(',')]:
        rec = {'lambda': lam}
        # image side: shift h_p (per-class bias field)
        hp_s = norm(hps + lam * gap_norm * d_hat)
        sc_i = np.stack([scores_from_h(hp_s[i], W_first).cpu().numpy()
                         for i in range(args.sample)])
        t1_i, tau_i = top1_tau(sc_i, labels, frozen_scores, topk5, args.sample)
        cg_i = (t_h.mean(0) - hp_s.mean(0)).norm().item()
        rec['image_side'] = {'top1': t1_i, 'tau': tau_i, 'CG': cg_i}
        # text side: shift the weight row of the first class token (no normalization: unembedding has no unit-norm constraint
        # ⟹ exact first-order zero reordering; the slight degradation of the CLIP text side comes precisely from its normalization — see the analysis)
        W_t = W_first + lam * gap_norm * d_hat[None, :]
        sc_t = np.stack([scores_from_h(hps[i], W_t).cpu().numpy()
                         for i in range(args.sample)])
        t1_t, tau_t = top1_tau(sc_t, labels, frozen_scores, topk5, args.sample)
        cg_t = (norm(t_h + lam * gap_norm * d_hat[None, :]).mean(0) - hps.mean(0)).norm().item()
        rec['text_side'] = {'top1': t1_t, 'tau': tau_t, 'CG': cg_t}
        results.append(rec)
        print('λ=%s: img top1=%.2f τ=%.3f | txt top1=%.2f τ=%.3f' %
              (lam, t1_i, tau_i, t1_t, tau_t), flush=True)

    out = {'model': args.model, 'n_images': args.sample,
           'skipped_images': skipped,
           'frozen': {'top1': float(frozen_top1), 'CG': float(gap_norm)},
           'gap_norm': gap_norm, 'results': results,
           'protocol': 'first-token logprob; h-space image surgery / unembedding-row text surgery'}
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print('saved', args.out, '| frozen top1=%.2f CG=%.4f' % (frozen_top1, gap_norm))


if __name__ == '__main__':
    main()
