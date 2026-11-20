"""Block attribution and alignment gradient used in target calibration."""

LAYER_SPLIT = {'text_shallow': (0, 2), 'text_mid': (3, 8), 'text_deep': (9, 11)}

def block_of(name: str) -> str:
    if name.startswith('vision_model.'):
        return 'vision'
    if name.startswith('text_model.'):
        parts = name.split('.')
        try:
            li = int(parts[parts.index('layers') + 1])
        except (ValueError, IndexError):
            return 'text_other'
        for blk, (lo, hi) in LAYER_SPLIT.items():
            if lo <= li <= hi:
                return blk
        return 'text_other'
    return 'other'

def measure(model, img, ids, am, device):
    import torch
    import torch.nn.functional as F
    params = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    assert img.shape[0] >= 2, f'LoRA runtime diagnostic{img.shape[0]}'
    model.zero_grad(set_to_none=True)
    o = model(pixel_values=img, input_ids=ids, attention_mask=am)
    I = F.normalize(o.image_embeds.float(), p=2, dim=-1)
    T = F.normalize(o.text_embeds.float(), p=2, dim=-1)
    E = ((I - T) ** 2).sum(-1).mean()
    logits = model.logit_scale.exp() * I @ T.T
    lab = torch.arange(I.shape[0], device=I.device)
    L = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
    assert float(L) > 0, f'LoRA runtime diagnostic{img.shape[0]}LoRA runtime diagnostic'
    E.backward(retain_graph=True)
    gE = {n: p.grad.detach().float().clone() for n, p in params if p.grad is not None}
    model.zero_grad(set_to_none=True)
    L.backward()
    gL = {n: p.grad.detach().float().clone() for n, p in params if p.grad is not None}
    model.zero_grad(set_to_none=True)
    acc: dict[str, dict[str, float]] = {}
    for n, g in gE.items():
        if n not in gL:
            continue
        b = block_of(n)
        d = acc.setdefault(b, {'dot': 0.0, 'nE': 0.0, 'nL': 0.0})
        d['dot'] += float((g * gL[n]).sum())
        d['nE'] += float((g * g).sum())
        d['nL'] += float((gL[n] * gL[n]).sum())
    out = {}
    for b, d in acc.items():
        nE, nL = (d['nE'] ** 0.5, d['nL'] ** 0.5)
        out[b] = {'gamma': -d['dot'], 'norm_gE': nE, 'norm_gL': nL, 'cos': -d['dot'] / (nE * nL) if nE > 0 and nL > 0 else 0.0, 'E': float(E), 'L': float(L)}
    return out
