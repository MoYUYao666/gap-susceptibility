"""A3 enhancement 1: sonar PEFT protectiveness (isomorphic to A2 PEFT).
On SonarCLIP same-source data (650 images / 8 classes + class-name prompts), run {lora_text, lora_both, bitfit}×10ep (same schedule),
post-training probes: same marine probe design — task R@1 (class-conditional i2t/t2i) + sonar zero-shot top-1 + τ@λ=1 + σ_m;
protectiveness compared with the existing sonar FullFT (sonar_ft).
Output: outputs/sonar_peft.json
"""
import os, sys, json, collections
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from transformers import CLIPModel, CLIPProcessor
from peft import LoraConfig, get_peft_model

TEMPLATE = 'a photo of a {}'
SEED = 42
EPOCHS = 10
MDIR = 'models/clip-vit-base-patch32'
IMG_ROOT = 'data/NKSID/NKSID'
OUT = 'outputs/sonar_peft.json'
CLASSES = ['big propeller', 'cylinder', 'fishing net', 'floats', 'iron pipeline',
           'small propeller', 'soft pipeline', 'tire']
CLASS_DIR = ['big_propeller', 'cylinder', 'fishing_net', 'floats', 'iron_pipeline',
             'small_propeller', 'soft_pipeline', 'tire']
CAP_PER_CLASS = 90
ARGS = {'lora_text': True, 'lora_both': True, 'bitfit': True, 'fullft': True}


def manifest():
    m = []
    for c, d in zip(CLASSES, CLASS_DIR):
        p = os.path.join(IMG_ROOT, d)
        if not os.path.isdir(p):
            p = IMG_ROOT
        fs = sorted(f for f in os.listdir(p) if f.lower().endswith(('.jpg', '.png')))[:CAP_PER_CLASS]
        m.extend((os.path.join(p, f), c) for f in fs)
    return m


def load_base():
    return CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda()


def set_seed(s):
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def probe(m, p, imgs, texts, labels, freeze):
    m.eval()
    ti = p(text=texts, return_tensors='pt', padding=True).to('cuda')
    with torch.no_grad():
        out = m.text_model(**ti)
        pooled = out[1] if isinstance(out, tuple) else out.pooler_output
        tf = F.normalize(m.text_projection(pooled), dim=-1)
        feats = []
        for i in range(0, len(imgs), 32):
            inp = p(images=imgs[i:i + 32], return_tensors='pt').to('cuda')
            vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
            vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            feats.append(F.normalize(m.visual_projection(vp), dim=-1))
        base = torch.cat(feats)
    gap = tf.mean(0) - base.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    S0 = (base @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    with torch.no_grad():
        sh = F.normalize(base + 1.0 * gnorm * dH, dim=-1)
    S1 = (sh @ tf.T).cpu().numpy()
    taus = []
    for i in range(len(S0)):
        r1, r2 = S0[i][topk5[i]], S1[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    # retrieval R@1 (class-conditional, same protocol as A2): i2t == top-1; t2i is text→image
    i2t = float((S0.argmax(1) == labels).mean())
    t2i = float(np.mean([labels[int(S0[:, c].argmax())] == c for c in range(len(CLASSES))]))
    return {'top1_0': round(float((S0.argmax(1) == labels).mean() * 100), 3),
            'tau_l1': round(float(np.mean(taus)), 4), 'R1': round((i2t + t2i) / 2, 4),
            'CG': round(gnorm, 4)}


def main():
    man = manifest()
    labels = np.array([CLASSES.index(c) for _, c in man])
    texts = [TEMPLATE.format(c) for c in CLASSES]
    imgs = [Image.open(fp).convert('RGB') for fp, _ in man]
    p = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
    n = len(man)
    res = {'meta': {'n_images': n, 'n_classes': len(CLASSES), 'epochs': EPOCHS}}
    for method in ['lora_text', 'lora_both', 'bitfit']:
        print('== %s ==' % method, flush=True)
        set_seed(SEED)
        m = load_base()
        if method == 'lora_text':
            cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                             target_modules=['qkv', 'c_fc', 'c_proj', 'in_proj', 'out_proj',
                                             'text_model.encoder.layers.*.self_attn.k_proj',
                                             'text_model.encoder.layers.*.self_attn.v_proj'])
            m = get_peft_model(m, cfg)
            for n_, prm in m.named_parameters():
                if 'vision_model' in n_.split('.'):
                    prm.requires_grad_(False)
                elif 'lora' not in n_ and 'vision' not in n_:
                    prm.requires_grad_(False)
        elif method == 'lora_both':
            cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                             target_modules=['q_proj', 'v_proj', 'k_proj', 'out_proj',
                                             'fc1', 'fc2', 'c_fc', 'c_proj', 'in_proj', 'out_proj'])
            m = get_peft_model(m, cfg)
        elif method == 'bitfit':
            for n_, prm in m.named_parameters():
                prm.requires_grad_(False)
            for n_, prm in m.named_parameters():
                if '.bias' in n_:
                    prm.requires_grad_(True)
        opt = torch.optim.AdamW([prm for prm in m.parameters() if prm.requires_grad], lr=1e-4, weight_decay=0.0)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
        for ep in range(EPOCHS):
            perm = np.random.RandomState(SEED + ep).permutation(n)
            tot, cnt = 0.0, 0
            for i in range(0, n, 32):
                sel = perm[i:i + 32]
                xs = torch.stack([p(images=imgs[j])['pixel_values'][0] for j in sel]).to('cuda')
                txt = p(text=[TEMPLATE.format(man[j][1]) for j in sel], return_tensors='pt',
                        padding=True)['input_ids'].to('cuda')
                opt.zero_grad()
                with torch.cuda.amp.autocast():
                    outm = m(pixel_values=xs, input_ids=txt, return_loss=False)
                    if_ = F.normalize(outm.image_embeds, dim=-1)
                    tf_ = F.normalize(outm.text_embeds, dim=-1)
                    logits = if_ @ tf_.T * m.logit_scale.exp()
                    lab = torch.arange(len(sel), device='cuda')
                    loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
                loss.backward()
                opt.step()
                tot += loss.item(); cnt += 1
            sched.step()
        r = probe(m, p, imgs, texts, labels, None)
        res[method] = r
        print('  %s: top1=%.2f tau_l1=%.4f R1=%.4f' % (method, r['top1_0'], r['tau_l1'], r['R1']), flush=True)
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        del m
        torch.cuda.empty_cache()
    # reference: existing FullFT results (sonar_protocol.json sonar_ft)
    sp = json.load(open('outputs/sonar_protocol.json', encoding='utf-8'))
    res['fullft'] = {'top1_0': sp['sonar_ft']['top1_0'],
                     'tau_l1': [r['tau_meas'] for r in sp['sonar_ft']['rows'] if r['lambda'] == 1.0][0],
                     'source': 'sonar_protocol.json'}
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
