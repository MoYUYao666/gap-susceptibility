"""Replay source-only projections and run loaded-weight synthetic qualification, offline."""
import argparse
from itertools import combinations
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys

for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
    os.environ[key] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
import transformers
from transformers import CLIPModel
from runner import BLOCKS, BUDGET, COSTS, feasible, inject, project, rank_tau, train_epochs

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent/"target_utility_readiness_2026_11_19/SourceDraws.json"
MODEL = ROOT/"models/clip-vit-base-patch32"
MODEL_SHA = "a63082132ba4f97a80bea76823f544493bffa8082296d62d71581a4feff1576f"
SOURCE_SHA = "947d4b9bea99f17235ea17d1f1b12cad540b4ad2bb4494151373ce63a2068e8f"
BASELINE = (4, 4, 4, 4)
SIZES = (2, 4, 8, 16)
INITIALIZATION_SEED = 20261119


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def emit(path, obj):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write("\n")


def hash_parameters(params):
    key=hashlib.sha256()
    for p in params:
        key.update(memoryview(p.detach().cpu().contiguous().numpy()).cast("B"))
    return key.hexdigest()


def source_projection():
    assert sha(SOURCE)==SOURCE_SHA
    source=json.loads(SOURCE.read_text(encoding="utf-8"))
    assert source["target_result"] is None
    rows=source["source_draws"]
    assert [(r["seed"],r["size"]) for r in rows]==[(s,n) for s in range(3) for n in SIZES]
    cells={}
    for r in rows:
        raw=[r["blocks"][b]["gamma"] for b in BLOCKS]
        cells[r["seed"],r["size"]]=project(raw)
    store=[]
    candidates=[r for r in feasible() if r!=BASELINE]
    for seed in range(3):
        pairs=[{"sizes":[i,j],"tau_b":rank_tau(cells[seed,i],cells[seed,j])} for i,j in combinations(SIZES,2)]
        finite=[p["tau_b"] for p in pairs if p["tau_b"] is not None]
        index=int.from_bytes(hashlib.sha256(f"P3-Rank-Control-v1:{seed}".encode()).digest(),"big") % len(candidates)
        store.append({"seed":seed, "uniform":BASELINE, "random":candidates[index], "target_calibrated":None,
                      "projected_source":[{"size":i,"rank":cells[seed,i]} for i in SIZES],
                      "pairs":pairs,"pact_minimum":min(finite) if len(finite)==len(pairs) else None})
    return {"scope":"Projected source-only rank concordance; not target utility",
            "target_result":None,"source_sha256":SOURCE_SHA,"block_order":BLOCKS,
            "feasible_rank_vectors":len(candidates)+1,"budget_trainable":BUDGET,
            "cost_per_rank":COSTS,"seed_records":store}


def tensors(model):
    gen=torch.Generator().manual_seed(INITIALIZATION_SEED)
    side=model.config.vision_config.image_size
    n=model.config.text_config.vocab_size
    return [
        (f"software:{i}", torch.randn((2,3,side,side),generator=gen),
         torch.tensor([[1,10+i,20,n-1],[1,30+i,10,n-1]]))
        for i in range(3)
    ]


def smoke_arm(ranks):
    model=CLIPModel.from_pretrained(str(MODEL), local_files_only=True).cpu().eval()
    frozen=list(model.parameters())
    frozen_before=hash_parameters(frozen)
    examples=tensors(model)

    def scores(row):
        return model(pixel_values=row[1], input_ids=row[2]).logits_per_image

    with torch.no_grad():
        reference=scores(examples[0])
    mods, block_counts=inject(model, ranks, INITIALIZATION_SEED)
    with torch.no_grad():
        modified=scores(examples[0])
    assert torch.equal(reference,modified), "Adapter insertion drift"
    trainable=[p for p in model.parameters() if p.requires_grad]
    initial=[hash_parameters([m.B]) for m in mods]
    optimizer=torch.optim.AdamW(trainable,lr=1e-4,weight_decay=0.)
    scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,T_max=2)

    def loss(row):
        logits=scores(row)
        y=torch.arange(len(logits),device=logits.device)
        return (torch.nn.functional.cross_entropy(logits,y)+torch.nn.functional.cross_entropy(logits.T,y))/2

    model.train()
    stats=train_epochs([examples],lambda row:row[0],loss,optimizer,scheduler,2)
    assert len(optimizer.state)==2*len(mods)
    assert {v["step"].item() for v in optimizer.state.values()}=={2}
    assert all(p.grad is None for p in trainable)
    assert scheduler.last_epoch==stats["update_count"]==stats["planned_updates"]==2
    assert stats["lr_used"]==[[1e-4],[5e-5]]
    assert all(torch.isfinite(p).all() for p in trainable)
    changed=sum(a!=hash_parameters([m.B]) for a,m in zip(initial,mods))
    assert changed==len(mods) and frozen_before==hash_parameters(frozen)
    return {"ranks":ranks,"trainables_by_block":block_counts,"adapted_modules":len(mods),
            "actual_trainables":sum(p.numel() for p in trainable),"ancillary_trainables":0,
            "frozen_parameters_unchanged":True, "initial_logits_unchanged":True,
            "updated_adapters":changed,"clock":stats}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--smoke",type=Path,help="Write a new synthetic test receipt")
    modes.add_argument("--project",type=Path,help="Write a new source-only projection receipt")
    modes.add_argument("--run",action="store_true",help="Refuse real execution pending independent target admission")
    args=p.parse_args()
    if args.run:
        print("BLOCKED: no independently selected target registry or target-calibrated control; no target backend.",
              file=sys.stderr)
        return 2
    projection=source_projection()
    if args.project:
        emit(args.project, projection)
        return 0
    assert sha(MODEL/"pytorch_model.bin")==MODEL_SHA
    torch.set_num_threads(min(6,os.cpu_count() or 1))
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(INITIALIZATION_SEED)
    uniform=smoke_arm(BASELINE)
    assert set(uniform["ranks"])=={4}
    # Use the predeclared ordered source slot, not a performance-selected allocation.
    vector=projection["seed_records"][0]["projected_source"][0]["rank"]
    assert tuple(vector)!=BASELINE
    arm=smoke_arm(vector)
    for name in ("example_sequence","update_count","microbatches_per_update","lr_used"):
        assert uniform["clock"][name]==arm["clock"][name]
    assert uniform["actual_trainables"]==arm["actual_trainables"]==BUDGET
    emit(args.smoke, {"status":"QUALIFIED_SYNTHETIC_CPU_SMOKE_ONLY","target_result":None,
                      "weights_downloaded":False,"model_hash":MODEL_SHA,"config_sha256":sha(MODEL/"config.json"),
                      "source_sha256":SOURCE_SHA,"python":platform.python_version(),"torch":torch.__version__,
                      "transformers":transformers.__version__,
                      "script_sha256":{n:sha(HERE/n) for n in ("runner.py","qualify.py","test_runner.py","PLAN.md")},
                      "uniform":uniform,"source_seed0_size2":arm})
    print("Two synthetic CLIP arms passed equal parameter and optimizer-update checks.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
