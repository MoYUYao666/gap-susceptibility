"""判别实验 A-③: 匹配规模 2×2 的海洋侧——bioclip + 海洋子集(rare-species 67类) FullFT 10 epoch。
与 A-②（Flickr 10 epoch）同训练配置（lr 5e-5 / cosine / seed 42 / 对称 CE），仅数据域不同。
输出: outputs/ocean_marineft10_bioclip.pt + outputs/ocean_marineft10_sigma.json
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
OUT_W = 'outputs/ocean_marineft10_bioclip.pt'
OUT = 'outputs/ocean_marineft10_sigma.json'


def set_seed(s):
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def main():
    set_seed(SEED)
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    sub = json.load(open(SUB, encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    cls_arr = np.array([classes.index(r['sciName']) for r in ds.select(idx)])  # 位置 j → 类序号
    n = len(idx)
    tok = open_clip.get_tokenizer('ViT-B-16')
    m, _, pre = open_clip.create_model_and_transforms(
        'ViT-B-16', pretrained='models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin', device='cuda')
    for p in m.parameters():
        p.requires_grad_(True)
    opt = torch.optim.AdamW(m.parameters(), lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)

    def marine_batch(sel):
        imgs = []
        caps = []
        for j in sel:
            b = ds[idx[j]]['file_name']
            im = Image.open(io.BytesIO(b['bytes'])) if isinstance(b, dict) and b.get('bytes') else \
                Image.open(b['path']) if isinstance(b, dict) else b
            imgs.append(im)
            caps.append(TEMPLATE.format(classes[int(cls_arr[j])]))
        xs = torch.stack([pre(im) for im in imgs]).to('cuda')
        txt = tok(caps).to('cuda')
        return xs, txt

    m.train()
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(n)
        tot = 0.0
        cnt = 0
        for i in range(0, n, 32):
            sel = perm[i:i + 32]
            xs, txt = marine_batch(sel)
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
        print('ep%d loss=%.4f' % (ep, tot / cnt), flush=True)
    torch.save(m.state_dict(), OUT_W)
    print('saved', OUT_W, flush=True)

    # 海洋协议测量
    texts = [TEMPLATE.format(c) for c in classes]
    labels = cls_arr
    m.eval()
    with torch.no_grad():
        tf = F.normalize(m.encode_text(tok(texts).to('cuda')), dim=-1)
        feats = []
        for i in range(0, n, 32):
            b = ds[idx[i:i + 32]]['file_name']
            imgs = []
            for x in b:
                imgs.append(Image.open(io.BytesIO(x['bytes'])) if isinstance(x, dict) and x.get('bytes')
                            else Image.open(x['path']) if isinstance(x, dict) else x)
            xs = torch.stack([pre(im) for im in imgs]).to('cuda')
            feats.append(F.normalize(m.encode_image(xs), dim=-1))
        base = torch.cat(feats)
    gap = tf.mean(0) - base.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    m_c = (dH @ tf.T).cpu().numpy()
    S0 = (base @ tf.T).cpu().numpy()
    top1_0 = float((S0.argmax(1) == labels).mean() * 100)
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    with torch.no_grad():
        sh = F.normalize(base + 1.0 * gnorm * dH, dim=-1)
    S1 = (sh @ tf.T).cpu().numpy()
    top1_1 = float((S1.argmax(1) == labels).mean() * 100)
    taus = []
    for i in range(len(S0)):
        r1, r2 = S0[i][topk5[i]], S1[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    out = {'gap_norm': round(gnorm, 4), 'mean_m': round(float(np.mean(m_c)), 4),
           'sigma_m': round(float(np.std(m_c)), 4),
           'top1_0': round(top1_0, 3), 'top1_l1': round(top1_1, 3), 'tau_l1': round(float(np.mean(taus)), 4)}
    json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1)
    print(json.dumps(out, indent=1), flush=True)
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
