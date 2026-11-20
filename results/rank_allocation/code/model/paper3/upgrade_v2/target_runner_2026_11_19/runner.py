"""Owned P3 qualification primitives, isolated from the shared trainer."""
from fractions import Fraction
from itertools import combinations
import math

import torch

BLOCKS = ("vision", "text_shallow", "text_mid", "text_deep")
COSTS = (36864, 6144, 12288, 6144)
BUDGET = 245760


def feasible():
    for v in range(1, 7):
        for s in range(1, 35):
            for m in range(1, 18):
                d = 40 - 6*v - s - 2*m
                if d >= 1:
                    yield (v, s, m, d)


def project(raw):
    if len(raw) != len(BLOCKS) or any(not math.isfinite(x) for x in raw):
        raise ValueError("Expected four finite Gamma values")
    gamma = [abs(Fraction(str(x))) for x in raw]
    total = sum(gamma)
    if not total:
        raise ValueError("Cannot project an all-zero Gamma vector")
    # Minimize squared error to the continuous legacy rank target; ties by block-order ranks.
    den = math.lcm(*(x.denominator for x in gamma))
    g = [int(x*den) for x in gamma]
    total = sum(g)
    return min(feasible(), key=lambda r: (sum((a*total-16*b)**2 for a,b in zip(r,g)), r))


def rank_tau(x, y):
    a, b, prod = 0, 0, 0
    for i,j in combinations(range(len(BLOCKS)),2):
        sx = int(x[i]>x[j])-int(x[i]<x[j])
        sy = int(y[i]>y[j])-int(y[i]<y[j])
        a += sx*sx
        b += sy*sy
        prod += sx*sy
    return prod / math.sqrt(a*b) if a and b else None


class Adapter(torch.nn.Module):
    def __init__(self, original, rank, *, generator, scaling=2.):
        super().__init__()
        self.original = original
        self.A = torch.nn.Parameter(torch.empty((rank, original.in_features),
                                              dtype=original.weight.dtype, device=original.weight.device))
        self.B = torch.nn.Parameter(torch.zeros((original.out_features, rank),
                                              dtype=original.weight.dtype, device=original.weight.device))
        if not original.weight.is_meta:
            torch.nn.init.kaiming_uniform_(self.A, a=math.sqrt(5), generator=generator)
        self.scaling = scaling

    def forward(self, x):
        return self.original(x) + self.scaling*((x @ self.A.T) @ self.B.T)


def inject(model, ranks, seed):
    """Canonical CLIP-B/32 q/v projections, no bias or other trainable parameters."""
    if (len(ranks)!=len(BLOCKS) or any(type(r) is not int or r<1 for r in ranks)
            or sum(c*r for c,r in zip(COSTS,ranks)) != BUDGET):
        raise ValueError("Invalid exact-budget rank vector")
    if len(model.vision_model.encoder.layers)!=12 or len(model.text_model.encoder.layers)!=12:
        raise ValueError("Unexpected CLIP layer layout")
    model.requires_grad_(False)
    modules, costs = [], [0]*len(BLOCKS)
    for is_vision, tower in ((True, model.vision_model), (False, model.text_model)):
        for i, layer in enumerate(tower.encoder.layers):
            block=0 if is_vision else (1 if i<3 else 2 if i<9 else 3)
            for j,key in enumerate(("q_proj","v_proj")):
                original=getattr(layer.self_attn,key)
                if not isinstance(original, torch.nn.Linear):
                    raise ValueError("Expected fresh Linear projection")
                gen=None if original.weight.is_meta else torch.Generator(
                    device=original.weight.device).manual_seed(seed+1000*block+2*i+j)
                adapter=Adapter(original, ranks[block], generator=gen)
                costs[block]+=adapter.A.numel()+adapter.B.numel()
                modules.append(adapter)
                setattr(layer.self_attn,key,adapter)
    allowed={id(p) for mod in modules for p in [mod.A,mod.B]}
    actual={id(p) for p in model.parameters() if p.requires_grad}
    if costs != [c*r for c,r in zip(COSTS,ranks)] or actual!=allowed:
        raise ValueError("Runtime trainables disagree with budget or include ancillary parameters")
    return modules, dict(zip(BLOCKS,costs))


@torch.no_grad()
def global_top1(images, texts, image_ids, caption_owner, query_chunk, gallery_chunk):
    """I→T top-1; store global score/index, count same-owner positives after search."""
    if (images.ndim!=2 or texts.ndim!=2 or images.shape[1]!=texts.shape[1] or images.shape[1]<1
            or not len(images) or not len(texts) or len(images)!=len(image_ids) or len(texts)!=len(caption_owner)
            or len(set(image_ids))!=len(image_ids) or set(image_ids)!=set(caption_owner)
            or min(query_chunk,gallery_chunk)<1 or images.device!=texts.device):
        raise ValueError("Invalid unique query IDs, caption ownership, chunks or feature shape")
    normalized=[]
    for x in (images,texts):
        x=x.to(torch.float64)
        norms=x.norm(dim=1,keepdim=True)
        if not torch.isfinite(norms).all() or not (norms>0).all():
            raise ValueError("Nonfinite or empty feature vector")
        normalized.append(x/norms)
    images,texts=normalized
    winners=[]
    for start in range(0,len(images),query_chunk):
        batch=images[start:start+query_chunk]
        best=torch.full((len(batch),), -float("inf"), device=batch.device, dtype=batch.dtype)
        indices=torch.zeros(len(batch), device=batch.device, dtype=torch.long)
        for base in range(0,len(texts),gallery_chunk):
            values, local=(batch @ texts[base:base+gallery_chunk].T).max(dim=1)
            better=values>best
            best=torch.where(better,values,best)
            indices=torch.where(better,local+base,indices)
        winners.extend(indices.tolist())
    hits=sum(image_id==caption_owner[j] for image_id,j in zip(image_ids,winners))
    return {"winning_columns":winners,"hits":hits,"queries":len(images),"recall_at_1":hits/len(images)}


def train_epochs(epochs, ids, loss, optimizer, scheduler, accumulation):
    """Average scalar microbatch objectives per update. Flush each epoch tail."""
    if type(accumulation) is not int or accumulation<1 or not epochs or any(not e for e in epochs):
        raise ValueError("Invalid accumulation or empty epoch")
    horizon=sum(math.ceil(len(e)/accumulation) for e in epochs)
    out={"planned_updates":horizon,"update_count":0,"example_sequence":[],
         "microbatches_per_update":[],"lr_used":[],"mean_loss_per_update":[]}
    optimizer.zero_grad(set_to_none=True)
    for epoch in epochs:
        for start in range(0,len(epoch),accumulation):
            batch=epoch[start:start+accumulation]
            values=[]
            for item in batch:
                value=loss(item)
                if value.ndim!=0 or not torch.isfinite(value).item():
                    raise ValueError("Training loss must be finite scalar")
                (value/len(batch)).backward()
                values.append(value.detach().item())
                out["example_sequence"].append(ids(item))
            out["lr_used"].append([float(g["lr"]) for g in optimizer.param_groups])
            optimizer.step()
            if scheduler is not None:
                scheduler.step()
            optimizer.zero_grad(set_to_none=True)
            out["update_count"]+=1
            out["microbatches_per_update"].append(len(batch))
            out["mean_loss_per_update"].append(sum(values)/len(values))
    return out
