"""A2 扩展 E1: 域-模型基阵法 —— ImageNet-5k / DTD / Food101 × 4 模型 冻结 λ 手术。
协议与海洋/声呐一致: τ 手术 (6λ) + σ_m + NCC 谱系 + 非对称(文本侧 λ=1)。
输出: outputs/domain_matrix.json
运行: conda run -n pytorch python tools/clip_domain_matrix.py
"""
import os, sys, json, io, glob, collections
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
import open_clip
import importlib.util

spec = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
ocm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocm)

OUT = 'outputs/domain_matrix.json'
LAMBDAS = [-1.0, -0.5, 0.0, 0.5, 1.0, 2.0]
TEMPLATE = 'a photo of a {}'
SEED = 42


def load(path):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else None


def load_domain(name, cap=5000):
    """返回 (image_paths, class_labels, class_names)。"""
    rng = np.random.RandomState(SEED)
    if name == 'imagenet5k':
        # A1 的 ImageNet-1K 验证集(14288 张, 1000 类) → 采样 5000
        from datasets import load_dataset as ld
        ds = ld('parquet', data_files=sorted(
            os.path.join('data/imagenet_hf', f) for f in os.listdir('data/imagenet_hf')
            if f.endswith('.parquet')), split='train')
        names = json.load(open('data/imagenet_1k_names.json', encoding='utf-8'))
        n = len(ds)
        idx = rng.choice(n, size=min(cap, n), replace=False)
        imgs, labels = [], []
        for i in idx:
            r = ds[int(i)]
            lbl = r['label'] if isinstance(r['label'], int) else int(r['label'])
            imgs.append(('img', r['image']))
            labels.append(lbl)
        classes = names if len(names) >= (max(labels) + 1) else [str(i) for i in range(max(labels) + 1)]
        return imgs, np.array(labels), classes
    if name == 'dtd':
        files = sorted(glob.glob('data/dtd/dtd/images/**/*.jpg', recursive=True))
        if not files:
            files = sorted(glob.glob('data/dtd/images/**/*.jpg', recursive=True))
        rng = np.random.RandomState(SEED)
        idx = rng.choice(len(files), size=min(cap, len(files)), replace=False)
        files = [files[int(i)] for i in idx]
        cls = sorted(set(os.path.basename(os.path.dirname(f)) for f in files))
        labels = np.array([cls.index(os.path.basename(os.path.dirname(f))) for f in files])
        return [('path', f) for f in files], labels, cls
    if name == 'food101':
        files = sorted(glob.glob('data/food-101/images/*/*.jpg'))
        rng = np.random.RandomState(SEED)
        idx = rng.choice(len(files), size=min(cap, len(files)), replace=False)
        files = [files[int(i)] for i in idx]
        cls = sorted(set(os.path.basename(os.path.dirname(f)) for f in files))
        labels = np.array([cls.index(os.path.basename(os.path.dirname(f))) for f in files])
        return [('path', f) for f in files], labels, cls
    raise ValueError(name)


def open_img(item):
    x = item[1]
    if hasattr(x, 'convert'):
        return x.convert('RGB')
    if isinstance(x, dict) and x.get('bytes'):
        return Image.open(io.BytesIO(x['bytes'])).convert('RGB')
    if isinstance(x, dict):
        return Image.open(x['path']).convert('RGB')
    return Image.open(item[1]).convert('RGB')


def run_transformers(tag, mdir, imgs, texts, labels, cap_batch=48):
    from transformers import CLIPModel, CLIPProcessor, SiglipModel, SiglipProcessor
    if tag == 'siglip':
        m = SiglipModel.from_pretrained(mdir, local_files_only=True).cuda().eval()
        p = SiglipProcessor.from_pretrained(mdir, local_files_only=True)
        ti = p(text=texts, return_tensors='pt', padding='max_length', max_length=64).to('cuda')
        with torch.no_grad():
            tf = m.text_model(**ti).pooler_output
        tf = F.normalize(tf, dim=-1)
    else:
        m = CLIPModel.from_pretrained(mdir, local_files_only=True).cuda().eval()
        p = CLIPProcessor.from_pretrained(mdir, local_files_only=True)
        ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
        with torch.no_grad():
            out = m.text_model(**ti)
            pooled = out[1] if isinstance(out, tuple) else out.pooler_output
            tf = F.normalize(m.text_projection(pooled), dim=-1)

    def enc(lst):
        out = []
        with torch.no_grad():
            for i in range(0, len(lst), cap_batch):
                inp = p(images=lst[i:i + cap_batch], return_tensors='pt').to('cuda')
                if tag == 'siglip':
                    vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                    vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                    f = m.visual_projection(vp) if hasattr(m, 'visual_projection') else vp
                else:
                    vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                    vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                    f = m.visual_projection(vp) if hasattr(m, 'visual_projection') else vp
                out.append(F.normalize(f, dim=-1))
        return torch.cat(out)
    return m, p, tf, enc, lambda: None


