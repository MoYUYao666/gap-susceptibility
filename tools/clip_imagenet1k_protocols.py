"""ImageNet-1K zero-shot protocol evaluation — adopted protocol: single template 'a photo of a {}' + full synset class names
(class names taken verbatim from the ClassLabel names of HF ILSVRC/imagenet-1k, with no comma truncation).
A 14288-image val subset (4 shards). Evaluates the three checkpoints frozen / text_only_r8 / both_r8,
and the results are written to outputs/imagenet1k_zs_synset_single.json (other protocol files are not overwritten).
The supplementary reference protocol (plain names + single template) is in outputs/imagenet1k_ckpt_check.json.
"""
import os, sys, json
os.environ['HF_HUB_OFFLINE'] = '1'

# ---------- 1. parquet first (datasets must be imported before torch to avoid a pyarrow segfault) ----------
from glob import glob
from datasets import Dataset
PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
assert PARQ, 'no parquet shards under data/imagenet_hf/'
ds = Dataset.from_parquet(PARQ)
print('ImageNet-1K shards loaded:', len(ds), 'images', flush=True)

labs = ds['label']
uniq = sorted(set(labs))
if uniq == [-1]:
    sys.exit('!! all labels are -1: this is the ILSVRC test set. Use the validation shards.')

# full class names (keeping the synset phrase after the comma), i.e. the dataset's original label names
CLASS_NAMES_FULL = ds.features['label'].names
assert len(CLASS_NAMES_FULL) == 1000
print('first 3 class names (full):', CLASS_NAMES_FULL[:3], flush=True)

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
print('Results saved to outputs/imagenet1k_zs_synset_single.json')
