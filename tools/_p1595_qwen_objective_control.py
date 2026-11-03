# -*- coding: utf-8 -*-
r"""Paper A control: isolate the TRAINING OBJECTIVE at fixed model, data, budget and site.

CORRECTION (2026-10-24): the image-token cap below is NOT honoured by transformers 5.x (the attribute
is silently discarded), so the runs archived as `outputs/analysis/qwen_objective_control_*.json`
happened at the processor default resolution (~1200-2500 tokens per image), not at 64/144. The archives
are kept as the record of what was actually run; the properly capped, matched ladder that supersedes them
is `tools/_p1612_objective_control_multimodel.py`. See docs/DECODER_CONTROL_CAP_CORRECTION_2026-10-24.md.
Motivation (see `docs/paperA_decoder_confound_paragraph.md`): the paper's two decoder experiments differ in
objective *and* scale *and* data *and* budget, so the opposite signs cannot be attributed. This script runs the
missing control on a third setup that is fully fixed except for the loss:

    model     Qwen2-VL-2B-Instruct (local, 4-bit)
    data      data/marine_captions (536 image-caption pairs, first --num-samples used)
    budget    LoRA r=8 alpha=16 dropout=0.05, batch 2, 3 epochs, AdamW lr 1e-4
    site      --arm (text_only | vision_only | both), tower isolation asserted
    loss      contrastive  = symmetric InfoNCE over pooled image/text representations (as the E table)
              generative   = causal-LM loss on the caption tokens (as the G table)

The gap is measured identically in both arms (image-token pool vs caption-position pool of the final hidden
state, L2-normalised, no projection, DG* = mean ||I - T||^2), mirroring `tools/_p1150_qwen_clean_sweep.py`.

    python tools/_p1595_qwen_objective_control.py --objective contrastive --arm both --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
import time
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

REPO = Path(__file__).resolve().parents[1]
os.chdir(REPO)

MODEL_CANDIDATES = [
    REPO / "models" / "ms_cache" / "models" / "Qwen--Qwen2-VL-2B-Instruct" / "snapshots" / "master",
    REPO / "models" / "ms_cache" / "models" / "Qwen--Qwen2-VL-2B-Instruct",
    REPO / "models" / "ms_cache" / "Qwen--Qwen2-VL-2B-Instruct",
]
DATA = REPO / "data" / "marine_captions"
OUT = REPO / "outputs" / "analysis"

ARMS = {
    "text_only": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "vision_only": ["qkv", "proj", "fc1", "fc2"],
    "both": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj",
             "qkv", "proj", "fc1", "fc2"],
}
RANK, ALPHA, DROPOUT = 8, 16, 0.05
# Qwen2-VL: image tokens = (H/28)*(W/28); the E-table protocol runs at about 196 image tokens.
MAX_IMAGE_TOKENS = 12  # 12*28 = 336 px longest edge -> about 144 image tokens
MAX_PIXELS = MAX_IMAGE_TOKENS * 28 * 28


def model_dir() -> Path:
    for c in MODEL_CANDIDATES:
        if c.is_dir():
            return c
    raise SystemExit("Qwen2-VL-2B not found locally; run the ModelScope snapshot_download first")


def load_pairs(n: int):
    from PIL import Image
    caps = json.load(io.open(DATA / "captions.json", encoding="utf-8"))["captions"]
    imgs = sorted(f for f in os.listdir(DATA) if f.lower().endswith((".jpg", ".jpeg", ".png")))
    pairs = []
    for img, cap in list(zip(imgs, caps))[:n]:
        pairs.append((Image.open(DATA / img).convert("RGB"), str(cap)))
    return pairs


def build(arm: str, use_4bit: bool):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoProcessor, BitsAndBytesConfig, Qwen2VLForConditionalGeneration

    md = str(model_dir())
    kw = {"device_map": "cuda"}
    if use_4bit:
        kw["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True, bnb_4bit_quant_type="nf4")
    else:
        kw["torch_dtype"] = torch.bfloat16
    model = Qwen2VLForConditionalGeneration.from_pretrained(md, **kw)
    proc = AutoProcessor.from_pretrained(md, trust_remote_code=True)
    try:
        proc.image_processor.size = {"longest_edge": MAX_IMAGE_TOKENS * 28, "shortest_edge": 112}
    except Exception as exc:
        print("  (image size override failed: %s)" % exc, flush=True)
    model.config.use_cache = False
    model = get_peft_model(model, LoraConfig(r=RANK, lora_alpha=ALPHA, lora_dropout=DROPOUT,
                                             bias="none", target_modules=list(ARMS[arm])))
    model.config.use_cache = False
    try:
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()
    except Exception as exc:  # keep going if a wrapper does not support it
        print("  (gradient checkpointing unavailable: %s)" % exc, flush=True)
    names = []
    for n, p in model.named_parameters():
        is_lora = ("lora_A" in n) or ("lora_B" in n)
        p.requires_grad = bool(is_lora)
        if is_lora:
            names.append(n)
    n_tr = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return model, proc, n_tr, names


def hidden_via_lm_head(model, inputs):
    """Last hidden state from the backbone only -- skips lm_head and its 152k-vocabulary logits."""
    import torch

    m = model
    while hasattr(m, "get_base_model"):
        nxt = m.get_base_model()
        if nxt is m:
            break
        m = nxt
    backbone = getattr(m, "model", m)
    keep = {k: v for k, v in inputs.items()
            if k in ("input_ids", "attention_mask", "pixel_values", "image_grid_thw",
                     "mm_token_type_ids", "second_per_grid_ts")}
    out = backbone(**keep)
    return out.last_hidden_state


def pooled(model, inputs, tokenizer, image_token_id):
    import torch
    h = hidden_via_lm_head(model, inputs)
    ids = inputs["input_ids"]
    im_mask = ids == image_token_id
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    cap_mask = torch.zeros_like(ids, dtype=torch.bool)
    for b in range(ids.shape[0]):
        pos = torch.nonzero(im_mask[b], as_tuple=False)
        start = int(pos[-1]) + 1 if len(pos) else 0
        end = ids.shape[1]
        tail = torch.nonzero(ids[b, start:] == im_end, as_tuple=False)
        if len(tail):
            end = start + int(tail[0])
        cap_mask[b, start:end] = True

    def pool(mask):
        w = mask.unsqueeze(-1).to(h.dtype)
        v = (h * w).sum(1) / w.sum(1).clamp(min=1)
        return v / v.norm(dim=-1, keepdim=True).clamp(min=1e-6)

    return pool(im_mask), pool(cap_mask), (int(im_mask.sum()), int(cap_mask.sum()))


def dg_cg(I, T):
    import torch
    d = ((I - T) ** 2).sum(-1)
    return float(d.mean()), float((I.mean(0) - T.mean(0)).norm())


def eval_inputs(proc, pairs, batch=2):
    """Packed batches (the processor pads within a batch), exactly as the E-table protocol did."""
    cache = []
    for i in range(0, len(pairs), batch):
        chunk = pairs[i:i + batch]
        texts = []
        for _img, cap in chunk:
            content = [{"type": "image"}, {"type": "text", "text": cap}]
            texts.append(proc.apply_chat_template([{"role": "user", "content": content}],
                                                  tokenize=False, add_generation_prompt=True))
        inp = proc(text=texts, images=[img for img, _ in chunk], return_tensors="pt", padding=True)
        cache.append(dict(inp))
    return cache


def gen_inputs(proc, pairs, prompt="Describe the image."):
    cache = []
    for img, cap in pairs:
        user = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
        p_txt = proc.apply_chat_template(user, tokenize=False, add_generation_prompt=True)
        full = user + [{"role": "assistant", "content": [{"type": "text", "text": cap}]}]
        f_txt = proc.apply_chat_template(full, tokenize=False, add_generation_prompt=False)
        p_ids = proc(text=[p_txt], images=[img], return_tensors="pt", padding=True)["input_ids"]
        f_inp = proc(text=[f_txt], images=[img], return_tensors="pt", padding=True)
        cache.append({"inputs": dict(f_inp), "prompt_len": int(p_ids.shape[1])})
    return cache


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--objective", choices=["contrastive", "generative"], required=True)
    ap.add_argument("--arm", choices=list(ARMS), default="both")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--num-samples", type=int, default=160)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--bf16", action="store_true", help="load in bfloat16 instead of 4-bit")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("dry run: would train", a.objective, a.arm, "on", a.num_samples, "pairs")
        return 0

    import torch
    import torch.nn.functional as F

    torch.manual_seed(a.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pairs = load_pairs(a.num_samples)
    print("pairs:", len(pairs), "| model:", model_dir().name, "| objective:", a.objective, flush=True)

    t0 = time.time()
    model, proc, n_tr, names = build(a.arm, use_4bit=not a.bf16)
    n_vis = sum(1 for n in names if ".visual." in n)
    n_lang = sum(1 for n in names if "language_model" in n)
    print("trainable %d | vision adapters %d | language adapters %d" % (n_tr, n_vis, n_lang), flush=True)
    if a.arm == "text_only" and n_vis:
        raise SystemExit("tower leak: text_only touched vision adapters")
    if a.arm == "vision_only" and n_lang:
        raise SystemExit("tower leak: vision_only touched language adapters")

    tokenizer = proc.tokenizer
    image_token_id = int(getattr(model.config, "image_token_id", None) or 151655)
    ev = eval_inputs(proc, pairs, a.batch)

    def measure():
        model.eval()
        II, TT = [], []
        with torch.no_grad():
            for j, c in enumerate(ev):
                inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in c.items()}
                I, T, _ = pooled(model, inp, tokenizer, image_token_id)
                II.append(I)
                TT.append(T)
                if j % 16 == 15:
                    torch.cuda.empty_cache()
        return dg_cg(torch.cat(II), torch.cat(TT))

    frozen_dg, frozen_cg = measure()
    print("frozen DG*=%.4f CG=%.4f" % (frozen_dg, frozen_cg), flush=True)

    cache = gen_inputs(proc, pairs) if a.objective == "generative" else ev
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.01)
    steps = (len(cache) + a.batch - 1) // a.batch
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(steps * a.epochs, 1))

    dg_h, cg_h, loss_h = [], [], []
    for ep in range(1, a.epochs + 1):
        model.train()
        ep_loss, nb = 0.0, 0
        index = list(range(0, len(cache), a.batch)) if a.objective == "generative" else list(range(len(cache)))
        for i in index:
            chunk = cache[i:i + a.batch]
            if a.objective == "contrastive":
                inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in chunk[0].items()}
                I, T, _ = pooled(model, inp, tokenizer, image_token_id)
                logits = I @ T.T
                labels = torch.arange(I.shape[0], device=device)
                loss = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2
            else:
                ids, mask, lab, mmt = [], [], [], []
                for c in chunk:
                    inp = c["inputs"]
                    ids.append(inp["input_ids"])
                    mask.append(inp["attention_mask"])
                    l = inp["input_ids"].clone()
                    l[:, :c["prompt_len"]] = -100
                    lab.append(l)
                    if "mm_token_type_ids" in inp:
                        mmt.append(inp["mm_token_type_ids"])
                maxlen = max(t.shape[1] for t in ids)
                pad = lambda t, v: F.pad(t, (0, maxlen - t.shape[1]), value=v)
                ids = torch.cat([pad(t, tokenizer.pad_token_id or 0) for t in ids], 0)
                mask = torch.cat([pad(t, 0) for t in mask], 0)
                lab = torch.cat([pad(t, -100) for t in lab], 0)
                pv = chunk[0]["inputs"].get("pixel_values")
                if pv is not None:
                    pv = torch.cat([c["inputs"]["pixel_values"] for c in chunk], 0)
                grid = chunk[0]["inputs"].get("image_grid_thw")
                if grid is not None:
                    grid = torch.cat([c["inputs"]["image_grid_thw"] for c in chunk], 0)
                fwd = {"input_ids": ids.to(device), "attention_mask": mask.to(device),
                       "labels": lab.to(device)}
                if mmt:
                    fwd["mm_token_type_ids"] = torch.cat(
                        [pad(x, 0) for x in mmt], 0).to(device)
                if pv is not None:
                    fwd["pixel_values"] = pv.to(device)
                if grid is not None:
                    fwd["image_grid_thw"] = grid.to(device)
                out = model(**fwd)
                loss = out.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            ep_loss += float(loss.detach())
            nb += 1
            if nb % 10 == 0:
                print("    step %d loss=%.4f" % (nb, float(loss.detach())), flush=True)
        dg, cg = measure()
        dg_h.append(dg)
        cg_h.append(cg)
        loss_h.append(ep_loss / max(nb, 1))
        print("  ep %d/%d loss=%.4f DG*=%.4f CG=%.4f (frozen %.4f)"
              % (ep, a.epochs, loss_h[-1], dg, cg, frozen_dg), flush=True)
        torch.cuda.empty_cache()

    rec = {
        "meta": {
            "script": "tools/_p1595_qwen_objective_control.py",
            "objective": a.objective, "arm": a.arm, "seed": a.seed, "epochs": a.epochs,
            "num_samples": len(pairs), "batch": a.batch, "lr": a.lr,
            "model": model_dir().name, "precision": "bf16" if a.bf16 else "4-bit nf4",
            "max_image_tokens": MAX_IMAGE_TOKENS,
            "dataset": "data/marine_captions (536 image-caption pairs; first --num-samples used)",
            "reduced_budget_note": "control protocol: 64 image tokens/image, batch 4, 160 pairs, 3 epochs; identical for both objectives",
            "lora": {"r": RANK, "alpha": ALPHA, "dropout": DROPOUT},
            "n_trainable": n_tr, "n_vision_adapters": n_vis, "n_language_adapters": n_lang,
            "measurement": {
                "I": "mean pool of final hidden state over image-token positions",
                "T": "mean pool over caption positions (after last image token, before <|im_end|>)",
                "normalisation": "L2 per side, no projection",
                "DG*": "mean_i ||I_i - T_i||^2",
            },
            "elapsed_sec": round(time.time() - t0, 1),
        },
        "frozen_dg_star": frozen_dg, "frozen_cg": frozen_cg,
        "dg_star": dg_h, "cg": cg_h, "loss": loss_h,
        "delta_DG_percent": (dg_h[-1] - frozen_dg) / frozen_dg * 100.0,
    }
    if a.objective == "generative":
        rec["meta"]["generative_protocol"] = {
            "prompt": "Describe the image.",
            "loss": "causal-LM cross-entropy on caption tokens (prompt masked with -100)",
            "eval": "same image+caption forward pass as the contrastive arm",
        }
    else:
        rec["meta"]["contrastive_protocol"] = {
            "loss": "symmetric cross-entropy over I @ T.T within the batch",
            "eval": "image+caption forward pass",
        }
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / ("qwen_objective_control_%s_%s_seed%d.json" % (a.objective, a.arm, a.seed))
    io.open(p, "w", encoding="utf-8", newline="").write(json.dumps(rec, ensure_ascii=False, indent=1))
    print("wrote", p, "| delta_DG%% = %+.2f" % rec["delta_DG_percent"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())