"""A1 #1 v2：解码器 VLM 的 logprob 零样本 + 隐藏态空间 gap surgery（云端，未执行）。

协议（修复 v1 的 ~3% 地板）：
  1. 图像表示 h_p：完整多模态前向（图 + "a photo of a" 前缀，processor 图像+文本
     同传，绕开 4.48 单模态 bug），取前缀最后一个真实 token 的末层 hidden state；
  2. 文本表示 t_h：语言模型纯文本前向，末 token 末层 hidden state；
  3. 鸿沟方向 d̂ = normalize(mean(t_h) − mean(h_p))，‖g‖ = 其模长；
  4. 零样本得分：logprob 协议——用 h_p 接续类别名 token（批量 1000），
     score_c = Σ 类别 token 位置的 log-softmax 对数概率；
  5. 手术（隐藏态空间，与 A1 偏置场同构）：
       图像侧  h_p' = norm(h_p + λ‖g‖ d̂) → 重算 score → top1/τ
       文本侧  类别 token 嵌入 += λ‖g‖ d̂ → 重算 score → top1/τ
  6. τ：冻结 top-5 类集上，冻结 vs 扰动 logprob 排序的 Kendall 系数（与 A1 同定义）。

已知注意事项（4.48.3）：
  - Qwen2VLProcessor 单模态输入有 bug → 文本用 tokenizer、图像用 image_processor、
    多模态（图+文同传）用 processor；
  - model.visual 需要 grid_thw，返回纯 Tensor；
  - 语言模型在 4.48 为 model.model（Qwen2VLModel），get_lm 兼容新旧。

用法（服务器）：
  python qwen_gap_surgery_v2.py --model /autodl-fs/data/models/qwen2vl-2b --local-only \
      --parquet-dir /autodl-fs/data/imagenet_hf/data --sample 64 \
      --out /autodl-fs/data/a1_qwen_v2_smoke.json
  正式：--sample 5000（预计 3–5 小时，4080）。
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
    """图像表示：图 + PREFIX 完整前向，取末真实 token 的末层 hidden。

    必须 add_generation_prompt=True：否则用户回合以 <|im_end|> 结尾，
    下一 token 是 <|im_start|>assistant 而非类别名，评分退化为噪声。
    """
    msgs = [{'role': 'user', 'content': [
        {'type': 'image'},
        {'type': 'text', 'text': PREFIX},
    ]}]
    prompt = processor.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
    inp = processor(images=img, text=prompt, return_tensors='pt').to(model.device)
    with torch.no_grad():
        o = model(**inp, output_hidden_states=True)
    h = o.hidden_states[-1]                                   # [1, L, D]
    p = int(inp['attention_mask'].sum() - 1)
    return h[0, p]                                            # [D]


def score_classes(model, processor, h_p, class_texts, text_shift=None):
    """h_p 接续类别名 token 的 logprob 得分 [K]。

    text_shift: 若非 None，则类别 token 嵌入加该偏移（文本侧手术，[D]）。
    """
    tok = processor.tokenizer
    lm = get_lm(model)
    K = len(class_texts)
    inp = tok(text=class_texts, return_tensors='pt', padding=True)
    ids = inp['input_ids'].to(model.device)                   # [K, L2]
    mask = inp['attention_mask'].to(model.device)
    emb = lm.get_input_embeddings()(ids)                      # [K, L2, D]
    if text_shift is not None:
        emb = emb + text_shift[None, None, :]
    hp = h_p[None, None, :].expand(K, 1, -1)                  # [K, 1, D]
    seq = torch.cat([hp, emb], dim=1)                         # [K, 1+L2, D]
    att = torch.cat([torch.ones(K, 1, device=ids.device, dtype=mask.dtype), mask], dim=1)
    with torch.no_grad():
        out = lm(inputs_embeds=seq, attention_mask=att)      # 基础模型：无 logits
        logits = model.lm_head(out.last_hidden_state)        # 分类头在顶层模型上
    lsm = torch.log_softmax(logits.float(), dim=-1)           # [K, 1+L2, V]
    scores = torch.zeros(K, device=ids.device)
    for t in range(ids.shape[1]):
        pos = mask[:, t].bool()                               # token t 真实存在
        if not pos.any():
            continue
        # token t 的概率来自 logits 位置 t（位置 0 的 logits 预测 token 0）
        scores[pos] += lsm[pos, t, ids[pos, t]]
    return scores


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

    # 文本表示 + 鸿沟方向（文本侧取"答案词"格式的类别名嵌入，与评分一致）
    t_h = norm(text_h(model, processor, names))
    print('text_h done', tuple(t_h.shape), flush=True)

    hps, f_scores = [], []
    for i, img in enumerate(imgs):
        hp = img_h_p(model, processor, img)
        hps.append(hp)
        f_scores.append(score_classes(model, processor, hp, names).cpu().numpy())
        if (i + 1) % 50 == 0:
            print('frozen pass %d/%d' % (i + 1, args.sample), flush=True)
    hps = torch.stack(hps)                                    # [N, D]
    hps = norm(hps)
    frozen_scores = np.stack(f_scores)                        # [N, K]

    g = t_h.mean(0) - hps.mean(0)
    gap_norm = g.norm().item()
    d_hat = g / gap_norm

    topk5 = np.argsort(-frozen_scores, axis=1)[:, :5]
    frozen_top1 = (frozen_scores.argmax(1) == labels).mean() * 100

    results = []
    for lam in [float(x) for x in args.lambdas.split(',')]:
        rec = {'lambda': lam}
        # 图像侧手术：h_p 平移后重算得分
        hp_s = norm(hps + lam * gap_norm * d_hat)
        sc_i = np.stack([score_classes(model, processor, hp_s[i], names).cpu().numpy()
                         for i in range(args.sample)])
        t1_i, tau_i = top1_tau(sc_i, labels, frozen_scores, topk5, args.sample)
        cg_i = (t_h.mean(0) - hp_s.mean(0)).norm().item()
        rec['image_side'] = {'top1': t1_i, 'tau': tau_i, 'CG': cg_i}
        # 文本侧手术：类别 token 嵌入平移
        shift = lam * gap_norm * d_hat
        sc_t = np.stack([score_classes(model, processor, hps[i], names, text_shift=shift)
                         .cpu().numpy() for i in range(args.sample)])
        t1_t, tau_t = top1_tau(sc_t, labels, frozen_scores, topk5, args.sample)
        cg_t = (norm(t_h + shift[None, :]).mean(0) - hps.mean(0)).norm().item()
        rec['text_side'] = {'top1': t1_t, 'tau': tau_t, 'CG': cg_t}
        results.append(rec)
        print('λ=%s: img top1=%.2f τ=%.3f | txt top1=%.2f τ=%.3f' %
              (lam, t1_i, tau_i, t1_t, tau_t), flush=True)

    out = {'model': args.model, 'n_images': args.sample,
           'frozen': {'top1': float(frozen_top1), 'CG': float(gap_norm)},
           'gap_norm': gap_norm, 'results': results}
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print('saved', args.out, '| frozen top1=%.2f CG=%.4f' % (frozen_top1, gap_norm))


if __name__ == '__main__':
    main()
