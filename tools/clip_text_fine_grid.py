"""L4 fine grid on the text side: fish-67 × {bioclip, oceanclip} × λ ∈ 8 values.
Reuses the subset/encoding/evaluation of clip_ocean_gap_surgery, text-side surgery only, so the Δτ curve has higher resolution.
Outputs outputs/text_fine_grid.json (rows: model, lam, CG, top1, tau) + the Theorem 4 slope check quantity.
"""
import os, sys, json
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
import importlib.util

spec = importlib.util.spec_from_file_location(
    'gs', os.path.join(os.path.dirname(__file__), 'clip_ocean_gap_surgery.py'))
gs = importlib.util.module_from_spec(spec)
sys.modules['gs'] = gs
spec.loader.exec_module(gs)

LAMS = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
OUT = 'outputs/text_fine_grid.json'

ds, sub = gs.build_subset()
classes = sub['classes']
idx = sub['subset_idx']
texts = [gs.TEMPLATE.format(c) for c in classes]
labels = torch.tensor([classes.index(r['sciName']) for r in ds.select(idx)])
print('subset: %d classes / %d images' % (len(classes), len(idx)), flush=True)

MODELS = gs.load_models()
rows = []
for tag in ['bioclip', 'oceanclip']:
    cfg = MODELS[tag]
    print('== %s ==' % tag, flush=True)
    tf = gs.encode_text(cfg, texts)
    img_full = gs.encode_images(cfg, ds, idx)
    mu_i, mu_t = img_full.mean(0), tf.mean(0)
    gap_vec = mu_t - mu_i
    gap_norm = gap_vec.norm().item()
    d_hat = gap_vec / gap_norm
    base_sims = img_full @ tf.T
    base_np = base_sims.cpu().numpy()
    topk5 = np.argsort(-base_np, axis=1)[:, :5]
    tau_idx = list(range(len(idx)))
    for lam in LAMS:
        with torch.no_grad():
            delta = -lam * gap_norm * d_hat
            tf2 = F.normalize(tf + delta, dim=-1)
            ft2 = F.normalize(tf + delta, dim=-1)
        cg, t1, tau = gs.evaluate(img_full, tf2, img_full, ft2, labels, tau_idx, base_np, topk5)
        rows.append(dict(model=tag, lam=lam, CG=round(cg, 4), top1=round(t1, 3), tau=round(tau, 4)))
        print('  %s T λ=%+.2f: CG=%.4f top1=%.2f tau=%.4f' % (tag, lam, cg, t1, tau), flush=True)
    json.dump(rows, open(OUT, 'w', encoding='utf-8'), indent=2)
    del img_full, tf
    torch.cuda.empty_cache()

json.dump(rows, open(OUT, 'w', encoding='utf-8'), indent=2)
print('DONE ->', OUT, flush=True)
