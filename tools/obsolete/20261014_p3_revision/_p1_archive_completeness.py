# -*- coding: utf-8 -*-
r"""归档完整性核查：能否从现有数据复现正文的 in-sample R²=0.986（2026-10-07）。

## 为什么必须做

`_p1_ode_loco2.py` / `_p1_ode_r2_caliber.py` 得到 LoRA in-sample R² = **0.949（逐 run）/ 0.964（种子均值）**，
而正文（`validation.tex:102`）写 **`CLIP + Flickr30k + LoRA  R² = 0.985 ± 0.008`（81 runs）**、
`conclusion.tex` 写 **mean 0.986（range 0.978–0.997）**。

**差异必须查清**，因为它决定：
1. 我的"拟合 vs 预测"结论是否成立；
2. **归档是否完整**（正文的 162 runs 是否能从 `outputs/` 复现）。

## 本脚本做三件事

1. **逐子集**算 R²（按方法 / 数据集 / 位置 / 秩），找是否有子集接近 0.985–0.997；
2. **对齐正文的逐秩表**（`validation.tex:61-66`：r=2→0.975、r=64→0.981 等）看能否复现；
3. **统计归档 run 数 vs 正文声称的 81+81**。

    python tools\_p1_archive_completeness.py
"""
from __future__ import annotations

import glob
import io
import json
import re
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

try:
    import numpy as np
except Exception:
    np = None


def r2(y, yh):
    y = np.asarray(y, float); yh = np.asarray(yh, float)
    ss = float(((y - y.mean()) ** 2).sum())
    return 1.0 - float(((y - yh) ** 2).sum()) / ss if ss > 0 else float("nan")


def grid_fit(t, y):
    t = np.asarray(t, float); y = np.asarray(y, float)
    dg0 = float(y[0]); r = y - dg0
    best = (float("nan"), float("nan"), float("inf"))
    for logb in np.linspace(np.log10(0.005), np.log10(20.0), 800):
        b = 10.0 ** logb
        u = 1.0 - np.exp(-b * t)
        den = float((u * u).sum())
        if den < 1e-12:
            continue
        a = float((u * r).sum()) / den
        resid = float(((r - a * u) ** 2).sum())
        if resid < best[2]:
            best = (a * b, b, resid)
    A, B, _ = best
    return float(A), float(B), r2(y, dg0 + (A / B) * (1.0 - np.exp(-B * t)))


def main() -> int:
    if np is None:
        print("  ❌ 需要 numpy"); return 1

    rows = []
    for f in sorted(glob.glob(str(REPO / "outputs/theory/**/dg_star_history.json"), recursive=True)):
        rel = Path(f).relative_to(REPO / "outputs" / "theory")
        top = rel.parts[0]
        conf = "/".join(rel.parts[:-2])
        d = json.loads(io.open(f, encoding="utf-8").read())
        if len(d["epochs"]) < 5:
            continue
        low = conf.lower()
        fam = ("adapter" if "adapter" in low
               else "full_ft" if ("full_ft" in low or "fullft" in low) else "lora")
        site = ("text_only" if "text_only" in low else
                "vision_only" if "vision_only" in low else "both")
        m = re.search(r"_r(\d+)$|_d(\d+)$", low)
        rows.append(dict(top=top, conf=conf, fam=fam, site=site,
                         rank=int(m.group(1) or m.group(2)) if m else None,
                         ep=d["epochs"], y=d["dg_star"],
                         A=grid_fit(d["epochs"], d["dg_star"])[0],
                         B=grid_fit(d["epochs"], d["dg_star"])[1],
                         R=grid_fit(d["epochs"], d["dg_star"])[2]))

    print(f"  === 归档统计 ===")
    print(f"  dg_star_history.json 可用 run: {len(rows)}")
    import collections
    print("  按目录:", dict(collections.Counter(r['top'] for r in rows)))
    print("  按方法:", dict(collections.Counter(r['fam'] for r in rows)))
    print()
    print("  正文声称: Flickr30k 81 runs ｜ COCO 81 runs ｜ 合计 **162**")
    print(f"  实测合计: **{len(rows)}** → 差额 {162 - len(rows)}")

    print(f"\n  === 逐子集 in-sample R²（看哪个口径能到 0.985）===")
    def sub(name, pred):
        s = [r for r in rows if pred(r)]
        rs = [r["R"] for r in s if r["R"] == r["R"]]
        if not rs:
            print(f"    {name:<42} 无样本"); return
        print(f"    {name:<42} n={len(rs):<3} 平均 {st.mean(rs):.4f}  "
              f"中位 {st.median(rs):.4f}  范围 {min(rs):.3f}–{max(rs):.3f}")
    sub("全部 run", lambda r: True)
    sub("LoRA 全部", lambda r: r["fam"] == "lora")
    sub("LoRA + Flickr30k（v1_trajectory）", lambda r: r["fam"] == "lora" and r["top"] == "v1_trajectory")
    sub("LoRA + Flickr30k（beta_pilot）", lambda r: r["fam"] == "lora" and r["top"] == "beta_pilot")
    sub("LoRA + COCO", lambda r: r["fam"] == "lora" and r["top"] == "coco")
    sub("Adapter", lambda r: r["fam"] == "adapter")
    sub("full-FT", lambda r: r["fam"] == "full_ft")

    print(f"\n  === 对齐正文逐秩表（validation.tex:61-66，Flickr30k both 位）===")
    print("    正文: r=2 → 0.975 ｜ r=64 → 0.981")
    byrank = collections.defaultdict(list)
    for r in rows:
        if r["fam"] == "lora" and r["top"] == "v1_trajectory" and r["site"] == "both" and r["rank"]:
            byrank[r["rank"]].append(r["R"])
    for k in sorted(byrank):
        v = byrank[k]
        print(f"    实测 r={k:<3} n={len(v)} → 平均 R² = {st.mean(v):.4f}")

    print(f"\n  === 结论 ===")
    lora = [r["R"] for r in rows if r["fam"] == "lora" and r["R"] == r["R"]]
    m = st.mean(lora)
    print(f"    LoRA 全部 run 平均 R² = {m:.4f}（正文 0.985–0.986）")
    print(f"    {'✅ 可复现' if abs(m - 0.985) < 0.01 else '⚠ **不可复现**：本地归档与正文声称存在差距'}")
    if abs(m - 0.985) >= 0.01:
        print("    → 说明正文的 162 runs **未全部归档**于 `outputs/theory/`，"
              "或正文用了**不同的拟合口径**（如含 OpenCLIP/SigLIP 或按 epoch 平均）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
