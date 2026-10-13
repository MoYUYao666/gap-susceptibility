# -*- coding: utf-8 -*-
r"""量一下 `_p464` 的输入到底有多少 visual token（解释单 run 只要 ~18 s）。

只加载 processor，不加载模型、不占卡。

    python tools\_p468_qwen_token_stats.py
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import torch
from PIL import Image
from transformers import AutoProcessor

REPO = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO / "models" / "Qwen2-VL-2B-Instruct"
MANIFEST = REPO / "outputs" / "analysis" / "p3d_manifest.json"
MIN_PIX = 64 * 64
MAX_PIX = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 128 * 128
TAG = "" if MAX_PIX == 128 * 128 else f"_mp{MAX_PIX}"

proc = AutoProcessor.from_pretrained(str(MODEL_DIR), local_files_only=True)
mf = json.loads(io.open(MANIFEST, encoding="utf-8").read())["datasets"]["coco"]
imgdir = REPO / "coco" / "val2014"
recs = mf["train_sel"]["16"][:4]

rows = []
for s in recs:
    with Image.open(imgdir / s["image"]) as im:
        img = im.convert("RGB")
    px = img.size
    msgs = [{"role": "user",
             "content": [{"type": "image"}, {"type": "text", "text": "Describe this image."}]},
            {"role": "assistant",
             "content": [{"type": "text", "text": s["caption"]}]}]
    prompt = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
    enc = proc(text=[prompt], images=[img], return_tensors="pt",
               min_pixels=MIN_PIX, max_pixels=MAX_PIX)
    ids = enc["input_ids"][0]
    n_vis = int((ids == 151655).sum())
    rows.append({"image": s["image"], "orig_wh": list(px), "seq_len": int(ids.numel()),
                 "n_visual_tokens": n_vis, "n_text_tokens": int(ids.numel()) - n_vis,
                 "grid": [int(x) for x in enc["image_grid_thw"][0].tolist()]})

for r in rows:
    print(f"  {r['image'][:28]:<30} 原始 {r['orig_wh']} → grid {r['grid']}  "
          f"visual={r['n_visual_tokens']}  文本={r['n_text_tokens']}  总={r['seq_len']}")
out = {"script": "tools/_p468_qwen_token_stats.py",
       "model": "models/Qwen2-VL-2B-Instruct",
       "min_pixels": MIN_PIX, "max_pixels": MAX_PIX, "image_token_id": 151655,
       "note": "只统计 processor 输出，未加载模型",
       "rows": rows,
       "mean_visual_tokens": sum(r["n_visual_tokens"] for r in rows) / len(rows),
       "mean_seq_len": sum(r["seq_len"] for r in rows) / len(rows)}
p = REPO / "outputs" / "analysis" / f"p3d_qwen_token_stats{TAG}.json"
io.open(p, "w", encoding="utf-8", newline="").write(
    json.dumps(out, ensure_ascii=False, indent=1))
print(f"  平均 visual token = {out['mean_visual_tokens']:.1f}, "
      f"平均序列长度 = {out['mean_seq_len']:.1f}")
print(f"  ✅ 已写 {p.relative_to(REPO)}")
