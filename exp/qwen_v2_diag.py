"""v2 diagnostic: print per image the greedy next token of h_p, logprob top-5, true-label rank.
Locate the bug layer behind frozen top-1=0. 8 images, takes seconds.
Usage (server /root/autodl-tmp):
  python qwen_v2_diag.py --model /autodl-fs/data/models/qwen2vl-2b \
      --parquet-dir /autodl-fs/data/imagenet_hf/data --n 8
"""
import argparse
import glob

import numpy as np
import torch
from datasets import Dataset
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

from qwen_gap_surgery_v2 import get_lm, img_h_p, score_classes

ap = argparse.ArgumentParser()
ap.add_argument('--model', default='/autodl-fs/data/models/qwen2vl-2b')
ap.add_argument('--parquet-dir', default='/autodl-fs/data/imagenet_hf/data')
ap.add_argument('--n', type=int, default=8)
args = ap.parse_args()

ds_in = Dataset.from_parquet(sorted(glob.glob(args.parquet_dir + '/*.parquet')))
names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
sub = ds_in.select(range(args.n))
labels = [int(sub['label'][i]) for i in range(args.n)]

model = Qwen2VLForConditionalGeneration.from_pretrained(
    args.model, torch_dtype=torch.bfloat16, local_files_only=True).eval().cuda()
processor = AutoProcessor.from_pretrained(args.model, local_files_only=True)
tok = processor.tokenizer
lm = get_lm(model)

for i in range(args.n):
    img = sub['image'][i]
    hp = img_h_p(model, processor, img)
    with torch.no_grad():
        logits0 = model.lm_head(hp)   # keep bf16, argmax/topk do not need float32
        topk_toks = torch.topk(logits0, 5).indices.tolist()
        greedy = topk_toks[0]
    print('--- img %d | true = %s (%s)' % (i, labels[i], names[labels[i]]))
    print('greedy next token:', repr(tok.decode([greedy])),
          '| top5 tokens:', [tok.decode([t]) for t in topk_toks])
    sc = score_classes(model, processor, hp, names).cpu().numpy()
    top5 = np.argsort(-sc)[:5]
    print('score top5:', [(names[t], round(float(sc[t]), 2)) for t in top5])
    print('true-label score: %.2f | rank: %d / 1000' %
          (float(sc[labels[i]]), int((sc > sc[labels[i]]).sum())))
    print()
