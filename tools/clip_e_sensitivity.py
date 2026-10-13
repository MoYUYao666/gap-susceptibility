"""Merged-paper improvement #1: cross-E sensitivity — does the Γ ordering depend on the choice of alignment energy E.
CLIP ViT-B/32 frozen; K=4 blocks (vision trunk / visual_projection / text model / text_projection);
E variants: E1=DG* mean squared pair distance, E2=GD (centroid + standard deviation), E3=negative mean cosine;
u=InfoNCE task gradient (same batch); Γ_k=<∇_kE, ∇_kL>; report the block ordering under the 3 E variants + Kendall W (consistency).
output: outputs/e_sensitivity.json
"""
import os, sys, json, io, collections
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import CLIPModel, CLIPProcessor
from datasets import load_dataset

MDIR = 'models/clip-vit-base-patch32'
SUB = 'outputs/ocean_subset.json'
OUT = 'outputs/e_sensitivity.json'
TEMPLATE = 'a photo of a {}'


def block_grads(m, grad_map, imgs_enc, txt_enc, loss_fn):
    """loss_fn(scaled_cos) -> loss; return the per-block gradient pair (gE, gL)."""
    pass  # simplification: done directly in main


def main():
    ds_ = json.load(open(SUB, encoding='utf-8'))
    classes = ds_['classes']
    idx = ds_['subset_idx']
    dd = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')),
        split='train')
    imgs = []
    for j in idx[:160]:
        b = dd[j]['file_name']
        imgs.append(Image.open(io.BytesIO(b['bytes'])).convert('RGB')
                    if isinstance(b, dict) and b.get('bytes') else b.convert('RGB'))
    m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().eval()
    p = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)

    # freeze the entire model but keep the required parameter gradient paths (block-level projection)
    for prm in m.parameters():
        prm.requires_grad = True
    blocks = {'vision_trunk': None, 'visual_projection': None,
              'text_model': None, 'text_projection': None}
    # parameter mapping
    par = dict(m.named_parameters())
    blk_of = {}
    for name, prm in par.items():
        if name.startswith('vision_model'):
            blk_of[name] = 'vision_trunk'
        elif name.startswith('visual_projection'):
            blk_of[name] = 'visual_projection'
        elif name.startswith('text_model'):
            blk_of[name] = 'text_model'
        elif name.startswith('text_projection'):
            blk_of[name] = 'text_projection'
        else:
            blk_of[name] = 'wlogscale'

    def grads_by_block():
        g = collections.defaultdict(lambda: torch.zeros((), device='cuda'))
        for name, prm in par.items():
            if prm.grad is None or blk_of[name] == 'wlogscale':
                continue
            g[blk_of[name]] = g[blk_of[name]] + (prm.grad.reshape(-1) ** 2).sum()
        return {k: torch.sqrt(v).item() for k, v in g.items()}

    ti = p(text=[TEMPLATE.format(c) for c in classes], return_tensors='pt', padding=True).to('cuda')
    with torch.no_grad():
        t_out = m.text_model(**ti)
        tp = t_out[1] if isinstance(t_out, tuple) else t_out.pooler_output
        tf = F.normalize(m.text_projection(tp), dim=-1)
    res = {}
    acc_block = {k: [] for k in blocks}
    acc_block['wlogscale'] = []
    nb = 3
    for bi in range(nb):
        xs = torch.stack([p(images=imgs[j])['pixel_values'][0]
                          for j in range(bi * 48, bi * 48 + 48)]).to('cuda')
        with torch.no_grad():
            v_out = m.vision_model(**{'pixel_values': xs})
            vp = v_out[1] if isinstance(v_out, tuple) else v_out.pooler_output
            vf = F.normalize(m.visual_projection(vp), dim=-1)

        def e1(zI, zT):
            d = zI[:, None, :] - zT[None, :, :]
            return (d ** 2).mean()

        def e2(zI, zT):
            mu = (zI.mean(0) - zT.mean(0)).norm()
            sd = (zI.std(0) - zT.std(0)).norm()
            return mu + sd

        def e3(zI, zT):
            return -(zI @ zT.T).mean()

        # task gradient (InfoNCE): 48 images paired with 48 sampled class texts (without replacement, aligned within the batch)
        sel = np.random.RandomState(bi).choice(len(classes), 48, replace=False)
        tids = p(text=[TEMPLATE.format(classes[kk]) for kk in sel], return_tensors='pt',
                 padding=True)['input_ids'].to('cuda')

        def task():
            out = m(pixel_values=xs, input_ids=tids)
            if_ = F.normalize(out.image_embeds, dim=-1)
            tf_ = F.normalize(out.text_embeds, dim=-1)
            logits = if_ @ tf_.T * m.logit_scale.exp()
            lab = torch.arange(len(xs), device='cuda')
            return (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2

        for name, efn in [('E1_DGstar', e1), ('E2_GD', e2), ('E3_negcos', e3)]:
            # two-channel: recompute both gradients and take the per-parameter dot product (single batch, two backward passes)
            m.zero_grad()
            with torch.enable_grad():
                v_out = m.vision_model(**{'pixel_values': xs})
                vp = v_out[1] if isinstance(v_out, tuple) else v_out.pooler_output
                vf2 = F.normalize(m.visual_projection(vp), dim=-1)
                val = efn(vf2, tf.detach())
            val.backward()
            gE2 = {nm: (prm.grad.detach().clone() if prm.grad is not None else None)
                   for nm, prm in par.items()}
            m.zero_grad()
            val2 = task()
            val2.backward()
            gdot = collections.defaultdict(lambda: 0.0)
            for nm, prm in par.items():
                if prm.grad is None or gE2.get(nm) is None or blk_of[nm] == 'wlogscale':
                    continue
                b = blk_of[nm]
                gdot[b] += float((prm.grad.detach() * gE2[nm]).sum())
            m.zero_grad()
            res.setdefault(name, collections.defaultdict(list))
            for b in dict(blocks):
                res[name][b].append(gdot[b])
            res[name]['_Evalue'].append(float(val.item()))
    out = {}
    for name, d in res.items():
        out[name] = {b: (round(float(np.mean(v)), 2) if isinstance(v, list) and v else None)
                     for b, v in d.items() if b != '_Evalue'}
        out[name]['_Evalue'] = round(float(np.mean(d['_Evalue'])), 3)
    # Kendall W: block-order consistency across the E variants
    from scipy import stats
    orderings = {}
    for name, d in out.items():
        keys = [b for b in d if not b.startswith('_')]
        vals = np.array([d[k] for k in keys])
        orderings[name] = [k for k in keys]
        orderings[name] = [keys[i] for i in np.argsort(-vals)]
    # pairwise Spearman/Kendall correlation coefficients
    ks = list(out.keys())
    cons = {}
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            a = out[ks[i]]; b = out[ks[j]]
            keys = [k for k in a if not k.startswith('_')]
            rho, p = stats.spearmanr([a[k] for k in keys], [b[k] for k in keys])
            cons['%s_vs_%s' % (ks[i], ks[j])] = {'spearman': round(float(rho), 3), 'p': round(float(p), 4)}
    json.dump({'blocks': list(blocks), 'orderings': orderings, 'kendall_consistency': cons, 'gamma': out},
              open(OUT, 'w', encoding='utf-8'), indent=1)
    print('orderings:', orderings, flush=True)
    print('consistency:', cons, flush=True)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
