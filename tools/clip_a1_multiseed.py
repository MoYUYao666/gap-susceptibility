"""A1 #8：关键数字多 seed 区间（防御性实验）。

对论文中的"headline"统计量做 N seed 复算，输出 均值±std：
  - 26 条件网格的四个 Spearman（τ 0.926 / CG −0.082 / CKA 0.755 / mean_cos 0.872）
  - 类偏置场验证 Pearson（r=1.000）与 std(m_c)
  - 各条件 top1 / τ 的跨 seed 均值±std（T/O/C/G/L/P 全部 26 个条件）
随机性两个来源都覆盖：
  (a) 扰动随机性：每个 seed 用 RandomState(seed) 重新抽噪声/正交方向/低秩子空间；
  (b) 采样随机性：每个 seed 用 RandomState(100000+seed) 重抽 5k 图像子集。

用法（Windows，conda env pytorch）：
  conda run -n pytorch python tools/clip_a1_multiseed.py --seeds 5 --sample 5000
预计时长：26 条件 × 5 seeds ≈ 130 次 5k 评测，RTX 4060 约 3–5 小时（夜跑）。
输出：outputs/a1_multiseed.json（per-seed 明细 + aggregate 均值/std）。

注意：本脚本只复算 5k 样本口径的统计量；50k 全量 headline 数字（59.28 等）
协议固定、不需 seed，只在 revision 回复里与 5k 区间并陈即可。
"""
import os
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')   # Windows + torch 必须
import argparse
import glob
import json
import sys
import pathlib

import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
from transformers import CLIPModel, CLIPProcessor
from datasets import Dataset
from torch.utils.data import DataLoader

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from src.dataset import Flickr30kDataset, _collate_fn   # noqa: E402

TEMPLATE = 'a photo of a {}'
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'


def linear_cka(X, Y):
    XX = X @ X.T
    YY = Y @ Y.T
    XY = X @ Y.T
    denom = (torch.trace(XX @ XX).item() * torch.trace(YY @ YY).item()) ** 0.5
    return (torch.trace(XY @ XY).item() / denom) if denom > 0 else 0.0


def build_base(model, processor, parq, sample_seed, n_images):
    """5k 子集 + Flickr30k 验证子集 + 冻结基线的全部公共量。"""
    ds_in = Dataset.from_parquet(parq)
    names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
    texts = [TEMPLATE.format(c.replace('_', ' ')) for c in names]
    rng = np.random.RandomState(sample_seed)
    idx = rng.choice(len(ds_in), n_images, replace=False)
    sub = ds_in.select(list(idx))
    labels = torch.tensor(sub['label'])

    ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
    val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
    loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0,
                        collate_fn=_collate_fn)

    with torch.no_grad():
        ti = processor(text=texts, return_tensors='pt', padding=True).to(DEVICE)
        tout = model.text_model(**ti)
        pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
        tf = F.normalize(model.text_projection(pooled), dim=-1)
        imgs = []
        for i in range(0, len(sub), 64):
            b = sub[i:i + 64]
            inp = processor(images=b['image'], return_tensors='pt').to(DEVICE)
            vout = model.vision_model(**inp)
            vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            imgs.append(F.normalize(model.visual_projection(vpooled), dim=-1))
        base = torch.cat(imgs)
        fi, ft = [], []
        for batch in loader:
            out = model(pixel_values=batch['image'].to(DEVICE),
                        input_ids=batch['input_ids'].to(DEVICE),
                        attention_mask=batch['attention_mask'].to(DEVICE),
                        return_loss=False)
            fi.append(F.normalize(out.image_embeds, dim=-1))
            ft.append(F.normalize(out.text_embeds, dim=-1))
        fi = torch.cat(fi)
        ft = torch.cat(ft)

    gap_vec = ft.mean(0) - fi.mean(0)
    gap_norm = gap_vec.norm().item()
    d_hat = gap_vec / gap_norm
    base_sims = base @ tf.T
    base_np = base_sims.cpu().numpy()
    topk5 = np.argsort(-base_np, axis=1)[:, :5]
    cls_ids = torch.tensor(sorted(set(labels.tolist())))
    cents = torch.stack([base[labels == c].mean(0) for c in cls_ids])
    cents = F.normalize(cents, dim=-1)
    lab_map = {int(c): i for i, c in enumerate(cls_ids)}
    return dict(base=base, fi=fi, ft=ft, tf=tf, labels=labels, names=names,
                base_np=base_np, topk5=topk5, cents=cents, lab_map=lab_map,
                gap_norm=gap_norm, d_hat=d_hat, n=n_images)


