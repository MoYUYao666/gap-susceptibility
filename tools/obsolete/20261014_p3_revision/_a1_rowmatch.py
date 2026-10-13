"""决定性测试：当前 data/imagenet_hf 里 sub_indices 指向的图像，是否还是 08-16 建缓存时的那批？

compute_tau 只用图像（Sc = cur @ tf.T，tf 亦取自缓存），与标签/类别名列表无关。
因此若图像一致，用缓存 tf 算出的 B 应与 S0 逐元素几乎相等。

  · 行最近邻是双射且距离 ≈ 0  → 只是行序被置换：可反解，旧 S0 完全可用
  · 否则                      → 内容不同：必须重建 frozen_refs.pt，所有 τ 重算
同时打印类别名列表长度（影响 50k top-1 是否与 08-17 那次可比）。
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

ck = torch.load(os.path.join(SAVE_ROOT, 'frozen_refs.pt'), weights_only=False)
tf_c, S0, topk5, sub_indices = ck['tf'], ck['S0'], ck['topk5'], ck['sub_indices']
print('缓存: tf%s  S0%s  topk5%s' % (tuple(tf_c.shape), S0.shape, topk5.shape))

parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
ds_in = HFDataset.from_parquet(parq)
nms = ds_in.features['label'].names
print('当前数据: 行数=%d  类别名数=%d  num_classes=%s'
      % (len(ds_in), len(nms), ds_in.features['label'].num_classes))
print('  names[:4] =', nms[:4])
print('  names[-3:] =', nms[-3:])
if len(nms) != tf_c.shape[0]:
    print('  !! 类别名数 %d ≠ 缓存文本塔 %d → 09-14 那批 50k top-1 用的文本集与 08-17 不同'
          % (len(nms), tf_c.shape[0]))

sub = ds_in.select(list(sub_indices))
model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32',
                                  local_files_only=True).cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32',
                                          local_files_only=True)
with torch.no_grad():
    imgs = []
    for i in range(0, N_TAU, 64):
        b = sub[i:i + 64]
        inp = processor(images=b['image'], return_tensors='pt').to('cuda')
        vout = model.vision_model(**inp)
        vpool = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        imgs.append(F.normalize(model.visual_projection(vpool), dim=-1))
    cur = torch.cat(imgs)
B = (cur @ tf_c.cuda().T).float().cpu().numpy()      # 用【缓存】tf，故列空间天然对齐
print('B', B.shape)

print()
print('--- 逐元素对齐 ---')
d = np.abs(B - S0)
print('  max|B − S0| = %.4e   mean = %.4e   （图像一致则应 ~1e-6 量级）' % (d.max(), d.mean()))
k1 = S0.argmax(1)
j1 = B.argmax(1)
print('  top-1 类一致率 = %.4f' % float((k1 == j1).mean()))

print()
print('--- 行最近邻匹配（是否只是行序置换）---')
S0t = torch.tensor(S0, dtype=torch.float32)
Bt = torch.tensor(B, dtype=torch.float32)
d2 = (S0t.pow(2).sum(1, keepdim=True) + Bt.pow(2).sum(1).unsqueeze(0) - 2 * S0t @ Bt.T)
mind, argmin = d2.clamp(min=0).sqrt().min(dim=1)
mind = mind.numpy()
argmin = argmin.numpy()
exact = float((mind < 1e-4).mean())
bi = len(set(argmin.tolist())) == N_TAU
print('  最近邻距离: median=%.4e p90=%.4e max=%.4e' % (np.median(mind),
      np.percentile(mind, 90), mind.max()))
print('  dist<1e-4 的比例 = %.4f   双射 = %s' % (exact, bi))

if exact > 0.99 and bi:
    print()
    print('  >>> 情形 A：仅行序被置换。可反解 → 旧 S0 仍可用，seed42 已有 τ 不变，')
    print('      只需为 09-14 的 seed123/456 换用重排后的索引。')
    perm = [int(sub_indices[int(j)]) for j in argmin]
    with open(os.path.join(SAVE_ROOT, 'sub_indices_orig_order.json'), 'w') as f:
        json.dump({'note': '重排回 2026-08-16 建缓存时的图像顺序；sub = ds_in.select(this) '
                           '后与 frozen_refs.pt 的 S0/topk5 一一对应',
                   'n': len(perm), 'sub_indices': perm}, f)
    print('  已写 outputs/a1_class_aligned/sub_indices_orig_order.json')
    # 验证：重排后 τ_init 应 ≈ 1
    from scipy import stats
    Bp = B[argmin]
    per = []
    for i in range(N_TAU):
        k5 = topk5[i]
        r1, r2 = S0[i][k5], Bp[i][k5]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            per.append(t)
    print('  重排后 τ_init = %.4f （应 ≈ 1.0000）' % float(np.mean(per)))
else:
    print()
    print('  >>> 情形 B：图像内容不同（非纯置换）。frozen_refs.pt 作废，')
    print('      必须重建缓存，全部 τ 重算；旧 0.711/0.611 仅在原数据上成立。')
    np.save(os.path.join(SAVE_ROOT, '_B_with_cached_tf.npy'), B)
