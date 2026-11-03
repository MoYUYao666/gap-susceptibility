"""A3 提升③: 方向解析算子 v1（每退化类型内在方向手术）。
在 clip_direction_aware.py 的负面结果上推进:
  对每种退化, 估计主损伤方向 ê_deg = normalize(mean δ_i) (及 PCA 第一主成分版),
  每图 α_i = δ_i·ê_deg; 类偏置场推广到 ê: m_c(ê) = ê·t_c;
  反转条件 α_i (m_j(ê) - m_i(ê)) > d_ij → τ_pred_deg。
  并测量结构占比: mean(||δ_i - α_i ê||/||δ_i||)（残差份额越小 → 单方向主导 → 可解析）。
对照: τ_pred_gap(现有 gap 轴) / τ_meas / 误差。
输出: outputs/direction_operator.json
运行: conda run -n pytorch python tools/clip_direction_operator.py
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
import open_clip
import importlib.util

spec = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
ocm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocm)

OUT = 'outputs/direction_operator.json'
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


def pred_tau(alpha_i, dm_ups, d_ups):
    """α_i: 逐图位移幅值; dm_ups/d_ups: 每图 10 个上三角对的类偏置差分与 margin。"""
    preds = []
    for i in range(len(d_ups)):
        inv = (alpha_i[i] * dm_ups[i] > d_ups[i]).sum()
        preds.append(1.0 - 2 * inv / 10.0)
    return float(np.mean(preds))


def measure(enc, tf, f0, deg_gen, deg_names):
    with torch.no_grad():
        gap = tf.mean(0) - f0.mean(0)
    gnorm = gap.norm().item()
    dH = (gap / gnorm).cpu().numpy()
    m_c = dH @ tf.cpu().numpy().T
    S0 = (f0 @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    upM = np.triu(np.ones((5, 5)), k=1).astype(bool)
    s5_list = [S0[i][topk5[i]] for i in range(len(S0))]
    dm_gap = [-(m_c[topk5[i]][:, None] - m_c[topk5[i]][None, :]) for i in range(len(S0))]
    d_up = [(s5[:, None] - s5[None, :])[upM] for s5 in s5_list]

    def tau_of(Sd):
        taus = []
        for i in range(len(S0)):
            r1, r2 = S0[i][topk5[i]], Sd[i][topk5[i]]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        return float(np.mean(taus))

    rows = []
    for name, deg_imgs in zip(deg_names, deg_gen):
        fd = enc(deg_imgs)
        delta = (fd - f0).cpu().numpy()
        Sd = (fd @ tf.T).cpu().numpy()
        tm = tau_of(Sd)
        # --- gap 轴基线 (幅值 = δ·d̂, 不除以 gnorm) ---
        a_gap = delta @ dH
        pred_gap = pred_tau(a_gap, [dm_gap[i][upM] for i in range(len(S0))], d_up)
        # --- 方向解析: mean-方向 & PCA 第一主成分 ---
        e_mean = delta.mean(0)
        e_mean = e_mean / (np.linalg.norm(e_mean) + 1e-12)
        X = delta - delta.mean(0)
        _, _, vh = np.linalg.svd(X, full_matrices=False)
        e_pca = vh[0]
        out = {'degrade': name, 'tau_meas': round(tm, 4), 'pred_gap': round(pred_gap, 4),
               'err_gap': round(abs(tm - pred_gap), 4)}
        tf_np = tf.cpu().numpy()
        for lab, e in [('mean', e_mean), ('pca', e_pca)]:
            alpha = delta @ e
            m_deg = e @ tf_np.T
            dm_deg = [-(m_deg[topk5[i]][:, None] - m_deg[topk5[i]][None, :])[upM] for i in range(len(S0))]
            p_deg = pred_tau(alpha, dm_deg, d_up)
            resid = np.linalg.norm(delta - np.outer(alpha, e), axis=1)
            out['alpha_%s' % lab] = round(float(alpha.mean()), 4)
            out['resid_frac_%s' % lab] = round(float(np.mean(resid / np.linalg.norm(delta, axis=1))), 4)
            out['pred_%s' % lab] = round(p_deg, 4)
            out['err_%s' % lab] = round(abs(tm - p_deg), 4)
        rows.append(out)
        print('  %-12s tau=%.4f | err_gap=%.4f -> err_mean=%.4f err_pca=%.4f | resid=%s/%s' %
              (name, tm, out['err_gap'], out['err_mean'], out['err_pca'],
               out['resid_frac_mean'], out['resid_frac_pca']), flush=True)
    return rows


def main():
    res = {}
    # ---------- 海洋: bioclip, 退化 haze/uw (与 direction_aware 同口径) ----------
    from clip_ocean_degradation import degrade as m_deg
    ds = ocm.load_ds()
    sub = json.load(open('outputs/ocean_subset.json', encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    texts = [TEMPLATE.format(c) for c in classes]
    imgs = []
    for j in idx:
        b = ds[j]['file_name']
        imgs.append(Image.open(io.BytesIO(b['bytes'])).convert('RGB')
                    if isinstance(b, dict) and b.get('bytes')
                    else Image.open(b['path']).convert('RGB') if isinstance(b, dict) else b.convert('RGB'))
    m, pre = ocm.load_openclip('bioclip')
    tok = open_clip.get_tokenizer('ViT-B-16')

    def enc_oc(lst):
        out = []
        with torch.no_grad():
            for i in range(0, len(lst), 32):
                xs = torch.stack([pre(im) for im in lst[i:i + 32]]).to('cuda')
                out.append(F.normalize(m.encode_image(xs), dim=-1))
        return torch.cat(out)

    with torch.no_grad():
        tf = F.normalize(m.encode_text(tok(texts).to('cuda')), dim=-1)
    f0 = enc_oc(imgs)
    dgen = [[Image.fromarray(m_deg(np.array(im), (n, k, a))) for im in imgs]
            for n, k, a in [('haze_t0.60', 'haze', 0.60), ('haze_t0.30', 'haze', 0.30),
                            ('uw_cast', 'uw', None)]]
    res['marine_bioclip'] = measure(enc_oc, tf, f0, dgen, ['haze_t0.60', 'haze_t0.30', 'uw_cast'])
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    del m, f0, tf
    torch.cuda.empty_cache()

    # ---------- 声呐: frozen CLIP, 退化 speckle/blur/shadow (650 子集, 与 direction_aware 同口径) ----------
    man = []
    for c, d in zip(SONAR_CLASSES, SONAR_DIR):
        p = os.path.join('data/NKSID/NKSID', d)
        if not os.path.isdir(p):
            p = 'data/NKSID/NKSID'
        fs = sorted(f for f in os.listdir(p) if f.lower().endswith(('.jpg', '.png')))[:90]
        man.extend((os.path.join(p, f), c) for f in fs)
    simgs = [Image.open(fp).convert('RGB') for fp, _ in man]
    stexts = [TEMPLATE.format(c) for c in SONAR_CLASSES]
    sm = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().eval()
    sp = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
    ti = sp(text=stexts, return_tensors='pt', padding=True).to('cuda')
    with torch.no_grad():
        out = sm.text_model(**ti)
        pooled = out[1] if isinstance(out, tuple) else out.pooler_output
        stf = F.normalize(sm.text_projection(pooled), dim=-1)

    def enc_s(lst):
        out = []
        with torch.no_grad():
            for i in range(0, len(lst), 32):
                inp = sp(images=lst[i:i + 32], return_tensors='pt').to('cuda')
                vout = sm.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                out.append(F.normalize(sm.visual_projection(vp), dim=-1))
        return torch.cat(out)

    sf0 = enc_s(simgs)
    sgen = [[sonar_deg(im, k, a) for im in simgs] for k, a in
            [('speckle', 0.20), ('speckle', 0.40), ('blur', 2), ('shadow', None)]]
    res['sonar_frozen'] = measure(enc_s, stf, sf0, sgen,
                                  ['speckle_p20', 'speckle_p40', 'blur_r2', 'shadow_strip'])
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
