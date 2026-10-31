"""Ocean λ 平移手术：把 A1 的 gap surgery 协议移植到海洋视觉模型。
协议（与 tools/clip_a1_crossmodel.py / clip_a1_text_surgery.py 一致）：
  d_hat = (mu_t - mu_i) / ||mu_t - mu_i||   文本质心 - 图像质心（海洋子集自估）
  图像侧: img' = normalize(img + lam*gap_norm*d_hat)        λ ∈ {-1,-0.5,-0.25,0,0.25,0.5,1,2}
  文本侧: txt' = normalize(txt - lam*gap_norm*d_hat)        λ ∈ {0,0.5,1,2}
  指标: CG=||mean(img') - mean(txt')||, top1(零样本, 类集=海洋子集 sciName),
        tau(逐图 top-5 类分数 Kendall 均值, 基线 vs 手术)
模型: oceanclip(BioCLIP基座+海洋微调) / bioclip(仅基座) / clip / openclip_tf / siglip
输出: outputs/ocean_gap_surgery.json + outputs/ocean_subset.json（子集索引）
运行环境: conda pytorch (torch 2.9.1+cu130, open_clip 3.3.0)
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
import open_clip

TEMPLATE = 'a photo of a {}'
MIN_PER_CLASS = 8      # 每类最少图像数（保证统计稳定）
MAX_PER_CLASS = 24     # 每类最多图像数（均衡，防长尾）
SEED = 42
OUT = 'outputs/ocean_gap_surgery.json'
OUT_SUB = 'outputs/ocean_subset.json'
FISH_CLASSES = ['Actinopterygii', 'Chondrichthyes', 'Coelacanthi']


def build_subset():
    """从 rare-species 抽取海洋鱼类子集：类 = sciName，图像按类均衡。"""
    files = sorted(os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data'))
    ds = load_dataset('parquet', data_files=files, split='train')
    print('总行数', len(ds), flush=True)
    idx_fish = [i for i, r in enumerate(ds) if r['class'] in FISH_CLASSES]
    print('鱼类行数', len(idx_fish), flush=True)
    sub = ds.select(idx_fish)
    import collections
    per_class = collections.defaultdict(list)
    for i, r in enumerate(sub):
        per_class[r['sciName']].append(idx_fish[i])   # 存原数据集索引
    keep_classes = {c: v for c, v in per_class.items() if len(v) >= MIN_PER_CLASS}
    print('≥%d 图的类数: %d' % (MIN_PER_CLASS, len(keep_classes)), flush=True)
    rng = np.random.RandomState(SEED)
    chosen = []
    for c, v in sorted(keep_classes.items()):
        v = sorted(v)
        if len(v) > MAX_PER_CLASS:
            v = [v[i] for i in rng.choice(len(v), MAX_PER_CLASS, replace=False)]
        for j in v:
            chosen.append((c, j))
    classes = sorted(set(c for c, _ in chosen))
    idx = [j for _, j in chosen]
    out = {
        'classes': classes,
        'class_counts': {c: sum(1 for cc, _ in chosen if cc == c) for c in classes},
        'n_images': len(idx),
        'subset_idx': idx,
    }
    json.dump(out, open(OUT_SUB, 'w', encoding='utf-8'), indent=2)
    return ds, out


def load_models():
    from transformers import CLIPModel, CLIPProcessor, SiglipModel, SiglipProcessor
    MODELS = {}
    # open_clip: BioCLIP 基座
    m_b, _, p_b = open_clip.create_model_and_transforms(
        'ViT-B-16', pretrained='models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin', device='cuda')
    m_b.eval()
    MODELS['bioclip'] = dict(kind='openclip', model=m_b, pre=p_b, tag='bioclip')
    # open_clip: OceanCLIP（海洋微调）
    ck = torch.load('models/oceanclip-0.15b/oceanclip-bio/epoch_50.pt', map_location='cpu')
    m_o, _, p_o = open_clip.create_model_and_transforms(
        'ViT-B-16', pretrained='models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin', device='cuda')
    m_o.load_state_dict(ck['state_dict'], strict=False)
    m_o.eval()
    MODELS['oceanclip'] = dict(kind='openclip', model=m_o, pre=p_o, tag='oceanclip')
    # transformers 家族
    for tag, mdir, use_siglip in [
            ('clip', 'models/clip-vit-base-patch32', False),
            ('openclip_tf', 'models/openclip', False),
            ('siglip', 'models/siglip-base-patch16-224', True)]:
        if not os.path.isdir(mdir):
            print('跳过 %s（目录 %s 不存在）' % (tag, mdir), flush=True)
            continue
        try:
            if use_siglip:
                M, P = SiglipModel, SiglipProcessor
            else:
                M, P = CLIPModel, CLIPProcessor
            m = M.from_pretrained(mdir, local_files_only=True).cuda().eval()
            p = P.from_pretrained(mdir, local_files_only=True)
            MODELS[tag] = dict(kind='transformers', model=m, pre=p, tag=tag)
        except Exception as e:
            print('%s 加载失败: %s' % (tag, str(e)[:160]), flush=True)
    return MODELS


def encode_text(cfg, texts):
    if cfg['kind'] == 'openclip':
        tok = open_clip.get_tokenizer('ViT-B-16')
        with torch.no_grad():
            f = cfg['model'].encode_text(tok(texts).to('cuda'))
        return F.normalize(f, dim=-1)
    m, p = cfg['model'], cfg['pre']
    if cfg['tag'] == 'siglip':
        ti = p(text=texts, return_tensors='pt', padding='max_length', max_length=64).to('cuda')
        with torch.no_grad():
            out = m.text_model(**ti)
        return F.normalize(out.pooler_output, dim=-1)
    ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
    with torch.no_grad():
        out = m.text_model(**ti)
        pooled = out[1] if isinstance(out, tuple) else out.pooler_output
        f = m.text_projection(pooled)
    return F.normalize(f, dim=-1)


def encode_images(cfg, ds, idx, batch=32):
    feats = []
    for i in range(0, len(idx), batch):
        imgs = []
        for j in idx[i:i + batch]:
            r = ds[j]
            b = r['file_name']
            if isinstance(b, dict):
                if b.get('bytes'):
                    im = Image.open(io.BytesIO(b['bytes']))
                else:
                    im = Image.open(b['path'])
            else:
                im = b
            imgs.append(im)
        if cfg['kind'] == 'openclip':
            xs = torch.stack([cfg['pre'](im) for im in imgs]).to('cuda')
            with torch.no_grad():
                f = cfg['model'].encode_image(xs)
            feats.append(F.normalize(f, dim=-1))
        else:
            m, p = cfg['model'], cfg['pre']
            inp = p(images=imgs, return_tensors='pt').to('cuda')
            with torch.no_grad():
                vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                f = m.visual_projection(vpooled) if hasattr(m, 'visual_projection') else vpooled
            feats.append(F.normalize(f, dim=-1))
    return torch.cat(feats)


def evaluate(img2, tf2, fi2, ft2, labels, tau_idx, base_np, topk5):
    cg = (fi2.mean(0) - ft2.mean(0)).norm().item()
    s = img2 @ tf2.T
    top1 = (s.argmax(1).cpu() == labels).float().mean().item() * 100
    s_np = s.cpu().numpy()
    taus = []
    for i in tau_idx:
        r1v = base_np[i][topk5[i]]
        r2v = s_np[i][topk5[i]]
        if np.std(r1v) < 1e-12 or np.std(r2v) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1v, r2v)
        if np.isfinite(t):
            taus.append(t)
    return cg, top1, float(np.mean(taus))


def main():
    ds, sub = build_subset()
    classes = sub['classes']
    idx = sub['subset_idx']
    texts = [TEMPLATE.format(c) for c in classes]
    labels = torch.tensor([classes.index(r['sciName']) for r in ds.select(idx)])
    print('子集: %d 类 / %d 图' % (len(classes), len(idx)), flush=True)

    MODELS = load_models()
    all_rows = []
    for tag, cfg in MODELS.items():
        print('== %s ==' % tag, flush=True)
        tf = encode_text(cfg, texts)
        img_full = encode_images(cfg, ds, idx)
        mu_i, mu_t = img_full.mean(0), tf.mean(0)
        gap_vec = mu_t - mu_i
        gap_norm = gap_vec.norm().item()
        d_hat = gap_vec / gap_norm
        base_sims = img_full @ tf.T
        base_np = base_sims.cpu().numpy()
        topk5 = np.argsort(-base_np, axis=1)[:, :5]
        tau_idx = list(range(len(idx)))
        # 图像侧 λ 扫描
        for lam in [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0]:
            with torch.no_grad():
                delta = lam * gap_norm * d_hat
                img2 = F.normalize(img_full + delta, dim=-1)
                fi2 = F.normalize(img_full + delta, dim=-1)
            cg, t1, tau = evaluate(img2, tf, fi2, tf, labels, tau_idx, base_np, topk5)
            row = dict(model=tag, side='image', lam=lam, CG=round(cg, 4), top1=round(t1, 3), tau=round(tau, 4))
            all_rows.append(row)
            print('  %s I λ=%+.2f: CG=%.4f top1=%.2f tau=%.4f' % (tag, lam, cg, t1, tau), flush=True)
            json.dump(all_rows, open(OUT, 'w', encoding='utf-8'), indent=2)
        # 文本侧 λ 扫描
        for lam in [0.0, 0.5, 1.0, 2.0]:
            with torch.no_grad():
                delta = -lam * gap_norm * d_hat
                tf2 = F.normalize(tf + delta, dim=-1)
                ft2 = F.normalize(tf + delta, dim=-1)
            cg, t1, tau = evaluate(img_full, tf2, img_full, ft2, labels, tau_idx, base_np, topk5)
            row = dict(model=tag, side='text', lam=lam, CG=round(cg, 4), top1=round(t1, 3), tau=round(tau, 4))
            all_rows.append(row)
            print('  %s T λ=%+.2f: CG=%.4f top1=%.2f tau=%.4f' % (tag, lam, cg, t1, tau), flush=True)
            json.dump(all_rows, open(OUT, 'w', encoding='utf-8'), indent=2)
        del img_full, tf
        torch.cuda.empty_cache()

    print('ALL DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
