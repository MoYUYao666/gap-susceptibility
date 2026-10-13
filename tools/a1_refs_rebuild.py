"""Stage 1: restore the class ID mapping of the old centroid table + verify the current shards + rebuild frozen_refs.pt.

Four things:
 1. Compute the image centroids of 1000 classes over the current full 50k and match them against the old cached cents(998,512)
    to restore the old cls_ids — this decides whether the misalignment "c_ema[y] is indexed by class ID, but cents is ordered by
    cls_ids position" ever affected the 08-16/09-14 training.
 2. Incidentally compute the base CLIP zero-shot 50k top-1 (1000 classes) on the current data, to check data equivalence.
 3. Back up and invalidate the old frozen_refs.pt.
 4. Rebuild the cache with the fixed build_frozen_refs() (cents is now a 1000-row table indexed by class ID).
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
print('current data: %d rows, %d classes (placeholder classes removed)' % (len(ds_in), len(names)), flush=True)
print('  matches data/imagenet_1k_names.json?',
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
print('full 50k forward pass done in %.1f s; base zero-shot top-1 = %.2f%% (n=%d)'
      % (time.time() - t0, correct / total * 100, total), flush=True)

E = torch.cat(embs).float()
L = torch.cat(labs)
del embs, labs
torch.cuda.empty_cache()

# per-class centroids (50 images per class over the full set, far more stable than the old 5k-subset cache)
new_cents = torch.zeros(len(names), E.shape[1])
cnt = np.zeros(len(names), dtype=int)
for c in range(len(names)):
    m = (L == c)
    cnt[c] = int(m.sum())
    if cnt[c]:
        new_cents[c] = F.normalize(E[m].mean(0), dim=-1)
print('samples per class: min=%d max=%d (each should be 50)' % (cnt.min(), cnt.max()), flush=True)

# ---- recover the class IDs of the old cents ----
ck = torch.load(os.path.join(SAVE_ROOT, 'frozen_refs.pt'), weights_only=False)
old_cents = ck['cents'].float()
print('old cents shape', tuple(old_cents.shape), flush=True)
sim = old_cents @ new_cents.T                      # (998, 1000)
best = sim.argmax(1).numpy()
bestv = sim.max(1).values.numpy()
srt = sim.sort(1).values
margin = (srt[:, -1] - srt[:, -2]).numpy()
cls_ids = sorted(best.tolist())
print('number of recovered class IDs = %d (unique %d)' % (len(cls_ids), len(set(cls_ids))), flush=True)
print('  match cosine: mean=%.4f min=%.4f' % (bestv.mean(), bestv.min()), flush=True)
print('  top1−top2 margin: median=%.4f  min=%.4f' % (np.median(margin), margin.min()), flush=True)
missing = [i for i in range(len(names)) if i not in set(cls_ids)]
print('  classes inferred missing from the old 5k subset: %s' % missing, flush=True)
shift_info = {}
if missing:
    first = min(missing)
    n_after = sum(1 for i in cls_ids if i > first)
    print('  first missing class id=%d; there are %d classes after it → in the old implementation the centroids of these classes are all shifted'
          % (first, n_after), flush=True)
    shift_info = {'first_missing': first, 'n_classes_after_first_gap': n_after,
                  'order_ok': first > max(cls_ids)}
print('  whether the old implementation was exactly correct (missing classes all at the end): %s' % shift_info.get('order_ok', False),
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
          'note': 'cls_ids are recovered by matching the old cents against the new full-set centroids; reliable when the match cosines are uniformly high'}
with open(os.path.join(SAVE_ROOT, 'old_cents_cls_ids_recovery.json'), 'w',
          encoding='utf-8') as f:
    json.dump(report, f, indent=1, ensure_ascii=False)
print('wrote', os.path.join(SAVE_ROOT, 'old_cents_cls_ids_recovery.json'), flush=True)

# ---- invalidate the old reference and rebuild ----
cache = os.path.join(SAVE_ROOT, 'frozen_refs.pt')
stale = os.path.join(SAVE_ROOT, 'frozen_refs.STALE_2026-08-16.pt')
if os.path.exists(cache) and not os.path.exists(stale):
    shutil.move(cache, stale)
    print('old reference backed up as', stale, flush=True)
del E, L, old_cents, sim, srt
torch.cuda.empty_cache()
print('rebuilding frozen_refs.pt ...', flush=True)
tca.build_frozen_refs()
print('rebuild done', flush=True)
ck2 = torch.load(cache, weights_only=False)
for k, v in ck2.items():
    print('  %-12s %s' % (k, tuple(v.shape) if hasattr(v, 'shape') else 'len=%d' % len(v)))
print('  the new cents must have 1000 rows:', ck2['cents'].shape[0])
