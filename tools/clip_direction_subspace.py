"""A2 extension E4: direction-resolution operator v2 — k=1/2/3 direction subspace projection.
On the marine(bioclip)+sonar(frozen) degraded set: direction sources = mean direction set of the degraded pairs (first k),
per image α_i∈R^k, reversal condition Σ_k α_ik (e_k·t_j - e_k·t_i) > d_ij.
Output: outputs/direction_subspace.json
Run: conda run -n pytorch python tools/clip_direction_subspace.py
"""
import os, sys, json, io
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))

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

OUT = 'outputs/direction_subspace.json'
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


def sub_pred(enc_f, tf, imgs, degs, res_tag):
    f0 = enc_f(imgs)
    gap = tf.mean(0) - f0.mean(0)
    gnorm = gap.norm().item()
    dH = (gap / gnorm).cpu().numpy()
    m_c = dH @ tf.cpu().numpy().T
    S0 = (f0 @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    upM = np.triu(np.ones((5, 5)), k=1).astype(bool)
    tf_np = tf.cpu().numpy()
    rows = []
    for dname, kind, arg in degs:
        fd = enc_f([sonar_deg(im, kind, arg) for im in imgs])
        delta = (fd - f0).cpu().numpy()
        Sd = (fd @ tf.T).cpu().numpy()
        tm = float(np.mean([stats.kendalltau(S0[i][topk5[i]], Sd[i][topk5[i]])[0]
                            for i in range(len(S0))
                            if np.std(S0[i][topk5[i]]) > 1e-12 and np.std(Sd[i][topk5[i]]) > 1e-12]))
        # direction subspace: mean direction set shared across degradations (Gram-Schmidt orthogonalization)
        e1 = delta.mean(0); e1 = e1 / (np.linalg.norm(e1) + 1e-12)
        # k=2/3: augmented with the top k-1 PCA components
        X = delta - delta.mean(0)
        _, _, vh = np.linalg.svd(X, full_matrices=False)
        dirs = [e1]
        for d in vh[:4]:
            w = d - e1 * (d @ e1)
            w = w / (np.linalg.norm(w) + 1e-12)
            if np.linalg.norm(w) > 0.1:
                dirs.append(w)
        res = {'tau_meas': round(tm, 4)}
        d_up = [(S0[i][topk5[i]][:, None] - S0[i][topk5[i]][None, :])[upM] for i in range(len(S0))]
        tfn = tf_np
        for k in [1, 2, 3, 4, 5]:
            E = np.stack(dirs[:k])
            alpha = delta @ E.T  # n x k
            proj = E @ tfn.T  # k x n_classes
            # per image: class-bias difference matrix for each direction e_kk (10 pairs)
            dm_full = np.zeros((len(S0), k, d_up[0].shape[0]))
            for i in range(len(S0)):
                pk = proj[:, topk5[i]]
                dm_full[i] = np.stack([(-(pk[kk][:, None] - pk[kk][None, :]))[upM] for kk in range(k)])
            preds = []
            for i in range(len(S0)):
                inv = ((alpha[i][:, None] * dm_full[i]).sum(0) > d_up[i]).sum()
                preds.append(1.0 - 2 * inv / 10.0)
            res['pred_k%d' % k] = round(float(np.mean(preds)), 4)
            res['err_k%d' % k] = round(abs(tm - float(np.mean(preds))), 4)
        rows.append({'degrade': dname, **res})
        print('  %-14s tau=%.4f err_k1=%.4f err_k2=%.4f err_k3=%.4f err_k4=%.4f err_k5=%.4f' %
              (dname, tm, rows[-1]['err_k1'], rows[-1]['err_k2'], rows[-1]['err_k3'],
               rows[-1]['err_k4'], rows[-1]['err_k5']), flush=True)
    return rows


def main():
    res = {}
    # marine bioclip
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
    res['marine_bioclip'] = sub_pred(enc_b, mtf, imgs_m,
                                     [('haze_t0.6', 'blur', 2), ('haze_t0.3', 'blur', 5),
                                      ('shadow_strip', 'shadow', None), ('speckle_p20', 'speckle', 0.20)],
                                     'marine')
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    del mb
    torch.cuda.empty_cache()
    # sonar frozen
    man = []
    for c, d in zip(SONAR_CLASSES, SONAR_DIR):
        pth = os.path.join('data/NKSID/NKSID', d)
        if not os.path.isdir(pth):
            pth = 'data/NKSID/NKSID'
        fs = sorted(f for f in os.listdir(pth) if f.lower().endswith(('.jpg', '.png')))[:90]
        man.extend((os.path.join(pth, f), c) for f in fs)
    sm = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().eval()
    sp = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
    ti = sp(text=[TEMPLATE.format(c) for c in SONAR_CLASSES], return_tensors='pt', padding=True).to('cuda')
    with torch.no_grad():
        out = sm.text_model(**ti)
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
    res['sonar_frozen'] = sub_pred(enc_s, stf, simgs,
                                   [('speckle_p20', 'speckle', 0.20), ('speckle_p40', 'speckle', 0.40),
                                    ('blur_r2', 'blur', 2), ('shadow_strip', 'shadow', None)], 'sonar')
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
