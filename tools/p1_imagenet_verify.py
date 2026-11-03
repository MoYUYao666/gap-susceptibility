"""ImageNet-1K 50k 复验（只读档案，不覆盖稿件引用文件）。

目的：在不重训 full-FT 的前提下，把稿件 Table 7 的 6 行在完整 50k val 上重跑一遍，
与 outputs/imagenet1k_zs_50k_plain.json 的档案值逐行比对（plain 单模板协议）。

- 只做 plain 协议（Table 7 用的就是它）；synset 协议不在此脚本内，避免 12 次评估。
- 结果写 outputs/imagenet1k_zs_50k_verify.json，绝不写 imagenet1k_zs_50k_plain.json。
- 每个配置跑完立即落盘，中断也保留已完成的行。
用法: python tools/p1_imagenet_verify.py
"""
import os, sys, json, time
os.environ['HF_HUB_OFFLINE'] = '1'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glob import glob
from datasets import Dataset
PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
ds = Dataset.from_parquet(PARQ)
print('50k 分片已加载:', len(ds), '张,', len(PARQ), '个分片', flush=True)
names_plain = [n.split(',')[0].strip() for n in ds.features['label'].names]

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


# 档案值（outputs/imagenet1k_zs_50k_plain.json，稿件 Table 7 引用）
ARCHIVE = {'frozen': 59.28, 'text_only_r8': 58.66, 'both_r8': 59.67,
           'full_ft_s42': 0.13, 'full_ft_s123': 4.09, 'full_ft_s999': 3.54}

CONFIGS = {
    'frozen': dict(ckpt=None),
    'text_only_r8': dict(ckpt='outputs/imagenet_zs/text_only_r8/best_checkpoint.pt', vision=False, text=True),
    'both_r8': dict(ckpt='outputs/imagenet_zs/both_r8/best_checkpoint.pt', vision=True, text=True),
    'full_ft_s42': dict(ckpt='outputs/imagenet_zs_rerun/full_ft/model_state_last.pt'),
    'full_ft_s123': dict(ckpt='outputs/imagenet_zs_rerun/full_ft_s123/model_state_last.pt'),
    'full_ft_s999': dict(ckpt='outputs/imagenet_zs_rerun/full_ft_s999/model_state_last.pt'),
}

OUT = 'outputs/imagenet1k_zs_50k_verify.json'
results, deltas = {}, {}
t0 = time.time()
for label, cfg in CONFIGS.items():
    print('== %s ==' % label, flush=True)
    ts = time.time()
    m = load_model(**cfg)
    v = round(zs_eval(m, names_plain), 2)
    results[label] = v
    deltas[label] = round(v - ARCHIVE[label], 2)
    print('  re-run: %.2f%%  archive: %.2f%%  delta: %+.2f' % (v, ARCHIVE[label], v - ARCHIVE[label]), flush=True)
    print('  (%.1f min)' % ((time.time() - ts) / 60), flush=True)
    del m
    torch.cuda.empty_cache()
    json.dump({'meta': {'n_images': len(ds), 'protocol': 'single template "a photo of a {}", 50k full val, plain class names',
                        'source': 'tools/p1_imagenet_verify.py', 'not_overwriting': 'outputs/imagenet1k_zs_50k_plain.json',
                        'elapsed_min': round((time.time() - t0) / 60, 1)},
               'archive': ARCHIVE, 'rerun': results, 'delta': deltas},
              open(OUT, 'w', encoding='utf-8'), indent=2)

n_exact = sum(1 for k in results if deltas[k] == 0.0)
print('', flush=True)
print('== 汇总 ==', flush=True)
for k in results:
    print('  %-14s rerun %6.2f  archive %6.2f  delta %+.2f' % (k, results[k], ARCHIVE[k], deltas[k]), flush=True)
print('  %d/%d 行逐位复现, 最大偏差 %.2f' % (n_exact, len(results), max(abs(d) for d in deltas.values())), flush=True)
ft = [results['full_ft_s42'], results['full_ft_s123'], results['full_ft_s999']]
print('  full-FT 三 seed 均值: %.2f%% (档案 %.2f%%)' % (sum(ft) / 3, sum(ARCHIVE[k] for k in ARCHIVE if k.startswith('full_ft')) / 3), flush=True)
print('saved', OUT, flush=True)
