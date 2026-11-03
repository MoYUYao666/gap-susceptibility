"""ImageNet-1K 全量 50k val 双协议零样本评测。
协议 A: plain 类名 + 单模板 'a photo of a {}'
协议 B: synset 全名 + 单模板
模型: frozen / text_only_r8 / both_r8（原 checkpoint）+ full FT 三 seed（重训）
结果存 outputs/imagenet1k_zs_50k_plain.json 与 outputs/imagenet1k_zs_50k_synset.json（不覆盖子集档案）。
"""
import os, sys, json
os.environ['HF_HUB_OFFLINE'] = '1'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glob import glob
from datasets import Dataset
PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
ds = Dataset.from_parquet(PARQ)
print('50k 分片已加载:', len(ds), '张,', len(PARQ), '个分片', flush=True)
names_full = ds.features['label'].names
names_plain = [n.split(',')[0].strip() for n in names_full]

import torch
from transformers import CLIPModel, CLIPProcessor
from src.lora import apply_lora_to_model

TEMPLATES = ['a photo of a {}']
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)


@torch.no_grad()
def zs_eval(m, class_names):
    texts = [t.format(c.replace('_', ' ')) for c in class_names for t in TEMPLATES]
    text_in = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = m.text_model(**text_in)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf = m.text_projection(pooled)
    tf = tf / tf.norm(dim=-1, keepdim=True)
    tf = tf.view(len(class_names), len(TEMPLATES), -1).mean(dim=1)
    tf = tf / tf.norm(dim=-1, keepdim=True)
    correct = total = 0
    for i in range(0, len(ds), 64):
        b = ds[i:i + 64]
        inp = processor(images=b['image'], return_tensors='pt').to('cuda')
        vout = m.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        imf = m.visual_projection(vpooled)
        imf = imf / imf.norm(dim=-1, keepdim=True)
        pred = (imf @ tf.T).argmax(-1).cpu().numpy()
        correct += sum(1 for p, y in zip(pred, b['label']) if p == y)
        total += len(b['label'])
        if total % 10000 == 0:
            print('  ... %d/%d' % (total, len(ds)), flush=True)
    return 100 * correct / total


def load_model(ckpt=None, vision=False, text=True):
    m = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
    if ckpt:
        if ckpt.endswith('.pt') and 'full_ft' in ckpt:
            m.load_state_dict(torch.load(ckpt, map_location='cpu', weights_only=False))
        else:
            m, lora_layers, _ = apply_lora_to_model(m, rank=8, alpha=16.0,
                                                    apply_to_vision=vision, apply_to_text=text)
            sd = torch.load(ckpt, map_location='cpu', weights_only=False)['lora_state_dict']
            with torch.no_grad():
                for k, w in sd.items():
                    lora_layers[k].lora_A.data.copy_(w['A'])
                    lora_layers[k].lora_B.data.copy_(w['B'])
    return m.cuda().eval()


CONFIGS = {
    'frozen': dict(ckpt=None),
    'text_only_r8': dict(ckpt='outputs/imagenet_zs/text_only_r8/best_checkpoint.pt', vision=False, text=True),
    'both_r8': dict(ckpt='outputs/imagenet_zs/both_r8/best_checkpoint.pt', vision=True, text=True),
    'full_ft_s42': dict(ckpt='outputs/imagenet_zs_rerun/full_ft/model_state_last.pt'),
    'full_ft_s123': dict(ckpt='outputs/imagenet_zs_rerun/full_ft_s123/model_state_last.pt'),
    'full_ft_s999': dict(ckpt='outputs/imagenet_zs_rerun/full_ft_s999/model_state_last.pt'),
}

out_plain, out_synset = {}, {}
for label, cfg in CONFIGS.items():
    print('== %s ==' % label, flush=True)
    m = load_model(**cfg)
    out_plain[label] = round(zs_eval(m, names_plain), 2)
    print('  plain:  %.2f%%' % out_plain[label], flush=True)
    out_synset[label] = round(zs_eval(m, names_full), 2)
    print('  synset: %.2f%%' % out_synset[label], flush=True)
    del m
    torch.cuda.empty_cache()

meta = {'n_images': len(ds), 'shards': PARQ, 'protocol': 'single template "a photo of a {}", 50k full val'}
json.dump({'meta': meta, 'results_plain': out_plain},
          open('outputs/imagenet1k_zs_50k_plain.json', 'w', encoding='utf-8'), indent=2)
json.dump({'meta': meta, 'results_synset': out_synset},
          open('outputs/imagenet1k_zs_50k_synset.json', 'w', encoding='utf-8'), indent=2)
print('saved 50k results. plain:', out_plain, flush=True)
print('saved 50k results. synset:', out_synset, flush=True)
