"""A1 #7：DINOv2 阴性对照——非对比式视觉模型的 gap surgery（云端脚本，未执行）。

问题：τ 剂量-响应 + CG 非单调这个"签名"是 CLIP 对比式训练特有，还是分类几何通用？
协议（DINOv2 无文本塔，做 vision-only 适配）：
  - 类表示 = 类质心原型（5k 样本上按真实标签求 mean，L2 归一化；自参照但 λ 间一致）；
  - 冻结分数 s_c = x_i · c_c（近质心分类），top-5 集与 τ 定义同 A1；
  - 手术：x' = norm(x + λ‖g‖ d̂)，d̂ = normalize(mean(原型) − mean(图像))（"原型-图像鸿沟"方向），
    另加正交方向与随机方向两个对照；
  - 指标：τ(λ)、top1(λ)（近质心）、CG(λ) = ‖mean(原型) − mean(x')‖。
判定：
  - 若 τ 单调崩塌 + CG 非单调 + 方向依赖都出现 → 签名与对比式训练无关（强化 A1 普适性）；
  - 若不存在 → 签名是 CLIP 类模型特有（划定 A1 主张边界）。两种结果都有价值。

⚠️ 模型权重规则（CLAUDE.md）：在服务器下载，禁止本地下载上传。
  HF 镜像：HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_XET=1 python -c "from huggingface_hub import snapshot_download; snapshot_download('facebook/dinov2-base', local_dir='/autodl-fs/data/models/dinov2-base')"
  ModelScope：python -c "from modelscope import snapshot_download; snapshot_download('tiansz/dinov2-base', local_dir='/autodl-fs/data/models/dinov2-base')"  # 或对应官方镜像名

用法（服务器）：
  python dinov2_gap_surgery.py --model /autodl-fs/data/models/dinov2-base --local-only \
      --parquet-dir /autodl-fs/data/imagenet_hf/data --sample 5000 \
      --out /autodl-fs/data/a1_dinov2_surgery.json
预计：dinov2-base 在 4080 上 5000 张 × 10 λ ≈ 15–25 分钟。
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

    x = encode(model, processor, imgs)                       # [N, D] 归一化
    cls_ids = sorted(set(labels.tolist()))
    protos = torch.stack([x[labels == c].mean(0) for c in cls_ids])
    protos = norm(protos)                                    # [K, D]

    g = protos.mean(0) - x.mean(0)
    gap_norm = g.norm().item()
    d_hat = g / gap_norm

    S0 = (x @ protos.T).float().cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    frozen_top1 = (S0.argmax(1) == labels).mean() * 100

    # 正交与随机对照方向
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
