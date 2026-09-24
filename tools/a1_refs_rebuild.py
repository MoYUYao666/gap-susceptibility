"""Stage 1：还原旧质心表的类 ID 映射 + 验证当前分片 + 重建 frozen_refs.pt。

做四件事：
 1. 用当前 50k 全量算 1000 个类的图像质心，并与旧缓存 cents(998,512) 做匹配，
    还原旧 cls_ids —— 由此判定"c_ema[y] 按类 ID 索引、但 cents 按 cls_ids 位置排列"
    这个错位是否真的影响过 08-16/09-14 的训练。
 2. 顺带算当前数据的基座 CLIP 零样本 50k top-1（1000 类），用于核对数据等价性。
 3. 备份并作废旧 frozen_refs.pt。
 4. 用修好的 build_frozen_refs() 重建缓存（现在 cents 为按类 ID 索引的 1000 行表）。
"""
import os
import sys
import glob
import json
import time
import shutil
import importlib.util

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from transformers import CLIPModel, CLIPProcessor
from datasets import Dataset as HFDataset

SAVE_ROOT = 'outputs/a1_class_aligned'
TEMPLATE = 'a photo of a {}'

spec = importlib.util.spec_from_file_location('tca', 'tools/train_class_aligned.py')
tca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tca)

parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
ds_in = HFDataset.from_parquet(parq)
names = tca.imagenet_class_names(ds_in)
print('当前数据: %d 行, %d 类（已剔除占位类）' % (len(ds_in), len(names)), flush=True)
print('  与 data/imagenet_1k_names.json 一致?',
      names == json.load(open('data/imagenet_1k_names.json', encoding='utf-8')), flush=True)

model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32',
                                  local_files_only=True).cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32',
                                          local_files_only=True)

t0 = time.time()
with torch.no_grad():
    ti = processor(text=[TEMPLATE.format(c) for c in names],
                   return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**ti)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf = F.normalize(model.text_projection(pooled), dim=-1)

    embs, labs, correct, total = [], [], 0, 0
    for shard in parq:
        d = HFDataset.from_parquet(shard)
        for i in range(0, len(d), 64):
            b = d[i:i + 64]
            inp = processor(images=b['image'], return_tensors='pt').to('cuda')
            vout = model.vision_model(**inp)
            vpool = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            ie = F.normalize(model.visual_projection(vpool), dim=-1)
            pred = (ie @ tf.T).argmax(1).cpu().numpy()
            lb = np.array(b['label'])
            correct += int((pred == lb).sum())
            total += len(lb)
            embs.append(ie.cpu())
            labs.append(torch.tensor(lb))
print('全量 50k 前向完成 %.1f s；基座零样本 top-1 = %.2f%% (n=%d)'
      % (time.time() - t0, correct / total * 100, total), flush=True)

E = torch.cat(embs).float()
L = torch.cat(labs)
del embs, labs
torch.cuda.empty_cache()

# 逐类质心（全量 50 张/类，比旧缓存 5k 子集稳得多）
new_cents = torch.zeros(len(names), E.shape[1])
cnt = np.zeros(len(names), dtype=int)
for c in range(len(names)):
    m = (L == c)
    cnt[c] = int(m.sum())
    if cnt[c]:
        new_cents[c] = F.normalize(E[m].mean(0), dim=-1)
print('每类样本数: min=%d max=%d（应各 50）' % (cnt.min(), cnt.max()), flush=True)

# ---- 还原旧 cents 的类 ID ----
ck = torch.load(os.path.join(SAVE_ROOT, 'frozen_refs.pt'), weights_only=False)
old_cents = ck['cents'].float()
print('旧 cents 形状', tuple(old_cents.shape), flush=True)
sim = old_cents @ new_cents.T                      # (998, 1000)
best = sim.argmax(1).numpy()
bestv = sim.max(1).values.numpy()
srt = sim.sort(1).values
margin = (srt[:, -1] - srt[:, -2]).numpy()
cls_ids = sorted(best.tolist())
print('还原出的类 ID 个数 = %d（唯一 %d）' % (len(cls_ids), len(set(cls_ids))), flush=True)
print('  匹配余弦: mean=%.4f min=%.4f' % (bestv.mean(), bestv.min()), flush=True)
print('  top1−top2 间隔: median=%.4f  min=%.4f' % (np.median(margin), margin.min()), flush=True)
missing = [i for i in range(len(names)) if i not in set(cls_ids)]
print('  推断旧 5k 子集缺失的类: %s' % missing, flush=True)
shift_info = {}
if missing:
    first = min(missing)
    n_after = sum(1 for i in cls_ids if i > first)
    print('  首个缺失类 id=%d；其后的类有 %d 个 → 旧实现中这些类的质心整体错位'
          % (first, n_after), flush=True)
    shift_info = {'first_missing': first, 'n_classes_after_first_gap': n_after,
                  'order_ok': first > max(cls_ids)}
print('  旧实现是否恰好正确（缺失类都在末尾）: %s' % shift_info.get('order_ok', False),
      flush=True)

report = {'checked_at': time.strftime('%Y-%m-%d %H:%M:%S'),
          'current_shards': {'n_files': len(parq), 'n_rows': len(ds_in),
                             'n_classes_used': len(names), 'per_class': int(cnt.min())},
          'base_zeroshot_50k_top1': correct / total * 100,
          'old_cents_rows': int(old_cents.shape[0]),
          'recovered_cls_ids': cls_ids,
          'missing_classes_infer': missing,
          'match_cosine_mean': float(bestv.mean()),
          'match_margin_median': float(np.median(margin)),
          'order_ok_in_old_impl': bool(shift_info.get('order_ok', False)),
          'note': 'cls_ids 由旧 cents 与新全量质心匹配还原，匹配余弦普遍很高时可信'}
with open(os.path.join(SAVE_ROOT, 'old_cents_cls_ids_recovery.json'), 'w',
          encoding='utf-8') as f:
    json.dump(report, f, indent=1, ensure_ascii=False)
print('已写', os.path.join(SAVE_ROOT, 'old_cents_cls_ids_recovery.json'), flush=True)

# ---- 作废旧参照并重建 ----
cache = os.path.join(SAVE_ROOT, 'frozen_refs.pt')
stale = os.path.join(SAVE_ROOT, 'frozen_refs.STALE_2026-08-16.pt')
if os.path.exists(cache) and not os.path.exists(stale):
    shutil.move(cache, stale)
    print('旧参照已备份为', stale, flush=True)
del E, L, old_cents, sim, srt
torch.cuda.empty_cache()
print('开始重建 frozen_refs.pt ...', flush=True)
tca.build_frozen_refs()
print('重建完成', flush=True)
ck2 = torch.load(cache, weights_only=False)
for k, v in ck2.items():
    print('  %-12s %s' % (k, tuple(v.shape) if hasattr(v, 'shape') else 'len=%d' % len(v)))
print('  新 cents 行数应为 1000:', ck2['cents'].shape[0])
