# -*- coding: utf-8 -*-
r"""风险 #2：把论文的核心量 **`Γ_m`（梯度敏感性）** 在**解码器 VLM** 上验证（2026-10-08）。

## 为什么

论文定义 `Γ_m = ‖∇_m DG*‖ · cos φ_m`（`φ_m` 为该侧梯度与总梯度的夹角），
并用它解释"为什么适配位置不同效果不同"。
**但 `Γ_m` 至今只在双塔模型上测过**，而本阶段已把框架扩到解码器 VLM
→ **若 `Γ_m` 在新架构上不成立，"机制"这一层就有一条腿是空的。**

## 测什么（`grounding` 与 `outputs/theory/encoder_side/` 同口径）

对 `text_only` / `vision_only` / `both` 三臂，各做一次**单批前向 + `∇DG*` 反传**，
分别汇总**两侧参数**的梯度：

| 量 | 定义 |
|---|---|
| `‖g_m‖` | 第 m 侧（视觉 / 语言）LoRA 参数的 `∇DG*` 范数 |
| `cos φ_m` | 该侧梯度与**全部可训梯度**的余弦 |
| **`Γ_m`** | `‖g_m‖ · cos φ_m` |

**同时给出硬校验**：未参与某侧适配的臂，该侧梯度范数应为 **0**
（对应 `encoder_side` 归档里的 `norm_g_vision = 0.0000`）。

## 预写判据

- **`text_only` 臂的 `‖g_vision‖` 必须为 0**（严格冻结下视觉侧无适配器）；
- **`vision_only` 臂的 `‖g_text‖` 必须为 0**；
- 若这两条不成立 → **分塔或冻结有误，结论不采信**。

    python tools\_p54_gamma_vlm.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
MDIR = REPO / "models" / "Qwen2-VL-2B-Instruct"
OUT = REPO / "outputs" / "analysis" / "gamma_vlm.json"

ARMS = {
    "text_only":   ["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    "vision_only": ["qkv", "proj", "fc1", "fc2"],
    "both":        ["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj",
                    "qkv", "proj", "fc1", "fc2"],
}
RANK, ALPHA = 8, 16


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("=== 风险 #2：Γ_m 在解码器 VLM 上的验证 ===")
        print(f"  模型 {MDIR}｜三臂 {list(ARMS)}｜rank {RANK}")
        print("  判据：text_only 的 ‖g_vision‖=0；vision_only 的 ‖g_text‖=0")
        print("  （预演；加 --apply 实跑）")
        return 0

    import torch
    import torch.nn.functional as F
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    from peft import LoraConfig, get_peft_model
    from src.dataset import create_dataloaders
    from PIL import Image

    device = "cuda" if torch.cuda.is_available() else "cpu"
    loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                      batch_size=4, max_samples=16)
    batch = next(iter(loader))
    print(f"=== Γ_m 测量启动（device={device}）===", flush=True)

    results = {}
    for arm, targets in ARMS.items():
        print(f"\n  ── {arm} ──", flush=True)
        torch.manual_seed(42)
        m = Qwen2VLForConditionalGeneration.from_pretrained(
            str(MDIR), torch_dtype=torch.bfloat16, device_map=device, low_cpu_mem_usage=True)
        proc = AutoProcessor.from_pretrained(str(MDIR), trust_remote_code=True)
        m.config.use_cache = False
        m = get_peft_model(m, LoraConfig(r=RANK, lora_alpha=ALPHA, lora_dropout=0.05,
                                         bias="none", target_modules=list(targets)))
        lora_keys = []
        for n, p in m.named_parameters():
            ok = ("lora_A" in n) or ("lora_B" in n)
            p.requires_grad = ok
            if ok:
                lora_keys.append(n)

        content = [[{"type": "image"}, {"type": "text", "text": str(c)}] for c in batch["caption"]]
        texts = [proc.apply_chat_template([{"role": "user", "content": c}],
                                         tokenize=False, add_generation_prompt=True)
                 for c in content]
        inp = proc(text=texts, images=[im for im in batch["image"]],
                   return_tensors="pt", padding=True).to(device)

        t0 = time.time()
        m.train()
        m.zero_grad(set_to_none=True)
        out = m(**inp, output_hidden_states=True)
        hid = out.hidden_states[-1]
        mask = inp["attention_mask"].unsqueeze(-1).to(hid.dtype)
        T = (hid * mask).sum(1) / mask.sum(1).clamp(min=1)
        tok = inp["input_ids"]
        vmask = ((tok >= 151652) & (tok <= 151656)).unsqueeze(-1).to(hid.dtype)
        nv = vmask.sum(1)
        I = (hid * vmask).sum(1) / nv.clamp(min=1) if float(nv.min()) > 0 else T
        I = F.normalize(I.float(), p=2, dim=-1)
        T = F.normalize(T.float(), p=2, dim=-1)
        dg = ((I - T) ** 2).sum(-1).mean()
        dg.backward()

        # **按张量逐元素求和算余弦**：两侧张量个数不同（258 vs 392），
        # 不能先 cat 成扁平向量再算（实测会因长度不同报 RuntimeError）。
        grads = []          # [(name, grad_flat)]
        for n, p in m.named_parameters():
            if p.requires_grad and p.grad is not None:
                grads.append((n, p.grad.detach().float().flatten()))
        g_vis = [(n, g) for n, g in grads if ".visual." in n]
        g_txt = [(n, g) for n, g in grads if "language_model" in n]

        def _dot(a, b):
            return float(sum(torch.dot(x, y) for (_, x), (_, y) in zip(a, b)))

        def _selfdot(a):
            return _dot(a, a)

        nv_ = _selfdot(g_vis) ** 0.5 if g_vis else 0.0
        nt_ = _selfdot(g_txt) ** 0.5 if g_txt else 0.0
        tot = _selfdot(grads) ** 0.5
        cos_v = _dot(g_vis, [t for t in grads if ".visual." in t[0]]) / (nv_ * tot) \
            if g_vis and tot > 0 else float("nan")
        cos_t = _dot(g_txt, [t for t in grads if "language_model" in t[0]]) / (nt_ * tot) \
            if g_txt and tot > 0 else float("nan")
        rec = {"arm": arm, "n_lora_tensors": len(lora_keys),
               "norm_g_vision": nv_, "norm_g_text": nt_,
               "cos_phi_vision": cos_v, "cos_phi_text": cos_t,
               "Gamma_vision": (nv_ * cos_v) if g_vis else 0.0,
               "Gamma_text": (nt_ * cos_t) if g_txt else 0.0,
               # 单批的瞬时量；论文的 Γ_m 是轨迹平均——两者不等价，须在文档写明
               "note": "single-batch instantaneous grad; paper Gamma_m is trajectory-averaged",
               "elapsed_sec": round(time.time() - t0, 1)}
        results[arm] = rec
        print(f"     ‖g_vision‖={nv_:.4f} ‖g_text‖={nt_:.4f} ｜ "
              f"cos_v={cos_v:+.4f} cos_t={cos_t:+.4f}", flush=True)
        print(f"     Γ_vision={rec['Gamma_vision']:+.4f} ｜ Γ_text={rec['Gamma_text']:+.4f}",
              flush=True)
        del m
        if device == "cuda":
            torch.cuda.empty_cache()

    print("\n=== 预写判据校验（硬校验）===")
    ok = True
    chk = [("text_only 的 ‖g_vision‖ 应为 0", results["text_only"]["norm_g_vision"]),
           ("vision_only 的 ‖g_text‖ 应为 0", results["vision_only"]["norm_g_text"])]
    for label, v in chk:
        good = abs(v) < 1e-6
        ok &= good
        print(f"  {'✅' if good else '❌'} {label} → 实测 {v:.6f}")

    print("\n=== 与双塔侧对照（归档 outputs/theory/encoder_side）===")
    es = REPO / "outputs/theory/encoder_side/encoder_side.json"
    if es.exists():
        d = json.loads(io.open(es, encoding="utf-8").read())
        s = d.get("summary", {})
        print(f"  CLIP text_only : ‖g_vision‖={s.get('text_only', {}).get('norm_g_vision')} ｜ "
              f"‖g_text‖={s.get('text_only', {}).get('norm_g_text')}")
        print(f"  CLIP vision_only: ‖g_text‖={s.get('vision_only', {}).get('norm_g_text')}")

    if apply and ok:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"model": "Qwen2-VL-2B-Instruct",
                        "protocol": "single batch, rank 8, strict freeze",
                        "arms": results, "hard_checks_passed": True},
                       ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    elif apply:
        print("\n  ❌ 硬校验未过 → **不落盘**（分塔或冻结有误，结论不可采信）")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
