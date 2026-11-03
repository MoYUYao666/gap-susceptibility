"""决定性验证：ImageNet-1K (val 子集, 4 shards=14288 张) 上的 zero-shot。
若 frozen ≈ 60.72 且 text_only/both 下降（≈59.06/56.14），则论文数据确为 ImageNet-1K。
协议与 TinyImageNet 验证一致：3 模板平均；类名取 synset 主名（逗号前）。"""
import os, sys, json
os.environ['HF_HUB_OFFLINE'] = '1'

# ---------- 1. 先 parquet（datasets 必须在 torch 前导入）----------
from glob import glob
from datasets import Dataset
PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
assert PARQ, 'data/imagenet_hf/ 下没有 parquet 分片'
ds = Dataset.from_parquet(PARQ)
print('ImageNet-1K 分片已加载:', len(ds), '张, 来自', len(PARQ), '个分片', flush=True)

# 标签守卫：ILSVRC test 集无标签（-1），必须用 validation 分片
labs = ds['label']
uniq = sorted(set(labs))
print('覆盖类数:', len(uniq), '| 标签范围:', min(uniq), '-', max(uniq), flush=True)
if uniq == [-1]:
    sys.exit('!! 标签全为 -1：这是 ILSVRC test 集（无标签，100k 张）。请下载 validation 分片（50k 张，带标签）替换 data/imagenet_hf/ 内容')

# 类名：ClassLabel names（words 格式），取逗号前主名
names = ds.features['label'].names
CLASS_NAMES = [n.split(',')[0].strip() for n in names]
assert len(CLASS_NAMES) == 1000
json.dump(CLASS_NAMES, open('data/imagenet_1k_names.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('1000 类名已存 data/imagenet_1k_names.json | 首 5:', CLASS_NAMES[:5], flush=True)

# ---------- 2. CLIP + LoRA（datasets 之后）----------
print('加载 CLIP ViT-B/32 ...', flush=True)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from transformers import CLIPModel, CLIPProcessor
from src.lora import apply_lora_to_model

processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)

if len(sys.argv) > 1 and sys.argv[1] == 'single':
    templates = ['a photo of a {}']  # zeroshot_extra.py 的唯一模板
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
    'frozen (论文 60.72)':   dict(ckpt=None),
    'text_only_r8 (论文 59.06)': dict(ckpt='outputs/imagenet_zs/text_only_r8/best_checkpoint.pt',
                                       vision=False, text=True),
    'both_r8 (论文 56.14)':  dict(ckpt='outputs/imagenet_zs/both_r8/best_checkpoint.pt',
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
        assert not missing and not extra, 'LoRA 层不匹配: missing=%s extra=%s' % (
            list(missing)[:3], list(extra)[:3])
        with torch.no_grad():
            for k, w in sd.items():
                lora_layers[k].lora_A.data.copy_(w['A'])
                lora_layers[k].lora_B.data.copy_(w['B'])
        print('%s: LoRA 注入 %d 层' % (label, len(sd)), flush=True)
    acc = eval_zs(m)
    print('%s => ImageNet-1K zero-shot top-1: %.2f%%' % (label, acc), flush=True)
    saved[label.split(' (')[0]] = round(acc, 2)

os.makedirs('outputs', exist_ok=True)
out = {'dataset': 'ImageNet-1K val (HF ILSVRC/imagenet-1k)',
       'protocol': {'templates': templates, 'n_images': len(ds),
                    'class_names': 'data/imagenet_1k_names.json', 'shards': PARQ},
       'results': saved, 'paper_values': {'frozen': 60.72, 'text_only': 59.06, 'both': 56.14}}
_json.dump(out, open('outputs/imagenet1k_ckpt_check.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('结果已存 outputs/imagenet1k_ckpt_check.json')
print('\n对照论文表值: 60.72 / 59.06 / 56.14 / 7.38')
