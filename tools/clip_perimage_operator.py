"""(b) Exact per-image direction (functional) operator---closes the direction analysis problem.
Derivation: the degraded embedding fd_i = normalize(f0_i + δ_i) is already normalized ⇒ the denominator is 1 ⇒ the score difference is exactly
Δs_c = δ_i · t_c ⇒ inversion iff δ_i·(t_j − t_i) > d_ij --- the closed-form exact inversion condition for a displacement in an arbitrary direction.
Compared against the shared direction subspace (k=1..5); if the per-image prediction err≈0 ⇒ the off-axis problem is closed (at the paired count).
Data: marine (bioclip frozen) 4 degradations + sonar (frozen) 4 degradations (same conditions as direction_subspace).
Output: outputs/perimage_operator.json
"""
import os, sys, json, io
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageFilter
from scipy import stats
from transformers import CLIPModel, CLIPProcessor
import importlib.util

spec = importlib.util.spec_from_file_location('ds', 'tools/clip_direction_subspace.py')
ds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ds)
spec2 = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
ocm = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(ocm)

TEMPLATE = 'a photo of a {}'
OUT = 'outputs/perimage_operator.json'
DEGS_M = [('haze_t0.6', 'blur', 2), ('haze_t0.3', 'blur', 5),
          ('shadow_strip', 'shadow', None), ('speckle_p20', 'speckle', 0.20)]
DEGS_S = [('speckle_p20', 'speckle', 0.20), ('speckle_p40', 'speckle', 0.40),
          ('blur_r2', 'blur', 2), ('shadow_strip', 'shadow', None)]


def perimage(f0, fd, tf, S0, topk5, tag, rows):
    dta = (fd - f0).cpu().numpy()
    tf_np = tf.cpu().numpy()
    Sd = (fd @ tf.T).cpu().numpy()
    taus, preds, taus_tie, invg = [], [], [], []
    for i in range(len(S0)):
        k5 = topk5[i]
        r1, r2 = S0[i][k5], Sd[i][k5]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
        r2e = r2
        # exact per-image inversion condition (theoretical identity: r2_a-r2_b = d_ab + (Δs_a-Δs_b) < 0 iff Δs_a-Δs_b < -d_ab)
        dm = tf_np[k5] @ dta[i]
        dms = dm[:, None] - dm[None, :]
        up = np.triu(np.ones((5, 5)), k=1).astype(bool)
        d_pairs = (S0[i][k5][:, None] - S0[i][k5][None, :])[up]
        inv = (dms[up] < -d_pairs).sum()
        preds.append(1.0 - 2 * inv / 10.0)
        # same-definition measurement (tau-a: count the true inversions directly from Sd)
        inv_true = np.sum((r2e[:, None] - r2e[None, :])[up] < 0)
        taus_tie.append(1.0 - 2 * inv_true / 10.0)
    tm = float(np.mean(taus))          # scipy tau-b (with tie correction)
    tp = float(np.mean(preds))         # formula prediction
    ta = float(np.mean(taus_tie))      # same-definition measurement (tau-a)
    rows.append({'name': tag, 'tau_meas_tauB': round(tm, 4), 'tau_meas_tauA': round(ta, 4),
                 'tau_pred_perimage': round(tp, 4),
                 'err_same_def': round(abs(ta - tp), 4),
                 'err_tie_bias': round(abs(ta - tm), 4)})
    print('  %-16s tauB=%.4f tauA=%.4f pred=%.4f err_same_def=%.4f tie_bias=%.4f' %
          (tag, tm, ta, tp, abs(ta - tp), abs(ta - tm)), flush=True)
    return rows


