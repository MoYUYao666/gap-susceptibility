# -*- coding: utf-8 -*-
r"""核实 a1_rr_ckpt 的逐 epoch 检查点是否可用于 τ 组内检验（2026-10-12）。

## 目的（方案②）

现归档只有 `epoch10.pt` 被评测 → 每个数据集仅 3 个点（3 seed）。
若 `epoch1..9` 的权重**确实不同**，则可评 10 个 epoch → **每个数据集 30 个检查点**
→ 组内 τ 相关可用 n=30 检验（现在 n=3 不可靠）。

**本脚本**：逐张量比较 epoch 之间的 lora_state_dict，确认权重在变。

    python tools\_p213_ckpt_verify.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASE = REPO / "outputs" / "a1_rr_ckpt"
OUT = REPO / "outputs" / "analysis" / "a1_ckpt_verify.json"


def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if hasattr(v, "shape"):
            out[key] = v
        elif isinstance(v, dict):
            out.update(flatten(v, key + "."))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    try:
        import torch
    except Exception as e:
        print(f"  ❌ torch 不可用: {e}")
        return 1

    res = {}
    for ds in ("coco", "dtd", "food101", "flickr30k_ref"):
        d0 = BASE / ds
        if not d0.exists():
            continue
        print("=" * 84)
        print(f"数据集 {ds}（{d0.relative_to(REPO)}）")
        print("=" * 84)
        sds = {}
        for e in range(1, 11):
            p = d0 / f"epoch{e}.pt"
            if not p.exists():
                print(f"  ❌ epoch{e}.pt 缺失")
                continue
            d = torch.load(str(p), map_location="cpu", weights_only=False)
            if e == 1:
                cfg = d.get("config", {})
                print(f"  config: dataset={cfg.get('dataset')} seed={cfg.get('seed')} "
                      f"pairs={cfg.get('pairs')} epochs={cfg.get('epochs')} "
                      f"lr={cfg.get('lr')} rank={cfg.get('rank')} "
                      f"vision={cfg.get('vision_lora')} text={cfg.get('text_lora')}")
                print(f"  config 全键: {list(cfg.keys())}")
            sds[e] = flatten(d.get("lora_state_dict", {}))
        if 1 not in sds:
            continue
        k0 = sorted(sds[1])
        print(f"  展平后张量数: {len(k0)}")
        print(f"  {'epoch':<7}{'与 epoch1 不同的张量':>22}{'判定':>10}")
        diffs = {}
        for e in sorted(sds):
            if e == 1:
                continue
            n = sum(1 for k in k0 if k in sds[e] and not torch.equal(sds[1][k], sds[e][k]))
            diffs[e] = n
            print(f"  {e:<7}{n:>16}/{len(k0):<5}{'✅ 在变' if n else '🔴 相同':>10}")
        # 相邻 epoch 之间
        print()
        print("  相邻 epoch 差异（确认是连续演化而非跳变）:")
        for e in range(2, 11):
            if e in sds and (e - 1) in sds:
                n = sum(1 for k in k0 if k in sds[e] and k in sds[e - 1]
                        and not torch.equal(sds[e - 1][k], sds[e][k]))
                print(f"    epoch{e-1}→{e}: {n}/{len(k0)} 不同")
        res[ds] = {"n_tensors": len(k0), "diff_vs_epoch1": diffs,
                   "usable": all(v > 0 for v in diffs.values()) if diffs else False}
        print()

    print("=" * 84)
    print("判定")
    print("=" * 84)
    for ds, v in res.items():
        print(f"  {ds:<16} {'✅ 可用于逐 epoch 评测' if v['usable'] else '🔴 权重未变，不可用'}")
    ok = sum(1 for v in res.values() if v["usable"])
    print(f"\n  → {ok}/{len(res)} 个数据集可用；**无需新训练**"
          if ok else f"\n  → 全部不可用，必须新训练")

    print()
    print("=" * 84)
    print("实现说明（若可行）")
    print("=" * 84)
    print("  评测脚本 `tools/a1_h_offset.py` 写死了 epoch10:")
    for ln in io.open(REPO / "tools" / "a1_h_offset.py", encoding="utf-8",
                      errors="replace").read().splitlines():
        if "epoch10.pt" in ln:
            print(f"    {ln.strip()[:100]}")
    print("  → 需参数化 epoch 后逐 epoch 评测（纯 forward，无训练）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
