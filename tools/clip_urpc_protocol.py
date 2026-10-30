"""A2/A3 合并提升⑦: 跨数据集声呐验证 —— URPC (PCL 多波束 FLS) 协议。
数据: fuhao7i/URPC = URPC2021 声呐检测数据集 (COCO 标注, train+test)。
流程: ① COCO 标注 → 目标裁剪(padding 10%, 滤小框) → 分类 manifest
      ② frozen CLIP 协议 (λ 手术/τ 预测/σ_m)
      ③ SonarCLIP(=NKSID 全量 FullFT sonar_clip_ft_full.pt) 跨数据集迁移评估
      ④ 陆地对照 flickrft
输出: outputs/sonar_urpc.json
运行: conda run -n pytorch python tools/clip_urpc_protocol.py
"""
import os, sys, json, io, collections
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from transformers import CLIPModel, CLIPProcessor

TEMPLATE = 'a photo of a {}'
MDIR = 'models/clip-vit-base-patch32'
ROOT = 'data/urpc'
OUT = 'outputs/sonar_urpc.json'
FT_WEIGHTS = 'outputs/sonar_clip_ft_full.pt'   # NKSID 全量 SonarCLIP
MIN_SIDE = 16          # 滤掉过小裁剪
CAP_PER_CLASS = 100    # 每类上限(与 NKSID 平衡口径类似)


def load_coco_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def build_crops():
    """从 train+test COCO 标注裁剪目标 → [(img_path, cat_name)]。仅加载实际存在的 split。"""
    cats, crops = {}, []
    img2file = {}
    for split in ['train', 'test']:
        annp = os.path.join(ROOT, 'coco', 'annotations', 'instances_%s.json' % split)
        imgdir = os.path.join(ROOT, 'coco', 'images', split)
        if not os.path.exists(annp) or not os.path.isdir(imgdir):
            print('split %s missing -> skip' % split, flush=True)
            continue
        ann = load_coco_json(annp)
        for c in ann['categories']:
            cats[c['id']] = c['name']
        for im in ann['images']:
            img2file[im['id']] = os.path.join(ROOT, 'coco', 'images', split, im['file_name'])
        for a in ann['annotations']:
            if a.get('area', 0) < 64:
                continue
            x, y, w, h = a['bbox']
            crops.append((img2file[a['image_id']], cats[a['category_id']], (x, y, w, h)))
    print('raw crops: %d, cats: %s' % (len(crops), {k: v for k, v in cats.items()}), flush=True)
    out = []
    for fp, cat, (x, y, w, h) in crops:
        if w < MIN_SIDE or h < MIN_SIDE:
            continue
        out.append((fp, cat, (x, y, w, h)))
    # 每类 cap(类数太少类不丢; 大长尾 cap 后保留)
    bycat = collections.defaultdict(list)
    for it in out:
        bycat[it[1]].append(it)
    manifest = []
    for c, lst in bycat.items():
        lst.sort(key=lambda t: t[0])
        manifest.extend(lst[:CAP_PER_CLASS])
    print('manifest: %d crops across %d classes' % (len(manifest), len(bycat)), flush=True)
    print('per-class: %s' % dict((c, len(v)) for c, v in bycat.items()), flush=True)
    return manifest


def crop_image(fp, bbox, pad=0.10):
    im = Image.open(fp).convert('RGB')
    x, y, w, h = bbox
    x0, y0 = max(0, int(x - pad * w)), max(0, int(y - pad * h))
    x1, y1 = min(im.width, int(x + w + pad * w)), min(im.height, int(y + h + pad * h))
    return im.crop((x0, y0, x1, y1))


def load_model(mdir=MDIR, weights=None):
    m = CLIPModel.from_pretrained(mdir, local_files_only=True).cuda().eval()
    p = CLIPProcessor.from_pretrained(mdir, local_files_only=True)
    if weights:
        m.load_state_dict(torch.load(weights, map_location='cpu'))
        m = m.cuda().eval()
    return m, p


