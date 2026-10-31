# -*- coding: utf-8 -*-
r"""Paper A objective control, generalised across decoder-VLM families and scales.

Why this script exists
----------------------
`tools/_p1595_qwen_objective_control.py` ran the missing *local* control: Qwen2-VL-2B-Instruct with
everything held fixed except the loss, and it produced contrastive `-73.5 %` against generative
`-14.2 %` on `DG*`. That single model, however, still cannot separate the objective from the scale,
the family, the data and the budget, because Paper A's two decoder experiments (supplement Table
`tab:vlm`, Qwen2-VL-2B, contrastive, narrows; supplement Table `tab:llava`, LLaVA-1.5-7B, generative,
widens) differ in all of those at once.

This script is the matched ladder that is meant to be run on a cloud GPU: the SAME protocol, the SAME
measurement and the SAME two losses across four models, so objective, scale and family can finally be
varied one at a time.

    model registry     qwen2vl-2b    Qwen/Qwen2-VL-2B-Instruct
                       qwen25vl-3b   Qwen/Qwen2.5-VL-3B-Instruct
                       qwen25vl-7b   Qwen/Qwen2.5-VL-7B-Instruct
                       llava15-7b    llava-hf/llava-1.5-7b-hf
    data               data/marine_captions (first --num-samples pairs, deterministic order)
    budget             LoRA r=8 alpha=16 dropout=0.05, AdamW lr 1e-4, gradient checkpointing on
    site               --arm (text_only | vision_only | both), tower isolation asserted
    loss               contrastive = symmetric InfoNCE over pooled I/T within the batch
                       generative  = causal-LM cross-entropy on caption tokens, prompt masked -100

The reported quantity is unchanged from the local control: `DG* = mean_i ||I_i - T_i||^2` with `I` the
mean pool of the final hidden state over image-token positions and `T` the mean pool over the caption
positions, both L2-normalised, no projection, paired by construction. `delta_DG_percent` is the single
signed number `(after - before) / before * 100`; negative means the gap narrowed.

Two protocols
-------------
`--protocol match` is the E-table-size protocol used for the cloud ladder (320 pairs, 3 epochs,
image-token cap 196, batch 4 for the Qwen family and 2 for LLaVA, whose 336x336 CLIP tower is fixed).
`--protocol reduced` is exactly the local 2B control (160 pairs, 1 epoch, image-token cap 144, batch 4)
so that a cloud run of the ladder stays directly comparable with the archived local result.

Notes that matter on a cloud box
--------------------------------
* `--dry-run` resolves the model id, the protocol and the output path and does no GPU work at all.
* `--smoke` is the 2-pair / 1-epoch / 32-image-token safety mode; it is what may be run on an 8 GB card.
* A LLaVA image is always 336x336 CLIP, i.e. 576 image tokens: the `--image-tokens` cap cannot bind
  there and the realised count is recorded in the output as `image_tokens_realised`.
* Nothing is written until the run has finished; the archived 2B JSONs are never touched.
* **Reproducibility, honestly stated.** The frozen measurement is bit-identical across processes at a
  fixed `(model, protocol, seed)` — verified, and it is what the cross-objective assertion relies on.
  The *trained* value is not bit-reproducible in 4-bit: repeated identical-seed smoke runs produced
  different LoRA weight hashes and moved `DG*` inside a small band (measured spread about 1 % of the
  frozen value on the smoke scale). That is bitsandbytes/CUDA nondeterminism in the 4-bit backward
  pass, not a seeding mistake, and it is why `delta_DG_percent` must never be compared run-to-run at
  the level of its last digit. Read the ladder as directions and multi-seed spreads, exactly as the
  acceptance criteria in `docs/decoder_attribution_cloud_notes.md` say. `--bf16` removes the
  quantisation step if true bitwise reproducibility is ever needed, at the cost of comparability with
  the 4-bit runs.

    python tools/_p1612_objective_control_multimodel.py --dry-run --model llava15-7b --objective generative
    python tools/_p1612_objective_control_multimodel.py --model llava15-7b --objective contrastive \
        --protocol match --apply
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import platform
import socket
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

REPO = Path(__file__).resolve().parents[1]
SCRIPT_REL = "tools/_p1612_objective_control_multimodel.py"
DATA = REPO / "data" / "marine_captions"
OUT = REPO / "outputs" / "analysis"

# --------------------------------------------------------------------------------------------------
# model registry
# --------------------------------------------------------------------------------------------------
# `hf_repo` is the canonical Hugging Face id and is what goes into the result JSON. `local` is the
# list of snapshot directories searched *first* (ModelScope layout, then the plain HF cache), because
# on this project the weights are normally fetched on the machine that runs them. `backbone_attr` is
# the attribute path from the conditioned wrapper down to the module that emits the final hidden
# state: taking it directly is what avoids materialising `lm_head` logits (152k vocabulary on Qwen,
# 32k on LLaVA) in the measurement path.
MODELS = {
    "qwen2vl-2b": {
        "hf_repo": "Qwen/Qwen2-VL-2B-Instruct",
        "family": "qwen2-vl",
        "model_class": "Qwen2VLForConditionalGeneration",
        "image_tokens": "dynamic",
        "patch_size": 14,
        "merge_size": 2,
        "backbone_attr": ("model",),
        "local": [
            REPO / "models" / "ms_cache" / "models" / "Qwen--Qwen2-VL-2B-Instruct" / "snapshots" / "master",
            REPO / "models" / "ms_cache" / "models" / "Qwen--Qwen2-VL-2B-Instruct",
        ],
    },
    "qwen25vl-3b": {
        "hf_repo": "Qwen/Qwen2.5-VL-3B-Instruct",
        "family": "qwen2.5-vl",
        "model_class": "Qwen2_5_VLForConditionalGeneration",
        "image_tokens": "dynamic",
        "patch_size": 14,
        "merge_size": 2,
        "backbone_attr": ("model",),
        "local": [
            REPO / "models" / "ms_cache" / "models" / "Qwen--Qwen2.5-VL-3B-Instruct" / "snapshots" / "master",
            REPO / "models" / "ms_cache" / "models" / "Qwen--Qwen2.5-VL-3B-Instruct",
        ],
    },
    "qwen25vl-7b": {
        "hf_repo": "Qwen/Qwen2.5-VL-7B-Instruct",
        "family": "qwen2.5-vl",
        "model_class": "Qwen2_5_VLForConditionalGeneration",
        "image_tokens": "dynamic",
        "patch_size": 14,
        "merge_size": 2,
        "backbone_attr": ("model",),
        "local": [
            REPO / "models" / "ms_cache" / "models" / "Qwen--Qwen2.5-VL-7B-Instruct" / "snapshots" / "master",
            REPO / "models" / "ms_cache" / "models" / "Qwen--Qwen2.5-VL-7B-Instruct",
        ],
    },
    "llava15-7b": {
        "hf_repo": "llava-hf/llava-1.5-7b-hf",
        "family": "llava-1.5",
        "model_class": "LlavaForConditionalGeneration",
        "image_tokens": "fixed",
        # CLIP ViT-L/14-336 with the "default" feature strategy: 336/14 = 24 patches per edge, the
        # CLS token is dropped and 576 patch tokens are spliced in.
        "patch_size": 14,
        "merge_size": 1,
        "backbone_attr": ("model",),
        "local": [
            REPO / "models" / "llava-hf",
        ],
    },
}

# --------------------------------------------------------------------------------------------------
# protocol and adaptation-site definitions
# --------------------------------------------------------------------------------------------------
PROTOCOLS = {
    "reduced": {
        "pairs": 160, "epochs": 1, "image_tokens": 144,
        "batch": {"qwen": 4, "llava": 4},
        "note": "local 2B control protocol (tools/_p1595_qwen_objective_control.py, seed 42)",
    },
    "match": {
        "pairs": 320, "epochs": 3, "image_tokens": 196,
        "batch": {"qwen": 4, "llava": 2},
        "note": "E-table-size protocol; LLaVA is held at batch 2 because its image is a fixed 336x336 "
                "CLIP crop and its LM is 7B",
    },
}
SMOKE = {"pairs": 2, "epochs": 1, "image_tokens": 32}

ARMS = {
    "text_only": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "vision_only": ["qkv", "proj", "fc1", "fc2", "k_proj", "v_proj", "out_proj", "linear_1", "linear_2"],
    "both": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj",
             "qkv", "proj", "fc1", "fc2", "out_proj", "linear_1", "linear_2"],
}
RANK, ALPHA, DROPOUT = 8, 16, 0.05
ADAMW_WEIGHT_DECAY = 0.01
GRAD_CLIP = 1.0
SEED_FROZEN_TOLERANCE = 0.0  # bit-identical: the frozen pass is deterministic once the seed is set


# --------------------------------------------------------------------------------------------------
# registry helpers
# --------------------------------------------------------------------------------------------------
def model_dir(name: str):
    """Locate the weights of a registry entry; return None when only the HF id is resolvable."""
    for c in MODELS[name]["local"]:
        if Path(c).is_dir():
            return Path(c)
    return None


def model_source(name: str) -> str:
    md = model_dir(name)
    return str(md) if md is not None else MODELS[name]["hf_repo"]


def resolve_revision(name: str, source: str) -> str:
    """Best-effort weight revision: the snapshot directory name when it looks like a hash."""
    d = model_dir(name)
    if d is not None:
        tail = d.name
        if tail and len(tail) >= 7 and all(ch in "0123456789abcdef" for ch in tail.lower()) and "master" != tail:
            return tail
        try:
            rp = d / "refs" / "main"
            if rp.is_file():
                return rp.read_text(encoding="utf-8").strip()
        except Exception:
            pass
        return "local snapshot (%s); no hash recorded" % tail
    return "unresolved (online repo id only)"


def load_class(dotted: str):
    import transformers
    cls = getattr(transformers, dotted, None)
    if cls is None:
        raise SystemExit(
            "this transformers build has no %s (version %s); upgrade transformers before running"
            % (dotted, transformers.__version__))
    return cls


# --------------------------------------------------------------------------------------------------
# data and protocol resolution
# --------------------------------------------------------------------------------------------------
def load_pairs(n: int):
    """First n image-caption pairs in deterministic (sorted filename) order."""
    from PIL import Image
    caps = json.load(io.open(DATA / "captions.json", encoding="utf-8"))["captions"]
    imgs = sorted(f for f in os.listdir(DATA) if f.lower().endswith((".jpg", ".jpeg", ".png")))
    if len(imgs) < n:
        raise SystemExit("only %d images in %s, %d requested" % (len(imgs), DATA, n))
    pairs = []
    for img, cap in list(zip(imgs, caps))[:n]:
        pairs.append((Image.open(DATA / img).convert("RGB"), str(cap)))
    return pairs


def resolve_protocol(a):
    """Fold --protocol, --smoke and the explicit overrides into one resolved configuration."""
    spec = dict(PROTOCOLS[a.protocol])
    protocol_name = a.protocol
    if a.smoke:
        spec.update(SMOKE)
        protocol_name = "smoke"
    key = "llava" if MODELS[a.model]["family"].startswith("llava") else "qwen"
    batch = spec["batch"][key]
    if a.batch is not None:
        batch = a.batch
    overrides = []
    if a.image_tokens is not None:
        spec["image_tokens"] = a.image_tokens
        overrides.append("image_tokens=%d" % a.image_tokens)
    if a.num_samples is not None:
        spec["pairs"] = a.num_samples
        overrides.append("num_samples=%d" % a.num_samples)
    if a.epochs is not None:
        spec["epochs"] = a.epochs
        overrides.append("epochs=%d" % a.epochs)
    if a.batch is not None:
        overrides.append("batch=%d" % a.batch)
    if a.smoke:
        note = ("smoke mode: 2 pairs, 1 epoch, 32 image tokens; a pipeline and memory check only, "
                "never a reportable result")
    else:
        note = spec["note"]
    if overrides:
        note += " | CLI overrides: " + ", ".join(overrides)
    return {
        "protocol": protocol_name,
        "pairs": spec["pairs"],
        "epochs": spec["epochs"],
        "image_tokens": spec["image_tokens"],
        "batch": batch,
        "batch_origin": "override" if a.batch is not None else "protocol default",
        "note": note,
    }


# --------------------------------------------------------------------------------------------------
# model construction
# --------------------------------------------------------------------------------------------------
def set_pixel_budget(ip, image_tokens: int, cfg: dict) -> str:
    """Apply the image-token cap to a Qwen image processor; return the way it was applied.

    One post-merge visual token is produced by a `patch_size x patch_size` block, so the pixel budget
    for `image_tokens` tokens per image is `image_tokens * patch_size**2`. Calibrated on this
    project's `marine_captions` images against transformers 5.16.1: a budget of 6272 px realised 21-28
    tokens, 28224 px realised ~135, 38416 px realised ~180. The realised count still lands *under*
    the cap, because Qwen resizes with the aspect ratio preserved and rounds both edges to a multiple
    of `patch_size * merge_size`; `image_tokens_realised` in the JSON is the number that counts.

    The attribute spelling moved between transformers generations and getting it wrong is silent:
    v4 spells two *total pixel budgets* `max_pixels`/`min_pixels` (the keys `preprocessor_config.json`
    ships), while v5 collapses them into the image processor's `size` attribute as a single pixel
    budget (`SizeDict.longest_edge`; `shortest_edge` is the *lower* bound). A v4-style assignment of
    the edges as if they were edge lengths raises nothing and simply does not bind, and that is the
    trap the archived local control fell into: its `image_processor.size = {...}` was discarded by
    the processor call, so it trained at about 12 image tokens per image while its own JSON claimed a
    144-token cap. Here the budget is written to whichever spelling the installed build has, and the
    realised count is reported so a silent failure becomes visible in the log and in the JSON.
    """
    ps = cfg["patch_size"]
    if cfg["image_tokens"] != "dynamic":
        # Fixed-crop processors (LLaVA's CLIPImageProcessor) have no pixel budget to set and their
        # `size` is a crop geometry that must not be touched: mutating it changes nothing about the
        # realised count but does change the forward pass (measured: frozen DG* moved from 0.554199
        # to 0.549316 on the same two pairs), which would silently break comparability with any run
        # made before the change. Leave it alone.
        return "not applied (fixed-crop image processor)"
    budget, floor = image_tokens * ps * ps, ps * ps
    done = []
    if hasattr(ip, "max_pixels") and hasattr(ip, "min_pixels"):
        ip.max_pixels, ip.min_pixels = budget, floor
        done.append("max_pixels/min_pixels")
    if hasattr(ip, "size") and hasattr(ip.size, "longest_edge"):
        # v5: the pixel budget lives in `size.longest_edge`. Mutating the existing SizeDict works;
        # replacing `ip.size` with a plain dict does not (the resize step then rejects it).
        ip.size.longest_edge, ip.size.shortest_edge = budget, floor
        done.append("size.longest_edge")
    for attr, val in (("patch_size", ps), ("merge_size", cfg["merge_size"])):
        try:
            setattr(ip, attr, val)
        except Exception:
            pass
    return ", ".join(done) if done else "NOTHING (no known pixel-budget attribute found)"


def build(name: str, arm: str, use_4bit: bool, image_tokens: int, source: str):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoProcessor, BitsAndBytesConfig

    cls = load_class(MODELS[name]["model_class"])
    kw = {"device_map": "cuda"}
    if use_4bit:
        kw["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True, bnb_4bit_quant_type="nf4")
    else:
        kw["dtype"] = torch.bfloat16
    try:
        model = cls.from_pretrained(source, **kw)
    except TypeError:
        # transformers < 5 spells the same argument torch_dtype
        kw.pop("dtype", None)
        if not use_4bit:
            kw["torch_dtype"] = torch.bfloat16
        model = cls.from_pretrained(source, **kw)

    proc = AutoProcessor.from_pretrained(source, trust_remote_code=True)
    applied = set_pixel_budget(proc.image_processor, image_tokens, MODELS[name])
    if MODELS[name]["image_tokens"] == "dynamic":
        # Qwen sizes the image by a pixel budget and resizes with the aspect ratio preserved, so the
        # cap is a ceiling rather than an equality: `image_tokens_realised` records what came out.
        print("  (image-token cap %d applied through %s)" % (image_tokens, applied), flush=True)
    else:
        print("  (note: %s uses a fixed 336x336 CLIP crop, so the %d-image-token cap cannot bind; "
              "budget set through %s)" % (MODELS[name]["family"], image_tokens, applied), flush=True)

    model.config.use_cache = False
    targets = targets_for(model, arm)
    if not targets:
        raise SystemExit("arm %s selected no Linear module in this model; inspect the module names" % arm)
    model = get_peft_model(model, LoraConfig(r=RANK, lora_alpha=ALPHA, lora_dropout=DROPOUT,
                                             bias="none", target_modules=targets))
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
    return model, proc, n_tr, names, targets, applied


def tower_of(module_name: str) -> str:
    """Which adaptation site a parameter or module belongs to.

    The two families name their towers differently but disjointly, and PEFT matches a target list by
    `key.endswith("." + entry)`, so a leaf name that exists on both sides is filtered by this
    classification rather than by the string alone.
    """
    n = module_name
    if ("vision_tower" in n) or n.startswith("vision") or ".visual." in n or ".vision_model." in n:
        return "vision"
    if "multi_modal_projector" in n:
        return "projector"
    if ("language_model" in n) or n.startswith("model.layers") or ".model.layers." in n:
        return "language"
    return "other"


def targets_for(model, arm: str) -> list:
    """Fully qualified Linear module names for one arm, classified by tower.

    Fully qualified names are used (not bare leaf names) so that a target cannot be matched on the
    wrong tower: `q_proj` alone exists in both LLaVA towers.
    """
    import torch
    wanted = set(ARMS[arm])
    out = []
    for n, m in model.named_modules():
        if not isinstance(m, torch.nn.Linear):
            continue
        leaf = n.rsplit(".", 1)[-1]
        if leaf not in wanted:
            continue
        t = tower_of(n)
        if arm == "text_only" and t == "language":
            out.append(n)
        elif arm == "vision_only" and t in ("vision", "projector"):
            out.append(n)
        elif arm == "both" and t in ("language", "vision", "projector"):
            out.append(n)
    return sorted(out)


# --------------------------------------------------------------------------------------------------
# hidden-state extraction and the gap measurement
# --------------------------------------------------------------------------------------------------
def backbone_of(model, name: str):
    """Walk past the PEFT wrapper and the conditioned wrapper down to the bare backbone.

    For LLaVA the registry path is `model`, i.e. `LlavaForConditionalGeneration.model`, a `LlavaModel`
    that owns `language_model` (a `LlamaModel`) and `vision_tower`; its `lm_head` hangs off
    `language_model` and is never reached from here. For the Qwen family the path is the same one
    attribute, `Qwen2VLForConditionalGeneration.model`. Going through the backbone is what keeps
    vocabulary-sized logits out of the measurement path.
    """
    m = model
    while hasattr(m, "get_base_model"):
        nxt = m.get_base_model()
        if nxt is m:
            break
        m = nxt
    for attr in MODELS[name]["backbone_attr"]:
        if not hasattr(m, attr):
            raise RuntimeError("backbone path %r does not exist on %s" % (attr, type(m).__name__))
        m = getattr(m, attr)
    if not hasattr(m, "forward"):
        raise RuntimeError("backbone resolution for %s produced %s" % (name, type(m).__name__))
    return m


def hidden_via_backbone(model, name: str, inputs):
    """Last hidden state, from the backbone only -- no lm_head, no vocabulary-sized logits."""
    import inspect
    bb = backbone_of(model, name)
    try:
        accepted = set(inspect.signature(bb.forward).parameters)
    except (TypeError, ValueError):
        accepted = set(inputs)
    keep = {k: v for k, v in inputs.items()
            if k in accepted and k in ("input_ids", "attention_mask", "pixel_values",
                                       "image_grid_thw", "mm_token_type_ids", "second_per_grid_ts")}
    out = bb(**keep)
    return out.last_hidden_state


def pooled(model, name: str, inputs, tokenizer, image_token_id):
    """The two sides of DG*: image-token pool and caption-position pool, L2-normalised."""
    import torch
    h = hidden_via_backbone(model, name, inputs)
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
    d = ((I - T) ** 2).sum(-1)
    return float(d.mean()), float((I.mean(0) - T.mean(0)).norm())


# --------------------------------------------------------------------------------------------------
# input construction
# --------------------------------------------------------------------------------------------------
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


def realised_image_tokens(name: str, inputs) -> int:
    """Image tokens the processor actually produced for the first batch, summed over the batch."""
    cfg = MODELS[name]
    if cfg["image_tokens"] == "fixed":
        img_id = 32000
        return int((inputs["input_ids"] == img_id).sum())
    grid = inputs.get("image_grid_thw")
    if grid is None:
        return -1
    mg = cfg["merge_size"]
    total = 0
    for row in grid.tolist():
        total += int(row[0] * row[1] * row[2]) // (mg * mg)
    return total


# --------------------------------------------------------------------------------------------------
# the two objectives
# --------------------------------------------------------------------------------------------------
def step_contrastive(model, name: str, batch_inputs, tokenizer, image_token_id, device, F):
    """Symmetric InfoNCE over the pooled I/T of one batch (same loss as the E table)."""
    import torch
    inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in batch_inputs.items()}
    I, T, _ = pooled(model, name, inp, tokenizer, image_token_id)
    logits = I @ T.T
    labels = torch.arange(I.shape[0], device=device)
    loss = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2
    return loss


def step_generative(model, chunk, tokenizer, device, F):
    """Causal-LM cross-entropy over the caption tokens, prompt positions masked with -100."""
    import torch
    ids, mask, lab, mmt = [], [], [], []
    for c in chunk:
        inp = c["inputs"]
        ids.append(inp["input_ids"])
        mask.append(inp["attention_mask"])
        l = inp["input_ids"].clone()
        plen = min(int(c["prompt_len"]), l.shape[1] - 1)  # keep at least one supervised token
        l[:, :plen] = -100
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
    fwd = {"input_ids": ids.to(device), "attention_mask": mask.to(device), "labels": lab.to(device)}
    if mmt:  # Qwen M-RoPE needs the modality id per position; LLaVA has no such input
        fwd["mm_token_type_ids"] = torch.cat([pad(x, 0) for x in mmt], 0).to(device)
    if pv is not None:
        fwd["pixel_values"] = pv.to(device)
    if grid is not None:
        fwd["image_grid_thw"] = grid.to(device)
    out = model(**fwd)
    return out.loss


# --------------------------------------------------------------------------------------------------
# matched-pair sanity check against the sibling objective
# --------------------------------------------------------------------------------------------------
SHARED_FIELDS = ("model", "model_repo", "protocol", "num_samples", "epochs", "max_image_tokens",
                 "batch", "seed", "precision", "lora", "arm")


def frozen_signature(rec: dict) -> dict:
    """Exactly what determines the untrained forward pass.

    Two runs may only be compared as an A/B pair when this signature is equal: a smoke run, an apply
    run and a different protocol all produce different frozen baselines, so comparing across them
    would be comparing two different experiments.
    """
    m = rec["meta"]
    return {"model": m["model"], "model_repo": m["model_repo"], "protocol": m["protocol"],
            "num_samples": m["num_samples"], "image_tokens": m["max_image_tokens"],
            "batch": m["batch"], "seed": m["seed"], "precision": m["precision"],
            "arm": m["arm"], "mode": m["mode"]}


def sibling_check(rec: dict, path: Path, other: str) -> dict:
    """The frozen forward pass must be identical between the two objectives of one model and seed.

    Both objectives of a (model, seed) pair are supposed to share the *same untrained* measurement,
    since the loss does not exist until after the frozen pass. If they disagree, the A/B is not
    matched and no conclusion may be drawn from it, so this raises instead of reporting a number.
    """
    other_path = path.parent / path.name.replace("_%s_" % rec["meta"]["objective"], "_%s_" % other)
    result = {"sibling_path": str(other_path.relative_to(REPO)).replace("\\", "/") if
              str(other_path).startswith(str(REPO)) else str(other_path),
              "sibling_present": other_path.is_file(), "compared": False}
    if not other_path.is_file():
        result["verdict"] = ("sibling objective not run yet; run %s for the same model and seed "
                             "and re-run this one to complete the A/B check" % other)
        return result
    sib = json.load(io.open(other_path, encoding="utf-8"))
    problems = []
    for f in SHARED_FIELDS:
        mine, theirs = rec["meta"].get(f, "<missing>"), sib.get("meta", {}).get(f, "<missing>")
        if mine != theirs:
            problems.append("%s: %r vs %r" % (f, mine, theirs))
    # A field added to the record but not to SHARED_FIELDS would be compared by nobody, so any new
    # key is treated as a potential protocol difference until it is classified here or in the
    # explicitly per-run list below.
    per_run = {"script", "mode", "objective", "elapsed_sec", "versions", "hostname", "platform",
               "device", "lora_targets", "n_trainable", "n_vision_adapters", "n_language_adapters",
               "n_projector_adapters", "gradient_checkpointing", "measurement", "image_tokens_realised",
               "image_token_id", "backbone_path", "lm_head_called", "dataset", "protocol_note",
               "contrastive_protocol", "generative_protocol", "frozen_signature", "ab_check",
               "model_family", "model_class", "model_source", "revision", "batch_origin", "lr",
               "image_token_budget_applied_via", "nonfinite_steps_skipped", "epochs_reported",
               "epochs_requested", "final_epoch_truncated"}
    unclassified = sorted(set(rec["meta"]) - set(SHARED_FIELDS) - per_run)
    if unclassified:
        problems.append("unclassified meta keys that no comparison covers: %s" % unclassified)
    mine_sig, theirs_sig = frozen_signature(rec), frozen_signature(sib)
    if mine_sig != theirs_sig:
        problems.append("frozen_signature: %r vs %r" % (mine_sig, theirs_sig))
    mine_f, theirs_f = rec.get("frozen_dg_star"), sib.get("frozen_dg_star")
    if isinstance(mine_f, (int, float)) and isinstance(theirs_f, (int, float)) and theirs_f:
        rel = abs(mine_f - theirs_f) / abs(theirs_f) * 100.0
        result["frozen_abs_diff"] = abs(mine_f - theirs_f)
        result["frozen_rel_diff_percent"] = rel
        if rel > 2.0:
            problems.append("frozen_dg_star differs by %.2f%% (%r vs %r) although the untrained forward pass "
                            "should be identical" % (rel, mine_f, theirs_f))
    if problems:
        raise SystemExit("A/B mismatch between the two objectives of %s seed %d: %s\n"
                         "Both objectives must share protocol and adaptation setup."
                         % (rec["meta"]["model"], rec["meta"]["seed"], "; ".join(problems)))
    mine = float(rec["frozen_dg_star"])
    theirs = float(sib["frozen_dg_star"])
    result["compared"] = True
    result["sibling_frozen_dg_star"] = theirs
    result["abs_diff"] = abs(mine - theirs)
    if not (abs(mine - theirs) <= SEED_FROZEN_TOLERANCE):
        raise SystemExit(
            "FROZEN MISMATCH: %s seed %d measured frozen DG* %.17g for %s but %.17g for %s.\n"
            "The two objectives must share one frozen forward pass, so the A/B is not matched and the "
            "delta_DG_percent values may not be compared. Do not report this pair."
            % (rec["meta"]["model"], rec["meta"]["seed"], mine, rec["meta"]["objective"], theirs, other))
    result["verdict"] = "identical frozen DG* across both objectives"
    return result


# --------------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Objective control for Paper A, matched across decoder-VLM families and scales.")
    ap.add_argument("--model", choices=list(MODELS), default="qwen2vl-2b")
    ap.add_argument("--objective", choices=["contrastive", "generative"], required=True)
    ap.add_argument("--protocol", choices=list(PROTOCOLS), default="match")
    ap.add_argument("--arm", choices=list(ARMS), default="both")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--epochs", type=int, default=None, help="default: from --protocol (reduced 1, match 3)")
    ap.add_argument("--num-samples", type=int, default=None, help="default: from --protocol (160 / 320)")
    ap.add_argument("--batch", type=int, default=None, help="default: from --protocol and model family")
    ap.add_argument("--image-tokens", type=int, default=None, help="default: from --protocol (144 / 196)")
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--bf16", action="store_true", help="load in bfloat16 instead of 4-bit nf4")
    ap.add_argument("--smoke", action="store_true",
                    help="2 pairs, 1 epoch, 32 image tokens: the 8 GB safety mode; implies --apply")
    ap.add_argument("--dry-run", action="store_true",
                    help="no GPU work: validate the model id and print the resolved protocol")
    ap.add_argument("--apply", action="store_true", help="actually train and write the result JSON")
    a = ap.parse_args()

    cfg = MODELS[a.model]
    res = resolve_protocol(a)

    if a.dry_run:
        src = model_source(a.model)
        md = model_dir(a.model)
        print("dry run -- no GPU work, no training, no write")
        print("  model id          : %s" % a.model)
        print("  hf repo           : %s" % cfg["hf_repo"])
        print("  family            : %s" % cfg["family"])
        print("  model class       : %s" % cfg["model_class"])
        print("  processor class   : %s" % ("Qwen2VLProcessor / Qwen2_5_VLProcessor"
                                             if cfg["image_tokens"] == "dynamic" else "LlavaProcessor"))
        print("  backbone for DG*  : %s (lm_head is never called)" % ".".join(["<peft base>"] + list(cfg["backbone_attr"])))
        print("  weights           : %s" % src)
        print("  weights local     : %s" % ("yes (%s)" % md if md is not None else
                                             "no -- the cloud box must snapshot_download it first"))
        print("  revision          : %s" % resolve_revision(a.model, src))
        print("  objective         : %s" % a.objective)
        print("  arm               : %s" % a.arm)
        print("  protocol          : %s" % res["protocol"])
        print("  pairs             : %d" % res["pairs"])
        print("  epochs            : %d" % res["epochs"])
        print("  image-token cap   : %d%s" % (res["image_tokens"],
                                              "" if cfg["image_tokens"] == "dynamic"
                                              else " (cannot bind: fixed 336x336 CLIP crop)"))
        print("  batch             : %d (%s)" % (res["batch"], res["batch_origin"]))
        print("  lr                : %g" % a.lr)
        print("  precision         : %s" % ("bf16" if a.bf16 else "4-bit nf4"))
        print("  lora              : r=%d alpha=%d dropout=%g, arm targets %s"
              % (RANK, ALPHA, DROPOUT, ARMS[a.arm]))
        print("  output json       : outputs/analysis/decoder_attribution_%s_%s_seed%d.json"
              % (a.model, a.objective, a.seed))
        print("  loss              : %s" % ("symmetric InfoNCE over pooled I/T within the batch"
                                            if a.objective == "contrastive" else
                                            "causal-LM cross-entropy on caption tokens (prompt -100)"))
        print("  protocol note     : %s" % res["note"])
        if md is None:
            print("  NOTE: weights are not present locally, so --apply would download %s" % cfg["hf_repo"])
        return 0

    if not (a.apply or a.smoke):
        print("refusing to run: pass --apply (or --smoke) to train, or --dry-run to inspect the settings")
        return 2

    import torch
    import torch.nn.functional as F

    torch.manual_seed(a.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("WARNING: no CUDA device; this run is not representative", flush=True)
    pairs = load_pairs(res["pairs"])
    src = model_source(a.model)
    print("model %s (%s) | objective %s | arm %s | protocol %s" %
          (a.model, cfg["hf_repo"], a.objective, a.arm, res["protocol"]), flush=True)
    print("pairs %d | epochs %d | image-token cap %d | batch %d | 4-bit %s"
          % (len(pairs), res["epochs"], res["image_tokens"], res["batch"], not a.bf16), flush=True)

    t0 = time.time()
    model, proc, n_tr, names, targets, budget_via = build(a.model, a.arm, use_4bit=not a.bf16,
                                                         image_tokens=res["image_tokens"], source=src)
    by_tower = {"language": 0, "vision": 0, "projector": 0, "other": 0}
    for n in names:
        by_tower[tower_of(n)] += 1
    n_lang, n_vis = by_tower["language"], by_tower["vision"] + by_tower["projector"]
    print("trainable %d | vision adapters %d | language adapters %d | projector adapters %d | targets %d"
          % (n_tr, by_tower["vision"], n_lang, by_tower["projector"], len(targets)), flush=True)
    if by_tower["other"]:
        raise SystemExit("tower leak: %d adapter tensors could not be assigned to a tower" % by_tower["other"])
    if a.arm == "text_only" and (by_tower["vision"] or by_tower["projector"]):
        raise SystemExit("tower leak: text_only touched %d vision-side adapters"
                         % (by_tower["vision"] + by_tower["projector"]))
    if a.arm == "vision_only" and n_lang:
        raise SystemExit("tower leak: vision_only touched %d language adapters" % n_lang)

    tokenizer = proc.tokenizer
    image_token_id = int(getattr(model.config, "image_token_id", None)
                         or getattr(model.config, "image_token_index", None) or 151655)
    ev = eval_inputs(proc, pairs, res["batch"])
    realised = realised_image_tokens(a.model, ev[0])
    print("image token id %d | realised image tokens in the first batch %d"
          % (image_token_id, realised), flush=True)
    if realised <= 0:
        raise SystemExit("no image tokens were found in the first batch: the image text never reached "
                         "the processor, so every measurement would compare text with text")
    if (ev[0]["input_ids"] == image_token_id).sum() == 0:
        raise SystemExit("image_token_id %d does not appear in input_ids for %s; the registry entry "
                         "and the tokenizer disagree" % (image_token_id, a.model))
    if MODELS[a.model]["image_tokens"] == "dynamic":
        expected = 0.6 * res["batch"] * res["image_tokens"]
        if realised > expected:
            raise SystemExit(
                "the image-token cap did not bind: %d image tokens in the first batch of %d, more "
                "than expected (%d) for a cap of %d tokens per image applied through '%s'.\n"
                "The pixel-budget attribute name probably differs in this transformers build, which "
                "fails silently; check docs/decoder_attribution_cloud_notes.md before continuing."
                % (realised, res["batch"], int(expected), res["image_tokens"], budget_via))

    def measure():
        model.eval()
        II, TT = [], []
        with torch.no_grad():
            for j, c in enumerate(ev):
                inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in c.items()}
                I, T, _ = pooled(model, a.model, inp, tokenizer, image_token_id)
                II.append(I)
                TT.append(T)
                if j % 16 == 15 and device == "cuda":
                    torch.cuda.empty_cache()
        return dg_cg(torch.cat(II), torch.cat(TT))

    frozen_dg, frozen_cg = measure()
    print("frozen DG*=%.6f CG=%.6f" % (frozen_dg, frozen_cg), flush=True)

    cache = gen_inputs(proc, pairs) if a.objective == "generative" else ev
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=ADAMW_WEIGHT_DECAY)
    steps = (len(cache) + res["batch"] - 1) // res["batch"]
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(steps * res["epochs"], 1))

    dg_h, cg_h, loss_h = [], [], []
    nonfinite_steps = 0
    for ep in range(1, res["epochs"] + 1):
        model.train()
        ep_loss, nb = 0.0, 0
        index = list(range(0, len(cache), res["batch"])) if a.objective == "generative" \
            else list(range(len(cache)))
        for i in index:
            chunk = cache[i:i + res["batch"]]
            if a.objective == "contrastive":
                loss = step_contrastive(model, a.model, chunk[0], tokenizer, image_token_id, device, F)
            else:
                loss = step_generative(model, chunk, tokenizer, device, F)
            if not torch.isfinite(loss):
                # a 4-bit + bf16 contrastive step can overflow late in training; do not let one bad batch
                # poison the weights (the first attempt at this arm went NaN in epoch 3 and lost the run)
                opt.zero_grad(set_to_none=True)
                nonfinite_steps += 1
                print("    step %d non-finite loss; optimizer step skipped" % (nb + 1), flush=True)
                nb += 1
                continue
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, GRAD_CLIP)
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
        print("  ep %d/%d loss=%.4f DG*=%.6f CG=%.6f (frozen %.6f)"
              % (ep, res["epochs"], loss_h[-1], dg, cg, frozen_dg), flush=True)
        if device == "cuda":
            torch.cuda.empty_cache()

    # keep the last epoch whose measurement is finite; report the truncation instead of losing the run
    finite_until = len(dg_h)
    while finite_until and not (math.isfinite(dg_h[finite_until - 1]) and math.isfinite(cg_h[finite_until - 1])):
        finite_until -= 1
    truncated = finite_until != len(dg_h)
    if finite_until == 0:
        raise SystemExit("every epoch measured non-finite; nothing to report")
    dg_h, cg_h, loss_h = dg_h[:finite_until], cg_h[:finite_until], loss_h[:finite_until]

    delta = (dg_h[-1] - frozen_dg) / frozen_dg * 100.0

    rec = {
        "meta": {
            "script": SCRIPT_REL,
            "mode": "smoke" if a.smoke else "apply",
            "model": a.model,
            "model_repo": cfg["hf_repo"],
            "model_family": cfg["family"],
            "model_class": cfg["model_class"],
            "model_source": str(Path(src).relative_to(REPO)).replace("\\", "/")
            if str(src).startswith(str(REPO)) else str(src),
            "revision": resolve_revision(a.model, src),
            "protocol": res["protocol"],
            "protocol_note": res["note"],
            "nonfinite_steps_skipped": nonfinite_steps,
            "epochs_reported": len(dg_h),
            "epochs_requested": res["epochs"],
            "final_epoch_truncated": bool(truncated),
            "objective": a.objective,
            "arm": a.arm,
            "seed": a.seed,
            "epochs": res["epochs"],
            "num_samples": len(pairs),
            "batch": res["batch"],
            "batch_origin": res["batch_origin"],
            "lr": a.lr,
            "precision": "bf16" if a.bf16 else "4-bit nf4",
            "max_image_tokens": res["image_tokens"],
            "image_tokens_realised": realised,
            "image_token_budget_applied_via": budget_via,
            "image_token_id": image_token_id,
            "backbone_path": ".".join(list(cfg["backbone_attr"])),
            "lm_head_called": False,
            "dataset": "data/marine_captions (536 image-caption pairs; first --num-samples used)",
            "lora": {"r": RANK, "alpha": ALPHA, "dropout": DROPOUT},
            "lora_targets": len(targets),
            "n_trainable": n_tr,
            "n_vision_adapters": by_tower["vision"],
            "n_language_adapters": n_lang,
            "n_projector_adapters": by_tower["projector"],
            "gradient_checkpointing": True,
            "measurement": {
                "I": "mean pool of final hidden state over image-token positions",
                "T": "mean pool over caption positions (after last image token, before <|im_end|>)",
                "normalisation": "L2 per side, no projection",
                "DG*": "mean_i ||I_i - T_i||^2",
                "scope": "whole evaluation set, measured once before training and once per epoch",
            },
            "elapsed_sec": round(time.time() - t0, 1),
            "versions": {
                "torch": torch.__version__,
                "cuda": torch.version.cuda,
                "transformers": __import__("transformers").__version__,
                "peft": __import__("peft").__version__,
                "python": sys.version.split()[0],
            },
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "device": (torch.cuda.get_device_name(0) if device == "cuda" else "cpu"),
        },
        "frozen_dg_star": frozen_dg,
        "frozen_cg": frozen_cg,
        "dg_star": dg_h,
        "cg": cg_h,
        "loss": loss_h,
        "delta_DG_percent": delta,
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

    if not math.isfinite(delta):
        raise SystemExit("delta_DG_percent is not finite (%r); refusing to write a result" % delta)
    if not math.isfinite(frozen_dg) or frozen_dg <= 0:
        raise SystemExit("frozen_dg_star is not a positive finite number (%r)" % frozen_dg)
    if len(dg_h) != len(loss_h) or not dg_h:
        raise SystemExit("per-epoch history is empty or inconsistent (dg=%d loss=%d)" % (len(dg_h), len(loss_h)))
    if not all(math.isfinite(v) for v in dg_h + cg_h + loss_h):
        raise SystemExit("per-epoch history contains a non-finite value: dg=%r loss=%r" % (dg_h, loss_h))
    if n_tr <= 0 or n_lang <= 0:
        raise SystemExit("adapter counts are not positive (trainable %d, language %d)" % (n_tr, n_lang))
    if a.arm == "both" and n_vis <= 0:
        raise SystemExit("arm both has no vision-side adapters")

    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / ("decoder_attribution_%s_%s_seed%d.json" % (a.model, a.objective, a.seed))
    other = "generative" if a.objective == "contrastive" else "contrastive"
    rec["meta"]["frozen_signature"] = frozen_signature(rec)
    # write first: a sibling mismatch must never destroy a completed GPU run, it is reported instead
    io.open(p, "w", encoding="utf-8", newline="").write(json.dumps(rec, ensure_ascii=False, indent=1))
    try:
        rec["meta"]["ab_check"] = sibling_check(rec, p, other)
    except SystemExit as exc:
        rec["meta"]["ab_check"] = {"verdict": "MISMATCH (recorded, not fatal)", "problems": str(exc)}
        io.open(p, "w", encoding="utf-8", newline="").write(json.dumps(rec, ensure_ascii=False, indent=1))
        print("WARNING: A/B check reported a mismatch for %s seed %d:\n%s" % (a.model, a.seed, exc), flush=True)
        print("AB_MISMATCH", flush=True)
    else:
        io.open(p, "w", encoding="utf-8", newline="").write(json.dumps(rec, ensure_ascii=False, indent=1))
    print("wrote %s" % p.relative_to(REPO), flush=True)
    print("frozen DG*=%.6f -> %.6f | delta_DG%% = %+.2f | %s"
          % (frozen_dg, dg_h[-1], delta, rec["meta"]["ab_check"].get("verdict", "")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())