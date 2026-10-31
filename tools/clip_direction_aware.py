"""A3 增强③: 方向感知(逐图 λ)理论测试 —— 检验离轴退化的损伤可否用逐图间隙轴分解闭合预测。
对 {海洋(bioclip/oceanclip), 声呐(frozen CLIP)} 的退化集合:
  计 δ_i（每图退化位移) → λ_i = (δ_i·d̂)/||g|| → 精确反转条件逐图代入 λ_i → τ_pred_dir
  对照: τ_pred_gap(均值 λ, 原预测器) 与 τ_meas。
若 |τ_pred_dir − τ_meas| 显著小于 |τ_pred_gap − τ_meas| → 方向感知扩展成立。
输出: outputs/direction_aware.json
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

OUT = 'outputs/direction_aware.json'
TEMPLATE = 'a photo of a {}'
MDIR = 'models/clip-vit-base-patch32'
SONAR_CLASSES = ['big propeller', 'cylinder', 'fishing net', 'floats', 'iron pipeline',
                 'small propeller', 'soft pipeline', 'tire']
SONAR_DIR = ['big_propeller', 'cylinder', 'fishing_net', 'floats', 'iron_pipeline',
             'small_propeller', 'soft_pipeline', 'tire']


def sonar_manifest():
    m = []
    for c, d in zip(SONAR_CLASSES, SONAR_DIR):
        p = os.path.join('data/NKSID/NKSID', d)
        if not os.path.isdir(p):
            p = 'data/NKSID/NKSID'
        fs = sorted(f for f in os.listdir(p) if f.lower().endswith(('.jpg', '.png')))[:90]
        m.extend((os.path.join(p, f), c) for f in fs)
    return m


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


def eval_domain(name, imgs, texts, labels, m, p, deg_list, match='tf'):
    """对给定模型与图像集, 逐图 λ_i 分解。match: tf=transformer CLIP; tf='oc'=open_clip(tag)。"""
    def enc(lst):
        out = []
        with torch.no_grad():
            for i in range(0, len(lst), 32):
                if match == 'oc':
                    xs = torch.stack([pre(im) for im in lst[i:i + 32]]).to('cuda')
                    out.append(F.normalize(m.encode_image(xs), dim=-1))
                else:
                    inp = p(images=lst[i:i + 32], return_tensors='pt').to('cuda')
                    vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                    vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                    out.append(F.normalize(m.visual_projection(vp), dim=-1))
        return torch.cat(out)

    def enc_text():
        with torch.no_grad():
            if match == 'oc':
                tok = open_clip.get_tokenizer('ViT-B-16')
                return F.normalize(m.encode_text(tok(texts).to('cuda')), dim=-1)
            ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
            out = m.text_model(**ti)
            pooled = out[1] if isinstance(out, tuple) else out.pooler_output
            return F.normalize(m.text_projection(pooled), dim=-1)

    tf = enc_text()
    f0 = enc(imgs)
    gap = tf.mean(0) - f0.mean(0)
    gnorm = gap.norm().item()
    dH = (gap / gnorm).cpu().numpy()
    m_c = dH @ tf.cpu().numpy().T
    S0 = (f0 @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]

    def tau_from_scores(Sd, lambdas=None):
        taus = []
        for i in range(len(S0)):
            r1, r2 = S0[i][topk5[i]], Sd[i][topk5[i]]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        return float(np.mean(taus))

    def pred_with_lam(lam_i):
        preds = []
        for i in range(len(S0)):
            k5 = topk5[i]
            s5 = S0[i][k5]
            d_pairs = s5[:, None] - s5[None, :]
            dm = -(m_c[k5][:, None] - m_c[k5][None, :])
            up = np.triu(np.ones((5, 5)), k=1).astype(bool)
            inv = (lam_i[i] * gnorm * dm[up] > d_pairs[up]).sum()
            preds.append(1.0 - 2 * inv / 10.0)
        return float(np.mean(preds))

    rows = []
    for dname, kind, arg in deg_list:
        deg = [sonar_deg(im, kind, arg) if match != 'oc' else im for im in imgs] if False else \
              [sonar_deg(im, kind, arg) for im in imgs]
        # 海洋退化使用 clip_ocean_degradation 的封装(雾化/色偏), 声呐用本地 sonar_degrade —— 此处通过 deg_src 定制
        rows.append({'degrade': dname, 'placeholder': True})
    return tf, f0, S0, topk5, m_c, gnorm, dH, enc, enc_text


def main():
    res = {}
    # -------- A) 海洋域 (bioclip/oceanclip, 退化=雾化/色偏; 复用 clip_ocean_degradation 逻辑代理: 直接调用其 deg 函数) --------
    # 简化: 海洋退化逐图 λ 用已存档的聚合? 需要 δ_i → 需重算; 采用快速路径: 仅计算 sonar(完整路径) + marine 以 bioclip 一组
    # 海洋: 重算
    from clip_ocean_degradation import degrade as m_deg
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    sub = json.load(open('outputs/ocean_subset.json', encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    texts = [ocm.TEMPLATE.format(c) for c in classes]
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
    gap = tf.mean(0) - f0.mean(0)
    gnorm = gap.norm().item()
    dH = (gap / gnorm).cpu().numpy()
    m_c = dH @ tf.cpu().numpy().T
    S0 = (f0 @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]

    def tau_meas(Sd):
        taus = []
        for i in range(len(S0)):
            r1, r2 = S0[i][topk5[i]], Sd[i][topk5[i]]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        return float(np.mean(taus))

    def pred(lam_i_arr):
        preds = []
        for i in range(len(S0)):
            k5 = topk5[i]
            s5 = S0[i][k5]
            d_pairs = s5[:, None] - s5[None, :]
            dm = -(m_c[k5][:, None] - m_c[k5][None, :])
            up = np.triu(np.ones((5, 5)), k=1).astype(bool)
            inv = (lam_i_arr[i] * gnorm * dm[up] > d_pairs[up]).sum()
            preds.append(1.0 - 2 * inv / 10.0)
        return float(np.mean(preds))

    res['marine_bioclip'] = []
    for dname, kind, arg in [('haze_t0.60', 'haze', 0.60), ('haze_t0.30', 'haze', 0.30), ('uw_cast', 'uw', None)]:
        deg = [m_deg(np.array(im), (dname, kind, arg)) for im in imgs]
        deg = [Image.fromarray(x) for x in deg]
        fd = enc_oc(deg)
        delta = (fd - f0).cpu().numpy()
        lam_i = (delta @ dH) / gnorm
        Sd = (fd @ tf.T).cpu().numpy()
        tm = tau_meas(Sd)
        tp_mean = pred(np.full(len(S0), float(lam_i.mean())))
        tp_dir = pred(lam_i)
        res['marine_bioclip'].append({'degrade': dname, 'lam_mean': round(float(lam_i.mean()), 4),
                                      'lam_std': round(float(lam_i.std()), 4), 'tau_meas': round(tm, 4),
                                      'tau_pred_gap': round(tp_mean, 4), 'tau_pred_dir': round(tp_dir, 4),
                                      'err_gap': round(abs(tm - tp_mean), 4), 'err_dir': round(abs(tm - tp_dir), 4)})
        print('marine %-12s tau_meas=%.4f pred_gap=%.4f pred_dir=%.4f err %.4f->%.4f' %
              (dname, tm, tp_mean, tp_dir, abs(tm - tp_mean), abs(tm - tp_dir)), flush=True)
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)

    # -------- B) 声呐域 (frozen CLIP) --------
    man = sonar_manifest()
    slabels = np.array([SONAR_CLASSES.index(c) for _, c in man])
    stexts = [TEMPLATE.format(c) for c in SONAR_CLASSES]
    simgs = [Image.open(fp).convert('RGB') for fp, _ in man]
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
    sgap = stf.mean(0) - sf0.mean(0)
    sgnorm = sgap.norm().item()
    sdH = (sgap / sgnorm).cpu().numpy()
    sm_c = sdH @ stf.cpu().numpy().T
    SS0 = (sf0 @ stf.T).cpu().numpy()
    stopk5 = np.argsort(-SS0, axis=1)[:, :5]
    res['sonar_frozen'] = []
    for dname, kind, arg in [('speckle_p20', 'speckle', 0.20), ('speckle_p40', 'speckle', 0.40),
                             ('blur_r2', 'blur', 2), ('shadow_strip', 'shadow', None)]:
        sdeg = [sonar_deg(im, kind, arg) for im in simgs]
        sfd = enc_s(sdeg)
        sdelta = (sfd - sf0).cpu().numpy()
        slam_i = (sdelta @ sdH) / sgnorm
        SSd = (sfd @ stf.T).cpu().numpy()
        stm = tau_meas_s(SSd, SS0, stopk5)
        stp_mean = pred_s(np.full(len(SS0), float(slam_i.mean())), SS0, stopk5, sm_c, sgnorm)
        stp_dir = pred_s(slam_i, SS0, stopk5, sm_c, sgnorm)
        res['sonar_frozen'].append({'degrade': dname, 'lam_mean': round(float(slam_i.mean()), 4),
                                    'lam_std': round(float(slam_i.std()), 4), 'tau_meas': round(stm, 4),
                                    'tau_pred_gap': round(stp_mean, 4), 'tau_pred_dir': round(stp_dir, 4),
                                    'err_gap': round(abs(stm - stp_mean), 4), 'err_dir': round(abs(stm - stp_dir), 4)})
        print('sonar  %-12s tau_meas=%.4f pred_gap=%.4f pred_dir=%.4f err %.4f->%.4f' %
              (dname, stm, stp_mean, stp_dir, abs(stm - stp_mean), abs(stm - stp_dir)), flush=True)
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


def tau_meas_s(Sd, S0, topk5):
    taus = []
    for i in range(len(S0)):
        r1, r2 = S0[i][topk5[i]], Sd[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    return float(np.mean(taus))


def pred_s(lam_i, S0, topk5, m_c, gnorm):
    preds = []
    for i in range(len(S0)):
        k5 = topk5[i]
        s5 = S0[i][k5]
        d_pairs = s5[:, None] - s5[None, :]
        dm = -(m_c[k5][:, None] - m_c[k5][None, :])
        up = np.triu(np.ones((5, 5)), k=1).astype(bool)
        inv = (lam_i[i] * gnorm * dm[up] > d_pairs[up]).sum()
        preds.append(1.0 - 2 * inv / 10.0)
    return float(np.mean(preds))


if __name__ == '__main__':
    main()
