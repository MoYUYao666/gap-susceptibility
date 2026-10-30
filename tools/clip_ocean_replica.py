"""L1 公开语料复刻实验:BioCLIP + MarineLife-16K 人工 QA 文本对 (数据完全已知) 10ep 匹配调度微调。
判别逻辑: 若复刻模型(海洋域+自然文本) 保留自然文本检索(R@1 高) 而 OceanCLIP(分类学文本)≈0.26%,
则特化代价由分类学文本驱动而非海洋域本身 → 支撑 Part V 机制解读。
评估: ① fish-67 协议(τ_pred/τ_meas/σ_m/top1/Δτ 文本侧λ=1) ② ML16K 视频级检索 R@1。
输出: outputs/ocean_replica.json
运行: conda run -n pytorch python tools/clip_ocean_replica.py
"""
import os, sys, json, glob
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

spec = importlib.util.spec_from_file_location('gs', 'tools/clip_ocean_gap_surgery.py')
gs = importlib.util.module_from_spec(spec)
sys.modules['gs'] = gs
spec.loader.exec_module(gs)
spec2 = importlib.util.spec_from_file_location('mt', 'tools/clip_ocean_ml16k_retrieval.py')
mt = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(mt)

TEMPLATE = 'a photo of a {}'
SEED = 42
EPOCHS = 10
BASE_CKPT = 'models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin'
FT_WEIGHTS = 'outputs/ocean_replica_ft.pt'
OUT = 'outputs/ocean_replica.json'
ROOT = 'data/marinelife16k/data/selected_frames'


def build_pairs(root):
    """每 QA 文本配其视频目录中的一帧 (确定性: 行号 % 帧数)。"""
    qa = []
    for qf in sorted(glob.glob(os.path.join(root, '*', '*', 'qa.jsonl'))):
        vdir = os.path.dirname(qf)
        frames = sorted(glob.glob(os.path.join(vdir, '*.jpg')))
        if not frames:
            continue
        vid = os.path.basename(os.path.dirname(vdir)) + '/' + os.path.basename(vdir)
        with open(qf, encoding='utf-8') as f:
            for li, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    import json as _j
                    qa_d = _j.loads(line)
                except Exception:
                    continue
                q = qa_d.get('question', '')
                a = qa_d.get('answer_text', '')
                if q and a:
                    fp = frames[li % len(frames)]
                    qa.append((fp, q + ' ' + a, vid))
    return qa


def main():
    pairs = build_pairs(ROOT)
    print('pairs=%d' % len(pairs), flush=True)

    m, _, pre = open_clip.create_model_and_transforms(
        'ViT-B-16', pretrained=BASE_CKPT, device='cuda')
    tok = open_clip.get_tokenizer('ViT-B-16')
    for pp in m.parameters():
        pp.requires_grad_(True)
    opt = torch.optim.AdamW(m.parameters(), lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    m.train()
    n = len(pairs)
    losses = []
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(n)
        tot, cnt = 0.0, 0
        for i in range(0, n, 32):
            sel = perm[i:i + 32]
            xs = torch.stack([pre(Image.open(pairs[j][0]).convert('RGB')) for j in sel]).to('cuda')
            txt = tok([pairs[j][1] for j in sel]).to('cuda')
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
        losses.append(round(tot / cnt, 4))
        print('  ep%d loss=%.4f' % (ep + 1, losses[-1]), flush=True)
    torch.save(m.state_dict(), FT_WEIGHTS)

    # ---- ① fish-67 协议 ----
    ds, sub = gs.build_subset()
    classes = sub['classes']
    idx = sub['subset_idx']
    labels_t = torch.tensor([classes.index(r['sciName']) for r in ds.select(idx)])
    cfg = dict(kind='openclip', model=m, pre=pre, tag='bioclip')
    tf = gs.encode_text(cfg, [TEMPLATE.format(c) for c in classes])
    img_full = gs.encode_images(cfg, ds, idx)
    gap = tf.mean(0) - img_full.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    m_c = dH.cpu().numpy() @ tf.cpu().numpy().T
    S0 = (img_full @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    tau_idx = list(range(len(idx)))
    mar = {'sigma_m': round(float(np.std(m_c)), 4), 'mean_m': round(float(np.mean(m_c)), 4),
           'top1_0': round(float((S0.argmax(1) == labels_t.numpy()).mean() * 100), 3), 'rows': []}
    for lam in [-1.0, -0.5, -0.25, 0.25, 0.5, 1.0, 2.0]:
        with torch.no_grad():
            sh = F.normalize(img_full + lam * gnorm * dH, dim=-1)
        cg, t1, tau = gs.evaluate(sh.cuda() if False else sh, tf, sh, tf, labels_t, tau_idx, S0, topk5)
        mar['rows'].append({'lambda': lam, 'top1': round(t1, 3), 'tau_meas': round(tau, 4)})
        print('  marine λ=%+.2f top1=%.2f tau=%.4f' % (lam, t1, tau), flush=True)
    # 文本侧 λ=1 (Δτ)
    with torch.no_grad():
        tf2 = F.normalize(tf - 1.0 * gnorm * dH, dim=-1)
    S2 = (img_full @ tf2.T).cpu().numpy()
    taus2 = []
    for i in tau_idx:
        r1, r2 = S0[i][topk5[i]], S2[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus2.append(t)
    mar['tau_text1'] = round(float(np.mean(taus2)), 4)
    del img_full, tf
    torch.cuda.empty_cache()

    # ---- ② ML16K 检索 (q_ans 变体) ----
    queries = mt.build_queries(ROOT)
    frames = sorted(glob.glob(os.path.join(ROOT, '*', '*', '*.jpg')))
    frame_meta = [(fp, os.path.basename(os.path.dirname(os.path.dirname(fp))) + '/'
                   + os.path.basename(os.path.dirname(fp))) for fp in frames]
    vids = sorted(set(v for _, v in frame_meta))
    print('videos=%d frames=%d queries=%d' % (len(vids), len(frame_meta), len(queries)), flush=True)
    m.eval()
    ret = mt.run('replica', m, pre, tok, queries, frame_meta, vids)

    res = {'meta': {'train_pairs': n, 'epochs': EPOCHS, 'losses': losses,
                    'data': 'MarineLife-16K frame + human QA (public, fully documented)'},
           'marine': mar, 'retrieval': ret}
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