def evaluate(ctx, img2, fi2):
    base, tf, ft, labels, base_np, topk5, n = (ctx['base'], ctx['tf'], ctx['ft'],
                                               ctx['labels'], ctx['base_np'],
                                               ctx['topk5'], ctx['n'])
    S = img2 @ tf.T
    top1 = (S.argmax(1).cpu() == labels).float().mean().item() * 100
    s_np = S.cpu().numpy()
    taus = []
    for i in range(n):
        r1v = base_np[i][topk5[i]]
        r2v = s_np[i][topk5[i]]
        if np.std(r1v) < 1e-12 or np.std(r2v) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1v, r2v)
        if np.isfinite(t):
            taus.append(t)
    tau = float(np.mean(taus))
    cg = (fi2.mean(0) - ft.mean(0)).norm().item()
    cka = linear_cka(base, img2)
    mean_cos = (base * img2).sum(1).mean().item()
    return dict(top1=top1, tau=tau, CG=cg, cka=cka, mean_cos=mean_cos)


def run_seed(model, processor, parq, seed, n_images):
    """单 seed：重抽样本 + 重抽扰动，跑 26 条件，返回该 seed 的全部统计量。"""
    s_seed = 100000 + seed
    ctx = build_base(model, processor, parq, s_seed, n_images)
    base, fi, d_hat, gap_norm, cents, lab_map, labels = (ctx['base'], ctx['fi'],
                                                         ctx['d_hat'], ctx['gap_norm'],
                                                         ctx['cents'], ctx['lab_map'],
                                                         ctx['labels'])
    D = base.shape[1]
    rng2 = np.random.RandomState(seed)          # 扰动随机性：每 seed 独立
    Q, _ = torch.linalg.qr(torch.tensor(rng2.randn(D, D), dtype=torch.float32, device=DEVICE))

    conds = []

    def push(name, img2, fi2):
        conds.append({'name': name, **evaluate(ctx, img2, fi2)})
        print('  [seed %d] %s: top1=%.2f tau=%.3f CG=%.3f' %
              (seed, name, conds[-1]['top1'], conds[-1]['tau'], conds[-1]['CG']), flush=True)

    with torch.no_grad():
        push('base', base, fi)
        r_hat = torch.tensor(rng2.randn(D), dtype=torch.float32, device=DEVICE)
        r_hat = r_hat - (r_hat @ d_hat) * d_hat
        r_hat = r_hat / r_hat.norm()
        for lam in [-1, -0.5, 0.25, 0.5, 1, 2, 4]:
            push('T%.2g' % lam, F.normalize(base + lam * gap_norm * d_hat, dim=-1),
                 F.normalize(fi + lam * gap_norm * d_hat, dim=-1))
            if lam > 0:
                push('O%.2g' % lam, F.normalize(base + lam * gap_norm * r_hat, dim=-1),
                     F.normalize(fi + lam * gap_norm * r_hat, dim=-1))
        for a in [0.1, 0.25, 0.5]:
            push('C%.2g' % a, F.normalize((1 - a) * base + a * fi.mean(0), dim=-1),
                 F.normalize((1 - a) * fi + a * fi.mean(0), dim=-1))
        for sig in [0.25, 0.5, 1, 2]:
            noise = torch.tensor(rng2.randn(ctx['n'], D), dtype=torch.float32, device=DEVICE)
            noise = noise / noise.norm(dim=-1, keepdim=True)
            push('G%.2g' % sig, F.normalize(base + sig * gap_norm * noise, dim=-1), fi)
        for k in [1, 4, 16, 64]:
            Pk = Q[:, :k] @ Q[:, :k].T
            v = torch.tensor(rng2.randn(D), dtype=torch.float32, device=DEVICE)
            v = Pk @ v
            v = v / v.norm()
            push('L%d' % k, F.normalize(base + gap_norm * v, dim=-1), fi)
        for a in [0.25, 0.5]:
            c_own = cents[torch.tensor([lab_map[int(x)] for x in labels], device=DEVICE)]
            push('P%.2g' % a, F.normalize((1 - a) * base + a * c_own, dim=-1), fi)

    # 指标 vs top-1 的 Spearman（该 seed）
    top1s = [c['top1'] for c in conds]
    corrs = {}
    for metric in ['tau', 'CG', 'cka', 'mean_cos']:
        vals = [c[metric] for c in conds]
        r, p = stats.spearmanr(top1s, vals)
        corrs[metric] = {'spearman_r': float(r), 'p': float(p)}

    # 类偏置场验证（该 seed，λ=1）
    with torch.no_grad():
        shifted = F.normalize(base + gap_norm * d_hat, dim=-1)
    S1 = shifted @ ctx['tf'].T
    m_c = (d_hat @ ctx['tf'].T).cpu().numpy()
    actual = (S1 - ctx['base'] @ ctx['tf'].T).mean(0).cpu().numpy()
    pred = gap_norm * m_c
    r_bias, p_bias = stats.pearsonr(actual, pred)
    theory = {'pearson_r': float(r_bias), 'p': float(p_bias),
              'std_m_c': float(np.std(m_c)), 'gap_norm': float(gap_norm)}
    return {'seed': seed, 'sample_seed': s_seed, 'conditions': conds,
            'spearman': corrs, 'theory': theory}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--sample', type=int, default=5000)
    ap.add_argument('--out', default='outputs/a1_multiseed.json')
    ap.add_argument('--parquet-dir', default='data/imagenet_hf')
    args = ap.parse_args()

    parq = sorted(glob.glob(args.parquet_dir + '/*.parquet'))
    assert parq, 'no parquet shards under %s' % args.parquet_dir
    print('shards: %d | seeds: %d | sample: %d' % (len(parq), args.seeds, args.sample))

    model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32',
                                      local_files_only=True).to(DEVICE).eval()
    processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32',
                                              local_files_only=True)

    per_seed = [run_seed(model, processor, parq, s, args.sample)
                for s in range(args.seeds)]

    # 聚合
    agg = {'spearman': {}, 'theory': {}, 'conditions': {}}
    for metric in ['tau', 'CG', 'cka', 'mean_cos']:
        rs = [s['spearman'][metric]['spearman_r'] for s in per_seed]
        agg['spearman'][metric] = {'mean': float(np.mean(rs)), 'std': float(np.std(rs, ddof=1)),
                                   'min': float(np.min(rs)), 'max': float(np.max(rs))}
    agg['theory'] = {
        'pearson_r': {'mean': float(np.mean([s['theory']['pearson_r'] for s in per_seed])),
                      'std': float(np.std([s['theory']['pearson_r'] for s in per_seed], ddof=1))},
        'std_m_c': {'mean': float(np.mean([s['theory']['std_m_c'] for s in per_seed])),
                    'std': float(np.std([s['theory']['std_m_c'] for s in per_seed], ddof=1))},
    }
    names = [c['name'] for c in per_seed[0]['conditions']]
    for nm in names:
        t1 = np.array([next(c['top1'] for c in s['conditions'] if c['name'] == nm)
                       for s in per_seed])
        tau = np.array([next(c['tau'] for c in s['conditions'] if c['name'] == nm)
                        for s in per_seed])
        agg['conditions'][nm] = {'top1_mean': float(t1.mean()), 'top1_std': float(t1.std(ddof=1)),
                                 'tau_mean': float(tau.mean()), 'tau_std': float(tau.std(ddof=1))}

    out = {'n_seeds': args.seeds, 'n_images': args.sample,
           'per_seed': per_seed, 'aggregate': agg}
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print('saved', args.out)

    print('\n===== 论文值 vs %d-seed 均值±std =====' % args.seeds)
    print('tau    spearman: 论文 0.926  | %d-seed %.4f±%.4f' %
          (args.seeds, agg['spearman']['tau']['mean'], agg['spearman']['tau']['std']))
    print('CG     spearman: 论文 -0.082 | %d-seed %.4f±%.4f' %
          (args.seeds, agg['spearman']['CG']['mean'], agg['spearman']['CG']['std']))
    print('CKA    spearman: 论文 0.755  | %d-seed %.4f±%.4f' %
          (args.seeds, agg['spearman']['cka']['mean'], agg['spearman']['cka']['std']))
    print('cos    spearman: 论文 0.872  | %d-seed %.4f±%.4f' %
          (args.seeds, agg['spearman']['mean_cos']['mean'], agg['spearman']['mean_cos']['std']))
    print('pearson (偏置场): 论文 1.000 | %d-seed %.4f±%.4f' %
          (args.seeds, agg['theory']['pearson_r']['mean'], agg['theory']['pearson_r']['std']))


if __name__ == '__main__':
    main()
