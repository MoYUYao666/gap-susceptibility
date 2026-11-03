# -*- coding: utf-8 -*-
r"""查各组原始 run 的准确配置（batch / epochs / samples / model）（2026-10-10）。

## 为什么关键

补 seed **必须与已有 run 同配置**，否则新旧混在一起就是混淆变量。
实测已发现：`strict_freeze_b32_r4` 用 **batch 128**，而 `strict_freeze_oclip/r4` 用 **batch 64**。

    python tools\_p166_config_audit.py
"""
from __future__ import annotations

import glob
import io
import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

GROUPS = [
    ("strict_freeze_b32_r4", "outputs/strict_freeze_b32_r4/**/results.json"),
    ("strict_freeze_b16/r4", "outputs/strict_freeze_b16/r4/**/results.json"),
    ("strict_freeze_oclip/r4", "outputs/strict_freeze_oclip/r4/**/results.json"),
    ("coco_sweep_text_only", "outputs/coco_sweep_text_only/**/results.json"),
    ("coco_sweep (both)", "outputs/coco_sweep/**/results.json"),
    ("adapter", "outputs/adapter/**/results.json"),
    ("beta_pilot", "outputs/theory/beta_pilot/**/results.json"),
    ("coco (old)", "outputs/coco/coco_*/**/results.json"),
]

KEYS = ("batch_size", "epochs", "max_samples", "elapsed_sec", "strict_freeze",
        "n_trainable_params")


def main() -> int:
    print("=" * 86)
    print("各组配置（按 (组, 臂) 汇总；不同值会列全）")
    print("=" * 86)
    for tag, pat in GROUPS:
        fs = sorted(glob.glob(str(REPO / pat), recursive=True))
        if not fs:
            print(f"\n── {tag}: 无文件")
            continue
        by = defaultdict(lambda: defaultdict(set))
        for f in fs:
            try:
                d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            except Exception:
                continue
            parts = Path(f).parts
            arm = next((x for x in parts if x in ("text_only", "both", "vision_only")),
                       parts[-2])
            for k in KEYS:
                v = d.get(k)
                if v is not None:
                    by[arm][k].add(v if not isinstance(v, float) else round(v, 1))
        print(f"\n── {tag}（{len(fs)} run）")
        for arm in sorted(by):
            vals = []
            for k in ("batch_size", "epochs", "max_samples", "strict_freeze"):
                s = by[arm].get(k, set())
                if s:
                    vals.append(f"{k}={sorted(s)}")
            el = sorted(by[arm].get("elapsed_sec", set()))
            if el:
                vals.append(f"elapsed≈{el[0]}–{el[-1]}s" if len(el) > 1 else f"elapsed={el[0]}s")
            print(f"   {arm:<12} " + " ｜ ".join(str(v) for v in vals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
