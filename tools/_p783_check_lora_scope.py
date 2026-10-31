# -*- coding: utf-8 -*-
r"""Determine whether the "LoRA" runs actually trained the whole text tower.

Facts so far:
  - LoRA injection adds 196,608 parameters over 24 modules
  - the trainer reports 145,170,177 trainable, i.e. 95.84% of the model
  - non-LoRA trainable names include text_model.embeddings.token_embedding.weight and
    text_model.encoder.layers.0.self_attn.k_proj.weight, which are ordinary tower weights
  - the archived coco_text_r8 run records n_trainable_params = 145,170,177, the same figure

That combination means the "LoRA rank 8" runs trained the entire text tower. The checkpoint stores
only lora_state_dict, so it cannot settle the question by itself; instead this compares the LoRA
tensors that were saved against a fresh initialisation, and inspects whether the checkpoint records
anything about the tower.

    python tools/_p783_check_lora_scope.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
OUT = REPO / "outputs" / "analysis" / "lora_scope_check.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    from src.config import ExperimentConfig, TrainConfig, LoRAConfig, GapConfig
    from src.trainer import GapAwareTrainer

    # fresh trainer with the same configuration used by the scale-up
    cfg = ExperimentConfig(
        name="scope_probe", peft_method="lora",
        lora=LoRAConfig(rank=8, alpha=8.0, dropout=0.0, apply_to_text=True, apply_to_vision=False),
        gap=GapConfig(compute_every_n_epochs=1, compute_per_layer=False, sample_size=100),
        train=TrainConfig(dataset="coco", batch_size=8, num_epochs=1, save_dir="outputs/_scope"))
    tr = GapAwareTrainer(cfg)
    tr.setup_model()

    tr_p = {n: tuple(p.shape) for n, p in tr.model.named_parameters() if p.requires_grad}
    lora = {n for n in tr_p if "lora_" in n}
    tower = {n for n in tr_p if "lora_" not in n}
    n_lora = sum(p.numel() for n, p in tr.model.named_parameters() if n in lora)
    n_tower = sum(p.numel() for n, p in tr.model.named_parameters() if n in tower)
    total = sum(p.numel() for p in tr.model.parameters())

    print("=" * 100)
    print("what is trainable in the configuration the scale-up used")
    print("=" * 100)
    print(f"  total parameters           : {total:,}")
    print(f"  trainable tensors          : {len(tr_p)}")
    print(f"     LoRA tensors            : {len(lora)}  ({n_lora:,} parameters)")
    print(f"     ordinary tower tensors  : {len(tower)}  ({n_tower:,} parameters)")
    print(f"  LoRA share of trainable    : {n_lora / (n_lora + n_tower):.4%}")
    print()
    print("  sample of the ordinary tower tensors that are trainable:")
    for n in sorted(tower)[:8]:
        print(f"     {n}")

    print()
    print("=" * 100)
    print("the checkpoint the scale-up wrote")
    print("=" * 100)
    ck = REPO / "outputs" / "scaleup_coco" / "coco_scaleup_text_only_r8_s42" / "best_checkpoint.pt"
    sd = torch.load(ck, map_location="cpu", weights_only=False)
    print(f"  top-level keys: {list(sd.keys())}")
    print(f"  lora_state_dict covers {len(sd['lora_state_dict'])} modules")
    print(f"  -> the {n_tower:,} trainable tower parameters are NOT in the checkpoint")

    # did the saved LoRA tensors actually move away from their initialisation?
    moved = 0
    checked = 0
    model_sd = tr.model.state_dict()
    for mod, ab in list(sd["lora_state_dict"].items())[:6]:
        for suffix, key in (("A", "lora_A"), ("B", "lora_B")):
            full = f"{mod}.{key}".replace("text.", "text_model.", 1)
            if full in model_sd:
                checked += 1
                same = torch.equal(model_sd[full].cpu(), ab[suffix].cpu())
                if not same:
                    moved += 1
                print(f"  {full:<62} differs from fresh: {not same}")
    print(f"  -> {moved} of {checked} checked LoRA tensors differ from a fresh initialisation")

    print()
    print("=" * 100)
    print("archived runs, for comparison")
    print("=" * 100)
    import subprocess
    r = subprocess.run(["git", "ls-files", "outputs/theory"], cwd=str(REPO / "publish_clean"),
                       capture_output=True)
    files = [x for x in r.stdout.decode("utf-8", "replace").splitlines()
             if x.endswith("results.json")]
    seen = {}
    for f in files:
        p = REPO / "publish_clean" / f
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        exp = str(d.get("experiment", ""))
        n = d.get("n_trainable_params")
        if n and ("r8" in exp or "r4" in exp or "r16" in exp):
            seen.setdefault(exp, n)
    for exp, n in sorted(seen.items())[:12]:
        print(f"  {exp:<28} n_trainable_params = {n:,}")
    print()
    print("  for reference, a rank-8 LoRA on the text tower alone is about 196,608 parameters,")
    print("  and the full text tower is 145,170,177.")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({
            "total": total, "trainable_tensors": len(tr_p),
            "lora_tensors": len(lora), "lora_parameters": n_lora,
            "tower_tensors": len(tower), "tower_parameters": n_tower,
            "lora_share_of_trainable": n_lora / (n_lora + n_tower),
            "checkpoint_keys": list(sd.keys()),
            "lora_tensors_moved": moved, "lora_tensors_checked": checked,
            "archived_n_trainable": seen}, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
