"""L5 trajectory hardening: multiple seeds + long range.
- CLIP+Sonar(balanced 650) 10ep × seed {0,99} (seed42 already available) + seed42 × 50ep
- BioCLIP+Marine(fish-67) 10ep × seed {0,99} (seed42 already available)
Evaluates top1/τ/σ_m every epoch. Outputs outputs/dynamics_seed.json
Run: conda run -n pytorch python tools/clip_dynamics_seed.py [sonar_seeds|bio_seeds|sonar50]
"""
import os, sys, json, io
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats

import clip_dynamics as cd

OUT = 'outputs/dynamics_seed.json'
TEMPLATE = 'a photo of a {}'


def set_seed(s):
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


# ---------- CLIP side: reuse cd.train_traj (parameterized through the module globals seed/epochs) ----------
def run_clip(tag, man, texts, labels, eval_info, seed, epochs):
    cd.SEED = seed
    cd.EPOCHS = epochs
    rows = cd.train_traj(tag, man, texts, labels, eval_info)
    return rows


def bio_eval(m, pre, tok, ds, idx, classes, labels, S0, topk5):
    """Evaluation of the current BioCLIP (open_clip) model: top1/tau/sigma_m."""
    with torch.no_grad():
        tf = F.normalize(m.encode_text(tok([TEMPLATE.format(c) for c in classes]).to('cuda')), dim=-1)
        feats = []
        for i in range(0, len(idx), 32):
            b = ds[idx[i:i + 32]]['file_name']
            imgs = [Image.open(io.BytesIO(x['bytes'])) if isinstance(x, dict) and x.get('bytes')
                    else (Image.open(x['path']) if isinstance(x, dict) else x) for x in b]
            xs = torch.stack([pre(im) for im in imgs]).to('cuda')
            feats.append(F.normalize(m.encode_image(xs), dim=-1))
        fi = torch.cat(feats)
    S = (fi @ tf.T).cpu().numpy()
    top1 = float((S.argmax(1) == labels).mean() * 100)
    taus = []
    for i in range(len(S)):
        r1, r2 = S0[i][topk5[i]], S[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    gap = (tf.mean(0) - fi.mean(0)).cpu().numpy()
    gnorm = np.linalg.norm(gap)
    dH = gap / gnorm
    mc = dH @ tf.cpu().numpy().T
    return {'top1': round(top1, 3), 'tau': round(float(np.mean(taus)), 4),
            'sigma_m': round(float(np.std(mc)), 4)}


def run_bio(mode, ds, sub, seed, epochs):
    import io
    import open_clip
    classes = sub['classes']
    idx = sub['subset_idx']
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    tok = open_clip.get_tokenizer('ViT-B-16')
    set_seed(seed)
    m, _, pre = open_clip.create_model_and_transforms(
        'ViT-B-16', pretrained='models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin', device='cuda')

    def feats():
        with torch.no_grad():
            tf = F.normalize(m.encode_text(tok([TEMPLATE.format(c) for c in classes]).to('cuda')), dim=-1)
            out = []
            for i in range(0, len(idx), 32):
                b = ds[idx[i:i + 32]]['file_name']
                imgs = [Image.open(io.BytesIO(x['bytes'])) if isinstance(x, dict) and x.get('bytes')
                        else (Image.open(x['path']) if isinstance(x, dict) else x) for x in b]
                xs = torch.stack([pre(im) for im in imgs]).to('cuda')
                out.append(F.normalize(m.encode_image(xs), dim=-1))
            return tf, torch.cat(out)

    tf0, base0 = feats()
    S0 = (base0 @ tf0.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]

    if mode == 'marine':
        caps = [TEMPLATE.format(classes[c]) for c in labels]
        data = []
        for j in range(len(idx)):
            b = ds[idx[j]]['file_name']
            im = (Image.open(io.BytesIO(b['bytes'])) if isinstance(b, dict) and b.get('bytes')
                  else Image.open(b['path']) if isinstance(b, dict) else b)
            data.append((im, caps[j]))
    else:
        pairs = cd.load_flickr(1000)
        data = [(Image.open(p), c) for p, c in pairs]
    n = len(data)
    for p in m.parameters():
        p.requires_grad_(True)
    opt = torch.optim.AdamW(m.parameters(), lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    m.train()
    rows = []
    for ep in range(epochs):
        perm = np.random.RandomState(seed + ep).permutation(n)
        tot, cnt = 0.0, 0
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
            tot += loss.item(); cnt += 1
        sched.step()
        m.eval()
        st = bio_eval(m, pre, tok, ds, idx, classes, labels, S0, topk5)
        st = {'epoch': ep + 1, 'loss': round(tot / cnt, 4), **st}
        rows.append(st)
        print('  %s seed%d ep%d tau=%.4f top1=%.2f sigma_m=%.4f' %
              (mode, seed, ep + 1, st['tau'], st['top1'], st['sigma_m']), flush=True)
        m.train()
    del m
    torch.cuda.empty_cache()
    return rows


def main():
    import io
    modes = [m for m in sys.argv[1:] if m in ('sonar_seeds', 'bio_seeds', 'sonar50')] or \
        ['sonar_seeds', 'bio_seeds', 'sonar50']
    res = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}

    if 'sonar_seeds' in modes or 'sonar50' in modes:
        man = cd.build_sonar()
        labels = np.array([cd.SONAR_CLASSES.index(c) for _, c in man])
        texts = [TEMPLATE.format(c) for c in cd.SONAR_CLASSES]
        simgs = [Image.open(fp).convert('RGB') for fp, _ in man]
        info = {'f0_imgs': simgs}
        if 'sonar_seeds' in modes:
            for s in [0, 1]:
                print('== CLIP+Sonar seed%d (10ep) ==' % s, flush=True)
                res['clip_sonar_s%d' % s] = run_clip('sonar', man, texts, labels, info, s, 10)
                json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        if 'sonar50' in modes:
            print('== CLIP+Sonar seed42 (50ep) ==', flush=True)
            res['clip_sonar_50ep'] = run_clip('sonar', man, texts, labels, info, 42, 50)
            json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)

    if 'bio_seeds' in modes:
        from datasets import load_dataset
        ds = load_dataset('parquet', data_files=sorted(
            os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')),
            split='train')
        sub = json.load(open('outputs/ocean_subset.json', encoding='utf-8'))
        for s in [0, 1]:
            print('== BioCLIP+Marine seed%d (10ep) ==' % s, flush=True)
            res['bio_marine_s%d' % s] = run_bio('marine', ds, sub, s, 10)
            json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)

    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
