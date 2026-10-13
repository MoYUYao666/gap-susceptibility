"""判定 frozen_refs.pt 的 S0 与当前 ImageNet 分片错位的性质。

情形 A（纯置换）：当前分片就是当初那批图，只是行序不同 → 可反解置换，S0 仍可用。
情形 B（换了图）：行的内容不同 → 必须重建缓存，所有 τ 必须重算。

做法：用当前数据算基座分数 B(5000,1000)，对每个 i 找 j* = argmin_j ||S0_i − B_j||。
若 i→j* 是双射且最小距离≈0 → 情形 A。
"""
import os
import sys
import glob
import json

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from transformers import CLIPModel, CLIPProcessor
from datasets import Dataset as HFDataset

SAVE_ROOT = 'outputs/a1_class_aligned'
N_TAU = 5000
TEMPLATE = 'a photo of a {}'

ck = torch.load(os.path.join(SAVE_ROOT, 'frozen_refs.pt'), weights_only=False)
S0 = ck['S0']
topk5 = ck['topk5']
sub_indices = ck['sub_indices']
print('cache S0', S0.shape, 'topk5', topk5.shape, 'n_sub', len(sub_indices))
print('sub_indices 前10:', sub_indices[:10])

parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
print('当前分片 %d 个：' % len(parq))
for p in parq:
    print('   %-46s %10d B  %s' % (os.path.basename(p), os.path.getsize(p),
          __import__('datetime').datetime.fromtimestamp(
              os.path.getmtime(p)).strftime('%Y-%m-%d %H:%M')))
ds_in = HFDataset.from_parquet(parq)
print('当前总行数:', len(ds_in))
names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
texts = [TEMPLATE.format(c.replace('_', ' ')) for c in names]

sub = ds_in.select(list(sub_indices))
labels_cur = np.array(sub['label'])
print('当前 sub 的标签分布: 前 20 =', labels_cur[:20].tolist())
print('当前 sub 唯一类数 =', len(set(labels_cur.tolist())))

model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32',
                                  local_files_only=True).cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32',
                                          local_files_only=True)
with torch.no_grad():
    ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**ti)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf_c = F.normalize(model.text_projection(pooled), dim=-1)
    imgs = []
    for i in range(0, N_TAU, 64):
        b = sub[i:i + 64]
        inp = processor(images=b['image'], return_tensors='pt').to('cuda')
        vout = model.vision_model(**inp)
        vpool = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        imgs.append(F.normalize(model.visual_projection(vpool), dim=-1))
    cur = torch.cat(imgs)
B = (cur @ tf_c.T).float().cpu().numpy()
print('当前基座分数矩阵 B', B.shape)

# --- 与缓存的一致性 ---
print()
print('--- 与缓存 tf 的一致性 ---')
tf_cache = ck['tf'].numpy()
print('  ||tf_cache − tf_cur||_max = %.3e  (0 表示文本塔一致)' % np.abs(tf_cache - tf_c.cpu().numpy()).max())

top1_cache = S0.argmax(1)
top1_cur = B.argmax(1)
agree = float((top1_cache == top1_cur).mean())
print('  逐样本 argmax(S0) vs argmax(B) 一致率 = %.4f' % agree)
print('  （匹配→接近基座 top-1 准确率；错位→≈1/1000 量级）')

# --- 最近邻匹配：是否为纯置换 ---
S0t = torch.tensor(S0, dtype=torch.float32)
Bt = torch.tensor(B, dtype=torch.float32)
# 余弦（S0/B 无归一化，用欧氏距离更直观）
d2 = (S0t.pow(2).sum(1, keepdim=True) + Bt.pow(2).sum(1).unsqueeze(0) - 2 * S0t @ Bt.T)
mind, argmin = d2.min(dim=1)
mind = mind.sqrt().numpy()
argmin = argmin.numpy()
print()
print('--- 最近邻匹配（判定情形 A/B）---')
print('  最小距离: median=%.3e  p90=%.3e  max=%.3e' % (np.median(mind),
      np.percentile(mind, 90), mind.max()))
exact = mind < 1e-3
print('  精确匹配比例 (dist<1e-3) = %.4f' % exact.mean())
print('  argmin 唯一值个数 = %d / 5000' % len(set(argmin.tolist())))
is_bijection = len(set(argmin.tolist())) == N_TAU
print('  是否为双射 =', is_bijection)

if exact.mean() > 0.99 and is_bijection:
    print()
    print('  >>> 判定：情形 A（同一批图，行序被置换）→ 可反解，S0 仍可用')
    np.save(os.path.join(SAVE_ROOT, 'sub_remap_argmin.npy'), argmin)
    # 用重排后的顺序再算一次 τ_init，应当 ≈ 1.0
    from scipy import stats
    Bp = B[argmin]                     # 重排后第 i 行 = 旧第 i 行对应的当前数据
    per = []
    for i in range(N_TAU):
        k5 = topk5[i]
        r1, r2 = S0[i][k5], Bp[i][k5]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            per.append(t)
    print('  重排后 τ_init = %.4f （应 ≈ 1.0，即自洽）' % float(np.mean(per)))
    perm = [int(sub_indices[int(j)]) for j in argmin]
    with open(os.path.join(SAVE_ROOT, 'sub_indices_orig_order.json'), 'w') as f:
        json.dump({'note': '重排回 2026-08-16 建缓存时的图像顺序：sub = ds_in.select(this)',
                   'sub_indices': perm}, f)
    print('  已写 outputs/a1_class_aligned/sub_indices_orig_order.json')
else:
    print()
    print('  >>> 判定：情形 B（图像内容不同 / 非纯置换）→ 必须重建 frozen_refs.pt，τ 全部重算')
    print('  距离分位: p10=%.3e p50=%.3e' % (np.percentile(mind, 10), np.percentile(mind, 50)))
