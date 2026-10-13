# -*- coding: utf-8 -*-
r"""搜 `tab:position` 各数字的归档出处（2026-10-10）。

表里：
| Dataset | Text-only | Both | Vision-only |
|---|---|---|---|
| Flickr30k | −0.064 | −0.032 | −0.003 |
| COCO | −0.041 | −0.052 | **+0.031** |

**`+0.031` 在 coco_sweep / coco_sweep_text_only 里都找不到** → 全归档搜。
（`vision_only` 臂在旧 sweep 里没跑过。）

    python tools\_p144_trace_table_values.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "tab_position_provenance.json"

TARGETS = {
    "Flickr30k.text_only": -0.064, "Flickr30k.both": -0.032, "Flickr30k.vision_only": -0.003,
    "COCO.text_only": -0.041, "COCO.both": -0.052, "COCO.vision_only": +0.031,
    "BLIP1.text_only": +0.047, "BLIP1.both": +0.152,
    "ViTL.text_only": -0.036, "ViTL.both": +0.128,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # 收录所有含 centroid_gap 的 results.json
    files = []
    for pat in ("outputs/**/results.json", "outputs/*.json", "paper2/**/results.json",
                "paper/**/results.json", "备选/**/results.json"):
        files += glob.glob(str(REPO / pat), recursive=True)
    files = sorted(set(files))
    print(f"=== 扫描 {len(files)} 个文件 ===")

    found = {k: [] for k in TARGETS}
    for f in files:
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        fg = (d.get("final_gap") or {}).get("centroid_gap")
        ig = (d.get("initial_gap") or {}).get("centroid_gap")
        if fg is None or ig is None:
            continue
        v = fg - ig
        for tag, t in TARGETS.items():
            if abs(v - t) < 5e-4:
                found[tag].append(str(Path(f).relative_to(REPO)))

    print("\n=== 各表值的归档出处 ===")
    for tag, t in TARGETS.items():
        hits = found[tag]
        mark = "✅" if hits else "❌"
        print(f"  {mark} {tag:<26} {t:+.4f}  → {len(hits)} 处")
        for h in hits[:3]:
            print(f"       {h}")

    print("\n=== 未找到出处的（这些数字需要处理）===")
    missing = [t for t in TARGETS if not found[t]]
    for t in missing:
        print(f"  ❌ {t} = {TARGETS[t]:+.4f}")
    if not missing:
        print("  （全部有出处）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"targets": TARGETS, "found": found,
             "missing": {t: TARGETS[t] for t in missing},
             "n_files_scanned": len(files)}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
