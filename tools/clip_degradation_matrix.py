"""A2 扩展 E3: 退化鲁棒性矩阵 —— 域(marine/sonar/imagenet) × 退化类型 × 强度档。
输出: outputs/degradation_matrix.json
运行: conda run -n pytorch python tools/clip_degradation_matrix.py
"""
import os, sys, json, io
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageFilter
from scipy import stats
from datasets import load_dataset
from transformers import CLIPModel, CLIPProcessor
import importlib.util

spec = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
ocm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocm)

OUT = 'outputs/degradation_matrix.json'
TEMPLATE = 'a photo of a {}'
MDIR = 'models/clip-vit-base-patch32'
SONAR_CLASSES = ['big propeller', 'cylinder', 'fishing net', 'floats', 'iron pipeline',
                 'small propeller', 'soft pipeline', 'tire']
SONAR_DIR = ['big_propeller', 'cylinder', 'fishing_net', 'floats', 'iron_pipeline',
             'small_propeller', 'soft_pipeline', 'tire']


def sonar_deg(im, kind, arg):
    if kind == 'speckle':
        a = np.asarray(im).astype(np.float32) / 255.0
        noise = np.random.default_rng(42).normal(0, arg, a.shape)
        return Image.fromarray((np.clip(a + a * noise, 0, 1) * 255).astype(np.uint8))
    if kind == 'blur':
        return im.filter(ImageFilter.GaussianBlur(arg))
    if kind == 'shadow':
        a = np.asarray(im).astype(np.float32)
        a[:, int(a.shape[1] * 0.55):] *= 0.45
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return im


def probe(tag, enc_f, tf, imgs, labels, degs, res):
    f0 = enc_f(imgs)
    gap = tf.mean(0) - f0.mean(0)
    gnorm = gap.norm().item()
    dH = (gap / gnorm).cpu().numpy()
    m_c = dH @ tf.cpu().numpy().T
    S0 = (f0 @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    top1_0 = float((S0.argmax(1) == labels).mean() * 100)
    rows = []
    for dname, kind, arg in degs:
        fd = enc_f([sonar_deg(im, kind, arg) for im in imgs])
        delta = (fd - f0).cpu().numpy()
        lam_eff = float((delta @ dH).mean() / gnorm)
        Sd = (fd @ tf.T).cpu().numpy()
        top1 = float((Sd.argmax(1) == labels).mean() * 100)
        taus = []
        for i in range(len(S0)):
            r1, r2 = S0[i][topk5[i]], Sd[i][topk5[i]]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        rows.append({'degrade': dname, 'lam_eff': round(lam_eff, 4),
                     'tau_meas': round(float(np.mean(taus)), 4), 'top1': round(top1, 3),
                     'rel_top1_loss': round(1.0 - top1 / top1_0, 4)})
        print('  %s %-14s tau=%.4f top1=%.2f lam_eff=%+.4f' %
              (tag, dname, np.mean(taus), top1, lam_eff), flush=True)
    res[tag] = {'n': len(imgs), 'top1_0': round(top1_0, 3),
                'sigma_m': round(float(np.std(m_c)), 4), 'rows': rows}
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)


