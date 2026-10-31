# -*- coding: utf-8 -*-
r"""核 `source_fingerprint` 的 sha256 是否与实际源文件逐位一致（修正我的检查写法）（2026-10-13）。

## 我上一版检查错在哪

`source_fingerprint` 是**扁平结构** `{"file": ..., "sha256": ..., "n_runs": ...}`，
我把它当成"文件名 → 元数据"的映射去遍历 ⇒ 把 `file`/`sha256`/`n_runs` **当成了文件名** ⇒ 假报"源文件不在"。
**这是"检查串/判据写错"的第 N 次**（本阶段同类错误已多次）。

    python tools\_p470_verify_fingerprint.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AD = REPO / "outputs" / "analysis"


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
    print("=" * 100)
    print("逐位核 sha256 与条数")
    print("=" * 100)
    allok = True
    for name in ("p3d_summary.json", "p3d_qwen_summary.json"):
        p = AD / name
        if not p.exists():
            print(f"  ⚠️ 缺 {name}")
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        fp = d.get("source_fingerprint") or {}
        src = AD / str(fp.get("file"))
        print(f"  ── {name} ──")
        print(f"     指向源文件: {fp.get('file')} ｜ 存在 {src.exists()}")
        if not src.exists():
            allok = False
            continue
        real = sha256(src)
        want = str(fp.get("sha256"))
        ok_sha = real == want
        sd = json.loads(io.open(src, encoding="utf-8", errors="replace").read())
        n_real = len(sd.get("runs") or [])
        ok_n = (fp.get("n_runs") == n_real)
        allok = allok and ok_sha and ok_n
        print(f"     {'✅' if ok_sha else '🔴'} sha256 一致")
        print(f"         记录 {want[:32]}…")
        print(f"         实际 {real[:32]}…")
        print(f"     {'✅' if ok_n else '🔴'} 条数一致（记录 {fp.get('n_runs')} ｜ 实际 {n_real}）")
        print()

    print("=" * 100)
    print("逐 run 的 device 混合（qwen ranksweep 有 cpu+cuda）")
    print("=" * 100)
    p = AD / "p3d_qwen_ranksweep.json"
    d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
    from collections import Counter
    c = Counter(r.get("device") for r in (d.get("runs") or []))
    print(f"  device 分布: {dict(c)}")
    for r in (d.get("runs") or []):
        if r.get("device") == "cpu":
            print(f"     唯一的 cpu run: condition={r.get('condition')} rank={r.get('rank')} "
                  f"seed={r.get('seed')} ｜ 有 delta_E: {isinstance(r.get('dE_train'), (int, float))}")
    print("  ⇒ 若 cpu 那条是**冻结基线**（无训练），则混合是设计如此；否则须核实")

    print()
    print(f"  **判定：{'✅ 指纹全部逐位一致' if allok else '🔴 有指纹不一致'}**")
    return 0 if allok else 2


if __name__ == "__main__":
    raise SystemExit(main())
