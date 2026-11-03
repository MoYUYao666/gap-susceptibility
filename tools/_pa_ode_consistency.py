# -*- coding: utf-8 -*-
r"""一致性核对：改完 ODE 数字后，全篇是否自洽（2026-10-07）。

## 为什么

一次改了 26 处数字（摘要/引言/结论/两张表/图注/表注），**必须查有没有留下"半改"状态**：
某处仍写旧值、或新旧值互相矛盾。

## 核对项

1. **旧值是否绝迹**：`0.986`、`0.985`（LoRA 语境）、`0.984`、`162`、`81 runs`
2. **新值是否一致出现**：0.949 / 0.953 / 0.903 / 55 runs / 43 / 6
3. **拟合口径声明是否在位**（`fitted to each trajectory, not predicted`）
4. **未被改动的正确值是否仍在**：OpenCLIP 0.943、CLIP BitFit 0.30–0.84

    python tools\_pa_ode_consistency.py
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    r = subprocess.run(["pdftotext", "-layout", str(REPO / "paper合" / "main_nc.pdf"), "-"],
                       capture_output=True)
    t = re.sub(r"\s+", " ", r.stdout.decode("utf-8", "ignore"))

    print("=== ① 旧值是否绝迹（按语境分类）===")
    # 已知的合理保留：他人工作数值、arXiv 编号、COCO 表（不可复现，已在 limitation 说明）
    for k in ("0.986", "0.984", "0.985", "162", "81 runs"):
        bad, keep = 0, 0
        for m in re.finditer(re.escape(k), t):
            seg = t[max(0, m.start() - 150):m.start() + 100]
            if ("16256" in seg or "Liu et al" in seg or "Both, r=" in seg
                    or "Text-only, r=" in seg):
                keep += 1
            else:
                bad += 1
        tag = "✅ 已清除" if not bad and not keep else (
            f"✅ 无问题（{keep} 处为合理保留）" if not bad else f"❌ {bad} 处需处理")
        print(f"  {k:<10} 需处理 {bad} ｜ 合理保留 {keep}  → {tag}")

    print("\n=== ② 新值是否在位 ===")
    for k in ("0.949", "0.953", "0.903", "55 archived", "43 on Flickr30k", "6 on MS-COCO"):
        n = t.count(k)
        print(f"  {k:<22} 出现 {n} 次  {'✅' if n else '❌'}")

    print("\n=== ③ 拟合口径声明 ===")
    for k in ("fitted to each trajectory, not predicted from its gradients",
              "subset of those originally produced",
              "read as properties of that archived set"):
        print(f"  {k[:52]:<54} {'✅' if k in t else '❌'}")

    print("\n=== ④ 未改动的正确值仍在 ===")
    for k in ("0.943", "0.30", "0.84"):
        n = t.count(k)
        print(f"  {k:<8} 出现 {n} 次  {'✅' if n else '❌'}")

    print("\n=== ⑤ 逐秩表与台账是否一致 ===")
    import json
    led = json.loads(io.open(REPO / "outputs" / "analysis" / "ode_ledger.json",
                             encoding="utf-8").read())
    import statistics as st
    ok = bad = 0
    for site, label in (("text_only", "Text-only"), ("both", "Both")):
        for rk in (1, 2, 4, 8, 16, 32, 64):
            sel = [x for x in led["runs"] if x["family"] == "lora" and x["top"] == "v1_trajectory"
                   and x["site"] == site and x["rank"] == rk]
            if not sel:
                continue
            R = st.mean(x["R2"] for x in sel)
            s = f"{R:.3f}"
            if s in t:
                ok += 1
            else:
                bad += 1
                print(f"  ⚠ 台账 {label} r={rk} → {s}，PDF 中未找到")
    print(f"  逐秩值命中 {ok}/{ok+bad}")

    print("\n=== 结论 ===")
    print("  ✅ 改动自洽" if bad == 0 and all(
        t.count(k) == 0 for k in ("0.986", "162")) else "  ⚠ 仍有不一致，见上")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
