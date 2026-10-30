# -*- coding: utf-8 -*-
r"""跑 SigLIP 严格冻结对照（5 seeds × {text_only, both} + frozen 基线）。

## 为什么跑这个

正文当前对 SigLIP 的处理是"保留数值但**不作主张**"——因为那两个归档 run（+0.067 vs +0.058）
来自**未冻结基座**的旧约定（可训 189M/175M），text-only 反而训练了更多参数，故不能解读为"位置选择"的证据。

**严格冻结**（只训练 LoRA 的 A/B 矩阵）让 text-only vs both **真正只差"适配器注入位置"**，
从而把该项从"已收窄"升级为"已验证"，并检验主结论是否跨架构成立。

## 设计（与论文自身的 strict-freeze 实验同口径）

| 项 | 值 | 依据 |
|---|---|---|
| max_samples | **5000** | 与 `strict_freeze_control.py`（CLIP）一致 |
| epochs | **10** | 同上 |
| batch_size | **64** | 脚本默认 |
| seeds | **42, 123, 456, 789, 1024** | 与 CLIP 严格冻结的 5 seeds 一致；**seed 42 可与归档 run 对照** |
| 配置 | `s4_siglip_lora_text_only`（rank8, vision=False）、`s4_siglip_lora_both`（rank8, vision=True）、`s1_siglip_frozen`（1 epoch） | 论文正好比较这两个位置 |

## 输出

`outputs/siglip_strict/seed<SEED>/<run>/results.json`

## 前置

已装 `sentencepiece`、`protobuf`（SigLIP tokenizer 依赖）。

    python tools\_run_siglip_strict.py            # 预演（打印命令）
    python tools\_run_siglip_strict.py --apply    # 实际执行
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
SCRIPT = REPO / "experiments" / "siglip_experiments.py"
OUT_ROOT = REPO / "outputs" / "siglip_strict"
SEEDS = [42, 123, 456, 789, 1024]
# 第一轮只跑通了 text-only（both 臂被一条写错的断言拦掉——严格冻结下 apply_to_vision=True
# **本来就应该**有视觉 LoRA 参数，正确的不变量是"可训参数只来自 LoRA 矩阵"）。
# 第二轮补跑 both；已存在的 run 会被脚本自身的 "跳过（已完成）" 逻辑跳过。
ONLY = "s4_siglip_lora_text_only,s4_siglip_lora_both"
COMMON = ["--strict-freeze", "--max_samples", "5000", "--epochs", "10",
          "--batch_size", "64", "--skip_full_ft", "--data_dir", "."]
# frozen 基线单跑一次即可（1 epoch，不训练）；它算不出 CGΔ，仅作 R@1 参照，不入对照。
SKIP_FROZEN = True


def main() -> int:
    apply = "--apply" in sys.argv
    jobs: list[tuple[int, str, list[str]]] = []
    # 每个 seed：text_only + both（rank8）
    for s in SEEDS:
        jobs.append((s, ONLY, [f"--outputs_dir", str(OUT_ROOT / f"seed{s}")]))
    # frozen 基线单跑一次即可（1 epoch，不训练）；它算不出 CGΔ，仅作 R@1 参照，不入对照。
    if not SKIP_FROZEN:
        jobs.append((42, "s1_siglip_frozen", [f"--outputs_dir", str(OUT_ROOT / "frozen")]))

    print(f"共 {len(jobs)} 个作业；预计每个 LoRA 作业约 21 分钟（5000 样本 × 10 epochs）\n")
    t0 = time.time()
    for i, (seed, only, extra) in enumerate(jobs, 1):
        cmd = [PY, str(SCRIPT), "--only", only, "--seed", str(seed)] + COMMON + extra
        print(f"[{i}/{len(jobs)}] seed={seed} only={only}  ({time.time()-t0:.0f}s elapsed)")
        if not apply:
            print("    " + " ".join(cmd))
            continue
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
        tail = [l for l in (r.stdout or "").splitlines()
                if any(k in l for k in ("严格冻结", "视觉侧", "CG Δ", "R@1=", "time=", "Error", "Traceback"))]
        for l in tail[-6:]:
            print("    " + l.strip()[:140])
        if r.returncode != 0:
            print(f"    ⚠ 退出码 {r.returncode}（继续下一个）")
            err = (r.stderr or "").strip().splitlines()
            for l in err[-4:]:
                print("      stderr: " + l[:140])
    print(f"\n总耗时 {(time.time()-t0)/60:.1f} 分钟")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
