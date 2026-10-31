#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44c_p3_nan_attribution.py -- P3 review item R3.22, GPU part.

Question put by the reviewer: is the NaN at high LoRA rank genuine representational
collapse, or numerical instability tied to 4-bit quantization / mixed precision /
optimizer settings?

Design (single variable at a time, everything else pinned to the paper's protocol):

  config A: rank 24, compute_dtype float16   <- the protocol that produced NaN
  config B: rank 24, compute_dtype bfloat16  <- SAME rank, only precision changes
  config C: rank  8, compute_dtype bfloat16  <- finite control at the same precision

Diagnostics recorded per step / per epoch:
  * task CE loss (finite? falling?)
  * gradient L2 norm before clip, per parameter group (vision / projector / LLM)
  * LoRA weight L2 norm (does the adapter itself blow up?)
  * last-layer hidden-state statistics at the ALIGNMENT-ENERGY measurement points:
    finite fraction, max |h|, and the two pooled vectors h_vis / h_lang
  * alignment energy E and the norm of dE/dtheta

Decisive reading:
  - loss finite AND weights finite AND activations finite, but E non-finite
      -> the non-finiteness is introduced by the energy functional
         (mean ||h_vis - h_lang||^2) applied to a rank-deficient geometry, i.e.
         a representation-side effect, not an optimizer blow-up.
  - loss or grad or weights non-finite
      -> classic numerical divergence.
  - NaN appears under float16 but NOT under bfloat16 at the same rank
      -> precision (range) is the driver: numerical instability.

Protocol is copied from paper3/scripts/run_training.py (positional 20-sample
window, blank 336x336 images, 4-bit nf4 + double quant, LoRA q/k/v/o, alpha=2r,
dropout 0.1, AdamW lr 5e-5, batch 1, 3 epochs, train = samples[4:], eval =
samples[:4]).

Output: outputs/analysis/p3_nan_attribution.json
"""
import argparse
import gc
import glob
import json
import math
import os
import sys
import time
from datetime import datetime

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "outputs", "analysis")
os.makedirs(OUTDIR, exist_ok=True)
MODEL_DIR = os.path.join(ROOT, "models", "llava-hf")


def log(m):
    print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), m), flush=True)


def fin_t(x):
    return bool(torch.isfinite(x).all().item())


def build_samples(num_samples=20, data_offset=0):
    files = glob.glob(os.path.join(ROOT, "paper3", "train-*.parquet"))
    if not files:
        raise SystemExit("no Alpaca parquet found")
    df = pd.read_parquet(sorted(files)[0])
    recs = df.iloc[data_offset:data_offset + num_samples].to_dict("records")
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rank", type=int, default=24)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--compute-dtype", default="float16", choices=["float16", "bfloat16"])
    ap.add_argument("--tag", default="")
    a = ap.parse_args()

    torch.manual_seed(a.seed)
    np.random.seed(a.seed)

    rec = {"rank": a.rank, "seed": a.seed, "epochs": a.epochs,
           "compute_dtype": a.compute_dtype, "tag": a.tag,
           "started": datetime.now().isoformat(timespec="seconds")}

    # ---------------- data
    samples = build_samples()
    log("loaded %d samples (positional window offset=0)" % len(samples))
    formatted = [{"instruction": s.get("instruction", ""), "output": s.get("output", "")}
                 for s in samples]

    # ---------------- model
    cdt = getattr(torch, a.compute_dtype)
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=cdt,
                             bnb_4bit_use_double_quant=True)
    log("loading LLaVA-1.5-7B (4-bit nf4, compute=%s) ..." % a.compute_dtype)
    model = LlavaForConditionalGeneration.from_pretrained(
        MODEL_DIR, quantization_config=bnb, device_map="auto")
    processor = AutoProcessor.from_pretrained(MODEL_DIR)
    rec["model_dir"] = os.path.relpath(MODEL_DIR, ROOT)

    from peft import LoraConfig, TaskType, get_peft_model
    cfg = LoraConfig(r=a.rank, lora_alpha=a.rank * 2,
                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                     lora_dropout=0.1, bias="none", task_type=TaskType.CAUSAL_LM)
    model = get_peft_model(model, cfg)
    n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)
    rec["n_trainable"] = int(n_train)
    log("LoRA applied r=%d alpha=%d, trainable=%.2fM" % (a.rank, a.rank * 2, n_train / 1e6))

    # parameter routing for grad norms
    route = {"vision": [], "proj": [], "llm": []}
    lora_params = []
    for n, p in model.named_parameters():
        if not p.requires_grad:
            continue
        k = "vision" if "vision_tower" in n else ("proj" if "multi_modal_projector" in n else "llm")
        route[k].append(p)
        if "lora_" in n:
            lora_params.append((n, p))

    # ---------------- pre-process (identical to run_training.py)
    blank = Image.fromarray(np.zeros((336, 336, 3), dtype=np.uint8))
    pixel_vals = processor.image_processor(blank, return_tensors="pt")["pixel_values"]
    img_tok = model.config.image_token_index
    img_tok_id = img_tok if isinstance(img_tok, int) else img_tok.item()
    processed = []
    for s in formatted:
        text = "USER: %s\nASSISTANT: %s" % (s["instruction"], s["output"])
        toks = processor.tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
        ids = torch.cat([torch.full((1, 576), img_tok_id, dtype=torch.long),
                         toks["input_ids"][:, 1:]], dim=1)
        att = torch.cat([torch.ones(1, 576, dtype=torch.long),
                         toks["attention_mask"][:, 1:]], dim=1)
        processed.append({"input_ids": ids[0], "attention_mask": att[0],
                          "pixel_values": pixel_vals.squeeze(0),
                          "labels": ids[0].clone()})
    train_data, eval_data = processed[4:], processed[:4]
    pad_id = processor.tokenizer.pad_token_id

    # ---------------- alignment-energy measurement with diagnostics
    def energy_and_stats(m, edata, max_n=4):
        m.eval()
        tot, n = 0.0, 0
        stats = []
        with torch.no_grad():
            for i in range(min(max_n, len(edata))):
                d = edata[i]
                b = {k: v.unsqueeze(0).cuda() for k, v in d.items()
                     if k in ("input_ids", "attention_mask", "pixel_values")}
                out = m(**b, output_hidden_states=True)
                h = out.hidden_states[-1][0]
                ids = b["input_ids"][0]
                vm = torch.zeros_like(ids, dtype=torch.bool); vm[:576] = True
                lm = torch.zeros_like(ids, dtype=torch.bool)
                lm[576:] = (ids[576:] != pad_id)
                hv = h[vm].mean(0); hl = h[lm].mean(0)
                e = ((hv - hl) ** 2).sum().item()
                stats.append({
                    "i": i,
                    "hidden_finite_frac": float(torch.isfinite(h).float().mean().item()),
                    "hidden_absmax": float(h.abs().max().item()) if fin_t(h) else None,
                    "hidden_absmax_finite_part": float(
                        h[torch.isfinite(h)].abs().max().item()) if torch.isfinite(h).any() else None,
                    "hv_finite": fin_t(hv), "hl_finite": fin_t(hl),
                    "hv_absmax": float(hv.abs().max().item()) if fin_t(hv) else None,
                    "hl_absmax": float(hl.abs().max().item()) if fin_t(hl) else None,
                    "E": e if math.isfinite(e) else None,
                    "n_vis": int(vm.sum().item()), "n_lang": int(lm.sum().item()),
                })
                if math.isfinite(e):
                    tot += e
                    n += 1
        m.train()
        return (tot / max(n, 1), n), stats

    (E0, n0), s0 = energy_and_stats(model, eval_data)
    rec["E0"] = E0 if math.isfinite(E0) else None
    rec["E0_n_valid"] = n0
    rec["E0_per_sample"] = s0
    log("E(0) = %s (n=%d)" % (rec["E0"], n0))

    # ---------------- training with per-step diagnostics
    from torch.utils.data import DataLoader, Dataset

    class ListDS(Dataset):
        def __init__(self, d): self.data = d
        def __len__(self): return len(self.data)
        def __getitem__(self, i): return self.data[i]

    def collate(batch, max_len=1024):
        def pad2d(t, v, L):
            need = max(0, L - t.size(0))
            return F.pad(t, (0, need), value=v) if need > 0 else t[:L]
        ids = torch.stack([pad2d(b["input_ids"], 0, max_len) for b in batch])
        att = torch.stack([pad2d(b["attention_mask"], 0, max_len) for b in batch])
        pix = torch.stack([b["pixel_values"] for b in batch])
        lbl = torch.stack([pad2d(b["labels"], -100, max_len) for b in batch])
        lbl[att == 0] = -100
        return {"input_ids": ids, "attention_mask": att, "pixel_values": pix, "labels": lbl}

    loader = DataLoader(ListDS(train_data), batch_size=1, shuffle=True, collate_fn=collate)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=5e-5)

    steps = []
    E_hist = [rec["E0"]]
    epoch_hist = []
    skipped = 0
    t0 = time.time()
    for epoch in range(a.epochs):
        model.train()
        ep_loss, ep_valid = 0.0, 0
        for step, batch in enumerate(loader):
            batch = {k: v.cuda() for k, v in batch.items()}
            opt.zero_grad(set_to_none=True)
            out = model(**batch)
            loss = out.loss
            row = {"epoch": epoch + 1, "step": step,
                   "loss": float(loss.item()) if fin_t(loss) else None,
                   "loss_finite": fin_t(loss)}
            if not fin_t(loss):
                skipped += 1
                row["skipped"] = True
                steps.append(row)
                continue
            loss.backward()
            # pre-clip gradient norms (the script does NOT clip, so these are the
            # values actually applied)
            gn = {}
            gn_finite = True
            for k, ps in route.items():
                tot = 0.0
                for p in ps:
                    if p.grad is not None:
                        g = p.grad.detach()
                        if fin_t(g):
                            tot += float(g.float().pow(2).sum().item())
                        else:
                            gn_finite = False
                gn[k] = math.sqrt(tot)
            row["grad_norm"] = gn
            row["grad_finite"] = gn_finite
            # LoRA weight norm
            wn = 0.0
            for _, p in lora_params:
                wn += float(p.detach().float().pow(2).sum().item())
            row["lora_weight_norm"] = math.sqrt(wn)
            opt.step()
            row["lr"] = opt.param_groups[0]["lr"]
            ep_loss += row["loss"]; ep_valid += 1
            steps.append(row)
            if step % 4 == 0:
                log("  ep%d step %d loss=%.4f gn(llm)=%.3f lora_wn=%.2f"
                    % (epoch + 1, step, row["loss"], gn["llm"], row["lora_weight_norm"]))

        (Ee, ne), se = energy_and_stats(model, eval_data)
        E_hist.append(Ee if math.isfinite(Ee) else None)
        epoch_hist.append({"epoch": epoch + 1, "E": Ee if math.isfinite(Ee) else None,
                           "n_valid": ne, "avg_loss": ep_loss / max(ep_valid, 1),
                           "n_valid_steps": ep_valid, "n_skipped_steps": skipped,
                           "per_sample": se})
        log("epoch %d: avg_loss=%.4f (%d valid) | E(%d)=%s"
            % (epoch + 1, ep_loss / max(ep_valid, 1), ep_valid, epoch + 1, E_hist[-1]))

    rec["elapsed_s"] = round(time.time() - t0, 1)
    rec["E_series"] = E_hist
    rec["dE"] = (E_hist[-1] - E_hist[0]) if (E_hist[-1] is not None and E_hist[0] is not None) else None
    rec["epoch_history"] = epoch_hist
    rec["steps"] = steps
    rec["n_steps"] = len(steps)
    rec["n_skipped_steps"] = skipped
    rec["loss_all_finite"] = all(s["loss_finite"] for s in steps)
    rec["grad_all_finite"] = all(s.get("grad_finite", True) for s in steps)
    rec["max_grad_norm"] = {k: max([s["grad_norm"][k] for s in steps if "grad_norm" in s], default=None)
                            for k in route}
    rec["max_lora_weight_norm"] = max([s["lora_weight_norm"] for s in steps
                                       if "lora_weight_norm" in s], default=None)
    rec["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None

    dst = os.path.join(OUTDIR, "p3_nan_attribution.json")
    prev = []
    if os.path.exists(dst):
        try:
            with open(dst, encoding="utf-8") as f:
                prev = json.load(f).get("configs", [])
        except Exception:
            prev = []
    prev = [c for c in prev if c.get("tag") != a.tag]
    prev.append(rec)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump({"meta": {"script": "tools/_p44c_p3_nan_attribution.py",
                            "task": "task-11 (P3 R3.22, GPU part)",
                            "protocol": ("paper3/scripts/run_training.py: positional "
                                         "20-sample Alpaca window, blank 336x336 images, "
                                         "4-bit nf4 + double quant, LoRA q/k/v/o "
                                         "alpha=2r dropout=0.1, AdamW lr=5e-5, batch 1, "
                                         "no gradient clipping, train=samples[4:], "
                                         "eval=samples[:4]"),
                            "dE_convention": "dE = E(last epoch) - E(0)"},
                    "configs": prev}, f, indent=1, ensure_ascii=False)
    log("DONE rank=%d %s dE=%s loss_all_finite=%s max_gn_llm=%s -> %s"
        % (a.rank, a.compute_dtype, rec["dE"], rec["loss_all_finite"],
           rec["max_grad_norm"]["llm"], dst))


if __name__ == "__main__":
    main()
