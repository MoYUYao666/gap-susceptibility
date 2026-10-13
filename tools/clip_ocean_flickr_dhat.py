"""Flickr d̂ consistency check: estimate d̂ with Flickr30k (terrestrial natural pairs, same protocol as A1),
rerun the λ∈{0.5,1.0} image-side/text-side surgery on the marine subset, and test whether finding ③ (asymmetry vanishes) is an artifact of the d̂ protocol.
Output: outputs/ocean_flickr_dhat.json
"""
import os, sys, json, io
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from datasets import load_dataset
import open_clip

TEMPLATE = 'a photo of a {}'
SUB = 'outputs/ocean_subset.json'
OUT = 'outputs/ocean_flickr_dhat.json'
LAMS = [0.5, 1.0]


def load_base(tag):
    if tag == 'bioclip':
        m, _, p = open_clip.create_model_and_transforms(
            'ViT-B-16', pretrained='models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin', device='cuda')
    else:
        ck = torch.load('models/oceanclip-0.15b/oceanclip-bio/epoch_50.pt', map_location='cpu')
        m, _, p = open_clip.create_model_and_transforms(
            'ViT-B-16', pretrained='models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin', device='cuda')
        m.load_state_dict(ck['state_dict'], strict=False)
    m.eval()
    return m, p


def flickr_pairs():
    import json as _j
    img_dir = os.path.join('flickr30k', 'flickr30k-images')
    data = _j.load(open(os.path.join('flickr30k', 'flickr30k.json'), encoding='utf-8'))
    out = []
    for it in data:
        fn = it['image']
        if os.path.exists(os.path.join(img_dir, fn)) and it.get('captions'):
            out.append((os.path.join(img_dir, fn), it['captions'][0]))
        if len(out) >= 1000:
            break
    return out


def main():
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    sub = json.load(open(SUB, encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    texts = [TEMPLATE.format(c) for c in classes]
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    tok = open_clip.get_tokenizer('ViT-B-16')
    pairs = flickr_pairs()
    res = {}
    for tag in ['bioclip', 'oceanclip']:
        m, pre = load_base(tag)
        # Flickr d̂ (A1 protocol: centroid difference of natural image-text pairs)
        fi, ft = [], []
        with torch.no_grad():
            for i in range(0, len(pairs), 64):
                xs = torch.stack([pre(Image.open(p)) for p, _ in pairs[i:i + 64]]).to('cuda')
                tids = tok([c for _, c in pairs[i:i + 64]]).to('cuda')
                fi.append(F.normalize(m.encode_image(xs), dim=-1))
                ft.append(F.normalize(m.encode_text(tids), dim=-1))
        fi = torch.cat(fi)
        ft = torch.cat(ft)
        gap = ft.mean(0) - fi.mean(0)
        gnorm = gap.norm().item()
        dH = gap / gnorm
        # marine features
        with torch.no_grad():
            tf = F.normalize(m.encode_text(tok(texts).to('cuda')), dim=-1)
            feats = []
            for i in range(0, len(idx), 32):
                b = ds[idx[i:i + 32]]['file_name']
                imgs = []
                for x in b:
                    imgs.append(Image.open(io.BytesIO(x['bytes'])) if isinstance(x, dict) and x.get('bytes')
                                else Image.open(x['path']) if isinstance(x, dict) else x)
                xs = torch.stack([pre(im) for im in imgs]).to('cuda')
                with torch.no_grad():
                    feats.append(F.normalize(m.encode_image(xs), dim=-1))
            base = torch.cat(feats)
        S = (base @ tf.T).cpu().numpy()
        topk5 = np.argsort(-S, axis=1)[:, :5]
        rows = {'flickr_gap_norm': round(gnorm, 4)}
        def eval_shift(delta_img=None, delta_txt=None):
            with torch.no_grad():
                b2 = F.normalize(base + delta_img, dim=-1) if delta_img is not None else base
                t2 = F.normalize(tf + delta_txt, dim=-1) if delta_txt is not None else tf
            S2 = (b2 @ t2.T).cpu().numpy()
            top1 = float((S2.argmax(1) == labels).mean() * 100)
            taus = []
            for i in range(len(S)):
                r1, r2 = S[i][topk5[i]], S2[i][topk5[i]]
                if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                    continue
                t, _ = stats.kendalltau(r1, r2)
                if np.isfinite(t):
                    taus.append(t)
            return top1, float(np.mean(taus))
        for l in LAMS:
            d_img = l * gnorm * dH
            t1, tau = eval_shift(delta_img=d_img)
            rows['img_%s' % l] = {'top1': round(t1, 3), 'tau': round(tau, 4)}
            t1, tau = eval_shift(delta_txt=-l * gnorm * dH)
            rows['txt_%s' % l] = {'top1': round(t1, 3), 'tau': round(tau, 4)}
            print('%s λ=%s: img(tau=%.4f top1=%.2f) txt(tau=%.4f top1=%.2f)' %
                  (tag, l, rows['img_%s' % l]['tau'], rows['img_%s' % l]['top1'],
                   rows['txt_%s' % l]['tau'], rows['txt_%s' % l]['top1']), flush=True)
        res[tag] = rows
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        del m
        torch.cuda.empty_cache()
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
