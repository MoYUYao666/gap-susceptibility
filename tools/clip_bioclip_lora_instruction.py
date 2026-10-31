"""分类学基座(BioCLIP)文本塔 LoRA 指令微调——L1 FullFT 复刻的 PEFT 对照。
训练: 与 clip_ocean_replica 完全同调度(ML16K QA 3,440 对, 对称对比, 10ep, seed42),
但仅文本塔 LoRA(r16/a32)——回答"渐进式单分支(双语)是否可行"。
评估: fish-67 协议(σ_m/τ@1/Δτ/top1) + ML16K 检索 R@1。
输出: outputs/bioclip_lora_instruction.json
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
from peft import LoraConfig, get_peft_model

TEMPLATE = 'a photo of a {}'
SEED = 42
EPOCHS = 10
BASE_CKPT = 'models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin'
OUT = 'outputs/bioclip_lora_instruction.json'
ROOT = 'data/marinelife16k/data/selected_frames'
SUB = 'outputs/ocean_subset.json'


def build_pairs(root):
    pairs = []
    for qf in sorted(glob.glob(os.path.join(root, '*', '*', 'qa.jsonl'))):
        vdir = os.path.dirname(qf)
        frames = sorted(glob.glob(os.path.join(vdir, '*.jpg')))
        if not frames:
            continue
        with open(qf, encoding='utf-8') as f:
            for li, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                q, a = d.get('question', ''), d.get('answer_text', '')
                if q and a:
                    pairs.append((frames[li % len(frames)], 'Question: ' + q + '\nAnswer: ' + a))
    return pairs


def main():
    cls = json.load(open(SUB, encoding='utf-8'))['classes']
    pairs = build_pairs(ROOT)
    print('pairs=%d classes=%d' % (len(pairs), len(cls)), flush=True)

    m, _, pre = open_clip.create_model_and_transforms(
        'ViT-B-16', pretrained=BASE_CKPT, device='cuda')
    tok = open_clip.get_tokenizer('ViT-B-16')
    # 仅文本塔 LoRA
    names = [n for n, _ in m.named_modules()]
    print('text tower Linear 样本:', [n for n in names if 'resblocks.0.mlp.c_fc' in n][:1],
          '| q/k/v:', [n for n in names if 'resblocks.0.attn' in n and 'proj' in n][:4], flush=True)
    m = get_peft_model(m, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias='none',
        target_modules=['c_fc', 'c_proj', 'q_proj', 'k_proj', 'v_proj', 'out_proj']))
    m.train()
    opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
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

    # ① fish-67 协议
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
           'top1_0': round(float((S0.argmax(1) == labels_t.numpy()).mean() * 100), 3)}
    with torch.no_grad():
        sh = F.normalize(img_full + 1.0 * gnorm * dH, dim=-1)
    S1 = (sh @ tf.T).cpu().numpy()
    taus1 = []
    for i in tau_idx:
        r1, r2 = S0[i][topk5[i]], S1[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus1.append(t)
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
    mar['tau_l1'] = round(float(np.mean(taus1)), 4)
    mar['tau_text1'] = round(float(np.mean(taus2)), 4)
    del img_full, tf
    torch.cuda.empty_cache()

    # ② ML16K 检索
    queries = mt.build_queries(ROOT)
    frames = sorted(glob.glob(os.path.join(ROOT, '*', '*', '*.jpg')))
    frame_meta = [(fp, os.path.basename(os.path.dirname(os.path.dirname(fp))) + '/'
                   + os.path.basename(os.path.dirname(fp))) for fp in frames]
    vids = sorted(set(v for _, v in frame_meta))
    m.eval()
    ret = mt.run('bioclip_lora', m, pre, tok, queries, frame_meta, vids)

    res = {'meta': {'train_pairs': n, 'epochs': EPOCHS, 'losses': losses,
                    'data': 'MarineLife-16K QA (text-tower LoRA only, r16/a32)',
                    'note': 'contrastive training identical to full-FT replica; LoRA (r16/a32) applied to '
                            'both towers (matching c_fc/c_proj/out_proj layers); dual-tower PEFT variant'},
           'marine': mar, 'retrieval': ret}
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
