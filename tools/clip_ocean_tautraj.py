"""海洋微调逐 epoch τ 轨迹（对接 A1 的"τ 最早侵蚀信号"协议，海洋域验证）。
对 bioclip 分别做 {marine, flickr} 10ep FullFT（与 A2 判别实验同配置、每模式从冻结基座重载），
每 epoch 后测量：marine top-1(t)、τ(t)（冻结 top-5 集上冻结 vs 当前模型分数序 Kendall）、CG(t)。
用法: python tools/clip_ocean_tautraj.py [marine|flickr|both]   (默认 both)
输出: outputs/ocean_tautraj.json
"""
import os, sys, json, io
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
SEED = 42
EPOCHS = 10
SUB = 'outputs/ocean_subset.json'
OUT = 'outputs/ocean_tautraj.json'


def set_seed(s):
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def build_flickr():
    import json as _j
    img_dir = os.path.join('flickr30k', 'flickr30k-images')
    data = _j.load(open(os.path.join('flickr30k', 'flickr30k.json'), encoding='utf-8'))
    out = []
    for it in data:
        fn = it['image']
        if os.path.exists(os.path.join(img_dir, fn)) and it.get('captions'):
            out.append((os.path.join(img_dir, fn), it['captions'][0]))
    return out


def main():
    modes = [m for m in sys.argv[1:] if m in ('marine', 'flickr')] or ['marine', 'flickr']
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    sub = json.load(open(SUB, encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    texts = [TEMPLATE.format(c) for c in classes]
    tok = open_clip.get_tokenizer('ViT-B-16')

    results = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}

    for mode in modes:
        print('== %s ==' % mode, flush=True)
        set_seed(SEED)
        mm, _, pre = open_clip.create_model_and_transforms(
            'ViT-B-16', pretrained='models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin', device='cuda')
        m = mm

        def marine_feats():
            with torch.no_grad():
                tf = F.normalize(m.encode_text(tok(texts).to('cuda')), dim=-1)
                feats = []
                for i in range(0, len(idx), 32):
                    b = ds[idx[i:i + 32]]['file_name']
                    imgs = []
                    for x in b:
                        imgs.append(Image.open(io.BytesIO(x['bytes'])) if isinstance(x, dict) and x.get('bytes')
                                    else Image.open(x['path']) if isinstance(x, dict) else x)
                    xs = torch.stack([pre(im) for im in imgs]).to('cuda')
                    feats.append(F.normalize(m.encode_image(xs), dim=-1))
                return F.normalize(tf, dim=-1), torch.cat(feats)

        tf0, base0 = marine_feats()
        S0 = (base0 @ tf0.T).cpu().numpy()
        topk5 = np.argsort(-S0, axis=1)[:, :5]

        def eval_now():
            tf, base = marine_feats()
            S = (base @ tf.T).cpu().numpy()
            top1 = float((S.argmax(1) == labels).mean() * 100)
            taus = []
            for i in range(len(S)):
                r1, r2 = S0[i][topk5[i]], S[i][topk5[i]]
                if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                    continue
                t, _ = stats.kendalltau(r1, r2)
                if np.isfinite(t):
                    taus.append(t)
            cg = (base.mean(0) - tf.mean(0)).norm().item()
            return {'top1': round(top1, 3), 'tau': round(float(np.mean(taus)), 4), 'CG': round(cg, 4)}

        if mode == 'marine':
            caps = [TEMPLATE.format(classes[c]) for c in labels]
            data = []
            for j in range(len(idx)):
                b = ds[idx[j]]['file_name']
                im = (Image.open(io.BytesIO(b['bytes'])) if isinstance(b, dict) and b.get('bytes')
                      else Image.open(b['path']) if isinstance(b, dict) else b)
                data.append((im, caps[j]))
        else:
            pairs = build_flickr()[:1000]
            data = [(Image.open(p), c) for p, c in pairs]
        n = len(data)
        for p in m.parameters():
            p.requires_grad_(True)
        opt = torch.optim.AdamW(m.parameters(), lr=5e-5, weight_decay=0.0)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
        m.train()
        traj = []
        for ep in range(EPOCHS):
            perm = np.random.RandomState(SEED + ep).permutation(n)
            tot = 0.0
            cnt = 0
            for i in range(0, n, 32):
                sel = perm[i:i + 32]
                xs = torch.stack([pre(data[j][0]) for j in sel]).to('cuda')
                txt = tok([data[j][1] for j in sel]).to('cuda')
                opt.zero_grad()
                with torch.cuda.amp.autocast():
                    if_ = F.normalize(m.encode_image(xs), dim=-1)
                    tf_ = F.normalize(m.encode_text(txt), dim=-1)
                    logits = if_ @ tf_.T * m.logit_scale.exp()
                    lab = torch.arange(len(sel), device='cuda')
                    loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
                loss.backward()
                opt.step()
                tot += loss.item()
                cnt += 1
            sched.step()
            m.eval()
            r = eval_now()
            traj.append({'epoch': ep + 1, 'loss': round(tot / cnt, 4), **r})
            print('  ep%d loss=%.4f top1=%.2f tau=%.4f CG=%.4f' %
                  (ep + 1, traj[-1]['loss'], r['top1'], r['tau'], r['CG']), flush=True)
            m.train()
        results[mode] = traj
        json.dump(results, open(OUT, 'w', encoding='utf-8'), indent=1)
        del m
        torch.cuda.empty_cache()
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
