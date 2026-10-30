"""ImageNet-1K zero-shot 协议评测 — 采用协议：单模板 'a photo of a {}' + 完整 synset 类名
（类名取自 HF ILSVRC/imagenet-1k 的 ClassLabel names 原文，不做逗号截断）。
14288 张 val 子集（4 个分片）。对 frozen / text_only_r8 / both_r8 三个 checkpoint 评测，
结果落盘 outputs/imagenet1k_zs_synset_single.json（不覆盖其他协议文件）。
补充参考协议（plain 名 + 单模板）见 outputs/imagenet1k_ckpt_check.json。
"""
import os, sys, json
os.environ['HF_HUB_OFFLINE'] = '1'

# ---------- 1. parquet 先行（datasets 必须在 torch 前导入，避免 pyarrow 段错误）----------
from glob import glob
from datasets import Dataset
PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
assert PARQ, 'data/imagenet_hf/ 下没有 parquet 分片'
ds = Dataset.from_parquet(PARQ)
print('ImageNet-1K 分片已加载:', len(ds), '张', flush=True)

labs = ds['label']
uniq = sorted(set(labs))
if uniq == [-1]:
    sys.exit('!! 标签全为 -1：这是 ILSVRC test 集。请用 validation 分片。')

# 完整类名（保留逗号后 synset 短语），即 dataset 的原始 label names
CLASS_NAMES_FULL = ds.features['label'].names
assert len(CLASS_NAMES_FULL) == 1000
print('首 3 类名(full):', CLASS_NAMES_FULL[:3], flush=True)

# ---------- 2. CLIP + LoRA ----------
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from transformers import CLIPModel, CLIPProcessor
from src.lora import apply_lora_to_model

TEMPLATES = ['a photo of a {}']
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
all_texts = [t.format(c.replace('_', ' ')) for c in CLASS_NAMES_FULL for t in TEMPLATES]
text_in = processor(text=all_texts, return_tensors='pt', padding=True).to('cuda')


@torch.no_grad()
def model_text_feats(m):
    out = m.text_model(**text_in)
    pooled = out[1] if isinstance(out, tuple) else out.pooler_output
    tf = m.text_projection(pooled)
    tf = tf / tf.norm(dim=-1, keepdim=True)
    tf = tf.view(1000, len(TEMPLATES), -1).mean(dim=1)
    return tf / tf.norm(dim=-1, keepdim=True)


@torch.no_grad()
def eval_zs(m):
    m = m.cuda().eval()
    text_feats = model_text_feats(m)
    correct = total = 0
    for i in range(0, len(ds), 64):
        batch = ds[i:i + 64]
        imgs, ys = batch['image'], batch['label']
        inp = processor(images=imgs, return_tensors='pt').to('cuda')
        vout = m.vision_model(**inp)
        pooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        img_feats = m.visual_projection(pooled)
        img_feats = img_feats / img_feats.norm(dim=-1, keepdim=True)
        sims = img_feats @ text_feats.T
        pred = sims.argmax(-1).cpu().numpy()
        correct += sum(1 for p, y in zip(pred, ys) if p == y)
        total += len(ys)
        if total % 3500 == 0:
            print('  ... %d/%d' % (total, len(ds)), flush=True)
    return 100 * correct / total


configs = {
    'frozen': dict(ckpt=None),
    'text_only_r8': dict(ckpt='outputs/imagenet_zs/text_only_r8/best_checkpoint.pt',
                         vision=False, text=True),
    'both_r8': dict(ckpt='outputs/imagenet_zs/both_r8/best_checkpoint.pt',
                    vision=True, text=True),
}
saved = {}
for label, cfg in configs.items():
    m = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
    if cfg.get('ckpt'):
        m, lora_layers, _ = apply_lora_to_model(
            m, rank=8, alpha=16.0,
            apply_to_vision=cfg['vision'], apply_to_text=cfg['text'])
        ckpt = torch.load(cfg['ckpt'], map_location='cpu', weights_only=False)
        sd = ckpt['lora_state_dict']
        with torch.no_grad():
            for k, w in sd.items():
                lora_layers[k].lora_A.data.copy_(w['A'])
                lora_layers[k].lora_B.data.copy_(w['B'])
    acc = eval_zs(m)
    print('%s => %.2f%%' % (label, acc), flush=True)
    saved[label] = round(acc, 2)

out = {
    'dataset': 'ImageNet-1K val (HF ILSVRC/imagenet-1k)',
    'protocol': {
        'templates': TEMPLATES,
        'n_images': len(ds),
        'class_names': 'full synset phrases from ClassLabel names (no comma truncation)',
        'shards': PARQ,
        'note': 'reference protocol (plain names, single template) in outputs/imagenet1k_ckpt_check.json',
    },
    'results': saved,
    'paper_values': {'frozen': 60.72, 'text_only': 59.06, 'both': 56.14, 'full_ft': 7.38},
}
os.makedirs('outputs', exist_ok=True)
json.dump(out, open('outputs/imagenet1k_zs_synset_single.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print('结果已存 outputs/imagenet1k_zs_synset_single.json')
