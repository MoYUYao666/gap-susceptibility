# -*- coding: utf-8 -*-
r"""把 2026-10-03 晚的阶段追加进 HANDOFF.md（停止实验 + 来源审计）。

    python tools\_docs_20261003_night.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **🛑 2026-10-03 晚 —— 停止实验 + 按「来源必须明确」审计全稿数字**
>
> **操作者指示**：*所有数据必须真实来源明确；不确定的可以重跑；不确定的删除；先停止实验。*
>
> ### ① 实验已停
>
> `job_kill` + `Stop-Process`，**无残留 python 进程、GPU 已释放**。
> 今晚那批（SigLIP/OpenCLIP r4 + CLIP r1/r64）**断点 0/10、0/10、0/6**（SigLIP 首个 run 未产出结果）。
> 续跑仍是同一条命令：`python tools\_run_tonight_6.py --apply`（幂等）。
>
> ### ② 图来源审计（新档 `docs/PAPERA_FIGURE_PROVENANCE.md`）
>
> 脚本 `tools/_audit_figure_provenance.py`。**12 张图中只有 3 张来源明确**：
>
> | 类 | 数量 | 说明 |
> |---|---|---|
> | ✅ 本轮从 `outputs/` 的 JSON 重绘、脚本在 `tools/` | **3** | `fig2.png`、`fig8_weight_svd.png`、`fig9_noise_sensitivity.png` |
> | 🔁 来源不明但**数据源仍在**（可写脚本重绘） | **7** | `fig1`、`fig1_ode_fits`、`fig3`、`fig4`、`fig10_layered_ft`、`fig12_zeroshot_more`、`fig14_adapter_layered` |
> | ❌ 来源不明且**无法复算** | **2** | `fig2_v5_falsification`、`fig4_effective_rank` |
>
> 根因：这些图由 **2026-08-02 的脚本**产出，而 **`paper合/scripts/` 不存在**。
>
> ### ③ `k = 0.043` 的调查（新档 `docs/K043_INVESTIGATION.md`）
>
> **它是全文唯一未满足「来源明确」标准的数字**，四条已核实事实：
>
> | # | 事实 | 证据 |
> |---|---|---|
> | 1 | **无法从归档复算** | 含 `norm_g_v` 的记录 **329 条，无一带 rank**；rank sweep 的 results.json 不含该字段 |
> | 2 | **text-only 臂的 $\|g_v\|$ 在构造上恒为 0** | `src/gap_susceptibility.py` 的 `_accumulate()` 有 `if name not in trainable_names: continue`，而 `trainable_names` 只含 `lora_A`/`lora_B`。**实测**：严格冻结下 rank 4/8/16/32 全为 0.0000；legacy 下 rank 4/8/16/32/64 亦全为 0.0000 |
> | 3 | **论文未写明曲线来自哪个臂** | `validation.tex:84`、`supplement.tex:77` 只称 "flat across $r\in[1,64]$" |
> | 4 | **归档值互不一致** | `beta_pilot_both_r8` = **7.675**；adapter 系列 = 0.978/0.623/0.881/0.710/0.294；复算 = 0.0000 |
>
> **处置（待操作者确认）**：**A. 重测**（对 both / vision_only 臂做 `compute_gap_susceptibility`，无训练、较快）
> ｜ **B. 删除**该声称与 2 张图（属次级机制，不影响主要结论）。
>
> ### ④ 防误导：删了两个全 0 结果文件
>
> 复算产生 `outputs/analysis/k_recomputed{,_legacy}.json`，其 `slope_k` 为 **0.0**——**会被误读成「复算成功」**。
> 已**删除**，并在 `tools/_pa_recompute_k.py` 加护栏：**全 0 时不再写文件**，改为提示「用错臂」。
>
> ### ⑤ 本轮已修（提交 d27b630）
>
> - `theory.tex:102` 的机制解释（原称 "$\beta$ increases moderately with rank"，**与自家 `tab:phase2` 相反**：text-only $\beta$ 由 r8 的 0.167 降到 r32 的 **0.119**）→ 改为「rank 效应经由 $\beta$」；
> - `theory.tex:4` 去掉已被否定的前提；`validation.tex:84` 的**循环解释**改为陈述 ERS 确实支持的部分；
> - **α_pred 复算成立且比声称更紧**：8 条记录全部为负，**|差| 最大 0.0026**（论文称 within 0.03）。
>
> ### ⑥ 编译状态（未受本轮影响）
>
> NC 版 **41 页**、Springer 版 **31 页**、0 错误、0 未定义引用、cites 41/bib 41。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "HANDOFF.md"
    t = io.open(p, encoding="utf-8").read()
    if "2026-10-03 晚 —— 停止实验" in t:
        print("  已记录，跳过")
        return 0
    anchor = "> **🔧 2026-10-03 下午"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if apply:
        io.open(p, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("K043_INVESTIGATION", "PAPERA_FIGURE_PROVENANCE", "329 条", "trainable_names"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
