"""Decisive check: zero-shot on ImageNet-1K (val subset, 4 shards = 14288 images).
If frozen ≈ 60.72 and text_only/both drop (≈59.06/56.14), then the paper data is indeed ImageNet-1K.
Protocol matches the TinyImageNet check: average over 3 templates; class names are the primary synset name (before the comma)."""
import os, sys, json
os.environ['HF_HUB_OFFLINE'] = '1'

# ---------- 1. parquet first (datasets must be imported before torch) ----------
from glob import glob
from datasets import Dataset
PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
assert PARQ, 'no parquet shards under data/imagenet_hf/'
ds = Dataset.from_parquet(PARQ)
print('ImageNet-1K shards loaded:', len(ds), 'images, from', len(PARQ), 'shards', flush=True)

# label guard: the ILSVRC test set is unlabeled (-1); the validation shards must be used
labs = ds['label']
uniq = sorted(set(labs))
print('classes covered:', len(uniq), '| label range:', min(uniq), '-', max(uniq), flush=True)
if uniq == [-1]:
    sys.exit('!! all labels are -1: this is the ILSVRC test set (unlabeled, 100k images). Please download the validation shards (50k, labeled) and replace the contents of data/imagenet_hf/')

# class names: ClassLabel names (words format), take the primary name before the comma
names = ds.features['label'].names
CLASS_NAMES = [n.split(',')[0].strip() for n in names]
assert len(CLASS_NAMES) == 1000
json.dump(CLASS_NAMES, open('data/imagenet_1k_names.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('1000 class names saved to data/imagenet_1k_names.json | first 5:', CLASS_NAMES[:5], flush=True)

# ---------- 2. CLIP + LoRA (after datasets) ----------
print('loading CLIP ViT-B/32 ...', flush=True)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from transformers import CLIPModel, CLIPProcessor
from src.lora import apply_lora_to_model

processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)

if len(sys.argv) > 1 and sys.argv[1] == 'single':
    templates = ['a photo of a {}']  # the only template in zeroshot_extra.py
else:
    templates = ['a photo of a {}', 'a photo of the {}', 'a photo of a {} in a photo']
all_texts = [t.format(c.replace('_', ' ')) for c in CLASS_NAMES for t in templates]
text_in = processor(text=all_texts, return_tensors='pt', padding=True).to('cuda')

@torch.no_grad()
def model_text_feats(m):
    tf = m.get_text_features(**text_in)
    tf = tf / tf.norm(dim=-1, keepdim=True)
    tf = tf.view(1000, len(templates), -1).mean(dim=1)
    return tf / tf.norm(dim=-1, keepdim=True)

@torch.no_grad()
def eval_zs(m):
    m = m.cuda().eval()
    text_feats = model_text_feats(m)
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
        if total % 3500 == 0:
            print('  ... %d/%d' % (total, len(ds)), flush=True)
    return 100 * correct / total

configs = {
    'frozen (paper 60.72)':   dict(ckpt=None),
    'text_only_r8 (paper 59.06)': dict(ckpt='outputs/imagenet_zs/text_only_r8/best_checkpoint.pt',
                                       vision=False, text=True),
    'both_r8 (paper 56.14)':  dict(ckpt='outputs/imagenet_zs/both_r8/best_checkpoint.pt',
                                       vision=True, text=True),
}
import json as _json
saved = {}
for label, cfg in configs.items():
    m = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
    if cfg.get('ckpt'):
        m, lora_layers, _ = apply_lora_to_model(
            m, rank=8, alpha=16.0,
            apply_to_vision=cfg['vision'], apply_to_text=cfg['text'])
        ckpt = torch.load(cfg['ckpt'], map_location='cpu', weights_only=False)
        sd = ckpt['lora_state_dict']
        missing = set(sd) - set(lora_layers)
        extra = set(lora_layers) - set(sd)
        assert not missing and not extra, 'LoRA layers mismatch: missing=%s extra=%s' % (
            list(missing)[:3], list(extra)[:3])
        with torch.no_grad():
            for k, w in sd.items():
                lora_layers[k].lora_A.data.copy_(w['A'])
                lora_layers[k].lora_B.data.copy_(w['B'])
        print('%s: LoRA injected into %d layers' % (label, len(sd)), flush=True)
    acc = eval_zs(m)
    print('%s => ImageNet-1K zero-shot top-1: %.2f%%' % (label, acc), flush=True)
    saved[label.split(' (')[0]] = round(acc, 2)

os.makedirs('outputs', exist_ok=True)
out = {'dataset': 'ImageNet-1K val (HF ILSVRC/imagenet-1k)',
       'protocol': {'templates': templates, 'n_images': len(ds),
                    'class_names': 'data/imagenet_1k_names.json', 'shards': PARQ},
       'results': saved, 'paper_values': {'frozen': 60.72, 'text_only': 59.06, 'both': 56.14}}
_json.dump(out, open('outputs/imagenet1k_ckpt_check.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('results saved to outputs/imagenet1k_ckpt_check.json')
print('\nreference paper table values: 60.72 / 59.06 / 56.14 / 7.38')
