# -*- coding: utf-8 -*-
r"""落账：判定实验结果 + 修正云端结论（2026-10-09 18:45）。

    python tools\_docs_layout_verdict.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🎯 2026-10-09 18:45 —— 判定实验：**数据布局无罪，问题在云端环境**（一句话结论得到证实）**
>
> ### 做法（操作者要求"先停当前实验去跑这个"）
>
> 云端与本地**同代码、同权重、同图片、同 CSV**，唯一差别是**我上传时把 `results.csv`
> 放到 `flickr30k/results.csv`**（本地在 `flickr30k/flickr30k-images/results.csv`）。
> **→ 在本地严格复刻云端布局跑一次**（`tools/_p77_local_cloud_layout.py`）：
>
> ```
> outputs/_cloud_layout/flickr30k/
> ├── flickr30k-images/    ← 1000 张 jpg（与云端同一批）
> └── results.csv          ← 放在 flickr30k/ 下（**与云端相同**）
> ```
>
> ### 结果（`both` / seed 42 / batch 64 / 3 epoch / max_samples 500，用时 1.7 min）
>
> | 指标 | **本地复刻云端布局** | 云端 | 本地正常 |
> |---|---|---|---|
> | **`R@1`** | **0.7200** ✅ | 0.0020 ❌ | 0.685 |
> | `loss 末` | **0.5256** ✅ | 4.81 ❌ | 0.16 |
> | **`cosine_separation(init)`** | **0.139767** ✅ | **0.000000** ❌ | 0.141407 |
> | 初始 Centroid | 0.8117 | 1.0710 | 0.8187 |
>
> **铁证**：本地用**完全相同的数据布局**得到 **`sep = 0.1398`**，
> 而云端是 **`0.000000`** → **数据布局不可能造成那个 0。**
>
> ### 结论修正
>
> | 我此前说 | 现状 |
> |---|---|
> | "问题在 `batch → 模型` 这一段，与数据集文件无关" | ✅ **得到证实**（不是数据文件布局） |
> | "可能是 `create_dataloaders` 的分支差异" | ❌ **排除**（同一布局本地正常） |
> | "可能是 transformers 5.x 的 CLIP padding 处理差异" | ⚠️ **仍是首要嫌疑，但未钉死** |
>
> **⚠️ 诚实标注**：我排除的是**数据布局**这一支；
> **云端环境里具体哪一项导致失效，仍未钉死**
> （我试过对齐 `transformers`/`peft` 版本，**仍失败**）。
> 剩余嫌疑：`torch 2.12.1` vs `2.9.1`、CUDA/驱动差异、云端 pip 环境中的其它包。
>
> ### 对"他人能否复现"的实际影响（操作者提出的问题）
>
> | 项 | 处置 |
> |---|---|
> | 根因 | **未钉死**——故文档只陈述**可观测事实 + 两个判定数**，不猜机制 |
> | 环境清单 | ✅ 已补 `requirements-lock.txt`（133 行精确版本）与 `docs/ENVIRONMENT.md` |
> | `requirements.txt` | ✅ 顶部已加警告，指向锁文件 |
> | **给复现者的判据** | **`R@1` 与 `final_train_loss` 两个数即可区分"训练失效"与"环境微差"** |
>
> ### 本次队列（已按操作者要求暂停，成果保留）
>
> | 骨干 | text_only | both | vision_only |
> |---|---|---|---|
> | CLIP B/32 r4 | **3** | **3** | **3** |
> | CLIP B/16 r4 | **3** | **3** | **3** |
> | OpenCLIP r4 | **3** | 1 | 1 |
> | **合计** | | | **23 个 `results.json`** |
>
> **断点**：OpenCLIP 的 `both`/`vision_only` 各缺 2 seed（约 4 h）。
> **续跑命令**：`python tools\\_p56_add_seeds.py --apply`（幂等，已完成自动跳过）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "数据布局无罪，问题在云端环境" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("数据布局无罪", "0.139767", "0.000000", "create_dataloaders` 的分支差异",
              "未钉死", "23 个 `results.json`"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    if "0T." not in m:
        add = """
**0T. 🎯 判定实验：数据布局无罪，问题在云端环境（2026-10-09 18:45）**

- **做法**：本地严格复刻云端数据布局（`results.csv` 放 `flickr30k/` 下）跑 `both`。
- **结果**：`R@1 = 0.7200` ｜ `loss 末 = 0.5256` ｜ **`cosine_separation(init) = 0.139767`** —— 本地正常，云端是 **0.000000**。
- **结论**：**数据布局无罪**；`create_dataloaders` 分支差异**排除**；**transformers 5.x 仍是首要嫌疑但未钉死**。
- ⚠️ **诚实标注**：云端环境里具体哪一项导致失效**仍未确定**（对齐 transformers/peft 后仍失败）；剩余嫌疑：torch 2.12.1 vs 2.9.1、CUDA/驱动、其它包。
- **对复现的影响**：已补 `requirements-lock.txt`（133 行）+ `docs/ENVIRONMENT.md` + `requirements.txt` 警告；**给复现者的判据是两个数**（`R@1`、`final_train_loss`）。
- 证据：`outputs/analysis/layout_verdict.json`｜`tools/_p77_local_cloud_layout.py`

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
