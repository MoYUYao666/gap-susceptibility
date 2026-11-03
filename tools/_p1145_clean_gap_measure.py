# -*- coding: utf-8 -*-
r"""Re-measure the LLaVA adapters under a clean, explicitly stated gap definition.

Why a second measurement. The numbers produced by the sweep's own measurement use the *prompt* as the text side
(`make_batch(..., with_labels=False)` builds "USER: <image> Describe this image in detail. ASSISTANT: " with no
caption), so they are not the image-caption gap the rest of the paper uses. Separately, the supplement's
Qwen2-VL-2B table was produced by `tools/_p47_qwen_train.py`, whose text side pools over **all non-padding
positions** -- on a Qwen2-VL sequence that is ~196 image tokens plus ~15 caption tokens -- and then applies two
*different* fixed random projections (`proj_i`, `proj_t`, seed 0). Those are two more conventions again.

This script measures the cleanest available definition, so the LLaVA statement in the paper rests on something
unambiguous:

    I = mean pool of the final hidden state over the image-token positions
    T = mean pool of the final hidden state over the caption-token positions (the supervised span, labels != -100)
    both L2-normalised, no projection
    DG*  = mean_i ||I_i - T_i||^2      CG = ||mean I - mean T||      DG_emp = sqrt(CG^2 + ||sd_I - sd_T||^2)

It also recomputes the prompt-based variant on the same batches, so the size of the convention effect is measured
rather than asserted.

Only forward passes: the nine adapters are loaded into a freshly built base model, so no retraining is needed.

    python _p1145_clean_gap_measure.py --out /root/p3/outputs/canonical_caption_metric.json
"""
from __future__ import annotations

import argparse
import glob
import json
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoProcessor, LlavaForConditionalGeneration

MODEL = "/root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf/snapshots/main"
COCO = Path("/root/p3/coco_eval")
ADAPT = Path("/root/p3/outputs/llava_canonical")
IMG_ID_DEFAULT = 32000
IMG_ID = IMG_ID_DEFAULT
RANK, ALPHA = 8, 16.0


def tower_of(name: str) -> str:
    if "vision_tower" in name or "vision_model" in name:
        return "vision"
    if "multi_modal_projector" in name:
        return "projector"
    if "language_model" in name:
        return "text"
    return "other"


def targets_for(arm, vis, txt, proj):
    if arm == "text_only":
        return txt
    if arm == "vision_only":
        return vis + proj
    return txt + vis + proj


