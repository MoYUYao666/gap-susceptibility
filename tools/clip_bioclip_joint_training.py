"""(e) Dual-branch joint (co-training) optimization -- a shared text tower learns both objectives in the same batch.
A: rare-species images × class prompts (taxonomic branch) B: ML16K frames × QA text (natural-language branch)
Each step: 16 pairs each from A/B → symmetric contrastive losses computed separately then averaged; dual-tower LoRA; 10ep.
Evaluation: fish-67(σ_m/τ/top1)+ ML16K retrieval R@1. Controls (LoRA single objective / FullFT).
Output: outputs/bioclip_joint_training.json
"""
import os, sys, json, glob, io
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
from datasets import load_dataset

TEMPLATE = 'a photo of a {}'
SEED = 42
EPOCHS = 10
BASE_CKPT = 'models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin'
OUT = 'outputs/bioclip_joint_training.json'
ROOT = 'data/marinelife16k/data/selected_frames'
SUB = 'outputs/ocean_subset.json'


def main():
    sub = json.load(open(SUB, encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    dd = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')),
        split='train')
    A = []
    tr_classes = sorted(classes)[:57]  # hold out the last 10 classes to evaluate true generalization
    for j in idx:
        b = dd[j]['file_name']
        if dd[j]['sciName'] not in tr_classes:
            continue
        im = (Image.open(io.BytesIO(b['bytes'])).convert('RGB') if isinstance(b, dict) and b.get('bytes')
              else Image.open(b['path']).convert('RGB') if isinstance(b, dict) else b.convert('RGB'))
        A.append((im, TEMPLATE.format(dd[j]['sciName'])))
    B = []
    for qf in sorted(glob.glob(os.path.join(ROOT, '*', '*', 'qa.jsonl'))):
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
                    B.append((frames[li % len(frames)], 'Question: ' + q + '\nAnswer: ' + a))
    print('A=%d B=%d' % (len(A), len(B)), flush=True)

    m, _, pre = open_clip.create_model_and_transforms(
        'ViT-B-16', pretrained=BASE_CKPT, device='cuda')
    tok = open_clip.get_tokenizer('ViT-B-16')
    m = get_peft_model(m, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias='none',
        target_modules=['c_fc', 'c_proj', 'q_proj', 'k_proj', 'v_proj', 'out_proj']))
    m.train()
    opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    nA, nB = len(A), len(B)
    losses = []
    for ep in range(EPOCHS):
        pa = np.random.RandomState(SEED + ep).permutation(nA)
        pb = np.random.RandomState(SEED * 7 + ep).permutation(nB)
        tot, cnt = 0.0, 0
        steps = max(nA, nB)
        for s in range(0, steps, 16):
            sel_a = pa[s % steps:s % steps + 16]
            sel_b = pb[s % steps:s % steps + 16]
            loss = 0.0
            for sel, data in [(sel_a, A), (sel_b, B)]:
                sel = [i % len(data) for i in sel]
                if not sel:
                    continue

                def get_img(data, i):
                    x = data[i][0]
                    if isinstance(x, str):
                        return Image.open(x).convert('RGB')
                    return x

                xs = torch.stack([pre(get_img(data, i)) for i in sel]).to('cuda')
                txt = tok([data[i][1] for i in sel]).to('cuda')
                opt.zero_grad()
                with torch.cuda.amp.autocast():
                    if_ = F.normalize(m.encode_image(xs), dim=-1)
                    tf_ = F.normalize(m.encode_text(txt), dim=-1)
                    logits = if_ @ tf_.T * m.logit_scale.exp()
                    lab = torch.arange(len(sel), device='cuda')
                    l = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
                l.backward()
                opt.step()
                loss += l.item()
            tot += loss / 2
            cnt += 1
        sched.step()
        losses.append(round(tot / max(cnt, 1), 4))
        print('  ep%d loss=%.4f' % (ep + 1, losses[-1]), flush=True)

    # fish-67 protocol
    cls = classes
    labels_t = torch.tensor([classes.index(r['sciName']) for r in dd.select(idx)])
    cfg = dict(kind='openclip', model=m, pre=pre, tag='bioclip')
    tf = gs.encode_text(cfg, [TEMPLATE.format(c) for c in cls])
    img_full = gs.encode_images(cfg, dd, idx)
    gap = tf.mean(0) - img_full.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    m_c = dH.cpu().numpy() @ tf.cpu().numpy().T
    S0 = (img_full @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    lbl = labels_t.numpy()
    ho = set(classes.index(s) for s in sorted(classes)[57:])
    ho_mask = [i for i, c in enumerate(lbl) if int(c) in ho]
    mar = {'sigma_m': round(float(np.std(m_c)), 4),
           'top1_0': round(float((S0.argmax(1) == labels_t.numpy()).mean() * 100), 3),
           'top1_heldout': round(float((S0.argmax(1)[ho_mask] == lbl[ho_mask]).mean() * 100), 3)}
    torch.save(m.state_dict(), 'outputs/bioclip_joint_ft.pt')
    with torch.no_grad():
        sh = F.normalize(img_full + 1.0 * gnorm * dH, dim=-1)
    S1 = (sh @ tf.T).cpu().numpy()
    taus1 = []
    for i in range(len(S0)):
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
    for i in range(len(S0)):
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

    queries = mt.build_queries(ROOT)
    frames = sorted(glob.glob(os.path.join(ROOT, '*', '*', '*.jpg')))
    frame_meta = [(fp, os.path.basename(os.path.dirname(os.path.dirname(fp))) + '/'
                   + os.path.basename(os.path.dirname(fp))) for fp in frames]
    vids = sorted(set(v for _, v in frame_meta))
    m.eval()
    ret = mt.run('joint', m, pre, tok, queries, frame_meta, vids)

    res = {'meta': {'model': 'BioCLIP dual-tower LoRA, joint objective (taxonomy + natural QA per batch)',
                    'epochs': EPOCHS, 'nA': nA, 'nB': nB, 'losses': losses},
           'marine': mar, 'retrieval': ret}
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