def main():
    res = {}
    # marine bioclip
    ds_ = json.load(open('outputs/ocean_subset.json', encoding='utf-8'))
    classes = ds_['classes']
    idx = ds_['subset_idx']
    dataset = json.load(open('outputs/ocean_subset.json', encoding='utf-8') ) if False else None
    from datasets import load_dataset
    dd = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')),
        split='train')
    imgs_m = []
    for j in idx:
        b = dd[j]['file_name']
        imgs_m.append(Image.open(io.BytesIO(b['bytes'])).convert('RGB')
                      if isinstance(b, dict) and b.get('bytes')
                      else (Image.open(b['path']).convert('RGB') if isinstance(b, dict)
                            else b.convert('RGB')))
    mb, pre_b = ocm.load_openclip('bioclip')
    import open_clip as ocl
    tok = ocl.get_tokenizer('ViT-B-16')
    with torch.no_grad():
        mtf = F.normalize(mb.encode_text(tok([TEMPLATE.format(c) for c in classes]).to('cuda')), dim=-1)
    f0 = []
    with torch.no_grad():
        for i in range(0, len(imgs_m), 48):
            xs = torch.stack([pre_b(im) for im in imgs_m[i:i + 48]]).to('cuda')
            f0.append(F.normalize(mb.encode_image(xs), dim=-1))
    f0 = torch.cat(f0)
    S0 = (f0 @ mtf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    rows = []
    for name, kind, arg in DEGS_M:
        deg = [ds.sonar_deg(im, kind, arg) for im in imgs_m]
        fd = []
        with torch.no_grad():
            for i in range(0, len(deg), 48):
                xs = torch.stack([pre_b(im) for im in deg[i:i + 48]]).to('cuda')
                fd.append(F.normalize(mb.encode_image(xs), dim=-1))
        fd = torch.cat(fd)
        perimage(f0, fd, mtf, S0, topk5, name, rows)
        json.dump({'marine_bioclip': rows}, open(OUT, 'w', encoding='utf-8'), indent=1)
        del fd
        torch.cuda.empty_cache()
    del mb
    torch.cuda.empty_cache()

    # sonar frozen
    man = []
    for c, d in zip(ds.SONAR_CLASSES, ds.SONAR_DIR):
        pth = os.path.join('data/NKSID/NKSID', d)
        if not os.path.isdir(pth):
            pth = 'data/NKSID/NKSID'
        fs = sorted(f for f in os.listdir(pth) if f.lower().endswith(('.jpg', '.png')))[:90]
        man.extend((os.path.join(pth, f), c) for f in fs)
    sm = CLIPModel.from_pretrained(ds.MDIR, local_files_only=True).cuda().eval()
    sp = CLIPProcessor.from_pretrained(ds.MDIR, local_files_only=True)
    ti = sp(text=[TEMPLATE.format(c) for c in ds.SONAR_CLASSES], return_tensors='pt', padding=True).to('cuda')
    with torch.no_grad():
        out = sm.text_model(**ti)
        pooled = out[1] if isinstance(out, tuple) else out.pooler_output
        stf = F.normalize(sm.text_projection(pooled), dim=-1)
    simgs = [Image.open(fp).convert('RGB') for fp, _ in man]
    f0s = []
    with torch.no_grad():
        for i in range(0, len(simgs), 48):
            inp = sp(images=simgs[i:i + 48], return_tensors='pt').to('cuda')
            vout = sm.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
            vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            f0s.append(F.normalize(sm.visual_projection(vp), dim=-1))
    f0s = torch.cat(f0s)
    S0s = (f0s @ stf.T).cpu().numpy()
    topk5s = np.argsort(-S0s, axis=1)[:, :5]
    rows_s = []
    for name, kind, arg in DEGS_S:
        deg = [ds.sonar_deg(im, kind, arg) for im in simgs]
        fds = []
        with torch.no_grad():
            for i in range(0, len(deg), 48):
                inp = sp(images=deg[i:i + 48], return_tensors='pt').to('cuda')
                vout = sm.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                fds.append(F.normalize(sm.visual_projection(vp), dim=-1))
        fds = torch.cat(fds)
        perimage(f0s, fds, stf, S0s, topk5s, name, rows_s)
        json.dump({'marine_bioclip': rows, 'sonar_frozen': rows_s}, open(OUT, 'w', encoding='utf-8'),
                  indent=1)
        del fds
        torch.cuda.empty_cache()
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
