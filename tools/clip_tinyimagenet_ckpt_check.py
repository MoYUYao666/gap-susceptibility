"""Decisive verification: zero-shot of the outputs/imagenet_zs/ fine-tuned checkpoints on TinyImageNet-200.
If text_only ≈ 59.06 and both ≈ 56.14 (the paper table values), the dataset identity = TinyImageNet-200 is confirmed.
Protocol matches clip_tinyimagenet_eval.py: 3-template average, all 10000 val images."""
import os, sys, json
os.environ['HF_HUB_OFFLINE'] = '1'

# ---------- 1. arrow first (datasets must be imported before torch, otherwise a pyarrow segfault) ----------
from datasets import Dataset
arrow = r'C:\Users\hongr\.cache\huggingface\datasets\zh-plus___tiny-imagenet\default\0.0.0\5a77092c28e51558c5586e9c5eb71a7e17a5e43f\tiny-imagenet-valid.arrow'
ds = Dataset.from_file(arrow)
print('TinyImageNet valid loaded:', len(ds), flush=True)

WNID_NAMES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'tiny_wnid_names.json'), encoding='utf-8'))
assert len(WNID_NAMES) == 200

# ---------- 2. CLIP + LoRA (after datasets) ----------
print('Loading CLIP ViT-B/32 ...', flush=True)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from transformers import CLIPModel, CLIPProcessor
from src.lora import apply_lora_to_model

model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True).cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)

templates = ['a photo of a {}', 'a photo of the {}', 'a photo of a {} in a photo']
all_texts = [t.format(c.replace('_', ' ')) for c in WNID_NAMES for t in templates]
text_in = processor(text=all_texts, return_tensors='pt', padding=True).to('cuda')

@torch.no_grad()
def model_text_feats(m):
    """Recompute the class embeddings with the text tower of the current model (including LoRA)"""
    tf = m.get_text_features(**text_in)
    tf = tf / tf.norm(dim=-1, keepdim=True)
    tf = tf.view(200, len(templates), -1).mean(dim=1)
    return tf / tf.norm(dim=-1, keepdim=True)

@torch.no_grad()
def eval_zs(m):
    m = m.cuda().eval()
    text_feats = model_text_feats(m)  # recomputed each time with the injected text tower
    correct = total = 0
    for i in range(0, len(ds), 64):
        batch = ds[i:i+64]
        imgs, ys = batch['image'], batch['label']
        inp = processor(images=imgs, return_tensors='pt').to('cuda')
        img_feats = m.get_image_features(**inp)
        img_feats = img_feats / img_feats.norm(dim=-1, keepdim=True)
        sims = img_feats @ text_feats.T
        pred = sims.argmax(-1).cpu().numpy()
        correct += sum(1 for p, y in zip(pred, ys) if p == y)
        total += len(ys)
    return 100 * correct / total

STEM = sys.argv[1] if len(sys.argv) > 1 else 'best_checkpoint.pt'
configs = {
    'frozen (paper 60.72)':   dict(ckpt=None),
    'text_only_r8 (paper 59.06)': dict(ckpt=f'outputs/imagenet_zs/text_only_r8/{STEM}',
                                       vision=False, text=True),
    'both_r8 (paper 56.14)':  dict(ckpt=f'outputs/imagenet_zs/both_r8/{STEM}',
                                       vision=True, text=True),
}
print('checkpoint stem:', STEM, flush=True)
saved = {}
for label, cfg in configs.items():
    m = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
    lora_layers = None
    if cfg.get('ckpt'):
        m, lora_layers, _ = apply_lora_to_model(
            m, rank=8, alpha=16.0,
            apply_to_vision=cfg['vision'], apply_to_text=cfg['text'])
        ckpt = torch.load(cfg['ckpt'], map_location='cpu', weights_only=False)
        sd = ckpt['lora_state_dict']
        missing = set(sd) - set(lora_layers)
        extra = set(lora_layers) - set(sd)
        assert not missing, 'checkpoint layers not in the model: %s' % list(missing)[:3]
        assert not extra, 'model layers not in checkpoint: %s' % list(extra)[:3]
        with torch.no_grad():
            for k, w in sd.items():
                lora_layers[k].lora_A.data.copy_(w['A'])
                lora_layers[k].lora_B.data.copy_(w['B'])
        print('%s: LoRA injected into %d layers, weights loaded' % (label, len(sd)), flush=True)
    acc = eval_zs(m)
    print('%s => TinyImageNet-200 zero-shot top-1: %.2f%%' % (label, acc), flush=True)
    saved[label.split(' (')[0]] = round(acc, 2)

import json as _json
os.makedirs('outputs', exist_ok=True)
out = {'dataset': 'TinyImageNet-200 val (zh-plus/tiny-imagenet arrow, 10000 images)',
       'protocol': {'templates': templates, 'n_images': len(ds),
                    'class_names': 'data/tiny_wnid_names.json', 'checkpoint': STEM},
       'results': saved, 'paper_values': {'frozen': 60.72, 'text_only': 59.06, 'both': 56.14}}
_json.dump(out, open('outputs/tinyimagenet_ckpt_check.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('Results saved to outputs/tinyimagenet_ckpt_check.json')
print('\nReference paper table values: 60.72 / 59.06 / 56.14 / 7.38')
