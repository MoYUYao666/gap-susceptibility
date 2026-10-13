# -*- coding: utf-8 -*-
r"""落账：α 起点差异的判决性排查 + 我造成的 GPU 争用（2026-10-08 11:35）。

    python tools\_docs_dgstar_investigation.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔬 2026-10-08 11:35 —— α 起点差异排查完毕（**排除初始化，锁定学习率**）｜我又一次造成 GPU 争用**
>
> ### 判决性实测：**LoRA 初始化是正确的**（`tools/_p29_dgstar_origin.py`）
>
> | 测试 | DG\\* |
> |---|---|
> | **纯 frozen 模型**（无 LoRA） | **1.3761** |
> | **LoRA 注入后、未训练** | **1.3763**（差 **+0.0002**） |
> | trainer 的 `_compute_dg_star_record` | **1.3757** |
> | `lora_B` 检查 | **48/48 全零** → ✅ 标准 LoRA（B 零初始化） |
>
> **→ 初始化无问题**（B 零初始化 ⇒ 注入后输出与 frozen 一致，实测差 0.0002）。
>
> ### 🔑 数据规模的关键发现
>
> ```
> 📦 Flickr30k [train]: 5000 样本 → 实际 train=4000 val=500 test=500
>    val 批数 = 8 → **验证集只有 500 个样本**
> ```
> **→ 我的探测（512 样本）与归档口径一致**（同为 500），故基线对比成立。
> **→ `_compute_dg_star_record` 的 `sample_size=5000` 实际只用到 500**（验证集上限）。
>
> ### 差异定位：**学习率，不是初始化**
>
> | 参数 | 归档（3 seed 均值） | 我的 run | 比值 |
> |---|---|---|---|
> | **α** | −0.02378 | −0.07611 | **3.20×** |
> | **β** | 0.0648 | 0.0181 | **0.28×** |
> | **渐近幅值 α/β** | 0.393 | 4.202 | **11.45×** |
> | 起始 DG\\* | 1.4767 | 1.88（**epoch 1 之后**） | — |
> | **第 1 轮漂移** | **0.038–0.052** | **0.0851** | **~2×** |
>
> **第 1 轮漂移只差约 2 倍**（不是 4–11 倍）→ **峰值学习率约需减半**。
> 故已给 `tools/_p21_alpha_trainer_based.py` 加 **`--lr`** 参数以便扫描。
>
> ### 🔴 我又一次造成 GPU 争用（**须记录**）
>
> 我在 COCO 队列运行期间启动了 lr 扫描 → **两个实验争 8 GB 显存**（实测 7932/8188 MiB）。
> **这违反了本项目已固化的铁律（GPU 只能跑一个实验）**，且与昨夜"三驱动撞车"同类。
> **已按精确命令行匹配终止自己的扫描**，COCO 恢复独占（7123 MiB / 99%）。
> **COCO 未受损**：`[done] both seed=456 ... 704s` ✅
>
> **教训（增补第 4 条对策）**：**在队列运行时，任何新实验必须先确认 GPU 空闲，
> 不得因为"我的实验很小"就并行**——8 GB 装不下两个。
>
> ### ✅ COCO 补跑进展
>
> `[done] both seed=456 cg 0.8529 -> 0.7624 R@1=0.1185 vis_nonzero=0 704s`（36.1 min）
> **36 run × 约 36 min ≈ 21.6 h**（跨会话，可续跑）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "α 起点差异排查完毕" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("α 起点差异排查完毕", "1.3761", "1.3763", "验证集只有 500 个样本", "我又一次造成 GPU 争用"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    if "0I." not in m:
        add = """
**0I. 🔬 α 起点差异排查结论（2026-10-08 11:35）**

- **LoRA 初始化正确**：frozen DG\\*=1.3761 ｜ 注入后 1.3763（差 **+0.0002**）｜ `lora_B` **48/48 全零**。
- **验证集只有 500 个样本**（`max_samples=5000` 下 train=4000/val=500/test=500）→ 我的 512 样本探测与归档同口径。
- **差异锁定在学习率**：第 1 轮漂移 归档 0.038–0.052 vs 我的 **0.0851**（**约 2 倍**）→ **峰值 lr 约需减半**。
- 已给 `tools/_p21_alpha_trainer_based.py` 加 `--lr` 参数。
- ⚠️ **注意**：A 的 lr 扫描**必须等 COCO 跑完**再跑（我曾在 COCO 运行期间并行启动，造成 GPU 争用，已终止）。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