def main():
    res = {'meta': {'grid': 'domain x degradation x intensity'}}
    # ---------- 1) sonar: frozen CLIP (650) ----------
    man = []
    for c, d in zip(SONAR_CLASSES, SONAR_DIR):
        pth = os.path.join('data/NKSID/NKSID', d)
        if not os.path.isdir(pth):
            pth = 'data/NKSID/NKSID'
        fs = sorted(f for f in os.listdir(pth) if f.lower().endswith(('.jpg', '.png')))[:90]
        man.extend((os.path.join(pth, f), c) for f in fs)
    sm = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().eval()
    sp = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
    sc_txt = sp(text=[TEMPLATE.format(c) for c in SONAR_CLASSES], return_tensors='pt', padding=True).to('cuda')
    with torch.no_grad():
        out = sm.text_model(**sc_txt)
        pooled = out[1] if isinstance(out, tuple) else out.pooler_output
        stf = F.normalize(sm.text_projection(pooled), dim=-1)

    def enc_s(imgs):
        out = []
        with torch.no_grad():
            for i in range(0, len(imgs), 48):
                inp = sp(images=imgs[i:i + 48], return_tensors='pt').to('cuda')
                vout = sm.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                out.append(F.normalize(sm.visual_projection(vp), dim=-1))
        return torch.cat(out)

    simgs = [Image.open(fp).convert('RGB') for fp, _ in man]
    slabels = np.array([SONAR_CLASSES.index(c) for _, c in man])
    print('== sonar frozen ==', flush=True)
    probe('sonar_frozen', enc_s, stf, simgs, slabels,
          [('speckle_p10', 'speckle', 0.10), ('speckle_p20', 'speckle', 0.20),
           ('speckle_p40', 'speckle', 0.40), ('blur_r1', 'blur', 1), ('blur_r2', 'blur', 2),
           ('blur_r4', 'blur', 4), ('shadow_strip', 'shadow', None)], res)
    del sm
    torch.cuda.empty_cache()
    # ---------- 2) marine: bioclip (fish-67) ----------
    ds = ocm.load_ds()
    sub = json.load(open('outputs/ocean_subset.json', encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    labels_m = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    texts_m = [TEMPLATE.format(c) for c in classes]
    imgs_m = []
    for j in idx:
        b = ds[j]['file_name']
        imgs_m.append(Image.open(io.BytesIO(b['bytes'])).convert('RGB')
                      if isinstance(b, dict) and b.get('bytes')
                      else Image.open(b['path']).convert('RGB') if isinstance(b, dict) else b.convert('RGB'))
    mb, pre_b = ocm.load_openclip('bioclip')
    import open_clip as ocl
    tok = ocl.get_tokenizer('ViT-B-16')
    with torch.no_grad():
        mtf = F.normalize(mb.encode_text(tok(texts_m).to('cuda')), dim=-1)

    def enc_b(imgs):
        out = []
        with torch.no_grad():
            for i in range(0, len(imgs), 48):
                xs = torch.stack([pre_b(im) for im in imgs[i:i + 48]]).to('cuda')
                out.append(F.normalize(mb.encode_image(xs), dim=-1))
        return torch.cat(out)
    print('== marine bioclip ==', flush=True)
    probe('marine_bioclip', enc_b, mtf, imgs_m, labels_m,
          [('haze_t0.6', 'blur', 2), ('haze_t0.3', 'blur', 5), ('shadow_strip', 'shadow', None),
           ('speckle_p20', 'speckle', 0.20), ('speckle_p40', 'speckle', 0.40)], res)
    del mb
    torch.cuda.empty_cache()
    # ---------- 3) imagenet-5k: frozen CLIP ----------
    ds_i = load_dataset('parquet', data_files=sorted(
        os.path.join('data/imagenet_hf', f) for f in os.listdir('data/imagenet_hf')
        if f.endswith('.parquet')), split='train')
    names_i = json.load(open('data/imagenet_1k_names.json', encoding='utf-8'))
    rng = np.random.RandomState(42)
    sel_i = [int(i) for i in rng.choice(len(ds_i), size=5000, replace=False)]
    imgs_i, labels_i = [], []
    for i in sel_i:
        r = ds_i[i]
        imgs_i.append(r['image'].convert('RGB') if hasattr(r['image'], 'convert') else r['image'])
        labels_i.append(int(r['label']))
    labels_i = np.array(labels_i)
    im = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().eval()
    ip = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
    ic_txt = ip(text=[TEMPLATE.format(c) for c in names_i], return_tensors='pt', padding=True).to('cuda')
    with torch.no_grad():
        out = im.text_model(**ic_txt)
        pooled = out[1] if isinstance(out, tuple) else out.pooler_output
        itf = F.normalize(im.text_projection(pooled), dim=-1)

    def enc_i(imgs):
        out = []
        with torch.no_grad():
            for i in range(0, len(imgs), 48):
                inp = ip(images=imgs[i:i + 48], return_tensors='pt').to('cuda')
                vout = im.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                out.append(F.normalize(im.visual_projection(vp), dim=-1))
        return torch.cat(out)
    print('== imagenet frozen ==', flush=True)
    probe('imagenet_clip', enc_i, itf, imgs_i, labels_i,
          [('haze_t0.6', 'blur', 2), ('haze_t0.3', 'blur', 5), ('shadow_strip', 'shadow', None),
           ('speckle_p20', 'speckle', 0.20), ('speckle_p40', 'speckle', 0.40)], res)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
