# -*- coding: utf-8 -*-
r"""清点本地可用骨干及其 **patch size**（2026-10-07，实验 ③ 的前置）。

论文的"patch size 规律"需要**更多 patch-16 骨干**。本脚本列出本地每个模型能否加载、
其视觉塔 patch size、是否为双塔对比模型——据此决定先跑谁。

    python tools\_p6_inventory_backbones.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODELS = REPO / "models"


def probe(name: str) -> dict:
    d = MODELS / name
    cfgp = d / "config.json"
    out = {"name": name, "path": str(d), "exists": d.exists(), "patch": None, "type": None}
    if not cfgp.exists():
        return out
    try:
        cfg = json.loads(cfgp.read_text(encoding="utf-8"))
    except Exception as e:
        out["error"] = str(e)[:60]
        return out
    out["type"] = cfg.get("model_type", "?")
    vc = cfg.get("vision_config", {}) or {}
    out["patch"] = vc.get("patch_size")
    out["image_size"] = vc.get("image_size")
    out["hidden"] = vc.get("hidden_size")
    return out


def main() -> int:
    rows = [probe(p.name) for p in sorted(MODELS.iterdir()) if p.is_dir()]
    print(f"  {'模型':<34} {'type':<22} {'patch':>6} {'img':>6} 双塔?")
    print("  " + "-" * 78)
    cliplike = []
    for r in rows:
        dual = r["type"] in ("clip", "siglip", "open_clip", "chinese_clip")
        mark = "✅" if dual else ""
        if dual:
            cliplike.append(r)
        print(f"  {r['name']:<34} {str(r['type']):<22} {str(r['patch']):>6} "
              f"{str(r.get('image_size')):>6} {mark}")

    print("\n  === 可用于 patch-size 对照的双塔骨干 ===")
    by_patch = {}
    for r in cliplike:
        by_patch.setdefault(r["patch"], []).append(r["name"])
    for p in sorted(by_patch, key=lambda x: (x is None, x)):
        print(f"    patch={p}: {by_patch[p]}")

    print("\n  === 与论文现有 7 配置的对照 ===")
    print("    论文 patch-32 组: CLIP B/32、(另 4 个)  → 规律：text-only 的 gap 变化最小")
    print("    论文 patch-16 组: CLIP B/16、BioCLIP   → 规律：both 的 gap 变化最小")
    print(f"    本地可再加 patch-16: {by_patch.get(16, ['（无）'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
