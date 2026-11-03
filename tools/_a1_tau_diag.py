"""A1 τ 异常诊断：同一份 frozen_refs 下，seed42 与 seed123/456 的 τ 为何差 0.8。

用当前代码、同一进程、同一参照，对以下检查点各算一次 τ：
  · 未载入权重（LoRA B=0，ΔW=0）→ 自洽检查，应恰好 = 1.0000
  · lr0.0/seed42/epoch10   （08-17 旧跑）
  · lr0.0/seed42/epoch1
  · lr0.0/seed123/epoch1
  · lr0.0/seed123/epoch10  （09-14 新跑）
  · lr0.0/seed456/epoch10
并打印每个检查点的 LoRA 增量范数、history、逐样本 τ 分布。
"""
import os
import sys
import json
import glob
import importlib.util

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
from transformers import CLIPModel, CLIPProcessor
from datasets import Dataset as HFDataset
from src.lora import apply_lora_to_model

SAVE_ROOT = 'outputs/a1_class_aligned'

# ---- 直接加载 train_class_aligned 模块，复用其 compute_tau（保真） ----
spec = importlib.util.spec_from_file_location('tca', 'tools/train_class_aligned.py')
tca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tca)

print('=== 各 seed 目录的文件与时间 ===', flush=True)
for seed in (42, 123, 456):
    d = os.path.join(SAVE_ROOT, 'lr0.0', 'seed%d' % seed)
    if not os.path.isdir(d):
        print('  缺目录', d)
        continue
    for f in sorted(os.listdir(d)):
        if f.endswith('.json'):
            p = os.path.join(d, f)
            print('  seed%-4d %-22s %s' % (seed, f, __import__('datetime')
                  .datetime.fromtimestamp(os.path.getmtime(p)).strftime('%Y-%m-%d %H:%M:%S')))

print()
print('=== 检查点元数据 ===', flush=True)
cks = {}
for seed, ep in ((42, 1), (42, 10), (123, 1), (123, 10), (456, 10)):
    p = os.path.join(SAVE_ROOT, 'lr0.0', 'seed%d' % seed, 'epoch%d.pt' % ep)
    ck = torch.load(p, weights_only=False)
    cks[(seed, ep)] = ck
    hist = ck.get('history')
    print('  seed%-4d ep%-3d keys=%s' % (seed, ep, sorted(ck.keys())))
    if hist:
        print('      history[0]=%s' % (json.dumps(hist[0])[:220],))
        print('      history[-1]=%s' % (json.dumps(hist[-1])[:220],))
    sg = ck['lora_state_dict']
    tot = 0.0
    for k, v in sg.items():
        A = v['A'].float()
        B = v['B'].float()
        tot += float((B @ A).pow(2).sum())
    print('      ||ΔW||_F over all layers = %.4f  (n_layers=%d)' % (tot ** 0.5, len(sg)))

print()
print('=== 参照一致性（自洽检查） ===', flush=True)
ck0 = torch.load(os.path.join(SAVE_ROOT, 'frozen_refs.pt'), weights_only=False)
tf, cents, S0, topk5, y_pseudo, sub_indices = (ck0['tf'], ck0['cents'], ck0['S0'],
                                               ck0['topk5'], ck0['y_pseudo'],
                                               ck0['sub_indices'])
print('  frozen_refs: tf%s S0%s topk5%s' % (tuple(tf.shape), S0.shape, topk5.shape))
print('  topk5 前 5 行:', topk5[:5].tolist())

parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
ds_in = HFDataset.from_parquet(parq)
sub = ds_in.select(list(sub_indices))
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
tf_gpu = tf.cuda()

print()
print('=== 逐检查点 τ（当前代码，同一进程） ===', flush=True)
print('%-26s %9s %9s %9s %8s' % ('checkpoint', 'tau_mean', 'tau_med', 'frac=+1', 'skipped'))


def per_sample_tau(model):
    with torch.no_grad():
        imgs = []
        for i in range(0, tca.N_TAU, 64):
            b = sub[i:i + 64]
            inp = processor(images=b['image'], return_tensors='pt').to('cuda')
            vout = model.vision_model(**inp)
            vpool = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            imgs.append(F.normalize(model.visual_projection(vpool), dim=-1))
        cur = torch.cat(imgs)
    Sc = (cur @ tf_gpu.T).float().cpu().numpy()
    per, skipped = [], 0
    for i in range(tca.N_TAU):
        k5 = topk5[i]
        r1, r2 = S0[i][k5], Sc[i][k5]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            skipped += 1
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            per.append(t)
    return np.array(per), Sc, skipped


rows = []


def run(tag, ck=None):
    m = CLIPModel.from_pretrained('openai/clip-vit-base-patch32',
                                  local_files_only=True)
    m, lora_layers, _ = apply_lora_to_model(m, rank=8, alpha=16.0,
                                            apply_to_vision=True, apply_to_text=True)
    m = m.cuda()
    if ck is not None:
        sd = ck['lora_state_dict']
        for k, v in lora_layers.items():
            if k not in sd:
                print('    [warn] 缺 key', k)
                continue
            v.lora_A.data.copy_(sd[k]['A'].to(v.lora_A.device, v.lora_A.dtype))
            v.lora_B.data.copy_(sd[k]['B'].to(v.lora_B.device, v.lora_B.dtype))
    m.eval()
    per, Sc, skipped = per_sample_tau(m)
    # 仅在两个关键配置上调用原版 compute_tau，证明本副本与出厂实现一致（其余配置省一次前向）
    real = tca.compute_tau(m, processor, sub, tf_gpu, S0, topk5) \
        if tag in ('init (B=0, ΔW=0)', 'seed42 ep10', 'seed123 ep10') else float('nan')
    print('%-26s %9.4f %9.4f %9.3f %8d   [compute_tau=%.4f]'
          % (tag, per.mean(), np.median(per), float((per > 0.999).mean()), skipped, real),
          flush=True)
    rows.append((tag, float(per.mean()), float(real), per))
    del m
    torch.cuda.empty_cache()


run('init (B=0, ΔW=0)')
for seed, ep in ((42, 1), (42, 10), (123, 1), (123, 10), (456, 10)):
    run('seed%d ep%d' % (seed, ep), cks[(seed, ep)])

print()
print('=== 逐样本 τ 取值分布（5 项 Kendall 只会落在 −1..1 的离散格点）===', flush=True)
for tag, mean, real, per in rows:
    vals, cnts = np.unique(np.round(per, 3), return_counts=True)
    top = sorted(zip(cnts, vals), reverse=True)[:6]
    print('  %-26s mean=%+.4f  ' % (tag, mean)
          + '  '.join('τ=%+.1f:%d' % (v, c) for c, v in top))

print()
print('=== seed42 vs seed123 的 LoRA 参数差异 ===', flush=True)
a, b = cks[(42, 10)]['lora_state_dict'], cks[(123, 10)]['lora_state_dict']
same = 0
tot_d = 0.0
tot_s = 0.0
for k in a:
    dA = (a[k]['A'].float() - b[k]['A'].float()).pow(2).sum()
    dB = (a[k]['B'].float() - b[k]['B'].float()).pow(2).sum()
    tot_d += float(dA + dB)
    tot_s += float(a[k]['A'].float().pow(2).sum() + b[k]['A'].float().pow(2).sum())
    if dA == 0 and dB == 0:
        same += 1
print('  完全相同的层数: %d / %d' % (same, len(a)))
print('  ||θ_42 − θ_123|| = %.4f ；||θ_42||+||θ_123|| ≈ %.4f' % (tot_d ** 0.5, tot_s ** 0.5))
