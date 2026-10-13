"""A3 enhancement ②: sonar PEFT/FullFT 3-seed ({1,42,99}; seed 42 reuses the existing sonar_peft.json/sonar_protocol.json).
Rerun {lora_both, fullft} × {1,99} (seed 42 already on file); probes same as clip_sonar_peft.
Output: outputs/sonar_peft_ms.json
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from transformers import CLIPModel, CLIPProcessor
from peft import LoraConfig, get_peft_model
from clip_sonar_peft import manifest, CLASSES, TEMPLATE, probe, load_base, set_seed

EPOCHS = 10
MDIR = 'models/clip-vit-base-patch32'
OUT = 'outputs/sonar_peft_ms.json'


def train(m, p, imgs, texts, labels, seed, method):
    set_seed(seed)
    m = load_base()
    if method == 'lora_both':
        cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                         target_modules=['q_proj', 'v_proj', 'k_proj', 'out_proj', 'fc1', 'fc2'])
        m = get_peft_model(m, cfg)
    elif method == 'fullft':
        for n_, prm in m.named_parameters():
            prm.requires_grad_(True)
    n = len(imgs)
    opt = torch.optim.AdamW([prm for prm in m.parameters() if prm.requires_grad],
                            lr=1e-4 if method != 'fullft' else 5e-5, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    for ep in range(EPOCHS):
        perm = np.random.RandomState(seed + ep).permutation(n)
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
            tot += loss.item()
            cnt += 1
        sched.step()
        print('  %s s%d ep%d loss=%.3f' % (method, seed, ep + 1, tot / cnt), flush=True)
    return m


man = manifest()
labels = np.array([CLASSES.index(c) for _, c in man])
texts = [TEMPLATE.format(c) for c in CLASSES]
imgs = [Image.open(fp).convert('RGB') for fp, _ in man]
p = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)
res = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
for method in ['lora_both', 'fullft']:
    for seed in [1, 99]:
        print('== %s / seed%d ==' % (method, seed), flush=True)
        m = train(None, p, imgs, texts, labels, seed, method)
        m = m.eval()
        r = probe(m, p, imgs, texts, labels, None)
        res['%s__s%d' % (method, seed)] = r
        print('  %s s%d: top1=%.2f tau_l1=%.4f R1=%.4f' % (method, seed, r['top1_0'], r['tau_l1'], r['R1']), flush=True)
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        del m
        torch.cuda.empty_cache()
print('DONE ->', OUT, flush=True)
