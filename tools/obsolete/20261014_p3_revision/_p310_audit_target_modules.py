# -*- coding: utf-8 -*-
r"""核查：论文用到的每个 backbone 的注意力层名，是否与 LoRA 注入的 default 匹配（2026-10-12）。

## 触发原因（task-8 成员实测发现）

`strict_freeze_control.py` 默认 `target_modules=["q_proj","v_proj"]`，
而 **DINOv2** 的投影层名是 `query`/`value`/`key` → 用默认值在 DINOv2 上
**一个 LoRA 层都注不进去**，静默跑成假实验（可训参数全来自文本侧）。

**同一个风险适用于论文用到的每个 backbone**：CLIP 用 `q_proj`/`v_proj` 没问题，
但 **OpenCLIP** 常见 `c_q_proj`/`in_proj_weight`，**SigLIP** 用 `q_proj`/`v_proj`，
**BLIP** 用 `query`/`value`。名字不匹配 = 该 tower 静默没训。

## 方法（不靠推断）

**直接实例化每个模型，列出 state_dict 里所有注意力投影层名**，再与代码用的
`target_modules` 对比。

    python tools\_p310_audit_target_modules.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "target_modules_audit.json"
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# 论文用到的 backbone -> 本地路径/标识
MODELS = {
    "clip_vit_b32": "models/clip-vit-base-patch32",
    "clip_vit_b16": "models/clip-vit-base-patch16",
    "siglip_b16": "models/siglip-base-patch16-224",
    "openclip_laion2b": "models/openclip",
    "dinov2_base": "models/dinov2-base",
}

# 代码里实际用的 target_modules（先从源码抓，抓不到再手工列）
CANDIDATES = ["q_proj", "v_proj", "k_proj", "out_proj", "query", "value", "key",
              "c_q_proj", "c_v_proj", "c_k_proj", "c_proj", "in_proj_weight",
              "qkv", "Wq", "Wv", "wk"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 100)
    print("① 代码里 LoRA 注入用的 target_modules 默认值")
    print("=" * 100)
    src_defaults = {}
    for f in list(Path(REPO / "src").rglob("*.py")) + \
            list(Path(REPO / "tools").glob("*.py")) + \
            list(Path(REPO / "paper" / "scripts").glob("*.py") if
                 (REPO / "paper" / "scripts").exists() else []):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'target_modules\s*=\s*(\[[^\]]{0,200}\])', t):
            src_defaults.setdefault(str(f.relative_to(REPO)), []).append(m.group(1))
    for k, v in src_defaults.items():
        print(f"  {k}")
        for x in v[:4]:
            print(f"     {x}")
    rep["code_defaults"] = src_defaults

    print()
    print("=" * 100)
    print("② 每个模型的真实投影层名（实例化后读 state_dict）")
    print("=" * 100)
    import torch  # noqa
    from transformers import AutoModel, AutoConfig  # noqa

    for name, rel in MODELS.items():
        p = REPO / rel
        if not p.exists():
            print(f"  ⚠️  {name}: 本地缺 {rel}")
            rep[name] = {"error": "path missing"}
            continue
        try:
            cfg = AutoConfig.from_pretrained(str(p), local_files_only=True)
            mdl = AutoModel.from_pretrained(str(p), local_files_only=True)
        except Exception as e:  # noqa
            print(f"  ⚠️  {name}: 加载失败 {type(e).__name__}: {str(e)[:110]}")
            rep[name] = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
            continue
        names = list(mdl.state_dict().keys())
        found = {}
        for cand in CANDIDATES:
            hits = [n for n in names if re.search(rf"\.{re.escape(cand)}\.weight$", n)]
            if hits:
                found[cand] = len(hits)
        print(f"  {name}  ({type(mdl).__name__}, {len(names)} tensors)")
        for cand, c in sorted(found.items(), key=lambda kv: -kv[1]):
            mark = "✅" if cand in ("q_proj", "v_proj") else "•"
            print(f"     {mark} {cand:<18} ×{c}")
        rep[name] = {"class": type(mdl).__name__, "found": found}
        del mdl
        import gc
        gc.collect()

    print()
    print("=" * 100)
    print("③ 判定：哪些 backbone 用 q_proj/v_proj 会「静默不注入」")
    print("=" * 100)
    verdict = {}
    for name, v in rep.items():
        if name == "code_defaults" or "found" not in v:
            continue
        f = v["found"]
        ok = ("q_proj" in f) and ("v_proj" in f)
        verdict[name] = "OK(q_proj/v_proj 存在)" if ok else \
            f"🔴 需改用 {list(f.keys())}"
        print(f"  {'✅' if ok else '🔴'} {name}: {verdict[name]}")
    rep["verdict"] = verdict

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
