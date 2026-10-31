"""A1 理论三剩余项统一验证（2026-08-22）。

① 经验分布 F̂_m 版相关结构界（消高斯保守差）
② O 正交族：复现 RandomState(7) 的 r_hat → σ̃=std(r·t_c) + Theorem 1 逐点预测 τ_O(λ) vs 实测
③ Theorem 5 类收缩逐图微验证：同 5k 样本质心 + 精确仿射序 → 预测 top-1/τ vs 实测(70.32/78.58)

所有口径与 tools/clip_a1_{margins,full,subspace}.py 一致（seed 42 五万张抽样、
Flickr30k 验证子集 2000-3000 算鸿沟、同 CLIP 权重）。输出 outputs/a1_theory_verify.json。
"""
import os
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
import glob
import json
import sys
import pathlib

import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
from scipy.special import erf
from transformers import CLIPModel, CLIPProcessor
from datasets import Dataset
from torch.utils.data import DataLoader

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from src.dataset import Flickr30kDataset, _collate_fn  # noqa: E402

TEMPLATE = 'a photo of a {}'
N = 5000
LAMBDAS = [-2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 4]


def phi(x):
    return 0.5 * (1.0 + erf(x / np.sqrt(2.0)))


def main():
    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    assert parq, 'no parquet shards'
    ds_in = Dataset.from_parquet(parq)
    names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
    texts = [TEMPLATE.format(c.replace('_', ' ')) for c in names]
    rng = np.random.RandomState(42)
    idx = rng.choice(len(ds_in), N, replace=False)
    sub = ds_in.select(list(idx))
    labels = torch.tensor(sub['label'])

    model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32',
                                      local_files_only=True).cuda().eval()
    processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32',
                                              local_files_only=True)

    with torch.no_grad():
        ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
        tout = model.text_model(**ti)
        pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
        tf = F.normalize(model.text_projection(pooled), dim=-1)
        imgs = []
        for i in range(0, N, 64):
            b = sub[i:i + 64]
            inp = processor(images=b['image'], return_tensors='pt').to('cuda')
            vout = model.vision_model(**inp)
            vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            imgs.append(F.normalize(model.visual_projection(vpooled), dim=-1))
        base = torch.cat(imgs)
        base = base / base.norm(dim=-1, keepdim=True)

    # 鸿沟方向（与 margins/full/subspace 同口径）
    ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
    val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
    loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0,
                        collate_fn=_collate_fn)
    fi, ft = [], []
    with torch.no_grad():
        for batch in loader:
            out = model(pixel_values=batch['image'].cuda(),
                        input_ids=batch['input_ids'].cuda(),
                        attention_mask=batch['attention_mask'].cuda(),
                        return_loss=False)
            fi.append(F.normalize(out.image_embeds, dim=-1))
            ft.append(F.normalize(out.text_embeds, dim=-1))
    fi = torch.cat(fi)
    ft = torch.cat(ft)
    gap_vec = ft.mean(0) - fi.mean(0)
    gap_norm = gap_vec.norm().item()
    d_hat = gap_vec / gap_norm

    m = (d_hat @ tf.T).cpu().numpy()           # 1000 类 m_c（原始单位）
    mean_m = float(np.mean(m))
    m0 = m - mean_m
    sigma_m = float(np.std(m0))
    S = (base @ tf.T).cpu().numpy()            # 5000×1000 冻结分数
    topk5 = np.argsort(-S, axis=1)[:, :5]
    out = {'meta': {'n_images': N, 'gap_norm': gap_norm, 'mean_m': mean_m,
                    'sigma_m': sigma_m, 'sigma_b': float(np.sqrt(2) * sigma_m)}}

    # ============ ① 经验分布 F̂_m 相关结构界 ============
    # 条件化 m_1 = u（该图实际值），竞争者从除该类外的 999 个 m 中经验抽样
    # λ>0: P_j = F̂_m(u + d/(λ‖g‖))；λ<0: P_j = 1 − F̂_m(u − d/(|λ|‖g‖))
    res_emp = {}
    for l in LAMBDAS:
        losses = []
        for i in range(N):
            k5 = topk5[i]
            c1 = k5[0]
            u = m[c1]
            dc = S[i][c1] - S[i][k5[1:]]              # 4 个 d_{1j}
            ps = []
            for t in (u + dc / (l * gap_norm)) if l > 0 else (u - dc / (abs(l) * gap_norm)):
                sgn_keep = 1.0 if l > 0 else -1.0
                # F̂_m(t) over other classes（排除 c1 的类）
                others = np.delete(m, c1)
                frac = float(np.mean(others <= t))
                prob = frac if l > 0 else 1.0 - frac
                ps.append(prob)
            losses.append(1.0 - float(np.prod(ps)))
        res_emp[str(l)] = float(np.mean(losses))
    out['predicted_rank1_loss_emp'] = res_emp

    # ============ ② O 正交族（Corollary 1 验证） ============
    rng2 = np.random.RandomState(7)
    rv = torch.tensor(rng2.randn(512), dtype=torch.float32)
    rv = rv - (rv @ d_hat.cpu()) * d_hat.cpu()
    r_hat = (rv / rv.norm()).numpy()
    mO = r_hat @ tf.cpu().numpy().T               # 1000 类 m^O_c
    sigma_O = float(np.std(mO))
    out['orthogonal'] = {'sigma_mO': sigma_O, 'ratio_sigmaO_over_sigmaM': sigma_O / sigma_m}
    # Theorem 1 算子：同一 top-5 结构与 margin，仅换偏置场 b^O（向量化版）
    mO_t = torch.tensor(mO)
    pred_tau_O = {}
    for l in LAMBDAS:
        inv = []
        for i in range(N):
            k5 = topk5[i]
            s5 = S[i][k5]
            dmat = s5[:, None] - s5[None, :]
            bmat = mO_t[k5][None, :] - mO_t[k5][:, None]   # m_i − m_j（需要 j−i）
            bmat = -bmat
            upper = np.triu(np.ones((5, 5)), k=1).astype(bool)
            inv.append(int(((l * gap_norm * bmat.numpy()[upper]) > dmat[upper]).sum()))
        pred_tau_O[str(l)] = 1.0 - 2 * float(np.mean(inv)) / 10.0
    out['predicted_tau_orthogonal'] = pred_tau_O
    meas_tau_O = {}
    fr = json.load(open('outputs/a1_full_results.json', encoding='utf-8'))
    for r in fr:
        if r.get('kind') == 'O':
            meas_tau_O[str(r['lambda'])] = r.get('tau_top5')
    out['measured_tau_orthogonal'] = meas_tau_O

    # ============ ③ Theorem 5：类收缩逐图微验证 ============
    cents = torch.stack([base[labels == c].mean(0) for c in sorted(set(labels.numpy().tolist()))])
    cents = cents / cents.norm(dim=-1, keepdim=True)
    cidx = torch.tensor([sorted(set(labels.numpy().tolist())).index(int(li)) for li in labels],
                        device='cuda')
    c_own = cents[cidx]
    e = (c_own - base)                           # 5000×512（不归一化；序由分子决定）
    Delta = (e @ tf.T).cpu().numpy()             # ⟨e, t_c⟩ 5000×1000
    resP = {}
    self_field = []
    for a in [0.25, 0.5]:
        S2 = S + a * Delta
        pred_top1 = float((S2.argmax(1) == labels.numpy()).mean() * 100)
        taus = []
        for i in range(N):
            k5 = topk5[i]
            r1, r2 = S[i][k5], S2[i][k5]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        resP[str(a)] = {'predicted_top1': round(pred_top1, 2),
                        'predicted_tau': round(float(np.mean(taus)), 4)}
        if a == 0.5:
            y = labels.numpy()
            self_field = [float(Delta[i, y[i]]) for i in range(N)]
    out['class_contraction'] = resP
    out['class_contraction']['self_field_mean_a1'] = float(np.mean(self_field))
    out['class_contraction']['self_field_std_a1'] = float(np.std(self_field))
    # 对照实测（a1_subspace_results.json P 行）
    sp = json.load(open('outputs/a1_subspace_results.json', encoding='utf-8'))
    measP = {}
    for r in sp['results']:
        if r['family'] == 'class_contraction':
            measP[str(r['param'])] = {'top1': r['top1'], 'tau': r['tau_top5']}
    out['class_contraction']['measured'] = measP

    with open('outputs/a1_theory_verify.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print('saved outputs/a1_theory_verify.json')
    print(' ① emp-F:', {k: round(v, 4) for k, v in res_emp.items()})
    print(' ② sigma_O=%.4f (ratio %.3f)  pred_tau_O:' % (sigma_O, out['orthogonal']['ratio_sigmaO_over_sigmaM']),
          {k: round(v, 4) for k, v in pred_tau_O.items()})
    print('    meas_tau_O:', {k: v for k, v in meas_tau_O.items()})
    print(' ③ P:', resP, 'vs measured:', measP)


if __name__ == '__main__':
    main()
