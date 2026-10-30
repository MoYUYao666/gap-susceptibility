# -*- coding: utf-8 -*-
r"""核 `p3-downstream` 的两处自查修复（2026-10-13）。

## 待核

1. **逐 run 自带超参**（原先只写在顶层 `protocol`，续跑改超参会静默误标旧 run）
2. **`_p472` 逐行加 `device`** + 设备一致性守卫（CPU↔GPU 的 bf16 E0 差 0.09%）
3. **`p3d_summary.json` 加 `source_fingerprint`**（源文件 sha256 + 条数）与 `derived_note`
4. **`p3d_*_ranksweep.json` 是否真的"只增不改"**（逐 run 自带超参）

    python tools\_p469_verify_source_hygiene.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import io
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3d_source_hygiene.json"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 100)
    print("① 逐 run 是否自带超参（来源文件必须自带，不能只靠顶层 protocol）")
    print("=" * 100)
    for f in ("p3d_clip_ranksweep.json", "p3d_qwen_ranksweep.json",
              "p3d_qwen_ranksweep_mp50176.json"):
        p = REPO / "outputs" / "analysis" / f
        if not p.exists():
            print(f"  ⚠️ 缺 {f}")
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        runs = d.get("runs") or []
        if not runs:
            print(f"  {f}: runs 为空")
            continue
        k0 = set(runs[0].keys())
        hp = [k for k in ("lr", "epochs", "batch", "dtype", "max_pixels", "min_pixels",
                          "device", "lora_targets", "n_train") if k in k0]
        print(f"  {f}")
        print(f"      runs={len(runs)} ｜ 逐 run 自带超参键: {sorted(hp)}")
        top = d.get("protocol") or {}
        print(f"      顶层 protocol 存在: {bool(top)}（{len(top)} 键）")
        # 逐 run 是否都带 device
        dev = {r.get("device") for r in runs if "device" in r}
        print(f"      逐 run device 取值: {dev if dev else '（无该键）'}")
        rep[f] = {"n_runs": len(runs), "per_run_hp": sorted(hp),
                  "protocol_keys": len(top), "devices": sorted(x for x in dev if x)}

    print()
    print("=" * 100)
    print("② summary 是否带 source_fingerprint，且指纹与实际源文件逐位一致")
    print("=" * 100)
    for f in ("p3d_summary.json", "p3d_qwen_summary.json"):
        p = REPO / "outputs" / "analysis" / f
        if not p.exists():
            print(f"  ⚠️ 缺 {f}")
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        fp = d.get("source_fingerprint")
        note = d.get("derived_note")
        print(f"  {f}")
        print(f"      source_fingerprint 存在: {bool(fp)} ｜ derived_note: {str(note)[:80]}")
        if isinstance(fp, dict):
            for src, meta in fp.items():
                sp = REPO / src
                if not sp.exists():
                    sp2 = REPO / "outputs" / "analysis" / os.path.basename(src)
                    sp = sp2 if sp2.exists() else sp
                if sp.exists():
                    real = sha256(sp)
                    want = meta.get("sha256") if isinstance(meta, dict) else meta
                    ok = (real == want)
                    print(f"         {'✅' if ok else '🔴'} {src}")
                    print(f"             记录 {str(want)[:24]}… ｜ 实际 {real[:24]}…")
                    if isinstance(meta, dict) and "n_runs" in meta:
                        dd = json.loads(io.open(sp, encoding="utf-8", errors="replace").read())
                        n_real = len(dd.get("runs") or [])
                        print(f"             条数 记录 {meta['n_runs']} ｜ 实际 {n_real}"
                              f" {'✅' if meta['n_runs'] == n_real else '🔴'}")
                else:
                    print(f"         ⚠️ 源文件不在: {src}")
        rep[f] = {"has_fingerprint": bool(fp), "has_note": bool(note)}

    print()
    print("=" * 100)
    print("③ `_p472` 的 rows 是否逐行带 device")
    print("=" * 100)
    for f in sorted(glob.glob(str(REPO / "outputs/analysis/p3d_e0_vs_token_budget*.json"))):
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        rows = d.get("rows") or []
        has = [("device" in r) for r in rows]
        print(f"  {os.path.basename(f):<52} rows={len(rows)} ｜ 逐行 device: "
              f"{'✅ 全部' if has and all(has) else ('🔴 部分/无' if rows else '—')} "
              f"｜ 顶层 device={d.get('device')}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
