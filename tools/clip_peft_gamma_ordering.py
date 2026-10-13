"""Tier A1: consistency of Γ block ordering across four parameterizations + coupling deviation quantification (direct measurement of paper limitation 3).

Background: the proof of the representation theorem assumes the reparameterization lies in the orthogonal subgroup; LoRA/Adapter/BitFit are all non-orthogonal.
On a frozen CLIP ViT-B/32, for the same alignment energy E and the same task gradient u, this script computes within four trainable subspaces:
  (a) full  : all-parameter gradients,
  (b) lora  : LoRA subspace of the attention projections (r=8, q/k/v/out, both encoders),
  (c) adapter: bottleneck adapter after the attention output (64),
  (d) bitfit: biases only,
computes Γ_k = Σ_{θ∈block} ⟨∇_θE, ∇_θL⟩, and reports:
  1) block ordering under each parameterization (E ∈ {DG*, GD, negcos} × 3 batches);
  2) per-block coupling deviation from full, ε_k = |Γ^peft_k − Γ^full_k| / |Γ^full_k|;
  3) block-ordering Spearman correlation between each pair of parameterizations.
Output: outputs/clip_peft_gamma_ordering.json
"""
import os
import sys
import json
import io
import math
import collections

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from transformers import CLIPModel, CLIPProcessor
from datasets import load_dataset

MDIR = 'models/clip-vit-base-patch32'
SUB = 'outputs/ocean_subset.json'
OUT = 'outputs/clip_peft_gamma_ordering.json'
TEMPLATE = 'a photo of a {}'
N_BATCH = 3
BS = 48
LORA_R = 8
ADAPTER_BOTTLENECK = 64


# ---------------- PEFT modules (hand-written, so blocks can be split by prefix) ----------------
class LoRALinear(nn.Module):
    """W x + scale * B (A x); only A/B are trainable (base frozen).

    Note: standard LoRA initializes B to 0 → at init the gradient w.r.t. A is identically 0, so coupling
    covers only half the subspace and is far below the full parameterization (dimension/scale artefact).
    To compare the **parameterization geometry**, B is randomly initialized at small scale here so both factors carry gradients at init.
    """

    def __init__(self, base: nn.Linear, r: int = LORA_R, alpha: int = 16, b_scale: float = 1e-2):
        super().__init__()
        self.base = base
        self.r = r
        self.scale = alpha / r
        self.lora_A = nn.Parameter(torch.empty(r, base.in_features))
        self.lora_B = nn.Parameter(torch.empty(base.out_features, r))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.normal_(self.lora_B, std=b_scale)

    def forward(self, x):
        return self.base(x) + self.scale * (x @ self.lora_A.t() @ self.lora_B.t())


class AdapterAttn(nn.Module):
    """Attention output followed by a bottleneck residual adapter h <- h + W_up relu(W_down h)."""

    def __init__(self, attn: nn.Module, dim: int, bottleneck: int = ADAPTER_BOTTLENECK,
                 up_scale: float = 1e-2):
        super().__init__()
        self.attn = attn
        self.down = nn.Linear(dim, bottleneck)
        self.up = nn.Linear(bottleneck, dim)
        nn.init.normal_(self.up.weight, std=up_scale)
        nn.init.zeros_(self.up.bias)

    def forward(self, *a, **k):
        out = self.attn(*a, **k)
        if isinstance(out, tuple):
            h, rest = out[0], out[1:]
            return (h + self.up(F.relu(self.down(h))),) + tuple(rest)
        return out + self.up(F.relu(self.down(out)))


def add_lora(model, targets=('q_proj', 'k_proj', 'v_proj', 'out_proj')):
    """Replace the attention projections inside both encoders with LoRA wrappers (base requires_grad=False)."""
    n = 0
    for name, module in list(model.named_modules()):
        for child_name, child in list(module.named_children()):
            if child_name in targets and isinstance(child, nn.Linear):
                setattr(module, child_name, LoRALinear(child))
                n += 1
    for p in model.parameters():
        p.requires_grad = False
    for name, p in model.named_parameters():
        if 'lora_A' in name or 'lora_B' in name:
            p.requires_grad = True
    return n


def add_adapters(model, bottleneck=ADAPTER_BOTTLENECK):
    n = 0
    for enc in (model.vision_model, model.text_model):
        for layer in enc.encoder.layers:
            dim = layer.self_attn.out_proj.in_features
            layer.self_attn = AdapterAttn(layer.self_attn, dim, bottleneck)
            n += 1
    for p in model.parameters():
        p.requires_grad = False
    for name, p in model.named_parameters():
        if name.endswith('down.weight') or name.endswith('down.bias') \
                or name.endswith('up.weight') or name.endswith('up.bias'):
            p.requires_grad = True
    return n


