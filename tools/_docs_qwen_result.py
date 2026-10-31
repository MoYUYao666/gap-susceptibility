# -*- coding: utf-8 -*-
r"""落账：实验 ④ 完成——**框架在解码器 VLM 上也成立**（2026-10-08 21:40）。

    python tools\_docs_qwen_result.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🎯 2026-10-08 21:40 —— 实验 ④ 完成：框架在**解码器 VLM** 上也成立（补充了论文自认的 scope 缺口）**
>
> ### 口径（三臂**完全一致**）
>
> **Qwen2-VL-2B ｜ 严格冻结 ｜ 4-bit ｜ 400 样本 ｜ 3 epoch ｜ batch 4 ｜ rank 8 ｜ lr 1e-4 ｜ seed 42**
>
> **为何用 4-bit**：bf16 下 `vision_only` 实测 **27 min 未完成 1 个 epoch**
> （`text_only` 为 2.4 min/epoch，**慢 13 倍**）→ 不可行；4-bit 下同臂 **5.4 min/3 epoch**。
>
> ### 结果
>
> | 臂 | `n_trainable` | DG\\* 起点 | DG\\* 末值 | **相对降幅** | CG 降幅 |
> |---|---|---|---|---|---|
> | **both** | 14,494,912 | 0.6364 | 0.1029 | **83.8%** | 77.2% |
> | text_only | 9,232,384 | 0.7100 | 0.1851 | 73.9% | 77.9% |
> | **vision_only** | 5,262,528 | **2.1759** | 1.9365 | **11.0%** | 22.6% |
>
> 逐 epoch `DG*`：
> - `text_only`  0.7100 → 0.2159 → 0.1851
> - `both`       0.6364 → 0.1194 → 0.1029
> - `vision_only` **2.1759 → 2.0213 → 1.9365**（几乎不动）
>
> **严格冻结校验**：三臂均为 `视觉/语言` 单侧或双侧且**互不污染**
> （`text_only` 视觉 0 ｜ `vision_only` 语言 0 ｜ `both` 258+392）✅
>
> ### ⚠️ 一个我自己先犯后改的判据错误（**须记录**）
>
> **第一版判据用 `DG*` 绝对跨度最小** → 判出 `vision_only` 最保护。
> **但三臂起点相差 3.4 倍**（0.6364 vs 2.1759）：
> **起点高的臂天然跨度大** → "绝对跨度最小"会把**"几乎不动"误判为"最保护"**。
>
> **论文的口径是 `ΔCG = final − initial`（绝对变化），但其各臂起点相同**
> （同一冻结模型 + LoRA B 零初始化）→ 绝对变化可比。**本实验起点不一致 → 必须用相对降幅。**
> **已改为两个口径都报，并以相对降幅判定。**
>
> ### 结论
>
> 1. **`vision_only` 在解码器 VLM 上同样最差**（相对降幅仅 11%，起点还高 3.4 倍）
>    —— **与双塔侧完全一致**，这是**跨架构稳健的负面结论**；
> 2. **框架在解码器 VLM 上产生清晰的指数衰减轨迹**（`text_only`/`both` 相对降幅 74–84%），
>    **故 ODE/DG\\* 框架不限于双塔**；
> 3. **最优位置不同**：此模型上 `both` 最保护（83.8%），而三个对比式双塔骨干是 `text_only`
>    —— **与"最优位置随配置而变、需实测"的既有结论一致**，不构成矛盾。
>
> ### 尚未做（如实标注）
>
> - **单 seed**；**单模型**（Qwen2-VL-2B 一个）；
> - 4-bit 量化与 bf16 的差异未量化（故三臂**全部**用 4-bit 以保证内部可比）；
> - 规模小（400 样本 3 epoch）——**用于测排序方向，不是最终性能**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "实验 ④ 完成" in t and "解码器 VLM" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("实验 ④ 完成", "83.8%", "11.0%", "相差 3.4 倍", "几乎不动"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    if "0O." not in m:
        add = """
**0O. 🎯 实验 ④ 完成：框架在解码器 VLM 上也成立（2026-10-08 21:40）**

- **口径**：Qwen2-VL-2B｜严格冻结｜4-bit｜400 样本｜3 epoch｜batch 4｜seed 42（**三臂一致**）。
- **结果**：`both` 相对降幅 **83.8%** ｜ `text_only` **73.9%** ｜ **`vision_only` 仅 11.0%（且起点高 3.4 倍）**。
- **结论**：① **`vision_only` 跨架构最差**（与双塔一致）；② **框架不止于双塔**（解码器 VLM 上有清晰指数衰减）；
  ③ **最优位置不同**（此模型 `both` 最优）—— 与"最优位置随配置而变、需实测"一致。
- ⚠️ **单 seed、单模型、4-bit**；规模小（测排序方向，非最终性能）。
- ⚠️ **我修正了自己一个判据错误**：初版用"绝对跨度最小"→ 误判 `vision_only` 最保护；**起点相差 3.4 倍时绝对跨度不可比** → 改用相对降幅。
- 证据：`outputs/vlm_strictfreeze/`、`outputs/analysis/qwen_verdict.json`、`tools/_p50_qwen_verdict2.py`。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
