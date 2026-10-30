# -*- coding: utf-8 -*-
r"""找出 Qwen2-VL 的"回复 token 起点"，以便把任务损失限制在回复区间。

为什么必须做：全序列 CE 会产出 `(B, L, 151936)` 的 logits 外加上游激活，
4 个样本就顶到 **17.8 GiB**（实测 `tools/_p430_gpu_calib.py`）——8 GB 卡必然溢出到
共享显存，单步 34 s。把损失限制在回复 token 上既**更快更省**，也更符合
instruction tuning 的标准做法。

    python tools\_p431_probe_template.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

if __name__ == "__main__":
    from transformers import AutoProcessor
    from PIL import Image

    proc = AutoProcessor.from_pretrained(str(REPO / "models" / "Qwen2-VL-2B-Instruct"))
    im_start = proc.tokenizer.convert_tokens_to_ids("<|im_start|>")
    im_end = proc.tokenizer.convert_tokens_to_ids("<|im_end|>")
    print("im_start id:", im_start, "| im_end id:", im_end)

    content = [{"type": "image"}, {"type": "text", "text": "Name a color."}]
    text = proc.apply_chat_template([{"role": "user", "content": content}],
                                    tokenize=False, add_generation_prompt=True)
    print("\n--- chat template（user only, add_generation_prompt=True）---")
    print(repr(text))

    # 完整对话（含 assistant 回复）——这才是训练时该用的模板
    full = proc.apply_chat_template(
        [{"role": "user", "content": content},
         {"role": "assistant", "content": "Blue."}], tokenize=False)
    print("\n--- chat template（含 assistant）---")
    print(repr(full))

    blank = Image.new("RGB", (28 * 14, 28 * 14), (0, 0, 0))
    inp = proc(text=[full], images=[blank], return_tensors="pt", padding=True)
    ids = inp["input_ids"][0].tolist()
    toks = proc.tokenizer.convert_ids_to_tokens(ids)
    print(f"\n--- token 序列（{len(ids)} 个）---")
    for i, (t, v) in enumerate(zip(toks, ids)):
        if v == im_start or v == im_end or (t and t.strip()):
            mark = ""
            if v == im_start:
                mark = "  <== im_start"
            elif v == im_end:
                mark = "  <== im_end"
            print(f"  [{i:>4}] {v:>7} {t!r}{mark}")

    # 视觉 token 统计
    vis = [(i, v) for i, v in enumerate(ids) if 151652 <= v <= 151656]
    print(f"\n视觉 token 数 = {len(vis)}（区间 [{vis[0][0]}, {vis[-1][0]}]）" if vis else "\n无视觉 token")
    print("image_grid_thw:", inp.get("image_grid_thw"))
