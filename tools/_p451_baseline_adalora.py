# -*- coding: utf-8 -*-
r"""task-9 步骤 6：**AdaLoRA 同预算基线**（答复 R2.4 / R3.9）。

## 结构性差异（必须讲清，否则"同预算"是假的）

- **本实验（Γ-guided）**：训练**前**把预算按 Γ 分到各块，方案**冻结**
  → `n_trainable_params` 恒定，可与预算**逐位**对齐。
- **AdaLoRA**：给每个模块初始 rank，训练中按敏感性 `S` **动态升降** rank
  （把预算从低敏感模块挪到高敏感模块）。⇒ **参数量在训练中会变**，
  初始值即使精确对齐，训练后也会偏离。

本脚本的处理：**初始**用 `rank_pattern` 精确对齐到 `B`（可做到，见下），
并把训练**过程中/结束**的实测参数量一并归档，**不掩盖偏差**。

## 为什么需要 rank_pattern 搜索

AdaLoRA 的 `rank_pattern` 与 LoRA 同机制（正则 → 逐模块 rank）。
因为 `cost_k`（每 rank 参数量）块间不等，**同一个 `init_r` 不可能命中预算**：
实测可用的 cost/rank 集合的 gcd 是 512，而目标预算 `7,237,632 = 512 × 14,136`
恰好是 512 的整数倍 ⇒ **存在精确解**，用贪心搜索即可找到。

## 用法

    python tools\_p451_baseline_adalora.py --search          # CPU，只搜 rank_pattern
    python tools\_p451_baseline_adalora.py --probe           # 需 GPU：建模型实测参数量
    python tools\_p451_baseline_adalora.py --apply           # 需 GPU：训练
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from _p43x_common import ALL_TARGETS, BLOCKS, MDIR, EXCLUDE_SUBSTR  # noqa: E402

PLANS = REPO / "outputs" / "analysis" / "p3_alloc_plans.json"
OUTDIR = REPO / "outputs" / "analysis" / "p3_alloc_runs"
SEARCH_OUT = REPO / "outputs" / "analysis" / "p3_alloc_adalora_config.json"


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search", action="store_true", help="CPU：搜出精确同预算的 rank_pattern")
    ap.add_argument("--probe", action="store_true", help="只测参数量（需 GPU 加载权重）")
    ap.add_argument("--apply", action="store_true", help="训练（需 GPU）")
    ap.add_argument("--seeds", type=str, default="42,123")
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--tag", type=str, default=None,
                    help="输出子目录名（用于 lr 扫描等场景，避免覆盖已有结果）")
    return ap.parse_args()


def load_modules(probe_path: Path):
    """从归档读出全部被适配模块的 (name, cost_per_rank, block)。"""
    p = json.loads(io.open(probe_path, encoding="utf-8").read())
    mods = []
    for b in BLOCKS:
        for m in p["per_block"][b]["modules"]:
            mods.append({"name": m["name"], "cost": int(m["cost_per_rank"]),
                         "block": b})
    return p, mods


def search_rank_pattern(mods, budget: int, max_rank: int = 12):
    """贪心搜出一组逐模块 rank，使 `Σ rank·cost == budget` 精确成立。

    策略：各模块 rank 初值取"**共同**的 r0 = floor(budget / Σcost)"，
    再按 cost 从大到小把剩余预算分给能放下的模块（+1 步长）。因为
    `Σcost` 的 gcd 整除 budget（实测 gcd=512，budget=512×14136），剩余量可被填满。
    """
    total_cost = sum(m["cost"] for m in mods)
    r0 = max(1, budget // total_cost)
    for m in mods:
        m["rank"] = r0
    used = r0 * total_cost
    if used > budget:
        return None, f"r0={r0} 已超预算（used={used:,} > {budget:,}）"
    # 按 cost 升序（便宜的先加，粒度细，容易精确填满）
    order = sorted(mods, key=lambda m: m["cost"])
    # 先贪心加，直到再加任何模块都会超预算
    while True:
        added = False
        for m in order:
            if used + m["cost"] <= budget and m["rank"] < max_rank:
                m["rank"] += 1
                used += m["cost"]
                added = True
                break
        if not added:
            break
    # 再做局部修正：尝试把某些模块 -1、另一些 +1 以逼近预算（步长 1 的组合）
    improved = True
    guard = 0
    while improved and used != budget and guard < 20000:
        improved = False
        guard += 1
        need = budget - used
        # 找一个 +1（cost ≤ need）与一个 -1（rank>1）的组合，使净增量最大且不超
        best = None
        for m in order:
            if m["rank"] >= max_rank or m["cost"] > max(need, 0):
                continue
            best = m
            break
        if best is not None and need >= best["cost"]:
            best["rank"] += 1
            used += best["cost"]
            improved = True
    return (mods, None) if used == budget else (mods, f"未能精确命中：used={used:,} vs {budget:,}"
                                                f"（差 {budget - used:,}）")


def build_adalora(rank_by_name: dict, device: str = "cpu", total_step: int = 96):
    """按逐模块 rank 构造 AdaLoRA（rank_pattern 为**正则**）。

    ⚠️ **调度参数必须与真实步数一致**：peft 的 `AdaLoraConfig` 校验
        `tinit < total_step − tfinal`
    （源码 `peft/tuners/adalora/config.py::__post_init__`）。
    本项目实际步数 = `n_train(32)/batch(1) × epochs(4)` = **96**。
    早先用 `tinit=100, tfinal=400, total_step=400` **直接 ValueError**
    （100 >= 400−400=0）—— 已修，并把校验显式复现以便提前失败。
    """
    import re
    import torch
    from transformers import Qwen2VLForConditionalGeneration
    from peft import AdaLoraConfig, get_peft_model

    tinit = max(1, int(total_step * 0.2))          # 前 20%：热身
    tfinal = max(tinit + 1, int(total_step * 0.4))  # 后 40%：固化
    if tinit >= (total_step - tfinal):
        raise ValueError(f"调度非法：tinit={tinit} >= total_step−tfinal={total_step - tfinal}")

    m = Qwen2VLForConditionalGeneration.from_pretrained(
        str(MDIR), torch_dtype=torch.bfloat16, low_cpu_mem_usage=True)
    m.config.use_cache = False
    pattern = {re.escape(n) + "$": int(r) for n, r in rank_by_name.items()}
    r_max = max(rank_by_name.values())
    cfg = AdaLoraConfig(
        # 注：AdaLoRA **忽略 `r`**（peft 会 warning）；初始 rank 由 `init_r` 决定
        lora_alpha=2 * r_max, lora_dropout=0.0, bias="none",
        target_modules=list(ALL_TARGETS), exclude_modules=r".*patch_embed.*",
        rank_pattern=pattern,
        init_r=r_max, target_r=r_max,
        beta1=0.85, beta2=0.85,
        tinit=tinit, tfinal=tfinal, deltaT=max(1, tinit // 2),
        total_step=total_step, orth_reg_weight=0.5,
    )
    m = get_peft_model(m, cfg)
    for name, p in m.named_parameters():
        keep = any(k in name for k in ("lora_A", "lora_B", "lora_E",
                                       "lora_magnitude", "lora_alpha"))
        p.requires_grad = bool(keep)
    n_all = int(sum(p.numel() for p in m.parameters() if p.requires_grad))
    return m, n_all


def main() -> int:
    args = parse_args()
    if not (args.search or args.probe or args.apply):
        print("=== AdaLoRA 同预算基线（预演）===")
        print("  --search（CPU 搜配置）｜--probe（实测参数量）｜--apply（训练）")
        return 0

    probe_path = REPO / "outputs" / "analysis" / "p3_alloc_budget_probe.json"
    if not probe_path.exists():
        print(f"[FATAL] 缺 {probe_path.relative_to(REPO)}")
        return 1
    pdata, mods = load_modules(probe_path)
    plans = json.loads(io.open(PLANS, encoding="utf-8").read()) if PLANS.exists() else {}
    budget = int(plans.get("budget_params",
                           4 * sum(pdata["per_block"][b]["cost_per_rank"] for b in BLOCKS)))
    print(f"目标预算 B = {budget:,}｜被适配模块 {len(mods)} 个"
          f"｜Σcost = {sum(m['cost'] for m in mods):,}")

    mods2, err = search_rank_pattern(mods, budget)
    used = sum(m["rank"] * m["cost"] for m in mods2)
    from collections import Counter
    dist = Counter(m["rank"] for m in mods2)
    print(f"\n搜索得到的 rank 分布: {dict(sorted(dist.items()))}")
    print(f"Σ rank·cost = {used:,}｜精确命中: {used == budget}"
          + (f"｜问题: {err}" if err else ""))
    per_block = {b: sum(m["rank"] * m["cost"] for m in mods2 if m["block"] == b)
                 for b in BLOCKS}
    print(f"逐块参数量 {per_block}")

    rec = {
        "script": "tools/_p451_baseline_adalora.py",
        "method": "AdaLoRA (peft AdaLoraConfig + rank_pattern)",
        "peft_version": __import__("peft").__version__,
        "target_budget_params": budget,
        "n_modules": len(mods2),
        "rank_distribution": {str(k): v for k, v in sorted(dist.items())},
        "sum_rank_cost": used,
        "budget_exact_match_by_cost_model": used == budget,
        "per_block_params_by_cost_model": per_block,
        "search_error": err,
        "rank_by_name": {m["name"]: m["rank"] for m in mods2},
        "note": ("AdaLoRA 训练中动态升降 rank ⇒ 参数量会变化；"
                 "这里只保证**初始**按成本模型精确等于预算，训练后实测值另行归档"),
    }
    SEARCH_OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(SEARCH_OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(rec, ensure_ascii=False, indent=1))
    print(f"\n已写 {SEARCH_OUT.relative_to(REPO)}")

    if args.search:
        return 0 if used == budget else 1

    # ---- 实测参数量（需 GPU/权重）----
    import torch
    print("\n=== 建 AdaLoRA 实测参数量 ===", flush=True)
    m, n_all = build_adalora(rec["rank_by_name"])
    n_layers = int(m.config.text_config.num_hidden_layers)
    print(f"  实测 n_trainable = {n_all:,}｜预算 {budget:,}｜"
          f"偏差 {(n_all - budget):+,}（{(n_all - budget) / budget * 100:+.4f}%）")
    check = {b: 0 for b in BLOCKS}
    from _p43x_common import block_of, is_excluded
    for name, p in m.named_parameters():
        if not p.requires_grad:
            continue
        base = name.rsplit(".lora_", 1)[0]
        if is_excluded(base):
            continue
        blk = block_of(base, n_layers)
        if blk:
            check[blk] += p.numel()
    print(f"  逐块实测 {check}")
    rec["n_trainable_measured"] = n_all
    rec["measured_matches_budget"] = (n_all == budget)
    rec["per_block_params_measured"] = check
    io.open(SEARCH_OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(rec, ensure_ascii=False, indent=1))
    if args.probe:
        del m
        return 0 if n_all == budget else 1

    # ---- 训练 ----
    from transformers import AutoProcessor
    import torch.nn.functional as F
    from _p43x_common import alignment_energy, load_alpaca
    from _p434_alloc_train import N_EVAL, N_TRAIN, PROMPT_TEXT, make_train_batch

    dev_name = "cuda"
    proc = AutoProcessor.from_pretrained(str(MDIR))
    samples = load_alpaca(N_TRAIN + N_EVAL, seed=0)
    train_samples, eval_texts = samples[:N_TRAIN], [PROMPT_TEXT] * N_EVAL
    seeds = [int(s) for s in args.seeds.split(",")]
    summary = {}
    # **独立 tag 目录**：lr 扫描等场景必须与既有结果隔离，否则会互相覆盖
    # （本任务先前正是因为没有 `--tag` 而差点让 lr=1e-3 与 lr=3e-4 覆盖同一文件）
    outdir = (OUTDIR / args.tag) if args.tag else OUTDIR
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"输出目录: {outdir.relative_to(REPO)}（lr={args.lr}）", flush=True)
    del m

    for seed in seeds:
        t0 = time.time()
        r = dict(rec); r.pop("rank_by_name", None)
        r.update({"seed": seed, "epochs": args.epochs, "batch": args.batch,
                  "n_train": N_TRAIN, "n_eval": N_EVAL, "lr": args.lr})
        try:
            torch.manual_seed(seed)
            torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats()
            model, n_init = build_adalora(
                json.loads(io.open(SEARCH_OUT, encoding="utf-8").read())["rank_by_name"])
            model = model.to(dev_name)
            r["n_trainable_init_measured"] = n_init
            model.eval()
            E0, E0p = alignment_energy(model, proc, eval_texts, dev_name)
            r["E0"] = E0; r["E0_per_sample"] = E0p
            params = [p for p in model.parameters() if p.requires_grad]
            opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01)
            nb = (len(train_samples) + args.batch - 1) // args.batch
            sched = torch.optim.lr_scheduler.CosineAnnealingLR(
                opt, T_max=max(nb * args.epochs, 1))
            traj, losses, ncounts = [E0], [], []
            for ep in range(1, args.epochs + 1):
                model.train(); ep_loss, k = 0.0, 0
                for bi in range(nb):
                    b = train_samples[bi * args.batch:(bi + 1) * args.batch]
                    if not b:
                        continue
                    inp, labels = make_train_batch(proc, b, dev_name)
                    out = model(**inp, output_hidden_states=True)
                    hid = out.hidden_states[-1]
                    tgt = labels[:, 1:]; mask = tgt.ne(-100)
                    logits = model.lm_head(hid[:, :-1, :][mask]).float()
                    loss = F.cross_entropy(logits, tgt[mask])
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(params, 1.0)
                    opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
                    ep_loss += float(loss.detach()); k += 1
                    del inp, labels, out, hid, loss
                model.eval()
                Ee, _ = alignment_energy(model, proc, eval_texts, dev_name)
                traj.append(Ee); losses.append(ep_loss / max(k, 1))
                ncur = int(sum(p.numel() for p in model.parameters() if p.requires_grad))
                ncounts.append(ncur)
                print(f"    ep{ep}/{args.epochs} loss={losses[-1]:.4f} E={Ee:.2f} "
                      f"n_trainable={ncur:,}", flush=True)
                torch.cuda.empty_cache()
            E1, E1p = alignment_energy(model, proc, eval_texts, dev_name)
            n_final = int(sum(p.numel() for p in model.parameters() if p.requires_grad))
            import statistics as st
            d = [b - a for a, b in zip(E0p, E1p)]
            r.update({
                "E1": E1, "delta_E": E1 - E0, "E_trajectory": traj,
                "train_loss": losses, "loss_first": losses[0], "loss_last": losses[-1],
                "n_trainable_final_measured": n_final,
                "n_trainable_per_epoch": ncounts,
                "n_trainable_change_pct": round((n_final - n_init) / n_init * 100, 4),
                "delta_E_per_sample_mean": st.mean(d),
                "delta_E_per_sample_sd": (st.stdev(d) if len(d) > 1 else 0.0),
                "peak_gpu_gib": round(torch.cuda.max_memory_allocated() / 1024 ** 3, 3),
                "ok": True,
            })
            print(f"    → AdaLoRA ΔE={r['delta_E']:+.2f}｜n_trainable "
                  f"{n_init:,}→{n_final:,}（{r['n_trainable_change_pct']:+.2f}%）", flush=True)
            del model; torch.cuda.empty_cache()
        except Exception as exc:  # noqa: BLE001
            r.update({"ok": False, "error": f"{type(exc).__name__}: {exc}",
                      "traceback": traceback.format_exc()[-1500:]})
            print(f"    ❌ seed{seed}: {type(exc).__name__}: {exc}", flush=True)
        r["elapsed_sec"] = round(time.time() - t0, 1)
        summary[f"adalora__seed{seed}"] = r
        io.open(outdir / f"adalora__seed{seed}.json", "w", encoding="utf-8",
                newline="").write(json.dumps(r, ensure_ascii=False, indent=1))
    io.open(outdir / "adalora_summary.json", "w", encoding="utf-8", newline="").write(
        json.dumps({"script": "tools/_p451_baseline_adalora.py",
                    "target_budget_params": budget, "runs": summary},
                   ensure_ascii=False, indent=1))
    n_ok = sum(1 for v in summary.values() if v.get("ok"))
    print(f"\n=== AdaLoRA {n_ok}/{len(summary)} → "
          f"{(outdir / 'adalora_summary.json').relative_to(REPO)} ===")
    return 0 if n_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
