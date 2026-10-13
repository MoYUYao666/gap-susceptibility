# -*- coding: utf-8 -*-
r"""加检索协议澄清段（PR R3.4：COCO 随机水平 + BLIP-1 选择性解冻）（2026-10-12）。

## 证据

| 事项 | 归档出处 |
|---|---|
| **COCO 行检索 = 随机水平** | `outputs/coco/rq2_text_only_coco/results.json`（Table 1 的 COCO 行取自该 run）：`R@1 = 0.00019999999494757503` = float32(1/5000)，`R@5 = 5/5000`，`R@10 = 10/5000`；执行口径 `src/dataset.py::create_dataloaders` 对 COCO 令 `test_dataset = val_dataset` 并沿用同一 `max_samples` 上限 |
| **BLIP-1 用选择性解冻** | `experiments/blip2_experiments.py:369` 注释 "BLIP-1 不支持 apply_lora_to_model，改用选择性解冻"，372–380 行只对 `query`/`value` 置 `requires_grad_(True)`；两臂 `n_trainable` **相同 = 196,672,514** |
| **ViT-L 两行也近似随机** | 0.0050 / 0.0025 |

    python tools\_p282_protocol_paragraph.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

PARA = (
    "\n"
    r"\paragraph{Retrieval protocol, and which rows we treat as informative.}"
    r" Three cautions apply to the cross-architecture and cross-dataset columns of "
    r"Table~\ref{tab:position}. First, the MS-COCO rows were evaluated with the validation "
    r"split reused as the retrieval gallery under the same sample cap as training "
    r"(\texttt{src/dataset.py}), and their recorded accuracies are at chance: "
    r"$R@1 = 1/5000$, $R@5 = 5/5000$, $R@10 = 10/5000$. We therefore report the COCO rows as "
    r"gap measurements and do not treat their retrieval column as evidence about retrieval, "
    r"and we report no ODE coefficients for MS-COCO for the same reason "
    r"(Section~\ref{sec:discussion}). Second, the BLIP-1 arms were not produced by LoRA "
    r"injection---BLIP-1 does not support our adapter wrapper, so the runs selectively "
    r"unfreeze the \texttt{query} and \texttt{value} projections instead, and both arms train "
    r"the same $196{,}672{,}514$ parameters. That comparison is therefore about which side is "
    r"unfrozen, not about where an adapter sits, and we exclude it from the adapter-placement "
    r"conclusions. Third, two ViT-L rows are also near chance ($R@1 = 0.0050$ and $0.0025$). "
    r"The claims we make about architecture generality rest on the rows whose retrieval is "
    r"above chance and whose arms differ only in adapter placement; Table~\ref{tab:position} "
    r"now reports $R@1$ for every row so that this filtering is visible to the reader."
    "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    if "Retrieval protocol, and which rows we treat as informative" in t:
        print("  已存在，跳过")
        return 0
    # 插在 tab:position 的表之后（\end{table} 之后）
    idx = t.find(r"\label{tab:position}")
    if idx < 0:
        print("  🔴 找不到 tab:position")
        return 1
    j = t.find(r"\end{table}", idx)
    if j < 0:
        print("  🔴 tab:position 之后找不到 \\end{table}")
        return 1
    j += len(r"\end{table}")
    t2 = t[:j] + "\n" + PARA + t[j:]
    print(f"  插入点：tab:position 的 \\end{{table}} 之后（偏移 {j}）")
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p282")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    ok = ("Retrieval protocol, and which rows we treat as informative" in t3
          and "196{,}672{,}514" in t3 and "1/5000" in t3)
    print(f"  {'✅ 已插入' if ok else '🔴 失败'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