def run_openclip(tag, imgs, texts, labels, cap_batch=48):
    m, pre = ocm.load_openclip(tag)
    tok = open_clip.get_tokenizer('ViT-B-16')
    with torch.no_grad():
        tf = F.normalize(m.encode_text(tok(texts).to('cuda')), dim=-1)

    def enc(lst):
        out = []
        with torch.no_grad():
            for i in range(0, len(lst), cap_batch):
                xs = torch.stack([pre(im) for im in lst[i:i + cap_batch]]).to('cuda')
                out.append(F.normalize(m.encode_image(xs), dim=-1))
        return torch.cat(out)
    return m, None, tf, enc, lambda: None


def protocol(tag, tf, enc, imgs, texts, labels, res):
    f0 = enc(imgs)
    gap = tf.mean(0) - f0.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    m_c = (dH @ tf.T).cpu().numpy()
    S0 = (f0 @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    top1_0 = float((S0.argmax(1) == labels).mean() * 100)
    rows = []
    for lam in LAMBDAS:
        with torch.no_grad():
            sh = F.normalize(f0 + lam * gnorm * dH, dim=-1)
        S = (sh @ tf.T).cpu().numpy()
        top1 = float((S.argmax(1) == labels).mean() * 100)
        taus, preds = [], []
        for i in range(len(S)):
            k5 = topk5[i]
            s5 = S0[i][k5]
            d_pairs = s5[:, None] - s5[None, :]
            dm = -(m_c[k5][:, None] - m_c[k5][None, :])
            up = np.triu(np.ones((5, 5)), k=1).astype(bool)
            inv = (lam * gnorm * dm[up] > d_pairs[up]).sum()
            preds.append(1.0 - 2 * inv / 10.0)
            r1, r2 = S0[i][k5], S[i][k5]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        rows.append({'lambda': lam, 'top1': round(top1, 3),
                     'tau_meas': round(float(np.mean(taus)), 4),
                     'tau_pred': round(float(np.mean(preds)), 4),
                     'CG': round((sh.mean(0) - tf.mean(0)).norm().item(), 4)})
    # 文本侧
    with torch.no_grad():
        tf2 = F.normalize(tf - 1.0 * gnorm * dH, dim=-1)
    S2 = (f0 @ tf2.T).cpu().numpy()
    taus2 = []
    for i in range(len(S0)):
        r1, r2 = S0[i][topk5[i]], S2[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus2.append(t)
    # NCC 谱系
    centroids = []
    for c in range(len(set(labels.tolist()))):
        idxc = np.where(labels == c)[0]
        if len(idxc) == 0:
            continue
        centroids.append(f0[idxc].mean(0))
    cent = F.normalize(torch.stack(centroids), dim=-1)
    ncc0 = float(((f0 @ cent.T).cpu().numpy().argmax(1) == labels).mean() * 100)
    res[tag] = {'gap_norm': round(gnorm, 4), 'sigma_m': round(float(np.std(m_c)), 4),
                'mean_m': round(float(np.mean(m_c)), 4), 'top1_0': round(top1_0, 3),
                'tau_text1': round(float(np.mean(taus2)), 4), 'ncc_0': round(ncc0, 3), 'rows': rows}
    print('  %s done: sigma_m=%.4f top1=%.2f tau@1=%.4f' %
          (tag, np.std(m_c), top1_0, [r['tau_meas'] for r in rows if r['lambda'] == 1.0][0]), flush=True)


def main():
    res = load(OUT) or {'meta': {'datasets': ['imagenet5k', 'dtd', 'food101'], 'n_domains': 3, 'grid': LAMBDAS}}
    doms = sys.argv[1:] if len(sys.argv) > 1 else ['imagenet5k', 'dtd', 'food101']
    for dom in doms:
        print('== domain %s ==' % dom, flush=True)
        items, labels, cls = load_domain(dom)
        texts = [TEMPLATE.format(c) for c in cls]
        imgs = [open_img(it) for it in items]
        res.setdefault(dom, {})
        for tag, mdir in [('clip_tf', 'models/clip-vit-base-patch32'), ('openclip_tf', 'models/openclip'),
                          ('siglip', 'models/siglip-base-patch16-224')]:
            print('  -- %s --' % tag, flush=True)
            m, p, tf, enc, _ = run_transformers(tag, mdir, imgs, texts, labels)
            protocol(tag, tf, enc, imgs, texts, labels, res[dom])
            del m
            torch.cuda.empty_cache()
        for tag in ['bioclip']:
            print('  -- %s --' % tag, flush=True)
            m, p, tf, enc, _ = run_openclip(tag, imgs, texts, labels)
            protocol(tag, tf, enc, imgs, texts, labels, res[dom])
            del m
            torch.cuda.empty_cache()
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
