# -*- coding: utf-8 -*-
r"""Generate one caption per image with the local vision-language model (LM Studio server).

The goal is an LLM-generated provenance arm for the A3 controlled comparison. Images are resized before sending so
that the request stays small; the output JSONL mirrors the schema of the other provenance corpora, with one text per
image. Existing lines are reused, so an interrupted run resumes.

Usage
  python make_llm_caption_corpus.py --dataset rsicd [--limit 3000] [--model qwen3-vl-8b-instruct]
"""
import argparse
import base64
import io
import json
import os
import time
import urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "http://127.0.0.1:1234/v1/chat/completions"
PROMPT = ("Describe this remote sensing image in one sentence. Mention the main objects, their layout, and the "
          "land-cover type. Do not use a list; write one fluent sentence of 10 to 25 words.")


def api_caption(image_b64, model, timeout=180):
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_b64}},
            ],
        }],
        "temperature": 0.2,
        "max_tokens": 80,
    }
    req = urllib.request.Request(API, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    return data["choices"][0]["message"]["content"].strip()


def encode(path, max_side=768):
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = min(1.0, max_side / float(max(w, h)))
        if scale < 1.0:
            im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--model", default="qwen3-vl-8b-instruct")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    src = os.path.join(ROOT, "corpora", args.dataset, "human.jsonl")
    out = args.out or os.path.join(ROOT, "corpora", args.dataset, "llmcaption.jsonl")
    images_root = os.path.join(ROOT, "data", "rsicd" if args.dataset == "rsicd" else "nwpu_captions")

    rows = []
    seen = set()
    for line in io.open(src, encoding="utf-8"):
        r = json.loads(line)
        if r["image_id"] in seen:
            continue
        seen.add(r["image_id"])
        rows.append(r)
    if args.limit:
        rows = rows[:args.limit]

    done = {}
    if os.path.exists(out):
        for line in io.open(out, encoding="utf-8"):
            r = json.loads(line)
            done[r["image_id"]] = r
    print("images %d | already captioned %d | model %s" % (len(rows), len(done), args.model), flush=True)

    t0 = time.time()
    n_new = 0
    with io.open(out, "a", encoding="utf-8", newline="") as f:
        for i, r in enumerate(rows):
            if r["image_id"] in done:
                continue
            text = None
            for attempt in range(3):
                try:
                    text = api_caption(encode(os.path.join(images_root, r["image_path"])), args.model)
                    break
                except Exception as e:
                    if attempt == 2:
                        print("  skip %s: %s" % (r["image_id"], str(e)[:90]), flush=True)
                    else:
                        time.sleep(2 + 2 * attempt)
            if text is None:
                continue
            rec = {"image_id": r["image_id"], "image_path": r["image_path"], "split": r["split"],
                   "text": text, "metadata": r.get("metadata", {}), "derived_objects": {},
                   "boxes": [], "source": "llm"}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            n_new += 1
            if n_new % 50 == 0:
                dt = time.time() - t0
                print("  %d/%d captioned (%.2f s/img, %.1f min elapsed)" % (i + 1, len(rows), dt / n_new, dt / 60),
                      flush=True)
    print("wrote %s | new %d" % (out, n_new))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
