# -*- coding: utf-8 -*-
r"""Qwen2.5-VL runner.Adaptation-site comparison on a modern decoder VLM, with the two towers properly separated.

What the draft got wrong: it passed one target_modules list to both adaptation sites, so the text
and vision arms adapted the same weights and no isolation existed. The supplement states the correct
approach for Qwen2-VL ("the two towers are separated by the fact that their linear layers carry
different names"), and this script applies it to LLaVA-1.5-7B and verifies the separation before any
training happens, exactly as the supplement does for its model.

Isolation for LLaVA-1.5-7B:
  vision tower  = vision_model.encoder.layers.*.{self_attn.q_proj,k_proj,v_proj,out_proj, mlp.fc1,fc2}
  language model = language_model.model.layers.*.{self_attn.q_proj,k_proj,v_proj,o_proj,
                                                   mlp.gate_proj,up_proj,down_proj}
  projector      = multi_modal_projector.linear_1, linear_2

The arms are frozen, text_only, vision_only and both. Verification counts the adapter tensors on each
side and refuses to train if a text-only run holds any vision tensor or vice versa.

Precision: the model loads in 4-bit because 7B in bfloat16 exceeds the 8.6 GB device. The supplement
records that 4-bit made its gap measurement unreproducible, so every result carries that caveat and
the runs are repeated across seeds so the within-condition spread is visible next to any effect.

Reported per arm: the distribution gap and centroid gap over the multimodal memory, and the relative
change in DG (the supplement's own convention, since arms start from different values).

    python tools/_p820_llava_sites.py --verify-only
    python tools/_p820_llava_sites.py --pilot
    python tools/_p820_llava_sites.py --samples 400 --epochs 3 --batch 2 --seeds 3 --apply
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "outputs" / "qwen_sites"
OUT = REPO / "outputs" / "analysis" / "llava_sites.json"
MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"
SEED_POOL = [42, 123, 456]

VISION_TARGETS = ["q_proj", "k_proj", "v_proj", "out_proj", "fc1", "fc2"]
TEXT_TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
PROJ_TARGETS = ["linear_1", "linear_2"]


def tower_of(name: str) -> str:
    """Three-way split. The real prefixes are model.vision_tower, model.language_model and
    model.multi_modal_projector (tools/_p823_name_probe.py), and the leaf names q_proj/k_proj/v_proj
    are shared between the towers, so only the qualified path identifies a tower."""
    if "vision_tower" in name or "vision_model" in name:
        return "vision"
    if "multi_modal_projector" in name:
        return "projector"
    if "language_model" in name:
        return "text"
    # Qwen2.5-VL: the projector is nested inside the vision prefix, so it is tested first.
    if "visual.merger" in name or "multi_modal_projector" in name:
        return "projector"
    if "visual." in name:
        return "vision"
    return "other"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=400)
    ap.add_argument("--eval-pairs", type=int, default=500)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--max-len", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--alpha", type=float, default=16.0)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--arms", type=str, default="frozen,text_only,vision_only,both")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report-every", type=int, default=10,
                    help="print a step heartbeat every N optimisation steps")
    ap.add_argument("--resume", action="store_true",
                    help="continue an interrupted run from its epoch checkpoint")
    ap.add_argument("--bench-steps", type=int, default=0,
                    help="stop training after this many steps (timing runs only)")
    ap.add_argument("--out-dir", type=str, default="",
                    help="write records here instead of outputs/llava_sites (timing runs)")
    ap.add_argument("--no-grad-ckpt", action="store_true",
                    help="disable gradient checkpointing (default on: it saves memory, costs time)")
    ap.add_argument("--tf32", action="store_true",
                    help="allow TF32 for fp32 matmuls (default off, as the script has always run)")
    ap.add_argument("--eval-batch", type=int, default=0,
                    help="pairs per forward in the held-out measurement (0 = same as --batch)")
    ap.add_argument("--alloc-warmup-gb", type=float, default=0.0,
                    help="cap the model-loading allocator reservation in GB (0 = transformers default)")
    ap.add_argument("--precision", choices=["4bit", "bf16"], default="4bit",
                    help="4bit matches the published configuration; bf16 needs about 16 GB")
    ap.add_argument("--deterministic", action="store_true",
                    help="force deterministic convolution selection (4.4x slower; parity runs)")
    ap.add_argument("--coco-root", type=str, default="",
                    help="directory holding annotations/captions_val2014.json and val2014/")
    a = ap.parse_args()
    if a.out_dir:
        global OUT_DIR
        OUT_DIR = Path(a.out_dir)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
    if a.pilot:
        a.samples, a.eval_pairs, a.epochs, a.batch, a.arms, a.seeds = 8, 40, 1, 1, "frozen,text_only", 1

    import torch
    from PIL import Image
    from transformers import (AutoProcessor, BitsAndBytesConfig,
                          Qwen2_5_VLForConditionalGeneration)

    if not torch.cuda.is_available():
        print("  no CUDA device")
        return 1
    free = (torch.cuda.get_device_properties(0).total_memory
            - torch.cuda.memory_reserved(0)) / 1e9
    print(f"  GPU {torch.cuda.get_device_properties(0).name}, {free:.1f} GB free")
    if free < 4.5:
        print("  !! less than 4.5 GB free; wait for the other run to finish")
        return 1

    if a.alloc_warmup_gb:
        # transformers reserves a buffer the size of the model before loading it (caching_allocator_warmup).
        # On a device where the weights nearly fill the memory that reservation cannot be satisfied, and the
        # load fails with CUDA out of memory even though the model itself would fit. Wrapping the function
        # and shrinking the reported device size keeps transformers' own capping arithmetic in charge.
        import transformers.modeling_utils as _mu
        _orig_warmup = _mu.caching_allocator_warmup

        def _capped_warmup(model, expanded_device_map, hf_quantizer):
            class _Small:
                type = "cuda"
                index = 0

                def __init__(self, size):
                    self._size = size

                @property
                def total_memory(self):
                    return self._size

            import torch as _t
            real = _t.cuda.get_device_properties(0).total_memory
            small = int(a.alloc_warmup_gb * 1024 ** 3)
            props = _Small(small)

            class _Props:
                @staticmethod
                def get_device_properties(_i):
                    return props
            real_get = _t.cuda.get_device_properties
            _t.cuda.get_device_properties = _Props.get_device_properties
            try:
                print(f"  allocator warmup capped: reporting {small / 1e9:.1f} GB instead of "
                      f"{real / 1e9:.1f} GB")
                return _orig_warmup(model, expanded_device_map, hf_quantizer)
            finally:
                _t.cuda.get_device_properties = real_get

        _mu.caching_allocator_warmup = _capped_warmup
    print(f"  loading {MODEL} ...")
    # 4-bit is only needed where the device cannot hold the weights; bf16 keeps the model in
    # its native precision, which removes the dequantisation rounding entirely.
    quant = None
    if a.precision == "4bit":
        quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                   bnb_4bit_compute_dtype=torch.bfloat16,
                                   bnb_4bit_use_double_quant=True)
    pixel_dtype = torch.float16 if a.precision == "4bit" else torch.bfloat16
    print(f"  precision: {a.precision}")
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL, quantization_config=quant if quant else None, torch_dtype=torch.bfloat16, device_map={"": 0},
        low_cpu_mem_usage=True)
    proc = AutoProcessor.from_pretrained(MODEL)
    proc.tokenizer.padding_side = "right"
    print(f"  loaded: {sum(p.numel() for p in model.parameters()):,} parameters (4-bit)")

    # ---- data: real COCO val pairs ----
    coco_root = Path(a.coco_root) if a.coco_root else (REPO / "coco")
    ann = json.loads((coco_root / "annotations" / "captions_val2014.json").read_text(
        encoding="utf-8", errors="ignore"))
    by_img = {}
    for c in ann["annotations"]:
        by_img.setdefault(c["image_id"], []).append(c["caption"])
    img_dir = coco_root / "val2014"
    ids = [i for i in by_img if (img_dir / f"COCO_val2014_{i:012d}.jpg").exists()]
    train_ids, eval_ids = ids[:a.samples], ids[a.samples:a.samples + a.eval_pairs]
    print(f"  {len(train_ids)} training pairs and {len(eval_ids)} held-out evaluation pairs")

    def make_batch(batch_ids, captions=None, with_labels=False):
        ims = [Image.open(img_dir / f"COCO_val2014_{i:012d}.jpg").convert("RGB") for i in batch_ids]
        _instr = "Describe this image in detail."
        pre = proc.apply_chat_template(
            [{"role": "user", "content": [{"type": "image"},
                                          {"type": "text", "text": _instr}]}],
            tokenize=False, add_generation_prompt=True)
        prompts = [pre + ((captions[k] if captions else by_img[i][0]) if with_labels else "")
                   for k, i in enumerate(batch_ids)]
        out = proc(images=ims, text=prompts, return_tensors="pt", padding=True,
                   truncation=True, max_length=a.max_len)
        # The processor returns uint8 pixels; the vision tower needs a float tensor, so the
        # conversion happens here to cover both the training and the measurement path.
        if out["pixel_values"].dtype == torch.uint8:
            out["pixel_values"] = out["pixel_values"].to(torch.float32) / 255.0
        out["pixel_values"] = out["pixel_values"].to(pixel_dtype)
        if with_labels:
            # The loss needs labels. They cannot be supplied to the processor alongside the images,
            # because the processor would then append the caption a second time, so the supervision
            # span is taken from the already-expanded sequence instead: everything up to and including
            # the last image token is prompt, the rest is the caption. Counting text tokens instead
            # does not work, because a single <image> placeholder expands to 577 tokens in the
            # processed sequence (the tokeniser reports 596 for the prompt while the caption alone is
            # 14, a discrepancy of one end-of-sequence token).
            labels = out["input_ids"].clone()
            # Qwen2.5-VL exposes `image_token_id`; there is no `image_token_index`, and the old
            # default of 32000 exists nowhere in Qwen vocabulary, which would make the mask a no-op.
            img_id = int(getattr(model.config, "image_token_id", None)
                         or getattr(model.config, "image_token_index", 151655))
            for b in range(labels.shape[0]):
                row = out["input_ids"][b]
                img_pos = (row == img_id).nonzero(as_tuple=True)[0]
                cut = int(img_pos[-1]) + 1 if len(img_pos) else 0
                labels[b, :cut] = -100
                labels[b, out["attention_mask"][b] == 0] = -100
            out["labels"] = labels
        return out

    # ---- tower separation, verified before training ----
    print()
    print("=" * 100)
    print("tower separation check (before any training)")
    print("=" * 100)
    counts = {}
    for n, _ in model.named_parameters():
        counts[tower_of(n)] = counts.get(tower_of(n), 0) + 1
    print(f"  backbone parameter tensors by tower: {counts}")
    if counts.get("vision", 0) == 0 or counts.get("text", 0) == 0:
        print("  !! the tower split did not find both towers; the names must be inspected")
        return 1

    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    # The adaptation sites are addressed by fully qualified module name. PEFT matches a list entry
    # with key.endswith("." + entry), so exact names cannot leak across towers, whereas the leaf
    # names q_proj/k_proj/v_proj exist on both sides and a regex attempt was rejected outright.
    def names_for(kind):
        out = []
        for n, m in model.named_modules():
            if not isinstance(m, torch.nn.Linear):
                continue
            t = tower_of(n)
            if kind == "vision" and t == "vision":
                out.append(n)
            elif kind == "text" and t == "text":
                out.append(n)
            elif kind == "projector" and t == "projector":
                out.append(n)
        return sorted(out)

    VIS_NAMES = names_for("vision")
    TXT_NAMES = names_for("text")
    PROJ_NAMES = names_for("projector")
    print(f"  vision-side layers {len(VIS_NAMES)}   text-side {len(TXT_NAMES)}   "
          f"projector {len(PROJ_NAMES)}")
    print(f"  e.g. vision {VIS_NAMES[0]}")
    print(f"       text   {TXT_NAMES[0]}")

    def targets_for(arm):
        if arm == "text_only":
            return TXT_NAMES
        if arm == "vision_only":
            return VIS_NAMES + PROJ_NAMES
        return TXT_NAMES + VIS_NAMES + PROJ_NAMES

    def fresh_base():
        """A new 4-bit base model for each arm.

        Reusing one instance is what made the first isolation attempt fail: the adapter library keeps
        the previous arm's adapters on the shared backbone, so vision_only ended up holding exactly
        the text adapter count (19,988,480 parameters in 448 tensors) as well as its own.
        """
        m = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            MODEL, quantization_config=quant if quant else None, torch_dtype=torch.bfloat16, device_map={"": 0},
            low_cpu_mem_usage=True)
        # For 4-bit the k-bit helper is required: it upcasts parameters to fp32, which a
        # quantised model needs. For bf16 the same call is fatal -- measured 2026-10-15, it took
        # the 15 GB model to 30 GB and the run died with CUDA out of memory before any activation.
        # The bf16 branch below does the parts that matter for training and skips the upcast.
        if a.precision == "4bit":
            return prepare_model_for_kbit_training(m, use_gradient_checkpointing=True)
        if not getattr(a, "no_grad_ckpt", False):
            m.gradient_checkpointing_enable()
        else:
            print("  gradient checkpointing DISABLED for this run")
            m.gradient_checkpointing_disable()
        try:
            m.config.use_cache = False
        except Exception:
            pass
        inner = getattr(m, "model", m)
        for _name, _mod in (("language_model", getattr(inner, "language_model", None)),
                            ("vision_tower", getattr(inner, "vision_tower", None))):
            if _mod is not None:
                try:
                    _mod.enable_input_require_grads()
                except Exception:
                    pass
        return m

    def build(arm):
        m = fresh_base()
        if arm == "frozen":
            for p in m.parameters():
                p.requires_grad_(False)
            return m
        cfg = LoraConfig(r=a.rank, lora_alpha=a.alpha, lora_dropout=0.0, bias="none",
                         task_type="CAUSAL_LM", target_modules=targets_for(arm))
        return get_peft_model(m, cfg)

    verified = {}
    for arm in [x for x in a.arms.split(",") if x]:
        mm = build(arm)
        trainable = [(n, p.numel()) for n, p in mm.named_parameters() if p.requires_grad]
        by_tower = {}
        for n, num in trainable:
            t = tower_of(n)
            by_tower[t] = by_tower.get(t, 0) + num
        verified[arm] = {"n_trainable": sum(num for _, num in trainable),
                         "by_tower": by_tower, "n_tensors": len(trainable)}
        print(f"  {arm:<12} trainable {sum(num for _, num in trainable):>12,}  "
              f"tensors {len(trainable):>4}  by tower {by_tower}")
        del mm
        torch.cuda.empty_cache()

    ok = True
    for arm, side, bad in (("text_only", "text", "vision"),
                           ("vision_only", "vision", "text")):
        if arm in verified:
            if verified[arm]["by_tower"].get(side, 0) == 0:
                print(f"  FAIL {arm} holds no {side}-side parameters")
                ok = False
            if verified[arm]["by_tower"].get(bad, 0) > 0:
                print(f"  FAIL {arm} also holds {bad}-side parameters")
                ok = False
    print()
    print(f"  ISOLATION: {'VERIFIED' if ok else 'NOT ACHIEVED'}")
    if not ok:
        return 1
    if a.verify_only:
        return 0

    # ---- training and measurement ----
    # The gap is measured in the shared input-embedding space, from the projected vision features on
    # one side and the language model's text embeddings on the other, with the definitions verified
    # in tools/_p821_gap_defs.py:
    #   centroid gap      ||mean(A) - mean(B)|| over L2-normalised embeddings
    #   distribution gap  mean cross-set distance minus the mean within-set distance
    # Measuring inside the transformer memory instead would hide the vision side: image tokens enter
    # through the projector, so their hidden states at the last layer are produced by the language
    # model, and a vision-only adapter would leave every such tensor in the vision path untouched.
    def _gap_metrics(A, B):
        import torch.nn.functional as F
        A = F.normalize(A.float(), p=2, dim=-1)
        B = F.normalize(B.float(), p=2, dim=-1)
        cg = float((A.mean(0) - B.mean(0)).norm())
        dg = float(torch.cdist(A, B).mean() - 0.5 * (torch.cdist(A, A).mean()
                                                     + torch.cdist(B, B).mean()))
        return cg, dg

    def _sides(mm, batch_ids):
        """Projected vision features and text token embeddings for a batch of real pairs.

        The inner module prefix is `model.` in this version of transformers
        (tools/_p823_name_probe.py recorded model.vision_tower, model.language_model,
        model.multi_modal_projector), so both the full model and the adapter-wrapped one are handled
        by looking the modules up once.
        """
        inp = make_batch(batch_ids, with_labels=False)
        inp = {k: (v.to(0) if hasattr(v, "to") else v) for k, v in inp.items()}

        base = mm
        while hasattr(base, "get_base_model"):
            nxt = base.get_base_model()
            if nxt is base:
                break
            base = nxt
        # Qwen2.5-VL cannot be measured the LLaVA way: its tower needs the patch grid of its
        # dynamic resolution, and calling it with pixel_values alone raises
        #   Qwen2_5_VisionTransformerPretrainedModel.forward() missing 1 required positional
        #   argument: 'grid_thw'
        # The processor does return that grid (`image_grid_thw`, recorded by tools/_p1039), and a
        # hook on `visual.merger` captures the projected vision features: a plain tensor, measured
        # (587, 3584) for two COCO images. Both sides therefore come from one full forward pass.
        inner = getattr(base, "model", base)
        merger = getattr(getattr(inner, "visual", None), "merger", None)
        lm = getattr(inner, "language_model", None)
        if merger is None or lm is None:
            raise RuntimeError(f"could not locate the submodules on {type(inner).__name__}")
        # Both sides are captured with hooks so that no per-layer activations are kept: the first
        # attempt used output_hidden_states=True, which holds a tensor for all 29 layers and ran
        # the device out of memory (31.46 GiB in use, 5.69 MiB free). The text side is the token
        # embedding, which a hook on the embedding module gives for the price of one tensor.
        _cap = {}

        def _hook_merger(_mod, _inp, outp):
            _cap["v"] = outp

        def _hook_embed(_mod, _inp, outp):
            _cap["t"] = outp

        _hm = merger.register_forward_hook(_hook_merger)
        _he = lm.get_input_embeddings().register_forward_hook(_hook_embed)
        try:
            with torch.no_grad():
                mm(**inp)
        finally:
            _hm.remove()
            _he.remove()
        V = _cap["v"]
        if isinstance(V, tuple):
            V = V[0]
        ids = inp["input_ids"]
        img_id = int(getattr(base.config, "image_token_id", None)
                     or getattr(base.config, "image_token_index", 151655))
        mask = inp["attention_mask"].bool() & (ids != img_id)
        T = _cap["t"][mask]
        return V.reshape(-1, V.shape[-1]), T

        with torch.no_grad():
            pv = inp["pixel_values"]
            # The vision tower's own dtype is not what the projector wants: after 4-bit quantisation
            # projector.linear_1.weight.dtype reports torch.uint8 because bitsandbytes stores the
            # packed weights that way, and casting the features to that dtype is what produced
            # "GeluCUDAKernelImpl not implemented for 'Byte'". The projector therefore gets an
            # explicit float dtype instead.
            feats = vision(pv.to(torch.bfloat16), output_hidden_states=False)
            f = feats.last_hidden_state if hasattr(feats, "last_hidden_state") else feats[0]
            V = projector(f.to(torch.bfloat16))
        ids = inp["input_ids"]
        img_id = int(getattr(base.config, "image_token_index", 32000))
        mask = inp["attention_mask"].bool() & (ids != img_id)
        emb = lm.get_input_embeddings()
        T = emb(ids)[mask]
        return V.reshape(-1, V.shape[-1]), T

    def measure(mm, batch_ids):
        cgs, dgs, n = [], [], 0
        was_training = mm.training
        mm.eval()
        with torch.no_grad():
            eb = a.eval_batch or a.batch
            for s in range(0, len(batch_ids), eb):
                chunk = batch_ids[s:s + eb]
                try:
                    V, T = _sides(mm, chunk)
                except Exception as exc:                     # keep the failure visible
                    import traceback
                    print(f"  measurement failed on batch at {s}: {type(exc).__name__}: {exc}")
                    print("  --- traceback ---")
                    for line in traceback.format_exc().splitlines()[-14:]:
                        print(f"  {line}")
                    raise
                if V.numel() == 0 or T.numel() == 0:
                    continue
                cg, dg = _gap_metrics(V, T)
                cgs.append(cg)
                dgs.append(dg)
                n += len(chunk)
        if was_training:
            mm.train()
        return (st.mean(cgs) if cgs else None, st.mean(dgs) if dgs else None, n)

    results = {"model": MODEL, "quantisation": "4-bit nf4",
               "caveat": ("4-bit is required to fit the 8.6 GB device; the supplement records that "
                          "4-bit made its gap measurement unreproducible, so these numbers carry "
                          "that limitation and the seed spread is reported alongside"),
               "isolation_verified": verified, "runs": []}

    for arm in [x for x in a.arms.split(",") if x]:
        for seed in SEED_POOL[:a.seeds]:
            name = f"{arm}_s{seed}"
            agg = OUT_DIR / f"{name}.json"
            if a.apply and agg.exists():
                # A finished run is one whose record carries a measured value AND was produced with
                # the settings now in force. Testing for R@1 alone was wrong on both counts: the
                # frozen arms have no R@1, so they were re-run every time, and a record left by an
                # earlier attempt at a different scale would be accepted and corrupt the aggregate.
                try:
                    prev = json.loads(agg.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    prev = {}
                measured = prev.get("dg_after") is not None
                same_scale = (prev.get("samples") == a.samples
                              and prev.get("epochs") == a.epochs
                              and prev.get("rank") == a.rank)
                if measured and same_scale:
                    print(f"  {name}: already complete, skipping")
                    results["runs"].append(prev)
                    continue
                if measured and not same_scale:
                    print(f"  {name}: discarding a record from a different scale "
                          f"(samples {prev.get('samples')} vs {a.samples}, "
                          f"epochs {prev.get('epochs')} vs {a.epochs})")
            print()
            print("=" * 100)
            print(f"{name}")
            print("=" * 100)
            import random
            random.seed(seed)
            import numpy as np
            np.random.seed(seed)
            torch.manual_seed(seed)
            # Determinism switches. Measured 2026-10-15: they pull the run-to-run spread down to
            # the 5e-3 that 4-bit kernels produce anyway, but they cost 4.4x in time (63 -> 279 s
            # per step), so they are used for the small parity runs only, never for the sweep.
            if a.deterministic:
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
                torch.backends.cuda.matmul.allow_tf32 = False
            if getattr(a, "tf32", False):
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                print("  TF32 enabled for fp32 matmuls")
            try:  # _arm_guard: one arm must not take the sweep down
                # Release the previous arm before building this one. Measured 2026-10-16: without this,
                # the second arm's load failed with 4.17 GiB free and 26.74 GiB still allocated, because
                # every build() loads a new 14 GB model and the old one stayed resident. The allocator
                # warm-up cap does not cover that case -- the failing allocation is inside the warm-up.
                try:
                    del mm
                except NameError:
                    pass  # first run: nothing to release
                try:
                    del opt
                except NameError:
                    pass
                import gc as _gc
                _gc.collect()
                torch.cuda.synchronize()
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()
                _allocated = torch.cuda.memory_allocated() / 1e9
                _reserved = torch.cuda.memory_reserved() / 1e9
                print(f"  after release: allocated {_allocated:.2f} GB, reserved {_reserved:.2f} GB",
                      flush=True)
                _free, _total = torch.cuda.mem_get_info()
                print(f"  device free before this arm: {_free / 1e9:.1f} GB of {_total / 1e9:.1f} GB",
                      flush=True)  # release_between_runs
                if _free < 16e9:
                    raise SystemExit("  not enough device memory to load the next arm; stopping rather "
                                     "than failing mid-run")
                mm = build(arm)
                before = measure(mm, eval_ids[:max(8, len(eval_ids) // 5)])
                if arm != "frozen":
                    opt = torch.optim.AdamW([p for p in mm.parameters() if p.requires_grad],
                                            lr=a.lr)
                    mm.train()
                    t0 = time.time()
                    # ---- step timing, added 2026-10-15 -------------------------------------------------
                    # The old loop printed once per epoch, so an 86-minute epoch was indistinguishable
                    # from a hang. Every step now records where its time went, and a heartbeat plus a
                    # progress file make the run observable while it is still going.
                    steps_total = a.epochs * -(-len(train_ids) // a.batch)
                    step_i = 0
                    run_t0 = time.time()
                    t_batch = t_compute = 0.0
                    t_epoch_start = run_t0
                    ep_start = 0
                    prog_path = OUT_DIR / "train_progress.json"
                    resume_path = OUT_DIR / f"{name}_ckpt.pt"
                    start_ep = 0
                    if a.resume and resume_path.exists():
                        try:
                            ck = torch.load(resume_path, map_location="cpu")
                            mm.load_state_dict(ck["model"], strict=False)
                            opt.load_state_dict(ck["opt"])
                            start_ep = int(ck["epoch"])
                            print(f"  resumed from epoch {start_ep} ({resume_path.name})")
                        except Exception as exc:
                            print(f"  resume failed ({type(exc).__name__}: {exc}); starting fresh")
                            start_ep = 0
                    for ep in range(start_ep, a.epochs):
                        if a.bench_steps and step_i >= a.bench_steps:
                            print("    bench cap already reached; not starting another epoch",
                                  flush=True)
                            break
                        order = list(train_ids)
                        random.shuffle(order)
                        tot = 0.0
                        nb = 0
                        ep_start = time.time()
                        for s in range(0, len(order), a.batch):
                            chunk = order[s:s + a.batch]
                            caps = [by_img[i][0] for i in chunk]
                            tb0 = time.time()
                            inp = make_batch(chunk, caps, with_labels=True)
                            inp = {k: (v.to(0) if hasattr(v, "to") else v) for k, v in inp.items()}
                            tb1 = time.time()
                            if step_i == 0:
                                _seq = int(inp["input_ids"].shape[1])
                                _tok = int(inp["input_ids"].numel())
                                _mean = _tok / max(1, int(inp["input_ids"].shape[0]))
                                print("    batch tokens: " + str(_tok) + " mean " + str(int(_mean))
                                      + " | sequence length in this batch: " + str(_seq), flush=True)
                            out = mm(**inp)
                            opt.zero_grad(set_to_none=True)
                            out.loss.backward()
                            opt.step()
                            tc1 = time.time()
                            t_batch += tb1 - tb0
                            t_compute += tc1 - tb1
                            tot += float(out.loss)
                            nb += 1
                            step_i += 1
                            if a.bench_steps and step_i >= a.bench_steps:
                                print("    bench stop after " + str(step_i) + " steps", flush=True)
                                break
                            if a.report_every and step_i % a.report_every == 0:
                                el = time.time() - run_t0
                                per = el / max(1, step_i)
                                eta = time.time() + per * (steps_total - step_i)
                                print(f"    step {step_i}/{steps_total}  loss {tot / nb:.4f}  "
                                      f"{per:.1f} s/step  elapsed {el / 60:.1f} min  "
                                      f"eta {time.strftime('%H:%M', time.localtime(eta))}", flush=True)
                                prog_path.write_text(
                                    json.dumps({"run": name, "step": step_i, "steps_total": steps_total,
                                                "epoch": ep + 1, "loss_running": tot / nb,
                                                "sec_per_step": round(per, 2),
                                                "elapsed_s": round(el, 1),
                                                "eta": time.strftime("%Y-%m-%d %H:%M", time.localtime(eta)),
                                                "t_batch_s": round(t_batch, 1),
                                                "t_compute_s": round(t_compute, 1)},
                                               indent=1), encoding="utf-8")
                        ep_s = time.time() - ep_start
                        print(f"  epoch {ep + 1}/{a.epochs}  loss {tot / max(1, nb):.4f}  "
                              f"[{ep_s / 60:.1f} min, {nb} steps, {ep_s / max(1, nb):.1f} s/step]",
                              flush=True)
                        try:
                            # Trainable tensors only. Saving `mm.state_dict()` wrote the whole 7 B model -- measured
                            # at 14.4 GB per epoch on a 30 GB filesystem, which filled the disk and killed a run. The
                            # checkpoint exists to resume an interrupted arm, and only the trainable tensors change.
                            _trainable = {k: v for k, v in mm.state_dict().items()
                                          if any(t is v for t in (p for p in mm.parameters() if p.requires_grad))}
                            torch.save({"model": _trainable,  # trainable state only
                                        "opt": opt.state_dict(), "epoch": ep + 1}, resume_path)
                        except Exception as exc:
                            print(f"  checkpoint not written ({type(exc).__name__}: {exc})")
                    train_s = time.time() - t0
                    print(f"  training breakdown: batch prep {t_batch:.1f} s, compute {t_compute:.1f} s")
                else:
                    train_s = 0.0
                _tm = time.time()
                after = measure(mm, eval_ids)
                print(f"  held-out measurement: {time.time() - _tm:.1f} s "
                      f"over {len(eval_ids)} pairs", flush=True)
                rec = {"name": name, "arm": arm, "seed": seed, "rank": a.rank,
                       "n_trainable": verified[arm]["n_trainable"],
                       "by_tower": verified[arm]["by_tower"],
                       "cg_before": before[0], "cg_after": after[0],
                       "dg_before": before[1], "dg_after": after[1],
                       "dg_rel_change": (None if not before[1] or before[1] == 0
                                         else (after[1] - before[1]) / before[1]),
                       "n_eval": after[2], "train_seconds": round(train_s, 1),
                       "samples": a.samples, "epochs": a.epochs, "batch": a.batch, "lr": a.lr}
                results["runs"].append(rec)
                print(f"  DG* {before[1]:.4f} -> {after[1]:.4f}  (rel {rec['dg_rel_change']:+.3%})  "
                      f"CG {before[0]:.4f} -> {after[0]:.4f}  ({train_s:.0f}s)")
                if a.apply:
                    OUT_DIR.mkdir(parents=True, exist_ok=True)
                    agg.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
                del mm
                torch.cuda.empty_cache()
            except BaseException as _arm_exc:  # noqa: BLE001 - the point is to survive anything
                import traceback as _tb
                _msg = f"{name}: {type(_arm_exc).__name__}: {_arm_exc}"
                print(f"  ARM FAILED {_msg}", flush=True)
                with open(OUT_DIR / "ARM_FAILURES.txt", "a", encoding="utf-8") as _fh:
                    _fh.write(_msg + chr(10) + _tb.format_exc() + chr(10))
                results.setdefault("failures", []).append(_msg)
                torch.cuda.empty_cache()
                continue

    print()
    print("=" * 100)
    print("summary by arm (relative change in DG*)")
    print("=" * 100)
    for arm in [x for x in a.arms.split(",") if x]:
        rs = [r for r in results["runs"] if r["arm"] == arm and r.get("dg_rel_change") is not None]
        if not rs:
            continue
        v = [r["dg_rel_change"] for r in rs]
        print(f"  {arm:<12} n={len(v)}  {st.mean(v):+.3%}"
              + (f" +/- {st.stdev(v):.3%}" if len(v) > 1 else "")
              + f"   trainable {rs[0]['n_trainable']:,}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
