# -*- coding: utf-8 -*-
r"""修 introduction / related_work / conclusion 的过期主张（2026-10-13）。

## 扫描（`tools/_p497`）抓出的真矛盾

| 文件:行 | 旧主张 |
|---|---|
| `conclusion.tex:7` | *"reduces allocation uncertainty by **$30\\times$**"* |
| `conclusion.tex:7` | *"**190 runs** (181 sweep runs plus 9…)"* |
| `conclusion.tex:7` | 三区制 *"safe ($r<6$), damaging, collapse ($r\\geq24$)"* + *"robust across sample sizes 16 to 256"*（未加协议限定） |
| `introduction.tex:18` | *"confirms an alignment **phase transition at $r_c$**"* |
| `introduction.tex:18` | *"demonstrating **architecture-dependent** diagnostic capability"* |
| `introduction.tex:18` | *"**190 runs** (181 sweep runs plus…)"* |
| `related_work.tex:21` | *"Our **alignment phase transition at** …"* |
| `theory.tex:230` | *"The critical rank $r_c$ is **architecture-dependent**"* |

**并核出我的两条判据**假阳性**（应改写规则而非改稿）：
- `discussion.tex:5` 的 *"not that it admits **exactly one** unconditionally"* —— **是否定式**，正确
- `experiments.tex:149` 的 *"**Finding 2: Architecture-dependent** …"* —— 需人工判断是否已撤回

    python tools\_p498_fix_stale_intro_concl.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee" / "sections"
IN = PI / "introduction.tex"
RW = PI / "related_work.tex"
CO = PI / "conclusion.tex"
TH = PI / "theory.tex"

# ---------- introduction ----------
IN_OLD = None  # 用正则定位整条 item


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    changes = []

    # ① introduction：定位 "Experimental validation" 那条 item，整条替换
    t = io.open(IN, encoding="utf-8", errors="replace").read()
    m = re.search(r"\\item \\textbf\{Experimental validation\}.*?(?=\n\s*\\item|\n\s*\\end\{)", t, re.S)
    if m:
        old = m.group(0)
        new = (
            r"\item \textbf{Experimental validation} (Sec.~\ref{sec:experiments}): zero-shot"
            "\n"
            r"Predictive Transfer on LLaVA-1.5-7B brackets a crossing in the alignment energy at"
            "\n"
            r"$r \in [5,6]$, and we report it as bracketed rather than sharp: the interval at"
            "\n"
            r"$r=5$ spans zero and an exact permutation test between neighbouring ranks is not"
            "\n"
            r"significant. The crossing is a property of the measurement protocol---blank images,"
            "\n"
            r"$16$ training samples, 4-bit QLoRA---rather than a model-independent constant, and it"
            "\n"
            r"does not reappear under real image--text pairs at the scales we could run. Under a"
            "\n"
            r"matched trainable-parameter budget the allocation we derive beats the uniform-rank"
            "\n"
            r"baseline at one learning rate, reverses at another, and is indistinguishable from a"
            "\n"
            r"random allocation of the same budget; an adaptive baseline (AdaLoRA) reaches lower"
            "\n"
            r"alignment energy than any of our arms once both sides are swept over the same rates,"
            "\n"
            r"so we present the rule as a zero-shot heuristic rather than as an optimum."
        )
        changes.append((IN, old, new, "introduction 的实验验证条"))

    # ② related_work：phase transition 措辞
    t = io.open(RW, encoding="utf-8", errors="replace").read()
    m = re.search(r"Our alignment phase transition at[^.]*\.", t, re.S)
    if m:
        changes.append((RW, m.group(0),
                        "Our crossing in the alignment energy satisfies the same bracketing "
                        "description, though we do not claim it is sharp.", "related_work 的相变句"))

    # ③ conclusion：整条"Experimental validation confirms…"句
    t = io.open(CO, encoding="utf-8", errors="replace").read()
    m = re.search(r"Experimental validation confirms these predictions through[^.]*\.[^.]*\.", t, re.S)
    if m:
        changes.append((CO, m.group(0),
                        "Experimental validation covers 126 runs on the present protocol plus the "
                        "capacity-matched allocation study reported in Section~IV. We bracket the "
                        "crossing in the alignment energy at $r \\in [5,6]$ without claiming it is "
                        "sharp, and we report that the allocation derived from $\\Gamma$ is "
                        "indistinguishable from a random allocation of the same parameter budget "
                        "and is beaten on alignment energy by an adaptive baseline swept over the "
                        "same learning rates.",
                        "conclusion 的 190 runs + 30× 句"))

    # ④ theory L230：architecture-dependent 的预测
    t = io.open(TH, encoding="utf-8", errors="replace").read()
    m = re.search(r"The critical rank \$r_c\$ is architecture-dependent[^.]*\.", t, re.S)
    if m:
        changes.append((TH, m.group(0),
                        "The critical rank $r_c$ should depend on the model's modality balance, "
                        "although we were unable to verify this prediction: the apparent "
                        "architecture dependence we first observed did not survive a change of "
                        "visual budget.", "theory 的 r_c 架构相关预测"))

    print(f"  计划改动 {len(changes)} 处：")
    for p, old, new, label in changes:
        print(f"     {p.name:<18} {label}（{len(old)} → {len(new)} 字符）")
    if not a.apply:
        print("  （预演）")
        return 0
    done = 0
    for p, old, new, label in changes:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if t.count(old) != 1:
            print(f"  ⚠️ {p.name}: {label} 命中 {t.count(old)}，跳过")
            continue
        bak = p.with_suffix(".tex.bak_p498")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
        done += 1
    print(f"  ✅ 已改 {done}/{len(changes)} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
