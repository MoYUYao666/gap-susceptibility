"""用标签做决定性检验：缓存的 S0 与当前 sub 的图像是否同一批。

图像一致 → argmax(S0[i]) 应≈该行真实标签，命中率接近基座零样本准确率（数十 %）。
图像不一致 → 命中率 ≈ 1/1000 量级。
同时检验 ±1 的类别名错位（旧 1000 类 vs 新 1001 类变体）。
"""
import os
import sys
import json
import glob

os.environ['HF_HUB_OFFLINE'] = '1'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
from datasets import Dataset as HFDataset

SAVE_ROOT = 'outputs/a1_class_aligned'
ck = torch.load(os.path.join(SAVE_ROOT, 'frozen_refs.pt'), weights_only=False)
S0, topk5, sub_indices = ck['S0'], ck['topk5'], ck['sub_indices']

parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
ds_in = HFDataset.from_parquet(parq)
sub = ds_in.select(list(sub_indices))
lab = np.array(sub['label'])
print('当前 sub 标签: min=%d max=%d 唯一个数=%d' % (lab.min(), lab.max(), len(set(lab.tolist()))))
print('全库标签: min=%d max=%d' % (min(ds_in['label']), max(ds_in['label'])))

print()
print('--- 检验 1：旧参照 S0 的 argmax 落在当前标签上的命中率 ---')
a_old = S0.argmax(1)
for off in (-2, -1, 0, 1, 2):
    hit = float(((a_old + off) == lab).mean())
    print('  offset %+d : 命中率 = %.4f' % (off, hit))

print()
print('--- 检验 2：缓存 topk5 的 top-1 是否等于当前标签 ---')
for off in (-1, 0, 1):
    hit = float(((topk5[:, 0] + off) == lab).mean())
    print('  offset %+d : 命中率 = %.4f' % (off, hit))

bp = os.path.join(SAVE_ROOT, '_B_with_cached_tf.npy')
if os.path.exists(bp):
    B = np.load(bp)
    print()
    print('--- 检验 3：当前基座（用缓存 tf）的 argmax 落在当前标签上的命中率 ---')
    a_new = B.argmax(1)
    for off in (-1, 0, 1):
        hit = float(((a_new + off) == lab).mean())
        print('  offset %+d : 命中率 = %.4f' % (off, hit))
    print()
    print('--- 检验 4：S0 与 B 的逐行 argmax 一致率（=%.4f 上面已算）---'
          % float((a_old == a_new).mean()))
    # 行范数与距离尺度，判断 NN 距离 0.59 到底算不算"匹配"
    n_old = np.linalg.norm(S0, axis=1)
    n_new = np.linalg.norm(B, axis=1)
    print('  ||S0||: mean=%.4f p50=%.4f   ||B||: mean=%.4f p50=%.4f'
          % (n_old.mean(), np.median(n_old), n_new.mean(), np.median(n_new)))
    d_rand = np.linalg.norm(S0 - B[np.roll(np.arange(len(B)), 1)], axis=1)
    d_self = np.linalg.norm(S0 - B, axis=1)
    print('  ||S0[i] − B[i]||      : p50=%.4f' % np.median(d_self))
    print('  ||S0[i] − B[随机另一行]||: p50=%.4f' % np.median(d_rand))
    print('  → 两者接近 ⇒ 行与行之间没有对应关系')