def canonical(I, T):
    dg_star = float(((I - T) ** 2).sum(dim=-1).mean())
    cg = float((I.mean(0) - T.mean(0)).norm())
    var_term = float((I.std(dim=0) - T.std(dim=0)).norm() ** 2)
    dg_emp = (cg ** 2 + var_term) ** 0.5
    return dg_star, cg, dg_emp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/root/p3/outputs/canonical_caption_metric.json")
    ap.add_argument("--pairs", type=int, default=500)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--max-len", type=int, default=2048)
    a = ap.parse_args()

    ann = json.loads((COCO / "annotations" / "captions_val2014.json").read_text(encoding="utf-8"))
    by_img = {}
    for c in ann["annotations"]:
        by_img.setdefault(c["image_id"], []).append(c["caption"])
    ids = [i for i in by_img if (COCO / "val2014" / f"COCO_val2014_{i:012d}.jpg").exists()]
    # the sweep trained on the first 1500 and evaluated on the next 500; reuse that held-out slice
    held = ids[1500:1500 + a.pairs]
    print(f"  held-out pairs: {len(held)}", flush=True)

    proc = AutoProcessor.from_pretrained(MODEL)
    proc.tokenizer.padding_side = "right"

    def build_batch(batch_ids, with_caption):
        ims = [Image.open(COCO / "val2014" / f"COCO_val2014_{i:012d}.jpg").convert("RGB") for i in batch_ids]
        pre = "USER: <image>\nDescribe this image in detail.\nASSISTANT: "
        texts = [pre + (by_img[i][0] if with_caption else "") for i in batch_ids]
        out = proc(images=ims, text=texts, return_tensors="pt", padding=True,
                   truncation=True, max_length=a.max_len)
        if out["pixel_values"].dtype == torch.uint8:
            out["pixel_values"] = out["pixel_values"].to(torch.float32) / 255.0
        out["pixel_values"] = out["pixel_values"].to(torch.bfloat16)
        return out

    def caption_span(input_ids, attention_mask):
        """The supervised span: everything after the last image token, and not padding."""
        labels = input_ids.clone()
        for b in range(labels.shape[0]):
            pos = (input_ids[b] == IMG_ID).nonzero(as_tuple=True)[0]
            cut = int(pos[-1]) + 1 if len(pos) else 0
            labels[b, :cut] = -100
            labels[b, attention_mask[b] == 0] = -100
        return labels != -100

    def measure(model, tag):
        model.eval()
        acc = {"clean": [], "prompt": []}
        n_cap_tok, n_img_tok = [], []
        t0 = time.time()
        for s in range(0, len(held), a.batch):
            chunk = held[s:s + a.batch]
            # --- clean: text side = caption positions; also record the prompt-based variant on the same logits
            inp = build_batch(chunk, with_caption=True)
            inp = {k: (v.to(0) if hasattr(v, "to") else v) for k, v in inp.items()}
            cap = caption_span(inp["input_ids"], inp["attention_mask"])
            gpu = {k: v for k, v in inp.items() if k in ("input_ids", "attention_mask", "pixel_values")}
            cap_dev = cap.to(0)
            n_cap_tok.extend(cap.sum(1).tolist())
            n_img_tok.extend((inp["input_ids"] == IMG_ID).sum(1).tolist())
            hid = _run_with_hidden(model, gpu)
            img_m = (inp["input_ids"] == IMG_ID)
            I = _pool(hid, img_m)
            T_clean = _pool(hid, cap_dev)
            T_prompt = _pool(hid, (inp["attention_mask"].bool() & ~img_m).to(0))
            del hid
            acc["clean"].append(canonical(*_norm2(I, T_clean)))
            acc["prompt"].append(canonical(*_norm2(I, T_prompt)))
            torch.cuda.empty_cache()
        rec = {}
        for k, rows in acc.items():
            dg = [r[0] for r in rows]
            rec[k] = {"dg_star": sum(dg) / len(dg), "cg": sum(r[1] for r in rows) / len(rows),
                      "dg_emp": sum(r[2] for r in rows) / len(rows),
                      "dg_min": min(dg), "dg_max": max(dg), "n_batches": len(rows)}
        rec["n_caption_tokens_mean"] = sum(n_cap_tok) / len(n_cap_tok)
        rec["n_image_tokens_mean"] = sum(n_img_tok) / len(n_img_tok)
        rec["seconds"] = round(time.time() - t0, 1)
        rec["tag"] = tag
        print(f"  {tag:<22} clean DG* {rec['clean']['dg_star']:.4f} | prompt DG* {rec['prompt']['dg_star']:.4f} "
              f"| cap tok {rec['n_caption_tokens_mean']:.0f} img tok {rec['n_image_tokens_mean']:.0f} "
              f"| {rec['seconds']:.0f}s", flush=True)
        return rec

    def _pool(hid, mask):
        m = mask.unsqueeze(-1).to(hid.dtype)
        return (hid * m).sum(1) / m.sum(1).clamp(min=1)

    def _norm2(I, T):
        return F.normalize(I.float(), p=2, dim=-1), F.normalize(T.float(), p=2, dim=-1)

    def _run_with_hidden(model, gpu):
        """Capture the last hidden state via the lm_head input, as in the sweep's corrected measurement."""
        base = model
        while hasattr(base, "get_base_model"):
            nxt = base.get_base_model()
            if nxt is base:
                break
            base = nxt
        cap = {}

        def grab(_m, inputs):
            cap["h"] = inputs[0]

        handle = base.lm_head.register_forward_pre_hook(grab)
        try:
            with torch.no_grad():
                model(**gpu)
        finally:
            handle.remove()
        if "h" not in cap:
            raise RuntimeError("lm_head hook did not fire")
        return cap["h"].detach()

    # --- frozen reference, then each adapter
    def fresh(with_adapters=None):
        m = LlavaForConditionalGeneration.from_pretrained(
            MODEL, torch_dtype=torch.bfloat16, device_map={"": 0}, low_cpu_mem_usage=True)
        m.config.use_cache = False
        if with_adapters is None:
            for p in m.parameters():
                p.requires_grad_(False)
            return m
        from peft import LoraConfig, get_peft_model
        vis = [n for n, mod in m.named_modules() if isinstance(mod, torch.nn.Linear) and tower_of(n) == "vision"]
        txt = [n for n, mod in m.named_modules() if isinstance(mod, torch.nn.Linear) and tower_of(n) == "text"]
        proj = [n for n, mod in m.named_modules() if isinstance(mod, torch.nn.Linear) and tower_of(n) == "projector"]
        # `with_adapters` is a FILE name (e.g. text_only_s123_ckpt.pt); the arm is its prefix. Passing the file
        # name straight to targets_for() made text_only build vision adapters too, so its own checkpoint could not
        # bind and the run aborted with 292 unbound vision LoRA weights.
        arm = with_adapters.split("_s")[0]
        cfg = LoraConfig(r=RANK, lora_alpha=ALPHA, lora_dropout=0.0, bias="none",
                         task_type="CAUSAL_LM", target_modules=targets_for(arm, vis, txt, proj))
        pm = get_peft_model(m, cfg)
        ck = ADAPT / with_adapters
        payload = torch.load(ck, map_location="cpu")
        sd = payload["model"] if isinstance(payload, dict) and "model" in payload else payload
        missing, unexpected = pm.load_state_dict(sd, strict=False)
        lo = [k for k in missing if "lora" in k]
        print(f"  {with_adapters}: {len(sd)} tensors loaded | missing {len(missing)} (lora {len(lo)}) "
              f"| unexpected {len(unexpected)}", flush=True)
        if lo:
            raise RuntimeError(f"{with_adapters}: {len(lo)} LoRA weights did not bind, e.g. {lo[:3]}")
        return pm

    results = {}
    print("\n=== frozen reference ===", flush=True)
    m = fresh()
    results["frozen"] = measure(m, "frozen")
    del m
    torch.cuda.empty_cache()

    for ck in sorted(glob.glob(str(ADAPT / "*_ckpt.pt"))):
        name = Path(ck).name
        print(f"\n=== {name} ===", flush=True)
        m = fresh(name)
        results[name.replace("_ckpt.pt", "")] = measure(m, name.replace("_ckpt.pt", ""))
        del m
        torch.cuda.empty_cache()

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"definition": {
        "I": "mean pool of final hidden state over image-token positions",
        "T": "mean pool of final hidden state over caption-token positions (labels != -100)",
        "normalisation": "L2 per side, no projection",
        "DG*": "mean_i ||I_i - T_i||^2", "CG": "||mean I - mean T||",
        "DG_emp": "sqrt(CG^2 + ||sd_I - sd_T||^2)",
        "held_out": "COCO val2014 ids[1500:2000], the sweep's held-out slice",
        "adapters": "outputs/llava_canonical/*_ckpt.pt (the 2026-10-17 canonical retrain)",
    }, "runs": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n  wrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
