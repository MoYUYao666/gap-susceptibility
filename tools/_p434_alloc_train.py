# -*- coding: utf-8 -*-
r"""task-9 步骤 4：**同预算**训练对比（R2.2 / R3.21 主实验）。

每个方案在**完全相同的参数量**（`p3_alloc_plans.json :: budget_params`）下训练，
记录 `E(t)`、`ΔE`、逐样本配对 ΔE、以及可训参数量硬断言。

## 为什么这样设计

审稿人 R3.21 的要害是"两组 rank 分布不同、有效参数预算没对齐"。本脚本对**每一个**
run 都：
1. `build_model(ranks)` 挂上逐块 rank；
2. 用 peft 的 `named_parameters()` **实测**可训参数量；
3. **断言** `== budget`（不等价直接 raise，绝不留"差不多"）；
4. 把 `n_trainable_params_measured` 写进每个 run 的归档。

## 显存

全序列 CE 在 Qwen2-VL-2B 上峰值 17.82 GiB（实测 `tools/_p430_gpu_calib.py`）。
本脚本用**只对回复位置投影**的写法（不物化 `(B,L,151936)`），并在必要时开启
gradient checkpointing。

## 用法

    python tools\_p434_alloc_train.py --verify           # 只验预算，不训练
    python tools\_p434_alloc_train.py --apply            # 全量训练
    python tools\_p434_alloc_train.py --apply --plans uniform,exp_paper_0.137 --seeds 42
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from _p43x_common import (BLOCKS, alignment_energy, build_model,  # noqa: E402
                          is_excluded, load_alpaca, measure_n_trainable)

PLANS = REPO / "outputs" / "analysis" / "p3_alloc_plans.json"
OUTDIR = REPO / "outputs" / "analysis" / "p3_alloc_runs"
DEFAULT_SEEDS = [42, 123, 456]
DEFAULT_EPOCHS = 4
DEFAULT_BATCH = 4
# 训练/评估样本数（**不可**按批次改动：改了会让不同批次的 run 不可比）
N_TRAIN = 32
N_EVAL = 32
LR = 5e-5
PROMPT_TEXT = "Describe this image."


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify", action="store_true", help="只验证预算对齐，不训练")
    ap.add_argument("--plans", type=str, default=None, help="逗号分隔的方案名（默认全部）")
    ap.add_argument("--seeds", type=str, default=None, help="逗号分隔的 seed")
    ap.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    ap.add_argument("--batch", type=int, default=DEFAULT_BATCH)
    ap.add_argument("--ckpt", action="store_true",
                    help="建模型时就开 gradient checkpointing（需 non-reentrant；"
                         "实测 batch=2/4 与本项目的 output_hidden_states 不兼容）")
    ap.add_argument("--grad-ckpt", action="store_true",
                    help="建完模型后再开 gradient checkpointing（旧路径，B=0 时可试）")
    ap.add_argument("--cpu", action="store_true",
                    help="在 CPU 上只做「建模型 + 参数量断言」（不训练，不占卡）")
    ap.add_argument("--tag", type=str, default="main", help="输出子目录名")
    ap.add_argument("--lr", type=float, default=LR,
                    help=f"学习率（默认 {LR}）。用于对称 lr 扫描；"
                         "**必须与基线扫同一范围**，否则对比不对称（审稿人 R1.6 批评的正是这个）")
    ap.add_argument("--force", action="store_true",
                    help="已存在的 run 也重跑（默认断点续跑：跳过已成功的）")
    return ap.parse_args()


def response_labels(ids, proc):
    """assistant 回复区间 → 监督标签，其余 -100。"""
    import torch
    im_start = proc.tokenizer.convert_tokens_to_ids("<|im_start|>")
    assistant = proc.tokenizer.encode("assistant", add_special_tokens=False)
    labels = torch.full_like(ids, -100)
    for b in range(ids.shape[0]):
        row = ids[b].tolist()
        chosen = None
        for i, v in enumerate(row):
            if v == im_start and row[i + 1:i + 1 + len(assistant)] == assistant:
                chosen = i + 1 + len(assistant) + 1
        if chosen is None:
            raise RuntimeError("未找到 assistant 区间")
        labels[b, chosen:] = ids[b, chosen:]
    return labels


def make_train_batch(proc, samples, device):
    """构造 (inputs, labels)：只监督 assistant 回复 token。"""
    from PIL import Image
    texts = [proc.apply_chat_template(
        [{"role": "user", "content": [{"type": "image"},
                                      {"type": "text", "text": s["instruction"]}]},
         {"role": "assistant", "content": s["output"]}], tokenize=False)
        for s in samples]
    blank = Image.new("RGB", (28 * 14, 28 * 14), (0, 0, 0))
    inp = proc(text=texts, images=[blank] * len(texts),
               return_tensors="pt", padding=True)
    inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in inp.items()}
    labels = response_labels(inp["input_ids"], proc).to(device)
    return inp, labels


def shifted_ce(model, inp, labels):
    """**只对回复位置**投影到词表 → 不物化 (B, L, 151936)。"""
    import torch.nn.functional as F
    out = model(**inp, output_hidden_states=True)
    hid = out.hidden_states[-1]
    tgt = labels[:, 1:]
    mask = tgt.ne(-100)
    if int(mask.sum()) == 0:
        raise RuntimeError("本批无监督 token")
    sel = hid[:, :-1, :][mask]
    logits = model.lm_head(sel).float()
    return F.cross_entropy(logits, tgt[mask])


def main() -> int:
    args = parse_args()
    if not (args.apply or args.verify):
        print("=== 同预算训练（预演）===")
        print(f"  方案来自 {PLANS.name}；seeds {DEFAULT_SEEDS}；{DEFAULT_EPOCHS} epochs")
        print(f"  train {N_TRAIN} / eval {N_EVAL} 样本（Alpaca，空白图）")
        print("  --verify 只验预算；--apply 训练")
        return 0

    import torch
    from transformers import AutoProcessor

    pd = json.loads(io.open(PLANS, encoding="utf-8").read())
    budget = int(pd["budget_params"])
    cost = pd["cost_per_rank"]
    plans = pd["plans"]
    if args.plans:
        names = args.plans.split(",")
    else:
        # 默认跑「主对比集」：uniform + exp 族 + inverse + exact_opt/corner + 全部 random。
        # 早先的写法把 random 追加到"非 random"列表，会漏掉 exp 族等 —— 已修正为显式枚举。
        names = [n for n in plans if not n.startswith("random_")]
        names += sorted(n for n in plans if n.startswith("random_"))
    seeds = ([int(s) for s in args.seeds.split(",")] if args.seeds else DEFAULT_SEEDS)
    missing = [n for n in names if n not in plans]
    if missing:
        print(f"[FATAL] 未知方案 {missing}；可选 {sorted(plans)}")
        return 1

    dev = "cuda"
    if args.cpu:
        dev = "cpu"
        print("=== CPU 模式：只建模型 + 断言参数量（不训练、不占卡）===", flush=True)
        names = ([n for n in plans if not n.startswith("random_")]
                 if not args.plans else args.plans.split(","))
        n_fail = 0
        for name in names:
            ranks = {b: int(plans[name]["ranks"][b]) for b in BLOCKS}
            expected = int(plans[name]["n_trainable_params"])
            try:
                import torch
                torch.manual_seed(0)
                model, n_scoped, per_blk, _, _ = build_model(ranks, device="cpu")
                n_all = measure_n_trainable(model)
                ok = (n_all == budget)
                ok2 = (n_scoped == expected)
                flag = "OK " if (ok and ok2) else "FAIL"
                if not (ok and ok2):
                    n_fail += 1
                print(f"  {flag} {name:<26} ranks={ranks} "
                      f"实测 n_all={n_all:,}（预算 {budget:,}）｜"
                      f"n_scoped={n_scoped:,}（计划 {expected:,}）｜逐块 {per_blk}",
                      flush=True)
                del model
            except Exception as exc:  # noqa: BLE001
                n_fail += 1
                print(f"  FAIL {name}: {type(exc).__name__}: {exc}", flush=True)
        print(f"\n=== CPU 断言完成：{len(names) - n_fail}/{len(names)} 通过 ===")
        return 0 if n_fail == 0 else 1
    print(f"=== 预算 {budget:,} 参数｜{len(names)} 方案 × {len(seeds)} seeds "
          f"× {args.epochs} epochs ===", flush=True)
    print(f"  plans: {names}", flush=True)

    proc = AutoProcessor.from_pretrained(str(REPO / "models" / "Qwen2-VL-2B-Instruct"))
    train_samples = load_alpaca(N_TRAIN + N_EVAL, seed=0)[:N_TRAIN]
    eval_samples = load_alpaca(N_TRAIN + N_EVAL, seed=0)[N_TRAIN:N_TRAIN + N_EVAL]
    eval_texts = [PROMPT_TEXT] * N_EVAL
    print(f"  数据：train {len(train_samples)}｜eval {len(eval_samples)}"
          f"（前 3 条 train 指令：{[s['instruction'][:40] for s in train_samples[:3]]}）",
          flush=True)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    tagdir = OUTDIR / args.tag
    tagdir.mkdir(parents=True, exist_ok=True)
    summary = {}

    for name in names:
        ranks = {b: int(plans[name]["ranks"][b]) for b in BLOCKS}
        expected = int(plans[name]["n_trainable_params"])
        for seed in seeds:
            key = f"{name}__seed{seed}"
            t0 = time.time()
            rec = {"plan": name, "seed": seed, "ranks": ranks,
                   "family": plans[name].get("family"),
                   "beta": plans[name].get("beta"),
                   "budget_params": budget,
                   "n_trainable_params_expected": expected,
                   "epochs": args.epochs, "batch": args.batch,
                   "n_train": len(train_samples), "n_eval": len(eval_samples),
                   "grad_checkpointing": bool(args.ckpt),
                   "lr": args.lr, "model": "models/Qwen2-VL-2B-Instruct",
                   "dtype": "bfloat16", "quantization": None}
            # **断点续跑**：已成功落盘的 run 直接跳过（不重跑、不覆盖）。
            # 动机：本机单 run 约 8–10 min，一次中断（GPU 让卡/日志问题）会白烧
            # 十几分钟；跳过已完成的 run 让重启的边际成本接近 0。
            prev_f = tagdir / f"{key}.json"
            if prev_f.exists() and not args.force:
                try:
                    prev = json.loads(io.open(prev_f, encoding="utf-8").read())
                    if prev.get("ok") and prev.get("budget_assert_passed"):
                        print(f"    SKIP {key}（已成功落盘，断点续跑）", flush=True)
                        summary[key] = prev
                        continue
                except Exception:  # noqa: BLE001
                    pass
            try:
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
                model, n_scoped, per_blk, _, n_layers = build_model(
                    ranks, grad_checkpointing=bool(args.ckpt))
                model = model.to(dev)
                n_all = measure_n_trainable(model)

                # ---- 硬断言：实测 == 计划 ----
                assert n_all == budget, (
                    f"[预算不等价] {name}: 实测 {n_all:,} != 预算 {budget:,}")
                assert n_scoped == expected, (
                    f"[逐块记账不一致] {name}: scoped {n_scoped:,} != {expected:,}")
                rec["n_trainable_params_measured"] = n_all
                rec["per_block_params"] = per_blk
                rec["budget_assert_passed"] = True

                if args.grad_ckpt:
                    model.gradient_checkpointing_enable()
                    if hasattr(model, "enable_input_require_grads"):
                        model.enable_input_require_grads()

                if args.verify:
                    print(f"  OK  {key:<34} ranks={ranks} params={n_all:,} "
                          f"(+=budget) 逐块={per_blk}", flush=True)
                    rec["verified_only"] = True
                    summary[key] = rec
                    del model
                    torch.cuda.empty_cache()
                    continue

                model.eval()
                E0, E0_per = alignment_energy(model, proc, eval_texts, dev)
                rec["E0"] = E0
                rec["E0_per_sample"] = E0_per

                params = [p for p in model.parameters() if p.requires_grad]
                opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01)
                # **配置错标自检**（Lead 2026-10-13 建议）：从**真实对象回读**再断言，
                # 能挡住所有"参数传了但没生效"的情形（不必靠人去找哪一行写错）。
                # 起因：本文件曾在汇总归档里写死常量 `LR`，导致 lr 扫描成果被错标。
                _actual_lr = opt.param_groups[0]["lr"]
                assert _actual_lr == args.lr == rec["lr"], \
                    f"[配置错标] optimizer lr={_actual_lr} args.lr={args.lr} archive={rec['lr']}"
                n_batches = (len(train_samples) + args.batch - 1) // args.batch
                total = n_batches * args.epochs
                sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(total, 1))

                traj, losses, skipped = [E0], [], 0
                for ep in range(1, args.epochs + 1):
                    model.train()
                    ep_loss, nb = 0.0, 0
                    for bi in range(n_batches):
                        b = train_samples[bi * args.batch:(bi + 1) * args.batch]
                        if not b:
                            continue
                        inp, labels = make_train_batch(proc, b, dev)
                        loss = shifted_ce(model, inp, labels)
                        if not torch.isfinite(loss):
                            skipped += 1
                            opt.zero_grad(set_to_none=True)
                            del inp, labels, loss
                            continue
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(params, 1.0)
                        opt.step()
                        sched.step()
                        opt.zero_grad(set_to_none=True)
                        ep_loss += float(loss.detach())
                        nb += 1
                        del inp, labels, loss
                    model.eval()
                    Ee, _ = alignment_energy(model, proc, eval_texts, dev)
                    traj.append(Ee)
                    losses.append(ep_loss / max(nb, 1))
                    print(f"    {key:<34} ep{ep}/{args.epochs} loss={losses[-1]:.4f} "
                          f"E={Ee:.2f}", flush=True)
                    torch.cuda.empty_cache()

                E1, E1_per = alignment_energy(model, proc, eval_texts, dev)
                import statistics as st
                d_per = [b - a for a, b in zip(E0_per, E1_per)]
                rec.update({
                    "E1": E1, "E1_per_sample": E1_per,
                    "delta_E": E1 - E0,
                    "delta_E_per_sample": d_per,
                    "delta_E_per_sample_mean": st.mean(d_per),
                    "delta_E_per_sample_sd": (st.stdev(d_per) if len(d_per) > 1 else 0.0),
                    "E_trajectory": traj,
                    "train_loss": losses,
                    "loss_first": losses[0] if losses else None,
                    "loss_last": losses[-1] if losses else None,
                    "skipped_nonfinite": skipped,
                    "peak_gpu_gib": round(torch.cuda.max_memory_allocated() / 1024 ** 3, 3),
                    "ok": True,
                })
                print(f"    → {key:<34} ΔE={rec['delta_E']:+.2f} "
                      f"(配对均值 {rec['delta_E_per_sample_mean']:+.2f} "
                      f"±{rec['delta_E_per_sample_sd']:.2f}) "
                      f"loss {rec['loss_first']:.3f}→{rec['loss_last']:.3f}", flush=True)
                del model
                torch.cuda.empty_cache()
            except Exception as exc:  # noqa: BLE001
                rec.update({"ok": False, "error": f"{type(exc).__name__}: {exc}",
                            "traceback": traceback.format_exc()[-1500:]})
                print(f"    ❌ {key}: {type(exc).__name__}: {exc}", flush=True)
            rec["elapsed_sec"] = round(time.time() - t0, 1)
            summary[key] = rec
            io.open(tagdir / f"{key}.json", "w", encoding="utf-8", newline="").write(
                json.dumps(rec, ensure_ascii=False, indent=1))

    io.open(tagdir / "summary.json", "w", encoding="utf-8", newline="").write(
        json.dumps({"script": "tools/_p434_alloc_train.py", "budget_params": budget,
                    "tag": args.tag, "epochs": args.epochs, "batch": args.batch,
                    # ⚠️ 必须写 `args.lr`，**不能写模块级常量 `LR`**：
                    # 写 `LR` 会让汇总归档在非默认 lr 下**错标**（文件名/逐 run 写 1e-3、
                    # 汇总却写 5e-5），而"错标"是**不可见**缺陷（产物齐全、数字真实、标签不符）。
                    # 由 Lead 机器穷举 161 个脚本发现，全仓库仅此一处真 bug。
                    "seeds": seeds, "lr": args.lr, "n_train": N_TRAIN, "n_eval": N_EVAL,
                    "cost_per_rank": cost, "runs": summary},
                   ensure_ascii=False, indent=1))
    n_ok = sum(1 for r in summary.values() if r.get("ok"))
    print(f"\n=== 完成 {n_ok}/{len(summary)} run 成功 → "
          f"{(tagdir / 'summary.json').relative_to(REPO)} ===")
    return 0 if n_ok or args.verify else 1


if __name__ == "__main__":
    raise SystemExit(main())
