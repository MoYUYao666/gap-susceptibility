# -*- coding: utf-8 -*-
r"""Qwen2-VL-2B strict-freezing sweep with a corrected gap measurement (2026-10-17 evening).

Derived from `tools/_p47_qwen_train.py`, which produced supplement Table E. The training protocol is unchanged so
the two runs are comparable; only the measurement is corrected.

## What was wrong with the original measurement

`_p47` pooled the "text" side over **all non-padding positions**:

    T = (hid * attention_mask).sum(1) / attention_mask.sum(1)

On a Qwen2-VL sequence the image placeholder expands to ~196 tokens and the caption is ~15 tokens, so that `T` is
about 93% image tokens. Both sides therefore carried mostly the same visual content, and they were then projected
by **two different fixed random matrices** (`proj_i`, `proj_t`, seed 0, 512-d) before the distance was taken. The
resulting `DG*` is dominated by the difference between those two arbitrary projections rather than by the
image-text gap.

## What this script measures instead

    I = mean pool of the final hidden state over the image-token positions
    T = mean pool of the final hidden state over the caption positions
        (everything after the last image token, up to the <|im_end|> that closes the user turn)
    both L2-normalised, **no projections** -- both come from the same hidden space, so none are needed
    DG* = mean_i ||I_i - T_i||^2 ,  CG = ||mean I - mean T||

For transparency the **old** construction is recomputed from the same forward pass, so the size of the convention
effect can be reported rather than asserted: `legacy_dg` = the projected, all-token variant of `_p47`.

Training is unchanged: LoRA rank 8, alpha 16, dropout 0.05, target modules per arm, bf16, batch 2, cosine schedule,
lr 1e-4, AdamW, contrastive InfoNCE on the unprojected pooled pair (the same objective as before, minus the random
projection whose only stated purpose was to unify dimensions -- unnecessary here because both sides already live in
the same 1536-d hidden space).

## Usage

    python _p1150_qwen_clean_sweep.py --apply --arms text_only --seed 42 --maxsamples 400 --epochs 3 \
        --outdir outputs/vlm_clean
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

REPO = Path("/root/p3")
sys.path.insert(0, str(REPO))
MDIR = Path("/root/autodl-tmp/hf/hub/models--Qwen--Qwen2-VL-2B-Instruct/snapshots/main")
OUT = REPO / "outputs" / "vlm_clean"

ARMS = {
    "text_only": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "vision_only": ["qkv", "proj", "fc1", "fc2"],
    "both": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj",
             "qkv", "proj", "fc1", "fc2"],
}
RANK, ALPHA = 8, 16
PROJ_DIM = 512


def build(arm, device, use_4bit):
    import torch
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    from peft import LoraConfig, get_peft_model

    kw = {"device_map": device}
    if use_4bit:
        from transformers import BitsAndBytesConfig
        kw["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True, bnb_4bit_quant_type="nf4")
    else:
        kw["torch_dtype"] = torch.bfloat16
    m = Qwen2VLForConditionalGeneration.from_pretrained(str(MDIR), **kw)
    proc = AutoProcessor.from_pretrained(str(MDIR), trust_remote_code=True)
    m.config.use_cache = False
    m = get_peft_model(m, LoraConfig(r=RANK, lora_alpha=ALPHA, lora_dropout=0.05,
                                     bias="none", target_modules=list(ARMS[arm])))
    lora_names = []
    for n, p in m.named_parameters():
        is_lora = ("lora_A" in n) or ("lora_B" in n)
        p.requires_grad = bool(is_lora)
        if is_lora:
            lora_names.append(n)
    n_tr = sum(p.numel() for p in m.parameters() if p.requires_grad)
    return m, proc, n_tr, lora_names


def precompute_inputs(proc, batches):
    cache = []
    for b in batches:
        content = [[{"type": "image"}, {"type": "text", "text": str(c)}] for c in b["caption"]]
        texts = [proc.apply_chat_template([{"role": "user", "content": c}],
                                         tokenize=False, add_generation_prompt=True)
                 for c in content]
        inp = proc(text=texts, images=[im for im in b["image"]], return_tensors="pt", padding=True)
        cache.append(dict(inp))
    return cache


def _hidden(model, inp):
    """Final hidden state via the lm_head input, avoiding the whole-layer stack `output_hidden_states` builds."""
    base = model
    while hasattr(base, "get_base_model"):
        nxt = base.get_base_model()
        if nxt is base:
            break
        base = nxt
    cap = {}

    def grab(_m, inputs):
        cap["h"] = inputs[0]

    h = base.lm_head.register_forward_pre_hook(grab)
    try:
        model(**inp)
    finally:
        h.remove()
    if "h" not in cap:
        raise RuntimeError("lm_head hook did not fire")
    return cap["h"]


def _caption_mask(input_ids, tokenizer, image_token_id):
    import torch
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    B, L = input_ids.shape
    m = torch.zeros((B, L), dtype=torch.bool, device=input_ids.device)
    for b in range(B):
        pos = (input_ids[b] == image_token_id).nonzero(as_tuple=True)[0]
        start = int(pos[-1]) + 1 if len(pos) else 0
        seg = input_ids[b, start:]
        stop = (seg == im_end).nonzero(as_tuple=True)[0]
        end = start + int(stop[0]) if len(stop) else L
        m[b, start:end] = True
    return m


def pooled(model, inp, tokenizer, image_token_id, proj_i, proj_t):
    """Return clean (I, T), the legacy projected pair, and the token counts used as a sanity check."""
    import torch
    import torch.nn.functional as F

    hid = _hidden(model, inp)                      # (B, L, D)
    tok = inp["input_ids"]
    attn = inp["attention_mask"].bool()
    img_m = (tok == image_token_id) & attn
    cap_m = _caption_mask(tok, tokenizer, image_token_id) & attn
    leg_m = attn

    def pool(mask):
        m = mask.unsqueeze(-1).to(hid.dtype)
        return (hid * m).sum(1) / m.sum(1).clamp(min=1)

    I = F.normalize(pool(img_m).float(), p=2, dim=-1)
    T = F.normalize(pool(cap_m).float(), p=2, dim=-1)
    T_leg = F.normalize(pool(leg_m).float(), p=2, dim=-1)
    # the original construction, for the convention comparison only
    I_leg = F.normalize(proj_i(pool(img_m).float()), p=2, dim=-1)
    T_leg = F.normalize(proj_t(pool(leg_m).float()), p=2, dim=-1)
    counts = {"img": img_m.sum(1).tolist(), "cap": cap_m.sum(1).tolist(), "all": attn.sum(1).tolist()}
    return (I, T), (I_leg, T_leg), counts


def dg_cg(I, T):
    dg = float(((I - T) ** 2).sum(-1).mean())
    cg = float((I.mean(0) - T.mean(0)).norm())
    return dg, cg


def main() -> int:
    argv = sys.argv
    apply_ = "--apply" in argv
    epochs = int(argv[argv.index("--epochs") + 1]) if "--epochs" in argv else 3
    maxs = int(argv[argv.index("--maxsamples") + 1]) if "--maxsamples" in argv else 400
    batch = int(argv[argv.index("--batch") + 1]) if "--batch" in argv else 2
    use_4bit = "--4bit" in argv
    seed = int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 42
    outdir = argv[argv.index("--outdir") + 1] if "--outdir" in argv else "outputs/vlm_clean"
    out = REPO / outdir
    if "--arms" in argv:
        arms = argv[argv.index("--arms") + 1].split(",")
    else:
        arms = list(ARMS)

    if not apply_:
        print("=== Qwen2-VL-2B clean sweep (dry run) ===")
        print(f"  model {MDIR}")
        print(f"  arms={arms} epochs={epochs} max_samples={maxs} batch={batch} seed={seed}")
        print("  measurement: I = image-token pool, T = caption-span pool, no projection; legacy variant also recorded")
        print("  (pass --apply to run)")
        return 0

    import torch
    import torch.nn.functional as F
    from src.dataset import create_dataloaders

    out.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"=== Qwen2-VL-2B clean sweep (device={device} bf16={not use_4bit}) ===", flush=True)

    torch.manual_seed(seed)
    loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                      batch_size=batch, max_samples=maxs)
    batches = list(loader)
    print(f"  data: {len(batches)} batches x batch {batch}", flush=True)

    summary = {}
    for arm in arms:
        print(f"\n  -- {arm} --", flush=True)
        t0 = time.time()
        model, proc, n_tr, lora_names = build(arm, device, use_4bit)
        n_vis = sum(1 for n in lora_names if ".visual." in n)
        n_lang = sum(1 for n in lora_names if "language_model" in n)
        print(f"     n_trainable={n_tr:,} | vision {n_vis} | language {n_lang}", flush=True)
        if arm == "text_only" and n_vis:
            print(f"     TOWER LEAK: text_only touched {n_vis} vision adapters", flush=True)
            return 1
        if arm == "vision_only" and n_lang:
            print(f"     TOWER LEAK: vision_only touched {n_lang} language adapters", flush=True)
            return 1

        image_token_id = int(getattr(model.config, "image_token_id", None)
                             or getattr(model.config, "image_token_index", 151655))
        hdim = model.config.text_config.hidden_size
        g = torch.Generator().manual_seed(0)
        proj_i = torch.nn.Linear(hdim, PROJ_DIM, bias=False).to(device)
        proj_t = torch.nn.Linear(hdim, PROJ_DIM, bias=False).to(device)
        with torch.no_grad():
            for L in (proj_i, proj_t):
                L.weight.copy_(torch.randn(PROJ_DIM, hdim, generator=g) / hdim ** 0.5)
        for L in (proj_i, proj_t):
            L.requires_grad_(False)

        cache = precompute_inputs(proc, batches)
        params = [p for p in model.parameters() if p.requires_grad]
        opt = torch.optim.AdamW(params, lr=1e-4, weight_decay=0.01)
        total = len(batches) * epochs
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(total, 1))
        tokenizer = proc.tokenizer

        dg_h, cg_h, leg_h, loss_h = [], [], [], []
        for ep in range(1, epochs + 1):
            model.train()
            ep_loss, nb = 0.0, 0
            for bi, b in enumerate(batches):
                inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in cache[bi].items()}
                (I, T), _, _ = pooled(model, inp, tokenizer, image_token_id, proj_i, proj_t)
                logits = I @ T.T
                labels = torch.arange(I.shape[0], device=device)
                loss = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2
                loss.backward()
                torch.nn.utils.clip_grad_norm_(params, 1.0)
                opt.step(); sched.step(); opt.zero_grad()
                ep_loss += float(loss); nb += 1
            model.eval()
            with torch.no_grad():
                II, TT, LL, MM = [], [], [], []
                counts_seen = None
                for bi, b in enumerate(batches):
                    inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in cache[bi].items()}
                    (i_, t_), (il_, tl_), counts = pooled(model, inp, tokenizer, image_token_id, proj_i, proj_t)
                    II.append(i_); TT.append(t_); LL.append(il_); MM.append(tl_)
                    counts_seen = counts_seen or counts
                dg, cg = dg_cg(torch.cat(II), torch.cat(TT))
                leg_dg, _ = dg_cg(torch.cat(LL), torch.cat(MM))
            dg_h.append(dg); cg_h.append(cg); leg_h.append(leg_dg); loss_h.append(ep_loss / max(nb, 1))
            print(f"     ep {ep:>2}/{epochs} loss={ep_loss/max(nb,1):.4f} "
                  f"clean DG*={dg:.4f} CG={cg:.4f} | legacy DG*={leg_dg:.4f}", flush=True)
            torch.cuda.empty_cache()

        rec = {
            "arm": arm, "seed": seed, "n_trainable": n_tr, "n_vis": n_vis, "n_lang": n_lang,
            "epochs": epochs, "max_samples": maxs, "batch": batch, "4bit": use_4bit,
            "dg_star": dg_h, "cg": cg_h, "legacy_dg_star": leg_h, "loss": loss_h,
            "dg_span": max(dg_h) - min(dg_h), "cg_span": max(cg_h) - min(cg_h),
            "legacy_dg_span": max(leg_h) - min(leg_h),
            "token_counts_first_batch": counts_seen,
            "measurement": {
                "I": "mean pool of final hidden state over image-token positions",
                "T": "mean pool of final hidden state over caption positions (after last image token, before <|im_end|>)",
                "normalisation": "L2 per side, NO projection",
                "DG*": "mean_i ||I_i - T_i||^2",
                "legacy_dg_star": "the _p47 construction (all-token T, two fixed random 512-d projections), same forward pass",
            },
            "elapsed_sec": round(time.time() - t0, 1),
        }
        summary[arm] = rec
        p = out / f"{arm}_seed{seed}.json"
        io.open(p, "w", encoding="utf-8", newline="").write(json.dumps(rec, ensure_ascii=False, indent=1))
        print(f"     wrote {p} ({rec['elapsed_sec']}s)", flush=True)
        del model
        torch.cuda.empty_cache()

    io.open(out / f"summary_seed{seed}.json", "w", encoding="utf-8", newline="").write(
        json.dumps(summary, ensure_ascii=False, indent=1))
    print(f"\n  seed {seed} done -> {out}/summary_seed{seed}.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
