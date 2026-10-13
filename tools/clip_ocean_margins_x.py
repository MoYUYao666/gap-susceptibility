"""Reinforcement experiment (5): exact Theorem 1 prediction check for siglip / openclip (margins protocol).
Same analyze logic as clip_ocean_margins.py, the encoder layer is a transformers model (siglip uses the native pooler convention).
Output: outputs/ocean_margins_x.json
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
from transformers import CLIPModel, CLIPProcessor, SiglipModel, SiglipProcessor

TEMPLATE = 'a photo of a {}'
LAMBDAS = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0]
SUB = 'outputs/ocean_subset.json'
OUT = 'outputs/ocean_margins_x.json'


def enc(m, p, tag, texts, ds, idx, batch=32):
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
        for i in range(0, len(idx), batch):
            b = ds[idx[i:i + batch]]['file_name']
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


def analyze(tf, base, labels_c, m, gap_norm, d_hat):
    S = (base @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S, axis=1)[:, :5]
    inv_exact, r1_exact, all_d, all_b = ({l: [] for l in LAMBDAS}, {l: [] for l in LAMBDAS}, [], [])
    for i in range(len(S)):
        k5 = topk5[i]
        s5 = S[i][k5]
        d_pairs = s5[:, None] - s5[None, :]
        dm = -(m[k5][:, None] - m[k5][None, :])
        upper = np.triu(np.ones((5, 5)), k=1).astype(bool)
        d_flat = d_pairs[upper]
        b_flat = dm[upper]
        all_d.append(d_flat)
        all_b.append(b_flat)
        for l in LAMBDAS:
            inv = (l * gap_norm * b_flat > d_flat).sum()
            inv_exact[l].append(1.0 - 2 * inv / 10.0)
            r1_exact[l].append(float((l * gap_norm * dm[0, 1:] > d_pairs[0, 1:]).any()))
    d_all = np.concatenate(all_d)
    r_dm, p_dm = stats.pearsonr(d_all, np.concatenate(all_b))
    measured = {}
    for l in LAMBDAS:
        with torch.no_grad():
            sh = F.normalize(base + l * gap_norm * d_hat, dim=-1)
        Sl = (sh @ tf.T).cpu().numpy()
        top1 = float((Sl.argmax(1) == labels_c).mean() * 100)
        taus = []
        for i in range(len(S)):
            r1, r2 = S[i][topk5[i]], Sl[i][topk5[i]]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        measured[str(l)] = {'top1': top1, 'tau': float(np.mean(taus))}
    return {'gap_norm': round(gap_norm, 4), 'sigma_m': round(float(np.std(m)), 4),
            'mean_m': round(float(np.mean(m)), 4),
            'margin_bias_pearson': round(float(r_dm), 4),
            'predicted_tau_exact': {str(l): round(float(np.mean(inv_exact[l])), 4) for l in LAMBDAS},
            'predicted_rank1_loss_exact': {str(l): round(float(np.mean(r1_exact[l])), 4) for l in LAMBDAS},
            'measured': {str(l): {'top1': round(measured[str(l)]['top1'], 3),
                                  'tau': round(measured[str(l)]['tau'], 4)} for l in LAMBDAS}}


def main():
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    sub = json.load(open(SUB, encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    texts = [TEMPLATE.format(c) for c in classes]
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
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
        res[tag] = analyze(tf, base, labels, m_c, gnorm, dH)
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        for l in ['0.5', '1.0', '2.0']:
            pr = res[tag]['predicted_tau_exact'][l]
            me = res[tag]['measured'][l]['tau']
            print('  %s λ=%s: tau_pred=%.4f tau_meas=%.4f (diff %.4f)' % (tag, l, pr, me, abs(pr - me)), flush=True)
        del m
        torch.cuda.empty_cache()
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
