# -*- coding: utf-8 -*-
r"""核实：a1_rr_ckpt 的 10 个 epoch 检查点能否直接用于 τ 组内检验（2026-10-12）。

## 为什么这是关键

`outputs/a1_rr_ckpt/{coco,dtd,flickr30k_ref}/epoch{1..10}.pt` **都在**
（每个 ~2 MB），但 `a1_h_offset.json` 只用了 `epoch10.pt`。

**→ 若 epoch1-9 的权重可加载，则每个数据集可评 10 个检查点（而非 3 个 seed）
→ 组内 τ 相关可用 n=10 检验（现在 n=3 不可靠）**
**→ 不需要新训练。**

    python tools\_p212_ckpt_inventory.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "a1_ckpt_inventory.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 88)
    print("① a1_rr_ckpt 全部文件（按数据集）")
    print("=" * 88)
    inv = {}
    for f in sorted(glob.glob(str(REPO / "outputs" / "a1_rr_ckpt" / "**" / "*.pt"),
                             recursive=True)):
        p = Path(f)
        ds = p.parent.name
        inv.setdefault(ds, []).append(p.name)
    for ds, fs in sorted(inv.items()):
        print(f"  {ds:<16} {len(fs)} 个: {sorted(fs, key=lambda x: int(''.join(c for c in x if c.isdigit()) or 0))}")

    print()
    print("=" * 88)
    print("② 检查点内容（用 torch 加载看键）")
    print("=" * 88)
    try:
        import torch
        f = REPO / "outputs" / "a1_rr_ckpt" / "coco" / "epoch1.pt"
        sd = torch.load(str(f), map_location="cpu", weights_only=False)
        print(f"  {f.name}: {type(sd).__name__}")
        if isinstance(sd, dict):
            keys = list(sd.keys())
            print(f"  顶层键（{len(keys)}）: {keys[:12]}")
            for k in keys[:6]:
                v = sd[k]
                if hasattr(v, "shape"):
                    print(f"    {k}: tensor{v.shape}")
                elif isinstance(v, dict):
                    print(f"    {k}: dict({len(v)} 键) 例: {list(v.keys())[:4]}")
                else:
                    print(f"    {k}: {type(v).__name__} = {str(v)[:80]}")
        # 与 epoch10 对比，确认不同
        f10 = REPO / "outputs" / "a1_rr_ckpt" / "coco" / "epoch10.pt"
        sd10 = torch.load(str(f10), map_location="cpu", weights_only=False)
        if isinstance(sd, dict) and isinstance(sd10, dict):
            common = set(sd) & set(sd10)
            diff = 0
            for k in list(common)[:200]:
                va, vb = sd[k], sd10[k]
                if hasattr(va, "shape") and hasattr(vb, "shape") and va.shape == vb.shape:
                    if not torch.equal(va, vb):
                        diff += 1
            print(f"\n  与 epoch10 对比：{diff}/{min(len(common), 200)} 个张量不同 "
                  f"→ {'✅ 权重确实在变，可用于组内检验' if diff else '🔴 相同（无信息）'}")
    except Exception as e:
        print(f"  ❌ 加载失败: {type(e).__name__}: {e}")

    print()
    print("=" * 88)
    print("③ 论文用的评测脚本")
    print("=" * 88)
    for cand in ("tools/a1_h_offset.py", "tools/a1_h_offset_common.py"):
        p = REPO / cand
        if p.exists():
            t = io.open(p, encoding="utf-8", errors="replace").read()
            print(f"  ✅ {cand}（{len(t.splitlines())} 行）")
            # 找它扫哪些 epoch
            for ln in t.splitlines():
                if "epoch" in ln.lower() and ("glob" in ln or "ckpt" in ln.lower()):
                    print(f"       {ln.strip()[:110]}")
        else:
            print(f"  ❌ {cand}")
    # 找其它可能的评测脚本
    print()
    print("  ── 含 'a1_rr_ckpt' 的脚本 ──")
    for f in sorted(glob.glob(str(REPO / "tools" / "*.py"))):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        if "a1_rr_ckpt" in t:
            print(f"     {Path(f).name}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {ds: sorted(fs) for ds, fs in inv.items()}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
