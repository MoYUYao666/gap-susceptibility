# -*- coding: utf-8 -*-
r"""落账：A 的 OOM 修复 + `inner` 取得真实值（2026-10-08 19:30）。

    python tools\_docs_a_oom_fix.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-08 19:30 —— A 的 OOM 已修，`inner` 终于取到真实值**
>
> ### 第五次尝试：先 OOM，再修好
>
> **故障**（第一次运行）：
> ```
> [Epoch 1 完成] → capture_inner → torch.OutOfMemoryError:
> GPU 0 总容量 8.00 GiB，0 字节空闲；PyTorch 已分配 21.15 GiB
> ```
>
> **根因**：`capture_inner` 在 `torch.enable_grad()` 下对**最多 8 个验证批**前向，
> **把每批的嵌入与计算图都留在列表里**；此时**训练循环的图尚未释放** → 叠加超 8 GB。
>
> **修法**（`tools/_p46_fix_alpha_oom.py`，三处，均不影响动力学）：
> 1. 梯度版**只取 2 批**（∇DG\\* 是期望的估计，128 样本足够）；
> 2. `backward()` 后立即 `del` 中间量；
> 3. 每 epoch 后 `torch.cuda.empty_cache()`。
>
> **口径未变**：`DG*` 轨迹仍由 `_compute_dg_star_record` 在**全验证集**上单独测（`no_grad`），
> **只有 `∇DG*` 的估计样本数减少**——属估计成本的取舍，**不是口径变更**。
>
> ### ✅ 修复后实测（`outputs/_alpha_A_full2.log`）
>
> ```
> ep  1 loss=4.1519 lr=9.76e-05 inner=-2.561e+00 DG*=1.8799
> ep  2 loss=3.8984 lr=9.05e-05 inner=-1.975e+00 DG*=1.7949
> ep  3 loss=3.4479 lr=7.94e-05 inner=-2.468e+00 DG*=1.7157
> ```
>
> - **`inner` 为负**（−2.0 ~ −2.6）→ `α̂ = −η̄·mean(inner) > 0`，**符号方向正确**
>   （`DG*` 确实在下降：1.88 → 1.72）；
> - **`inner` 取得值**：`[capture_inner] 用 397 对，跳过 1 个`（每 epoch 打印一次）。
>
> ### 这一条的教训（本阶段反复出现的同一类）
>
> **我先开跑，后验证。** `lr` 扫描与 OOM 都是"跑起来才发现"。
> 但这次 **OOM 是在 epoch 1 结束时报出的**，**只损失约 4 min**（而非 1 h）——
> 因为我把梯度测量放在**每 epoch 末尾**，故障自然早暴露。
> **→ 有意的设计：把高风险的测量放在每 epoch 的早段/末尾，让故障尽早暴露。**
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "A 的 OOM 已修" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("A 的 OOM 已修", "21.15 GiB", "inner=-2.561e+00", "符号方向正确",
              "把高风险的测量放在每 epoch 的早段/末尾"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
