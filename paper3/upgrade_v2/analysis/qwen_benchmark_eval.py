# -*- coding: utf-8 -*-
"""Qwen2-VL-2B cross-architecture evaluation on public benchmarks."""
import argparse, collections, io, json, os, re, string, sys, time
import numpy as np, pandas as pd, torch
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from benchmark_eval import flickr_rows, coco_rows, scienceqa_rows, mmbench_rows

REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
AN = os.path.join(REPO, "outputs", "analysis")
MODEL = os.path.join(REPO, "models", "Qwen2-VL-2B-Instruct")
VQA_TEST = os.path.join(REPO, "paper3", "data", "test-vqarad.parquet")
VQA_IMAGES = os.path.join(REPO, "data", "vqa_rad", "images")
POPE = os.path.join(REPO, "paper3", "data", "test-pope-random.parquet")
COCO = os.path.join(REPO, "data", "a4", "coco5k", "images_mscoco_2014_5k_test")
ADAPTERS = os.path.join(REPO, "outputs", "qwen_vqa_adapters")


def norm(s):
    s = str(s).lower().strip()
    s = re.sub(r"[%s]" % re.escape(string.punctuation), " ", s)
    return " ".join(s.split())


def f1(r, h):
    rt = collections.Counter(norm(r).split())
    ht = collections.Counter(norm(h).split())
    c = sum((rt & ht).values())
    if c == 0:
        return 0.0
    p = c / max(sum(ht.values()), 1)
    rec = c / max(sum(rt.values()), 1)
    return 2 * p * rec / max(p + rec, 1e-12)


def bleu4(refs, hyps):
    prec = []
    for n in range(1, 5):
        num = den = 0
        for r, h in zip(refs, hyps):
            rt = norm(r).split()
            ht = norm(h).split()
            rng = [tuple(rt[j:j+n]) for j in range(len(rt)-n+1)]
            for i in range(len(ht)-n+1):
                den += 1
                if tuple(ht[i:i+n]) in rng:
                    num += 1
        prec.append(num / den if den else 0.0)
    if min(prec) <= 0:
        return 0.0
    return float(np.exp(sum(np.log(p) for p in prec) / 4))


def yesno(s):
    m = re.search(r"\b(yes|no)\b", norm(s))
    return m.group(1) if m else ("yes" if norm(s).startswith("yes") else "no")


def letter(s):
    m = re.search(r"\b([abcde])\b", norm(s))
    return m.group(1) if m else ""


def open_img(src):
    if isinstance(src, dict):
        if src.get("bytes") is not None:
            return Image.open(io.BytesIO(src["bytes"])).convert("RGB")
        if src.get("path"):
            return Image.open(src["path"]).convert("RGB")
    if isinstance(src, (bytes, bytearray)):
        return Image.open(io.BytesIO(src)).convert("RGB")
    return Image.open(src).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["vqarad", "pope", "flickr", "coco", "scienceqa", "mmbench"], required=True)
    ap.add_argument("--arm", default="base")
    ap.add_argument("--n", type=int, default=100)
    args = ap.parse_args()
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    os.environ["HF_HUB_OFFLINE"] = "1"
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
    from peft import PeftModel
    q = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                           bnb_4bit_use_double_quant=True)
    proc = AutoProcessor.from_pretrained(MODEL)
    base = Qwen2VLForConditionalGeneration.from_pretrained(MODEL, quantization_config=q, device_map="auto")
    model = base
    adir = None
    if args.arm != "base":
        adir = os.path.join(ADAPTERS, "r" + str(args.arm))
        if not os.path.exists(os.path.join(adir, "adapter_config.json")):
            raise FileNotFoundError(adir)
        model = PeftModel.from_pretrained(base, adir, is_trainable=False)
    model.eval()

    if args.task == "vqarad":
        df = pd.read_parquet(VQA_TEST).head(args.n)
        rows = [(os.path.join(VQA_IMAGES, str(r["image"])), str(r["instruction"]), str(r["output"]))
                for _, r in df.iterrows()]
    elif args.task == "pope":
        df = pd.read_parquet(POPE); rows = []
        for _, r in df.iterrows():
            img = os.path.join(COCO, str(r["image_source"]) + ".jpg")
            if os.path.exists(img):
                rows.append((img, str(r["instruction"]), str(r["output"])))
            if len(rows) >= args.n:
                break
    elif args.task == "flickr":
        rows = flickr_rows(args.n)
    elif args.task == "coco":
        rows = coco_rows(args.n)
    elif args.task == "scienceqa":
        rows = scienceqa_rows(args.n)
    else:
        rows = mmbench_rows(args.n)

    refs, hyps, t0 = [], [], time.time()
    for img_src, prompt, ref in rows:
        img = open_img(img_src)
        msgs = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
        text = proc.apply_chat_template(msgs, add_generation_prompt=True)
        inp = proc(text=[text], images=[img], return_tensors="pt").to(model.device)
        with torch.inference_mode():
            out = model.generate(**inp, max_new_tokens=32, do_sample=False)
        gen = proc.tokenizer.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        refs.append(ref); hyps.append(gen)
        if len(hyps) % 10 == 0:
            print(args.task, args.arm, len(hyps), flush=True)

    source = (VQA_TEST if args.task == "vqarad" else
              (POPE if args.task == "pope" else args.task))
    out = {"meta": {"task": args.task, "arm": args.arm, "n": len(hyps), "model": MODEL,
                    "adapter": adir, "seed": 42, "source": source,
                    "protocol": "cross-architecture held-out evaluation; archived Qwen VQA-RAD adapter",
                    "elapsed_min": round((time.time() - t0) / 60, 2)},
           "refs": refs, "hypotheses": hyps}
    if args.task == "vqarad":
        out["token_f1"] = float(np.mean([f1(r, h) for r, h in zip(refs, hyps)]))
        out["exact_match"] = float(np.mean([norm(r) == norm(h) for r, h in zip(refs, hyps)]))
    elif args.task in ("scienceqa", "mmbench"):
        out["pred"] = [letter(h) for h in hyps]
        out["accuracy"] = float(np.mean([p == str(r).lower() for p, r in zip(out["pred"], refs)]))
    elif args.task == "pope":
        out["pred"] = [yesno(h) for h in hyps]
        out["accuracy"] = float(np.mean([p == str(r).lower() for p, r in zip(out["pred"], refs)]))
    else:
        out["token_f1"] = float(np.mean([f1(r, h) for r, h in zip(refs, hyps)]))
        out["bleu4"] = bleu4(refs, hyps)
    path = os.path.join(AN, f"p3_v2_qwen_{args.task}_{args.arm}.json")
    io.open(path, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1) + "\n")
    print("wrote", os.path.relpath(path, REPO), out.get("token_f1"), out.get("bleu4"), out.get("accuracy"), flush=True)


if __name__ == "__main__":
    main()
