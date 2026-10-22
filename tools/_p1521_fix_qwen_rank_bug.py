# -*- coding: utf-8 -*-
"""Fix the Qwen runner: `--rank` was only a label; the actual LoRA rank came from block_config.

The six Qwen2.5-VL records produced on 2026-10-22 all have trainable_params=1,843,200 and llm_rank=None, i.e. every
"rank 5/6" run actually used the default rank 4. This script fixes run_training_qwen25.py (and the Qwen2-VL copy) and
moves the invalid records aside.
"""
import ast
import io
import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAD_DIR = os.path.join(REPO, "outputs", "analysis", "_invalid_qwen25_rank_bug")

PATCH_OLD = """if args.llm_rank is not None:          # 云端补强: 显式覆盖 LLM 侧基础秩
    lora_rank = int(args.llm_rank)"""
PATCH_NEW = """if args.llm_rank is not None:          # 云端补强: 显式覆盖 LLM 侧基础秩
    lora_rank = int(args.llm_rank)
if args.block_config == 'uniform' and args.llm_rank is None:
    # fix 2026-10-22: --rank was previously only a label; use it as the actual LoRA rank
    lora_rank = int(args.rank)"""

for rel in ("paper3/scripts/run_training_qwen25.py", "paper3/scripts/run_training_qwen.py"):
    p = os.path.join(REPO, rel)
    t = io.open(p, encoding="utf-8").read()
    if PATCH_NEW not in t:
        assert t.count(PATCH_OLD) == 1, (rel, t.count(PATCH_OLD))
        t = t.replace(PATCH_OLD, PATCH_NEW, 1)
        io.open(p, "w", encoding="utf-8", newline="").write(t)
        ast.parse(t)
        print("patched", rel)

os.makedirs(BAD_DIR, exist_ok=True)
import glob
moved = 0
for f in glob.glob(os.path.join(REPO, "paper3", "scripts", "outputs", "experiments",
                                "qwen_cf_uniform_rank*_q25_r*.json")):
    shutil.move(f, os.path.join(BAD_DIR, os.path.basename(f)))
    moved += 1
print("moved invalid records:", moved)
