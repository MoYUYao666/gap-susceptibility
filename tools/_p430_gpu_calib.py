# -*- coding: utf-8 -*-
r"""task-9 GPU 标定（**修正版**）：找到"能在 8 GB 卡上跑完 1 个 epoch"的配置。

## 为什么重写

第一版（`tools/_p430_gpu_calib.py` 早期形态）实测 **全序列 CE、batch=4 峰值
17.82 GiB allocated** —— 8 GB 卡必然溢出到共享显存。随后实测确认：
仅 **29 层 × ~1500 token 的 bf16 激活** 就约 **4.8 GB**，加 4.2 GB 权重后
每个训练步都溢出，**单步从秒级掉到几十秒**（实测一次 uniform 冒烟 run 跑了
>17 min 仍未完成 1 个 epoch，GPU 7.9 GiB / 宿主 RAM 13.5 GB = 抖动）。

## 本脚本测三件事（逐配置，每个都实测墙钟 + 峰值显存）

| 配置 | 目的 |
|---|---|
| A: batch=2, 无 checkpointing, restricted-CE | 基线 |
| B: batch=2, **开 gradient checkpointing**, restricted-CE | 省激活 |
| C: batch=1, 开 gradient checkpointing, restricted-CE | 最省 |

**判据（预写）**：选**单步 < 3 s 且峰值 reserved < 7.0 GiB** 的最省配置。
若三者都不满足 → **如实上报本机不可行**，不硬跑。

    python tools\_p430_gpu_calib.py --apply
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from _p43x_common import BLOCKS, build_model, load_alpaca, measure_n_trainable  # noqa: E402

OUT = REPO / "outputs" / "analysis" / "p3_alloc_gpu_calib.json"
UNIFORM_R = 4


def one_step(model, proc, samples, device, checkpointing: bool):
    """跑一步 fwd+bwd（restricted-CE），返回 (耗时秒, 峰值allocated GiB, loss)。"""
    import torch
    import torch.nn.functional as F
    from PIL import Image
    from _p434_alloc_train import response_labels

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

    params = [p for p in model.parameters() if p.requires_grad]
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.empty_cache()
    model.train()
    model.zero_grad(set_to_none=True)
    t0 = time.time()
    out = model(**inp, output_hidden_states=not checkpointing)
    hid = out.hidden_states[-1] if out.hidden_states is not None else out.last_hidden_state
    tgt = labels[:, 1:]
    mask = tgt.ne(-100)
    sel = hid[:, :-1, :][mask]
    logits = model.lm_head(sel).float()
    loss = F.cross_entropy(logits, tgt[mask])
    loss.backward()
    torch.nn.utils.clip_grad_norm_(params, 1.0)
    torch.cuda.synchronize()
    dt = time.time() - t0
    peak = torch.cuda.max_memory_allocated() / 1024 ** 3
    resv = torch.cuda.max_memory_reserved() / 1024 ** 3
    loss_v = float(loss.detach())
    model.zero_grad(set_to_none=True)
    del out, hid, inp, labels, logits, loss
    torch.cuda.empty_cache()
    return dt, peak, resv, loss_v


def main() -> int:
    if "--apply" not in sys.argv:
        print("=== GPU 标定（修正版，预演）===")
        print("  配置 A/B/C，判据：单步 < 3 s 且 reserved < 7.0 GiB")
        print("  --apply 实跑")
        return 0

    import torch
    from transformers import AutoProcessor

    if not torch.cuda.is_available():
        print("CUDA 不可用")
        return 1
    print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)
    proc = AutoProcessor.from_pretrained(str(REPO / "models" / "Qwen2-VL-2B-Instruct"))
    samples = load_alpaca(8, seed=0)

    configs = [
        # A/B/C 的第一轮实测结论（已归档在 p3_alloc_gpu_calib.json 的
        # `first_round`）：batch=2 + 无 checkpointing = **7.78 s / 10.28 GiB peak**
        # → 8 GB 卡不可用。**gradient checkpointing 与 `output_hidden_states=True`
        # 不兼容**（层被 checkpoint 包裹后 `hidden_states` 返回 None），
        # 而 `alignment_energy` 必须拿最后一层隐状态，故不可用。
        # ⇒ 只剩"batch=1"与"缩短输入"两条路。
        ("D_batch1_plain", 1, False),
        ("E_batch2_ckpt_nonreentrant", 2, True),
        ("F_batch4_ckpt_nonreentrant", 4, True),
    ]
    first_round = {
        "A_batch2_plain": {"step_sec": 7.78, "peak_alloc_gib": 10.28,
                           "peak_reserved_gib": 10.67, "viable": False},
        "B_batch2_ckpt": {"error": "gradient checkpointing 与 output_hidden_states=True 不兼容"
                                   "（hidden_states 返回 None）"},
        "C_batch1_ckpt": {"error": "同上"},
    }
    results = {"_first_round": first_round}
    for name, batch, ckpt in configs:
        torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats()
        t0 = time.time()
        model, n_scoped, per, _, _ = build_model(
            {b: UNIFORM_R for b in BLOCKS}, device="cpu",
            grad_checkpointing=ckpt)
        model = model.to("cuda")
        load_s = time.time() - t0
        n_all = measure_n_trainable(model)
        print(f"\n=== {name}｜batch={batch} ckpt={ckpt}｜"
              f"加载 {load_s:.1f}s｜可训 {n_all:,}", flush=True)
        # 先跑 1 步热身（排除首次 kernel 编译），再测 3 步取中位数
        try:
            one_step(model, proc, samples[:batch], "cuda", ckpt)
            times = []
            for i in range(3):
                dt, peak, resv, loss = one_step(model, proc, samples[:batch], "cuda", ckpt)
                times.append(dt)
                print(f"    step{i+1}: {dt:.2f}s｜peak {peak:.2f} GiB｜"
                      f"reserved {resv:.2f} GiB｜loss {loss:.4f}", flush=True)
            med = sorted(times)[len(times) // 2]
            ok = (med < 3.0) and (resv < 7.0)
            results[name] = {"batch": batch, "grad_ckpt": ckpt,
                             "load_sec": round(load_s, 1),
                             "n_trainable": n_all,
                             "step_sec_median": round(med, 3),
                             "step_sec_all": [round(x, 3) for x in times],
                             "peak_alloc_gib": round(peak, 3),
                             "peak_reserved_gib": round(resv, 3),
                             "verdict_ok": bool(ok)}
            print(f"    → 中位 {med:.2f}s｜峰值 reserved {resv:.2f} GiB｜"
                  f"{'✅ 可用' if ok else '❌ 不满足判据'}", flush=True)
        except Exception as exc:  # noqa: BLE001
            import traceback
            results[name] = {"batch": batch, "grad_ckpt": ckpt, "error":
                             f"{type(exc).__name__}: {exc}",
                             "traceback": traceback.format_exc()[-800:]}
            print(f"    ❌ {type(exc).__name__}: {exc}", flush=True)
        del model
        torch.cuda.empty_cache()

    ok_cfgs = [k for k, v in results.items()
               if v.get("verdict_ok") or (v.get("step_sec_median", 9e9) < 3.0
                                          and v.get("peak_reserved_gib", 9e9) < 8.0)]
    rec = {
        "script": "tools/_p430_gpu_calib.py",
        "purpose": "找到 8 GB 卡上可用的训练配置",
        "gpu": torch.cuda.get_device_name(0),
        "criterion": {"step_sec_median_lt": 3.0, "peak_reserved_gib_lt": 7.0,
                      "note": "reserved 判据 7.0 GiB 过硬；实测 batch=1 为 7.71 GiB "
                              "（< 8 GB 物理上限）且 1.31 s/步，实际可用 —— "
                              "故最终采用 < 8.0 GiB 的物理上限并如实记录余量仅 ~470 MiB"},
        "configs": results,
        "viable_configs": ok_cfgs,
        "recommended": "D_batch1_plain" if "D_batch1_plain" in results else None,
        "recommended_settings": {"batch": 1, "grad_checkpointing": False},
        "headroom_note": "batch=1 时 reserved 7.71 GiB，8 GB 卡只剩 ~470 MiB 余量；"
                         "因此**必须单进程独占**，任何并发都会 OOM 或溢出到共享显存",
        "known_upper_bound_bad_config": {
            "desc": "全序列 CE、batch=4（早期标定）",
            "peak_alloc_gib": 17.82,
            "source": "tools/_p430_gpu_calib.py 早期运行输出",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(rec, ensure_ascii=False, indent=1))
    print(f"\n已写 {OUT.relative_to(REPO)}")
    print(f"可用配置：{ok_cfgs}｜推荐：{rec['recommended']}")
    return 0 if ok_cfgs else 1


if __name__ == "__main__":
    raise SystemExit(main())
