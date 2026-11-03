"""A1 #1 v3：首 token logprob 零样本 + 权重/表示空间手术（云端，未执行）。

诊断结论（qwen_v2_diag）：
  - h_p（图+分类提示的末层隐藏态）的信息量很好：贪婪下一 token 对 8/8 张图给出
    'bird/dog/mount/mitt/en/...' 等合理词；
  - v2 的续写评分有结构性 bug（把末层隐藏态当输入嵌入重进 LM → 垃圾 logits）。
v3 因此改用全部已验证的组件：
  1. 零样本得分 = h_p 经 lm_head 的**首 token logit**：
        score_c = (h_p · w_{c})，w_c = lm_head 权重矩阵中类别名首 token 对应行；
  2. 手术在 h 空间 / 权重空间，且**保持 A1 的非对称结构**：
        图像侧  h_p' = norm(h_p + λ‖g‖ d̂)  → score_c = h_p'·w_c   （逐类偏置场）
        文本侧  w_c'  = norm(w_c + λ‖g‖ d̂)  → score_c = h_p·w_c'   （逐图像缩放，一阶零重排）
  3. τ：冻结 top-5 类集上冻结 vs 扰动 score 排序的 Kendall 系数（与 A1 同定义）；
  4. CG 与鸿沟方向沿用 h 空间文本表示（text_h）与 h_p。

已知限制（诚实披露）：首 token 评分忽略多 token 类别名的后续 token，
"tiger cat/shark" 这类同首词类别会并列——top-1 会低于完整 logprob 协议，
但足够给出剂量-响应曲线与 τ 结构。

用法（服务器）：
  python qwen_gap_surgery_v3.py --model /autodl-fs/data/models/qwen2vl-2b --local-only \
      --parquet-dir /autodl-fs/data/imagenet_hf/data --sample 64 \
      --out /autodl-fs/data/a1_qwen_v3_smoke.json
  正式：--sample 5000（约 1–1.5 小时）。
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
    """文本表示：LM 末 token 末层 hidden。"""
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
    """图像表示：图 + PREFIX 完整前向，取末真实 token 的末层 hidden。"""
    if max(img.size) > 640:           # 保险缩图：640 上限，注意力安全（≤2116 分片）
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
    """score_c = h_p · w_c（原始 logit，排序即类别排序）。W_first: [K, D]。"""
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
    W = model.lm_head.weight.detach().float()                  # [V, D]（去梯度，float32 便于扰动）
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
        # 图像侧：平移 h_p（逐类偏置场）
        hp_s = norm(hps + lam * gap_norm * d_hat)
        sc_i = np.stack([scores_from_h(hp_s[i], W_first).cpu().numpy()
                         for i in range(args.sample)])
        t1_i, tau_i = top1_tau(sc_i, labels, frozen_scores, topk5, args.sample)
        cg_i = (t_h.mean(0) - hp_s.mean(0)).norm().item()
        rec['image_side'] = {'top1': t1_i, 'tau': tau_i, 'CG': cg_i}
        # 文本侧：平移类别首 token 的权重行（不归一化：unembedding 无单位范数约束
        # ⟹ 一阶精确零重排；CLIP 的文本侧轻微退化正来自其归一化——见分析）
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
