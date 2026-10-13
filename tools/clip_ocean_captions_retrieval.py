"""Experiment D: BLIP-generated marine image-text pairs → caption retrieval probe (tests whether "retrieval tracks CG" also holds for natural text).
1) BLIP-base generates a natural-sentence caption for 8 images per class of the fish-67 subset (one per image, varying per image);
2) retrieval protocol (same convention as A2): image side λ∈{0,0.5,1,2}(+ text side λ=1); models bioclip/oceanclip/openclip_tf;
   metrics: i2t R@1 / t2i R@1 / mean / CG; criterion: does R@1 follow CG (near zero at λ=1, rebound at λ=2) or vary monotonically with τ.
Output: data/marine_captions/ + outputs/ocean_waterbench.json
"""
import os, sys, json, io, importlib.util
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from datasets import load_dataset
from transformers import BlipProcessor, BlipForConditionalGeneration
import open_clip

spec = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
ocm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocm)

OUT = 'outputs/ocean_waterbench.json'
CAP_DIR = 'data/marine_captions'
PER_CLASS = 8
LAMS = [0.0, 0.5, 1.0, 2.0]


def load_subset():
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    sub = json.load(open('outputs/ocean_subset.json', encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    pick = []
    for c in range(len(classes)):
        cand = np.where(labels == c)[0]
        pick.extend(cand[:PER_CLASS])
    return ds, classes, [int(idx[i]) for i in pick]


def make_captions(ds, idx):
    os.makedirs(CAP_DIR, exist_ok=True)
    cap_json = os.path.join(CAP_DIR, 'captions.json')
    if os.path.exists(cap_json):
        data = json.load(open(cap_json, encoding='utf-8'))
        print('captions cached: %d' % len(data['captions']), flush=True)
        return data
    proc = BlipProcessor.from_pretrained('models/blip-caption-base', local_files_only=True)
    model = BlipForConditionalGeneration.from_pretrained('models/blip-caption-base', local_files_only=True).cuda().eval()
    caps = []
    for k, j in enumerate(idx):
        b = ds[j]['file_name']
        im = (Image.open(io.BytesIO(b['bytes'])).convert('RGB')
              if isinstance(b, dict) and b.get('bytes')
              else Image.open(b['path']).convert('RGB') if isinstance(b, dict) else b.convert('RGB'))
        im.save(os.path.join(CAP_DIR, '%04d.jpg' % k))
        inp = proc(images=im, return_tensors='pt').to('cuda')
        with torch.no_grad():
            out = model.generate(**inp, max_new_tokens=24)
        caps.append(proc.batch_decode(out, skip_special_tokens=True)[0].strip())
        if k % 100 == 0:
            print('  captioned %d/%d' % (k, len(idx)), flush=True)
    json.dump({'captions': caps}, open(cap_json, 'w', encoding='utf-8'), indent=1)
    return {'captions': caps}


def enc_text(tag, m, caps):
    if tag == 'openclip_tf':
        proc = m['proc']
        ti = proc(text=caps, return_tensors='pt', padding=True).to('cuda')
        with torch.no_grad():
            out = m['model'].text_model(**ti)
            pooled = out[1] if isinstance(out, tuple) else out.pooler_output
            return F.normalize(m['model'].text_projection(pooled), dim=-1)
    with torch.no_grad():
        tok = open_clip.get_tokenizer('ViT-B-16')
        return F.normalize(m['model'].encode_text(tok(caps).to('cuda')), dim=-1)


def enc_imgs(tag, m, idx_list):
    out = []
    for i in range(0, len(idx_list), 32):
        imgs = [Image.open(os.path.join(CAP_DIR, '%04d.jpg' % j)) for j in idx_list[i:i + 32]]
        if tag == 'openclip_tf':
            inp = m['proc'](images=imgs, return_tensors='pt').to('cuda')
            with torch.no_grad():
                vout = m['model'].vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                f = m['model'].visual_projection(vp)
            out.append(F.normalize(f, dim=-1))
        else:
            xs = torch.stack([m['pre'](im) for im in imgs]).to('cuda')
            with torch.no_grad():
                out.append(F.normalize(m['model'].encode_image(xs), dim=-1))
    return torch.cat(out)


def main():
    ds, classes, idx = load_subset()
    data = make_captions(ds, idx)
    caps = data['captions']
    n = len(caps)
    uniq = len(set(caps))
    avg_len = float(np.mean([len(c.split()) for c in caps]))
    print('pairs: %d | unique captions: %d | avg words: %.1f' % (n, uniq, avg_len), flush=True)
    res = {'meta': {'source': 'BLIP-base captions (per image, machine-generated)', 'n_pairs': n,
                    'unique_captions': uniq, 'avg_words': avg_len, 'per_class': PER_CLASS, 'n_idx': len(idx)}}
    for tag in ['bioclip', 'oceanclip', 'openclip_tf']:
        print('== %s ==' % tag, flush=True)
        if tag == 'openclip_tf':
            from transformers import CLIPModel, CLIPProcessor
            m = {'model': CLIPModel.from_pretrained('models/openclip', local_files_only=True).cuda().eval(),
                 'proc': CLIPProcessor.from_pretrained('models/openclip', local_files_only=True)}
        else:
            mm, pp = ocm.load_openclip(tag)
            m = {'model': mm, 'pre': pp}
        tf = enc_text(tag, m, caps)
        base = enc_imgs(tag, m, list(range(n)))
        gap = tf.mean(0) - base.mean(0)
        gnorm = gap.norm().item()
        dH = gap / gnorm
        rows = []
        for l in LAMS:
            with torch.no_grad():
                sh = F.normalize(base + l * gnorm * dH, dim=-1)
            S = (sh @ tf.T).cpu().numpy()
            i2t = float((S.argmax(1) == np.arange(n)).mean())
            t2i = float((S.argmax(0) == np.arange(n)).mean())
            cg = (sh.mean(0) - tf.mean(0)).norm().item()
            rows.append({'lambda': l, 'i2t': round(i2t, 4), 't2i': round(t2i, 4),
                         'R1': round((i2t + t2i) / 2, 4), 'CG': round(cg, 4)})
            print('  I λ=%.1f R1=%.4f (i2t %.4f/t2i %.4f) CG=%.4f' % (l, (i2t + t2i) / 2, i2t, t2i, cg), flush=True)
        with torch.no_grad():
            tf2 = F.normalize(tf - 1.0 * gnorm * dH, dim=-1)
        S2 = (base @ tf2.T).cpu().numpy()
        i2t = float((S2.argmax(1) == np.arange(n)).mean())
        t2i = float((S2.argmax(0) == np.arange(n)).mean())
        cg = (base.mean(0) - tf2.mean(0)).norm().item()
        rows.append({'lambda': 'text1.0', 'i2t': round(i2t, 4), 't2i': round(t2i, 4),
                     'R1': round((i2t + t2i) / 2, 4), 'CG': round(cg, 4)})
        print('  T λ=1   R1=%.4f CG=%.4f' % ((i2t + t2i) / 2, cg), flush=True)
        res[tag] = {'gap_norm': round(gnorm, 4), 'rows': rows}
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        del m
        torch.cuda.empty_cache()
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
