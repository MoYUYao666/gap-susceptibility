"""判定 1000→1001 类错位是否可反解。

思路：若当前分片就是当初那批图、只是类别名列表多插了一项 p，则存在列映射
    m_p(j) = j        (j < p)
    m_p(j) = j + 1    (j >= p)
使 B[:, m_p(j)] ≈ S0[:, j]（逐元素近乎相等）。找到这样的 p 即可完全复原旧参照。
若任何 p 都对不上 → 图像本身不同，必须重建缓存。
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
S0, topk5, sub_indices = ck['S0'], ck['topk5'], ck['sub_indices']

parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
ds_in = HFDataset.from_parquet(parq)
names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
print('当前类别名数 =', len(names))
print('  前 5:', names[:5])
print('  后 5:', names[-5:])
print('  原始 ClassLabel: num_classes=%s  names[:3]=%s'
      % (ds_in.features['label'].num_classes, ds_in.features['label'].names[:3]))
texts = [TEMPLATE.format(c.replace('_', ' ')) for c in names]

sub = ds_in.select(list(sub_indices))
labels_cur = np.array(sub['label'])
print('sub 标签范围: min=%d max=%d 唯一=%d' % (labels_cur.min(), labels_cur.max(),
                                              len(set(labels_cur.tolist()))))

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
print('B', B.shape, ' S0', S0.shape)
np.save(os.path.join(SAVE_ROOT, '_B_current.npy'), B)

# --- 文本塔：缓存 tf 是否是当前 tf 的子集（去掉某一列） ---
tfc = ck['tf'].numpy()
tfn = tf_c.cpu().numpy()
print()
print('--- 文本塔列匹配 ---')
best = None
for p in range(tfn.shape[0]):
    cand = np.delete(tfn, p, axis=0)
    d = np.abs(cand - tfc).max()
    if best is None or d < best[1]:
        best = (p, d)
print('  最优删列 p=%d 时  max|tf_cache − tf_cur\\{p}| = %.3e' % best)
print('  不删列时      max|tf_cache − tf_cur[:1000]| = %.3e'
      % np.abs(tfn[:1000] - tfc).max())

# --- 分数矩阵：找插入位置 p ---
print()
print('--- 分数矩阵列匹配（子样本 500 行搜 p）---')
ns = 500
best_p = None
for p in range(B.shape[1]):
    cols = np.r_[np.arange(p), np.arange(p + 1, B.shape[1])]
    if len(cols) != S0.shape[1]:
        continue
    d = np.abs(B[:ns][:, cols] - S0[:ns]).max()
    if best_p is None or d < best_p[1]:
        best_p = (p, d)
print('  最优插入位置 p=%d  →  max|B[m_p] − S0| (500 行) = %.3e' % best_p)
p = best_p[0]
cols = np.r_[np.arange(p), np.arange(p + 1, B.shape[1])]
d_all = np.abs(B[:, cols] - S0)
print('  全量 5000 行: max=%.3e  mean=%.3e  (≈0 表示图像与基座完全一致)'
      % (d_all.max(), d_all.mean()))
print('  若 p=%d，被剔除的类别名 = %r' % (p, names[p]))

if d_all.max() < 1e-2:
    print()
    print('  >>> 判定：情形 A′（同一批图，类别名列表多插了一项）→ 可完全复原旧参照')
    Bm = B[:, cols]
    k1 = S0.argmax(1)
    j1 = Bm.argmax(1)
    print('  列对齐后 top-1 一致率 = %.4f' % float((k1 == j1).mean()))
    # 行是否也错位
    d2 = (torch.tensor(S0).pow(2).sum(1, keepdim=True)
          + torch.tensor(Bm).pow(2).sum(1).unsqueeze(0)
          - 2 * torch.tensor(S0) @ torch.tensor(Bm).T)
    mind, argmin = d2.min(dim=1)
    mind = mind.clamp(min=0).sqrt().numpy()
    argmin = argmin.numpy()
    bi = len(set(argmin.tolist())) == N_TAU
    print('  行最近邻: median=%.3e  max=%.3e  双射=%s' % (np.median(mind), mind.max(), bi))
    with open(os.path.join(SAVE_ROOT, 'class_name_insert_pos.json'), 'w') as f:
        json.dump({'insert_pos': int(p), 'dropped_name': names[p],
                   'n_cur': len(names), 'n_cache': int(S0.shape[1]),
                   'row_bijection': bool(bi),
                   'row_perm': argmin.tolist() if bi else None}, f)
    print('  已写 outputs/a1_class_aligned/class_name_insert_pos.json')
else:
    print()
    print('  >>> 判定：情形 B（图像内容不同）→ 必须重建 frozen_refs.pt，τ 全部重算')
