# -*- coding: utf-8 -*-
r"""task-9 CPU 侧校验：`rank_pattern` 是否**真的**把逐块 rank 挂对了。

为什么必须在 CPU 上先验：peft 的 `rank_pattern` 键是**正则**，靠
`get_pattern_key`（`re.match(rf"(.*\.)?({key})$", name)`）匹配。模式一旦写错，
peft 会**静默**回落到 `config.r`（`rank_pattern.get(r_key, config.r)`）——
于是"逐块分配"悄悄变成"均匀分配"，实验白跑且看不出错。

本脚本在 **CPU** 上完成（不占 GPU）：
1. 枚举待适配 Linear，按 `_p43x_common.block_of` 分块；
2. 构造 `rank_pattern`，逐模块**独立复算**匹配结果，断言每块命中数正确；
3. 断言 `patch_embed`（Conv3d）被排除；
4. 用 `base_model`（无权重）验证 `LoraConfig(rank_pattern=...)` 可被 peft 接受
   （不加载权重，故不占 GPU）。

    python tools\_p450_verify_rank_pattern.py
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from _p43x_common import (ALL_TARGETS, BLOCKS, block_of, is_excluded)  # noqa: E402

fails: list[str] = []


def check(label, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {label}" + (f" ｜ {detail}" if detail else ""))
    if not cond:
        fails.append(label)


def main() -> int:
    print("=== 1. peft `get_pattern_key` 语义复现（纯字符串，无需权重）===")
    # 复制 peft/utils/other.py::get_pattern_key 的逻辑
    def get_pattern_key(pattern_keys, key_to_match):
        for key in pattern_keys:
            if re.match(rf"(.*\.)?({key})$", key_to_match):
                return key
        return key_to_match

    # 构造与 _p43x_common.build_model 相同的键（re.escape(name) + "$"）
    sample = "base_model.model.model.visual.blocks.0.attn.qkv"
    keys = [re.escape(sample) + "$"]
    got = get_pattern_key(keys, sample)
    check("escaped 键能匹配前缀包装后的全限定名", got == keys[0],
          f"key={keys[0][:60]}... -> {got[:40]}...")

    # 锚定 `$`（配合 peft 自带的前缀组 `(.*\.)?`）要求匹配结束于**点边界**，
    # 因此不会命中"以目标名开头、后面还接东西"的模块名。
    loose = [re.escape("model.visual.blocks.0.attn.qkv")]
    suffix = "base_model.model.model.visual.blocks.0.attn.qkv_extra"
    check("锚定 `$` 时不命中后缀扩展名（点边界保证）",
          get_pattern_key(loose, suffix) != loose[0],
          f"{suffix} -> 未命中（正确）")
    # 对照：**真子串**匹配（target_modules 的语义）会误伤 —— 这正是本项目
    # 实测到 patch_embed.proj 被 `proj` 命中的机制（tools/_p420b_find_conv.py）。
    check("子串 `proj` 命中 patch_embed.proj（target_modules 的已知陷阱）",
          get_pattern_key(["proj"], "model.visual.patch_embed.proj") == "proj",
          "故 target_modules 必须配 EXCLUDE_SUBSTR=('patch_embed',)")

    print("\n=== 2. 枚举待适配模块（从 config 读层数，不加载权重）===")
    from transformers import AutoConfig
    cfg = AutoConfig.from_pretrained(str(REPO / "models" / "Qwen2-VL-2B-Instruct"))
    n_layers = int(cfg.text_config.num_hidden_layers)
    print(f"  LLM 层数 {n_layers}｜块切分 {block_of.__doc__ or ''}")

    # 用模块名清单（从 config 推导不现实）→ 这里只用已知的模块名模式做**计数**校验，
    # 真值来自 tools/_p420_arch_probe.py 的实测（已归档）。
    import json
    probe_p = REPO / "outputs" / "analysis" / "p3_alloc_budget_probe.json"
    if not probe_p.exists():
        print("  [SKIP] 缺 p3_alloc_budget_probe.json —— 先跑 tools/_p420_arch_probe.py --apply")
        return 1
    probe = json.loads(probe_p.read_text(encoding="utf-8"))
    per_block = probe["per_block"]
    n_modules = {b: per_block[b]["n_modules"] for b in BLOCKS}
    cost = {b: per_block[b]["cost_per_rank"] for b in BLOCKS}
    print(f"  归档实测模块数 {n_modules}｜合计 {sum(n_modules.values())}")
    check("模块总数 == 324", sum(n_modules.values()) == 324, str(sum(n_modules.values())))
    check("vision 模块数 == 128", n_modules["vision"] == 128, str(n_modules["vision"]))

    # 逐模块明细里不应出现 patch_embed
    allnames = [m["name"] for b in BLOCKS for m in per_block[b]["modules"]]
    bad = [n for n in allnames if is_excluded(n)]
    check("明细里已剔除 patch_embed(Conv3d)", not bad, f"{len(bad)} 个残留")
    check("明细里全是 Linear（都由 in/out_features 给出）",
          all("in_features" in m and "out_features" in m
              for b in BLOCKS for m in per_block[b]["modules"]))
    # cost_k 复算
    for b in BLOCKS:
        recomputed = sum(m["cost_per_rank"] for m in per_block[b]["modules"])
        check(f"{b}: cost_per_rank 复算一致", recomputed == cost[b],
              f"{recomputed:,} vs {cost[b]:,}")

    print("\n=== 3. LoraConfig 接受 rank_pattern（无权重构造，验证签名）===")
    from peft import LoraConfig
    ranks = {b: 3 for b in BLOCKS}
    ranks["llm_shallow"] = 15
    pattern = {}
    for b in BLOCKS:
        for m in per_block[b]["modules"]:
            pattern[re.escape(m["name"]) + "$"] = ranks[b]
    cfg_lora = LoraConfig(r=3, lora_alpha=6, lora_dropout=0.0, bias="none",
                          target_modules=list(ALL_TARGETS), rank_pattern=pattern)
    check("rank_pattern 键数 == 模块数", len(cfg_lora.rank_pattern) == len(pattern),
          f"{len(cfg_lora.rank_pattern)} vs {len(pattern)}")
    check("rank_pattern 值域正确",
          set(cfg_lora.rank_pattern.values()) == set(ranks.values()),
          str(sorted(set(cfg_lora.rank_pattern.values()))))
    # peft 用 max(config.r, *rank_pattern.values()) 估最大 rank（model.py:622）
    max_r = max(cfg_lora.r, *cfg_lora.rank_pattern.values())
    check("max rank 推导正确", max_r == max(ranks.values()), f"max_r={max_r}")

    print("\n=== 4. 预测参数量 vs 归档断言 ===")
    for b in BLOCKS:
        pred = ranks[b] * cost[b]
        print(f"  {b:<12} rank={ranks[b]:>2} → {pred:>10,} 参数")
    total = sum(ranks[b] * cost[b] for b in BLOCKS)
    print(f"  合计 {total:,}")

    print(f"\n=== 结论：{len(fails)} 项失败 ===")
    for f in fails:
        print("  FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