def add_bitfit(model):
    for p in model.parameters():
        p.requires_grad = False
    n = 0
    for name, p in model.named_parameters():
        if name.endswith('bias'):
            p.requires_grad = True
            n += 1
    return n


BLOCKS = ['vision_trunk', 'visual_projection', 'text_model', 'text_projection']


def block_of(name):
    if name.startswith('vision_model'):
        return 'vision_trunk'
    if name.startswith('visual_projection'):
        return 'visual_projection'
    if name.startswith('text_model'):
        return 'text_model'
    if name.startswith('text_projection'):
        return 'text_projection'
    return None


def main():
    ds_ = json.load(open(SUB, encoding='utf-8'))
    classes = ds_['classes']
    idx = ds_['subset_idx']
    files = sorted(os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data'))
    dd = load_dataset('parquet', data_files=files, split='train')
    imgs = []
    for j in idx[:BS * N_BATCH]:
        b = dd[j]['file_name']
        imgs.append(Image.open(io.BytesIO(b['bytes'])).convert('RGB')
                    if isinstance(b, dict) and b.get('bytes') else b.convert('RGB'))
    print('images:', len(imgs), flush=True)

    proc = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)

    def e1(zI, zT):  # DG*
        return ((zI[:, None, :] - zT[None, :, :]) ** 2).mean()

    def e2(zI, zT):  # GD: centroids + standard deviations
        return (zI.mean(0) - zT.mean(0)).norm() + (zI.std(0) - zT.std(0)).norm()

    def e3(zI, zT):  # negative mean cosine
        return -(zI @ zT.t()).mean()

    EFNS = [('DGstar', e1), ('GD', e2), ('negcos', e3)]

    def measure(mode):
        """Return (mean gamma[E][block], trainable parameter count per block) — each mode loads its own model."""
        m = CLIPModel.from_pretrained(MDIR, local_files_only=True)
        if mode == 'lora':
            nmod = add_lora(m)
            ntr = sum(p.numel() for p in m.parameters() if p.requires_grad)
        elif mode == 'adapter':
            nmod = add_adapters(m)
            ntr = sum(p.numel() for p in m.parameters() if p.requires_grad)
        elif mode == 'bitfit':
            nmod = add_bitfit(m)
            ntr = sum(p.numel() for p in m.parameters() if p.requires_grad)
        else:
            for p in m.parameters():
                p.requires_grad = True
            nmod, ntr = 0, sum(p.numel() for p in m.parameters())
        m = m.cuda().eval()
        par = [(n, p) for n, p in m.named_parameters() if p.requires_grad]
        blk_sizes = collections.Counter()
        for n, p in par:
            b = block_of(n)
            if b:
                blk_sizes[b] += p.numel()
        print(f'[{mode}] modules wrapped={nmod} trainable={ntr/1e6:.3f}M', flush=True)

        # Text features (frozen, consistent with e_sensitivity_v2)
        ti = proc(text=[TEMPLATE.format(c) for c in classes], return_tensors='pt', padding=True).to('cuda')
        with torch.no_grad():
            t_out = m.text_model(**ti)
            tp = t_out[1] if isinstance(t_out, tuple) else t_out.pooler_output
            tf = F.normalize(m.text_projection(tp), dim=-1)

        acc = {name: collections.defaultdict(list) for name, _ in EFNS}
        for bi in range(N_BATCH):
            xs = torch.stack([proc(images=imgs[j])['pixel_values'][0]
                              for j in range(bi * BS, bi * BS + BS)]).to('cuda')
            sel = np.random.RandomState(bi).choice(len(classes), BS, replace=False)
            tids = proc(text=[TEMPLATE.format(classes[k]) for k in sel], return_tensors='pt',
                        padding=True)['input_ids'].to('cuda')

            def task():
                out = m(pixel_values=xs, input_ids=tids)
                if_ = F.normalize(out.image_embeds, dim=-1)
                tf_ = F.normalize(out.text_embeds, dim=-1)
                logits = if_ @ tf_.t() * m.logit_scale.exp()
                lab = torch.arange(len(xs), device='cuda')
                return (F.cross_entropy(logits, lab) + F.cross_entropy(logits.t(), lab)) / 2

            for name, efn in EFNS:
                m.zero_grad()
                with torch.enable_grad():
                    # E must depend on both modalities: the text branch must also be forwarded under
                    # enable_grad (else ∂E/∂θ ≡ 0 on all text-side params and the text block's Γ is always 0)
                    t_out2 = m.text_model(**ti)
                    tp2 = t_out2[1] if isinstance(t_out2, tuple) else t_out2.pooler_output
                    tf2 = F.normalize(m.text_projection(tp2), dim=-1)
                    v_out = m.vision_model(pixel_values=xs)
                    vp = v_out[1] if isinstance(v_out, tuple) else v_out.pooler_output
                    vf = F.normalize(m.visual_projection(vp), dim=-1)
                    val = efn(vf, tf2)
                val.backward()
                gE = {n: (p.grad.detach().clone() if p.grad is not None else None) for n, p in par}
                m.zero_grad()
                task().backward()
                gdot = collections.defaultdict(float)
                for n, p in par:
                    if p.grad is None or gE.get(n) is None:
                        continue
                    b = block_of(n)
                    if b is None:
                        continue
                    gdot[b] += float((p.grad.detach() * gE[n]).sum())
                m.zero_grad()
                for b in BLOCKS:
                    acc[name][b].append(gdot[b])
            del xs, tids
            torch.cuda.empty_cache()
        out = {name: {b: float(np.mean(acc[name][b])) for b in BLOCKS} for name, _ in EFNS}
        del m
        torch.cuda.empty_cache()
        return out, dict(blk_sizes), ntr

    res, sizes, ntrain = {}, {}, {}
    for mode in ['full', 'lora', 'adapter', 'bitfit']:
        g, bs, nt = measure(mode)
        res[mode] = g
        sizes[mode] = bs
        ntrain[mode] = nt

    # Ordering + pairwise Spearman (also gives the "per-parameter normalized" coupling, removing dimension/scale artefacts)
    from scipy import stats
    norm = {}
    for mode in res:
        norm[mode] = {}
        for E in res[mode]:
            norm[mode][E] = {b: (res[mode][E][b] / max(sizes[mode].get(b, 1), 1)) for b in BLOCKS}
    orderings = {mode: {E: [b for b in sorted(BLOCKS, key=lambda x: -abs(norm[mode][E][x]))]
                        for E in res[mode]} for mode in res}
    spear = {}
    modes = list(res.keys())
    for i in range(len(modes)):
        for j in range(i + 1, len(modes)):
            for E in res[modes[i]]:
                a = [norm[modes[i]][E][b] for b in BLOCKS]
                b_ = [norm[modes[j]][E][b] for b in BLOCKS]
                rho, p = stats.spearmanr(a, b_)
                spear[f'{modes[i]}_vs_{modes[j]}|{E}'] = {'spearman': round(float(rho), 3),
                                                          'p': round(float(p), 4)}
    # Coupling deviation (after normalization) ε_k = |Γ^peft - Γ^full| / |Γ^full|
    dev = {}
    for mode in ['lora', 'adapter', 'bitfit']:
        dev[mode] = {}
        for b in BLOCKS:
            rel = [abs(norm[mode][E][b] - norm['full'][E][b]) / max(abs(norm['full'][E][b]), 1e-12)
                   for E in res['full']]
            dev[mode][b] = round(float(np.median(rel)), 4)
        allrel = [dev[mode][b] for b in BLOCKS]
        dev[mode]['_median'] = round(float(np.median(allrel)), 4)
        dev[mode]['_max'] = round(float(np.max(allrel)), 4)
    # Ordering-consistency summary: for each E, whether full and the three PEFT orderings are exactly the same
    same = {E: all(orderings[m][E] == orderings['full'][E] for m in ['lora', 'adapter', 'bitfit'])
            for E in res['full']}
    json.dump({'blocks': BLOCKS, 'gamma': res, 'gamma_per_param': norm,
               'block_trainable_params': sizes,
               'trainable_total': ntrain, 'orderings': orderings, 'spearman': spear,
               'coupling_deviation_median_rel': dev, 'identical_order_to_full': same,
               'config': {'lora_r': LORA_R, 'adapter_bottleneck': ADAPTER_BOTTLENECK,
                          'batches': N_BATCH, 'batch_size': BS, 'E': [n for n, _ in EFNS],
                          'note': 'LoRA B and adapter up use non-zero small-scale random init so both factors carry gradients at the init point'}},
              open(OUT, 'w', encoding='utf-8'), indent=1)
    print('orderings:', json.dumps(orderings, indent=1), flush=True)
    print('identical_order_to_full:', same, flush=True)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
