"""判别实验 A-①: 无微调对照——openclip / siglip 在海洋类集上的 σ_m。
同一协议（海洋 67 类子集 + 类文本质心 d̂）测量 m_c 分布，检验 0.0078（oceanclip）是
"预训练族差异"还是"微调效应"。
输出: outputs/ocean_sigma_other.json
"""
import os, sys, json, io
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from datasets import load_dataset
from transformers import CLIPModel, CLIPProcessor, SiglipModel, SiglipProcessor

TEMPLATE = 'a photo of a {}'
SUB = 'outputs/ocean_subset.json'
OUT = 'outputs/ocean_sigma_other.json'


def enc(m, p, tag, texts, ds, idx):
    if tag == 'siglip':
        ti = p(text=texts, return_tensors='pt', padding='max_length', max_length=64).to('cuda')
        with torch.no_grad():
            tf = m.text_model(**ti).pooler_output
        tf = F.normalize(tf, dim=-1)
    else:
        ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
        with torch.no_grad():
            out = m.text_model(**ti)
            pooled = out[1] if isinstance(out, tuple) else out.pooler_output
            tf = F.normalize(m.text_projection(pooled), dim=-1)
    feats = []
    with torch.no_grad():
        for i in range(0, len(idx), 32):
            b = ds[idx[i:i + 32]]['file_name']
            imgs = []
            for x in b:
                imgs.append(Image.open(io.BytesIO(x['bytes'])) if isinstance(x, dict) and x.get('bytes')
                            else Image.open(x['path']) if isinstance(x, dict) else x)
            inp = p(images=imgs, return_tensors='pt').to('cuda')
            if tag == 'siglip':
                vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                f = m.visual_projection(vp) if hasattr(m, 'visual_projection') else vp
            else:
                vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                f = m.visual_projection(vp) if hasattr(m, 'visual_projection') else vp
            feats.append(F.normalize(f, dim=-1))
    return tf, torch.cat(feats)


def main():
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    sub = json.load(open(SUB, encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    texts = [TEMPLATE.format(c) for c in classes]
    res = {}
    for tag, mdir in [('openclip_tf', 'models/openclip'), ('siglip', 'models/siglip-base-patch16-224')]:
        print('== %s ==' % tag, flush=True)
        if tag == 'siglip':
            m = SiglipModel.from_pretrained(mdir, local_files_only=True).cuda().eval()
            p = SiglipProcessor.from_pretrained(mdir, local_files_only=True)
        else:
            m = CLIPModel.from_pretrained(mdir, local_files_only=True).cuda().eval()
            p = CLIPProcessor.from_pretrained(mdir, local_files_only=True)
        tf, base = enc(m, p, tag, texts, ds, idx)
        gap = tf.mean(0) - base.mean(0)
        gnorm = gap.norm().item()
        dH = gap / gnorm
        m_c = (dH @ tf.T).cpu().numpy()
        res[tag] = {'gap_norm': round(gnorm, 4), 'mean_m': round(float(np.mean(m_c)), 4),
                    'sigma_m': round(float(np.std(m_c)), 4),
                    'min_m': round(float(m_c.min()), 4), 'max_m': round(float(m_c.max()), 4)}
        print('  %s: gap=%.4f mean_m=%.4f sigma_m=%.4f' % (tag, gnorm, res[tag]['mean_m'], res[tag]['sigma_m']), flush=True)
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        del m
        torch.cuda.empty_cache()
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