def encode(m, p, imgs, texts=None, cap_batch=32):
    with torch.no_grad():
        if texts is not None:
            ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
            out = m.text_model(**ti)
            pooled = out[1] if isinstance(out, tuple) else out.pooler_output
            tf = F.normalize(m.text_projection(pooled), dim=-1)
        feats = []
        for i in range(0, len(imgs), cap_batch):
            inp = p(images=imgs[i:i + cap_batch], return_tensors='pt').to('cuda')
            vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
            vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            feats.append(F.normalize(m.visual_projection(vp), dim=-1))
        base = torch.cat(feats)
    return (tf if texts is not None else None), base


def protocol(tag, m, p, manifest, texts, classes, outdict):
    imgs = [crop_image(fp, bb) for fp, _, bb in manifest]
    labels = np.array([classes.index(c) for _, c, _ in manifest])
    tf, base = encode(m, p, imgs, texts)
    gap = tf.mean(0) - base.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    m_c = (dH.cpu().numpy() @ tf.cpu().numpy().T)
    S0 = (base @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :min(5, S0.shape[1])]
    top1 = float((S0.argmax(1) == labels).mean() * 100)
    rows = []
    for l in [-1.0, -0.5, 0.0, 0.5, 1.0, 2.0]:
        with torch.no_grad():
            sh = F.normalize(base + l * gnorm * dH, dim=-1)
        S = (sh @ tf.T).cpu().numpy()
        top1_l = float((S.argmax(1) == labels).mean() * 100)
        taus, preds = [], []
        for i in range(len(S)):
            k5 = topk5[i]
            s5 = S0[i][k5]
            d_pairs = s5[:, None] - s5[None, :]
            dm = -(m_c[k5][:, None] - m_c[k5][None, :])
            up = np.triu(np.ones((len(k5), len(k5))), k=1).astype(bool)
            inv = (l * gnorm * dm[up] > d_pairs[up]).sum()
            preds.append(1.0 - 2 * inv / float(len(k5) * (len(k5) - 1)))
            r1, r2 = S0[i][k5], S[i][k5]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        cg = (sh.mean(0) - tf.mean(0)).norm().item()
        rows.append({'lambda': l, 'top1': round(top1_l, 3), 'tau_meas': round(float(np.mean(taus)), 4),
                     'tau_pred': round(float(np.mean(preds)), 4), 'CG': round(cg, 4)})
        print('  %s λ=%+.1f top1=%.2f tau_pred=%.4f tau_meas=%.4f CG=%.4f' %
              (tag, l, top1_l, np.mean(preds), np.mean(taus), cg), flush=True)
    outdict[tag] = {'gap_norm': round(gnorm, 4), 'sigma_m': round(float(np.std(m_c)), 4),
                    'mean_m': round(float(np.mean(m_c)), 4), 'top1_0': round(top1, 3), 'rows': rows}
    json.dump(outdict, open(OUT, 'w', encoding='utf-8'), indent=1)


def main():
    manifest = build_crops()
    classes = sorted(set(c for _, c, _ in manifest))
    texts = [TEMPLATE.format(c) for c in classes]
    out = {'meta': {'dataset': 'URPC2021 sonar (PCL, COCO mirror fuhao7i/URPC)', 'n_classes': len(classes),
                    'n_images': len(manifest), 'classes': classes,
                    'per_class': dict(collections.Counter(c for _, c, _ in manifest))}}
    m, p = load_model()
    protocol('clip_frozen', m, p, manifest, texts, classes, out)
    if os.path.exists(FT_WEIGHTS):
        m2, _ = load_model(weights=FT_WEIGHTS)
        protocol('sonar_ft_nksid_transfer', m2, p, manifest, texts, classes, out)
        del m2
    if os.path.exists('outputs/ocean_clip_flickrft.pt'):
        m3, _ = load_model(weights='outputs/ocean_clip_flickrft.pt')
        protocol('clip_flickrft', m3, p, manifest, texts, classes, out)
        del m3
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
