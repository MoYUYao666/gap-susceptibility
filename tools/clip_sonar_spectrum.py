"""A3 enhancement ①: sonar-task sensitivity spectrum (corresponds to A2-B: NCC / top-1 / R@1 on the same λ grid).
Models: clip_frozen / sonar_ft (loads sonar_clip_ft.pt) / clip_flickrft (loads ocean_clip_flickrft.pt + sonar probe)
Output: outputs/sonar_spectrum.json
"""
import os, sys, json
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

TEMPLATE = 'a photo of a {}'
MDIR = 'models/clip-vit-base-patch32'
IMG_ROOT = 'data/NKSID/NKSID'
OUT = 'outputs/sonar_spectrum.json'
CLASSES = ['big propeller', 'cylinder', 'fishing net', 'floats', 'iron pipeline',
           'small propeller', 'soft pipeline', 'tire']
CLASS_DIR = ['big_propeller', 'cylinder', 'fishing_net', 'floats', 'iron_pipeline',
             'small_propeller', 'soft_pipeline', 'tire']
CAP = 90
LAMS = [0.0, 0.5, 1.0, 2.0]
CKPTS = {'clip_frozen': None, 'sonar_ft': 'outputs/sonar_clip_ft.pt',
         'clip_flickrft': 'outputs/ocean_clip_flickrft.pt'}


def manifest():
    m = []
    for c, d in zip(CLASSES, CLASS_DIR):
        p = os.path.join(IMG_ROOT, d)
        if not os.path.isdir(p):
            p = IMG_ROOT
        fs = sorted(f for f in os.listdir(p) if f.lower().endswith(('.jpg', '.png')))[:CAP]
        m.extend((os.path.join(p, f), c) for f in fs)
    return m


def enc(m, p, imgs):
    out = []
    with torch.no_grad():
        for i in range(0, len(imgs), 32):
            inp = p(images=imgs[i:i + 32], return_tensors='pt').to('cuda')
            vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
            vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            out.append(F.normalize(m.visual_projection(vp), dim=-1))
    return torch.cat(out)


def main():
    man = manifest()
    labels = np.array([CLASSES.index(c) for _, c in man])
    texts = [TEMPLATE.format(c) for c in CLASSES]
    imgs = [Image.open(fp).convert('RGB') for fp, _ in man]
    res = {}
    for tag, ck in CKPTS.items():
        print('== %s ==' % tag, flush=True)
        m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda()
        if ck:
            m.load_state_dict(torch.load(ck, map_location='cpu'))
        m = m.cuda().eval()
        p = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
        ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
        with torch.no_grad():
            out = m.text_model(**ti)
            pooled = out[1] if isinstance(out, tuple) else out.pooler_output
            tf = F.normalize(m.text_projection(pooled), dim=-1)
        base = enc(m, p, imgs)
        gap = tf.mean(0) - base.mean(0)
        gnorm = gap.norm().item()
        dH = gap / gnorm
        centroids = torch.zeros(len(CLASSES), base.shape[1], device='cuda')
        for c in range(len(CLASSES)):
            cc = base[labels == c]
            centroids[c] = F.normalize(cc.mean(0), dim=-1)
        rows = []
        for l in LAMS:
            with torch.no_grad():
                sh = F.normalize(base + l * gnorm * dH, dim=-1)
            S = (sh @ tf.T).cpu().numpy()
            top1 = float((S.argmax(1) == labels).mean() * 100)
            Sn = (sh @ centroids.T).cpu().numpy()
            ncc = float((Sn.argmax(1) == labels).mean() * 100)
            i2t = float((S.argmax(1) == labels).mean())
            t2i = float(np.mean([labels[int(S[:, c].argmax())] == c for c in range(len(CLASSES))]))
            cg = (sh.mean(0) - tf.mean(0)).norm().item()
            rows.append({'lambda': l, 'NCC': round(ncc, 3), 'top1': round(top1, 3),
                         'R1': round((i2t + t2i) / 2, 4), 'CG': round(cg, 4)})
            print('  λ=%.1f NCC=%.2f top1=%.2f R1=%.4f CG=%.4f' % (l, ncc, top1, (i2t + t2i) / 2, cg), flush=True)
        res[tag] = {'gap_norm': round(gnorm, 4), 'rows': rows}
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        del m
        torch.cuda.empty_cache()
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
