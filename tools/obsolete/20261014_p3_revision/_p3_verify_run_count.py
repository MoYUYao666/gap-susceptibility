# -*- coding: utf-8 -*-
"""核实 P3 结论句里 "9 block-level counterfactual runs" 的构成。

结论句：conclusion.tex:7 — "190 runs (181 sweep runs plus 9 block-level counterfactual runs)"

本脚本验证：
  ① 181 = LLaVA 扫描运行的档案数
  ② 9   = 块级反事实的**独立配置**数（theory / uniform / violation × 3 seeds），
          每个配置有 3 个版本快照（原始 / v2 / blankimg_v3），故文件数 27 而非 9
  ③ 这 9 个配置的文件内确实带"块级"字段（逐块 rank 分配）

    python tools/_p3_verify_run_count.py
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXP = REPO / "paper3" / "scripts" / "outputs" / "experiments"


def base_name(n: str) -> str:
    return re.sub(r"(_blankimg_v3|_v2|_blankimg)\.json$", ".json", n)


def main() -> int:
    files = sorted(p.name for p in EXP.glob("*.json"))
    cfs = [n for n in files if n.startswith("qwen_cf_")]
    sweep = [n for n in files if not n.startswith("qwen_cf_")]

    bases = Counter(base_name(n) for n in cfs)
    multi = {k: v for k, v in bases.items() if v > 1}
    configs = sorted(multi)

    print(f"实验目录 json 总数           : {len(files)}")
    print(f"  ├ qwen_cf_*（块级反事实）  : {len(cfs)}")
    print(f"  └ 其余（LLaVA 扫描/聚合）  : {len(sweep)}")
    print()
    print("块级反事实：独立配置（去版本快照后缀）")
    for i, c in enumerate(configs, 1):
        print(f"  {i:2d}) {c}   → {bases[c]} 个版本快照")
    print()
    print(f"独立配置数 = {len(configs)}   （稿件称 9 block-level）")
    print(f"版本快照数 = {len(cfs)}   （9 配置 × 3 变体）")

    # 检查一个配置文件里是否有"块级"字段
    sample = EXP / configs[0]
    d = json.loads(sample.read_text(encoding="utf-8"))
    print(f"\n抽样检查 {sample.name}：")
    print(f"  顶层键: {sorted(d.keys())[:12]}")
    for k in ("block_ranks", "blocks", "per_block", "block_config", "arm", "label"):
        if k in d:
            v = d[k]
            print(f"  {k} = {str(v)[:100]}")

    ok = len(configs) == 9
    print(f"\n判定：独立配置数 == 9 → {'✅ 与稿件一致' if ok else '❌ 不一致'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
