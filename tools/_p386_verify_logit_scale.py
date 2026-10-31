# -*- coding: utf-8 -*-
r"""核实 `logit_scale` —— 权重里的真值 vs 代码硬编码（2026-10-12）。

## 待核（审计成员主张）

1. `models/clip-vit-base-patch32/pytorch_model.bin` 里 `logit_scale = 4.605170 = ln(100)`
   （而 `config.json` 写 `logit_scale_init_value: 2.6592`）→ **权重与 config 不符**
2. `tools/_p293_dinov2_hetero_strict.py` 硬编码 `LOGIT_SCALE_INIT = 2.659260036932778`
   → **与实验所对照的权重不符**
3. `src/trainer.py:419` 训练损失用 `self.model.logit_scale.exp()`
   → **论文各臂在 exp(4.605)=100 下训练**

**若成立**：论文的 CLIP 臂与本实验的 logit 尺度差 **7×**（100 vs 14.29）
→ **DINOv2 的 ΔCG 不可与论文 ΔCG 并列**。

    python tools\_p386_verify_logit_scale.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "logit_scale_verify.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    rep = {"script": "tools/_p386_verify_logit_scale.py"}

    print("=" * 92)
    print("① 权重文件里的真实 logit_scale")
    print("=" * 92)
    import torch
    mp = REPO / "models" / "clip-vit-base-patch32"
    for fn in ("pytorch_model.bin", "model.safetensors"):
        p = mp / fn
        if not p.exists():
            continue
        sha = hashlib.sha256(p.read_bytes()).hexdigest().upper()
        print(f"  {fn}")
        print(f"     SHA256 = {sha}")
        rep[f"sha256_{fn}"] = sha
        try:
            if fn.endswith(".bin"):
                sd = torch.load(str(p), map_location="cpu", weights_only=True)
            else:
                from safetensors.torch import load_file
                sd = load_file(str(p))
            ls = sd.get("logit_scale")
            if ls is not None:
                v = float(ls.reshape(-1)[0])
                print(f"     logit_scale = {v:.9f} ｜ exp = {float(torch.tensor(v).exp()):.6f}")
                print(f"     ln(100) = {float(torch.log(torch.tensor(100.0))):.9f} ｜ "
                      f"ln(1/0.07) = {float(torch.log(torch.tensor(1/0.07))):.9f}")
                rep[f"logit_scale_{fn}"] = v
                rep[f"logit_scale_exp_{fn}"] = float(torch.tensor(v).exp())
        except Exception as e:
            print(f"     ⚠️ 读取失败: {type(e).__name__}: {str(e)[:120]}")
            rep[f"error_{fn}"] = str(e)[:200]

    print()
    print("=" * 92)
    print("② transformers 载入后 model.logit_scale 的实际值")
    print("=" * 92)
    from transformers import CLIPModel
    m = CLIPModel.from_pretrained(str(mp), local_files_only=True)
    v = float(m.logit_scale.reshape(-1)[0])
    print(f"  CLIPModel.logit_scale = {v:.9f} ｜ exp = {float(m.logit_scale.exp()):.6f}")
    rep["transformers_logit_scale"] = v
    rep["transformers_exp"] = float(m.logit_scale.exp())
    cfg = json.loads((mp / "config.json").read_text(encoding="utf-8"))
    print(f"  config.json::logit_scale_init_value = {cfg.get('logit_scale_init_value')}")
    rep["config_logit_scale_init_value"] = cfg.get("logit_scale_init_value")

    print()
    print("=" * 92)
    print("③ 代码里的硬编码 vs 训练损失用法")
    print("=" * 92)
    for f, pat in (("tools/_p293_dinov2_hetero_strict.py", "LOGIT_SCALE_INIT"),
                   ("src/trainer.py", "logit_scale")):
        p = REPO / f
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        import re
        for mm in list(re.finditer(pat, t))[:4]:
            ln = t[:mm.start()].count("\n") + 1
            seg = " ".join(t[max(0, mm.start() - 80):mm.start() + 110].split())
            print(f"  [{f}:{ln}] …{seg[:170]}…")
    rep["verdict"] = ("权重 logit_scale 与代码硬编码不一致 → 论文臂与本实验的 logit 尺度不同"
                      if abs(v - 2.659260036932778) > 1e-3 else
                      "权重与硬编码一致")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
