# -*- coding: utf-8 -*-
r"""记录 BioCLIP 部分结果与四骨干分析（2026-10-06）。

    python tools\_docs_bioclip_result.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

REPORT = r"""# BioCLIP 严格冻结对照：部分结果与四骨干分析

> 日期：**2026-10-06** ｜ 状态：**部分完成**（操作者要求停止）
> 脚本：`tools/_exp3_bioclip_strict.py`（运行）、`tools/_exp3_bioclip_harvest.py`（结果抢救）、
> `tools/_pa_four_backbone_analysis.py`（分析）
> 产物：`outputs/strict_freeze_bioclip/results_partial.json`、`run_log.txt`

## 为什么做

已测三个骨干，位置效应**按骨干分组**（CLIP/OpenCLIP → `text_only` 更降；SigLIP → `both` 更降）。
但"骨干"这个变量**混了架构、预训练数据、训练目标**三件事。BioCLIP 提供了一个新点：
**OpenCLIP ViT-B/16（patch 16）+ 生物域预训练**。

## 加载（无需格式转换）

`models/oceanclip-0.15b/bioclip/` 含 `open_clip_config.json` + `open_clip_pytorch_model.bin`。
`open_clip_torch` 3.3.0 已装 → `create_model_and_transforms('ViT-B-16', pretrained=None, **model_cfg)`
+ `load_state_dict`：**缺失 0 / 多余 0**（302 键全匹配，已实测）。

## 完成度

| rank | 状态 |
|---|---|
| **4** | ✅ **9/9 run 完成**（3 臂 × 3 seeds） |
| 8 | ❌ 未跑（操作者 2026-10-06 要求停止） |

**注意**：BioCLIP 的初始 CG 为 **1.79**，远高于 B/32 骨干的 0.81——
**生物域模型对自然图像的间隙本来就大得多**，故其 ΔCG 的**绝对值**不可与 B/32 直接比较
（本分析只用**同骨干内的臂间排序**）。

## rank 4 结果（3 seeds 平均）

| 臂 | ΔCG | ± sd | 可训参数 |
|---|---|---|---|
| **both** | **−0.4515** | 0.0149 | 737,280 |
| text_only | −0.3671 | 0.0104 | 294,912 |
| vision_only | −0.2927 | 0.0022 | 442,368 |

**排序 `both` < `text_only` < `vision_only`**（ΔCG 越小越好）。

## 四骨干 × rank 的位置排序（全部严格冻结）

| 骨干 | 架构 | rank | text_only | both | vision_only | 最佳 |
|---|---|---|---|---|---|---|
| CLIP | patch32 | 4 | **−0.0285** | −0.0184 | — | text_only |
| CLIP | patch32 | 8 | **−0.0465** | −0.0258 | +0.0106 | text_only |
| OpenCLIP | patch32 | 4 | **+0.0807** | +0.0840 | — | text_only |
| OpenCLIP | patch32 | 8 | **+0.0694** | +0.0881 | +0.0925 | text_only |
| SigLIP | patch16 | 4 | +0.0831 | **+0.0090** | — | both |
| SigLIP | patch16 | 8 | +0.0664 | **−0.0114** | +0.0522 | both |
| **BioCLIP** | **patch16** | **4** | −0.3671 | **−0.4515** | −0.2927 | **both** |

## 判定（脚本给出，非手工读）

```
patch32 各配置最佳臂: ['text_only']  → 一致（4 个配置）
patch16 各配置最佳臂: ['both']       → 一致（3 个配置）
✅ 位置效应按 patch 尺寸分组：patch32 → text_only ｜ patch16 → both
```

**7 个配置（4 骨干 × 至多 2 rank）无一例外。**

## ⚠️ 必须如实标注的混淆与边界

| 项 | 说明 |
|---|---|
| **BioCLIP 只有 rank 4** | rank 8 未跑，故 patch16 组只有 1 个 rank 点来自 BioCLIP |
| **BioCLIP 是域外模型** | 生物域预训练，在自然图像（Flickr30k）上初始 CG 1.79（B/32 为 0.81）→ **域偏移本身可能影响臂间排序**，不能只归因于 patch 尺寸 |
| **两个 patch32 骨干共享同一实现** | CLIP（HF）与 OpenCLIP 是不同权重，但都是 patch32 ViT-B |
| **n=4 骨干** | 结论是**模式**而非定律；patch 尺寸与骨干数**未解耦**（每个 patch 尺寸各 2 个骨干） |

**因此正文只能写"该效应在 7 个配置中按 patch 尺寸一致分组"，不能写"patch 尺寸导致"。**

## 对正文的意义（**待操作者决定**）

| 发现 | 可加强 | 建议 |
|---|---|---|
| patch32/patch16 分组无例外 | **设计模式①（位置）的表述更精确** | 在 §empirical 的设计模式①里补一句"按 patch 尺寸分组"，并**标注 BioCLIP 为域外模型、仅 rank 4** |
| B/16 骨干的初始 CG 更大 | **如实边界** | 可选：§Discussion 局限 |

## 复核入口

```powershell
python tools\_pa_four_backbone_analysis.py      # 四骨干分析（本报告的数字来源）
python tools\_exp3_bioclip_harvest.py --apply   # 从日志重新解析（幂等）
```
"""

ENTRY = r"""> **🧬 2026-10-06 —— BioCLIP 部分结果：位置效应按 **patch 尺寸**分组（7 个配置无例外）**
>
> 操作者要求做**优先级 3**，随后要求**停止**（rank 8 未跑）。
> 报告：`docs/BIOCLIP_RESULT_20261006.md`
>
> ### 加载：无需格式转换
>
> `models/oceanclip-0.15b/bioclip/` 是标准 OpenCLIP 格式，且 **`open_clip_torch` 3.3.0 已装** →
> `create_model_and_transforms('ViT-B-16', ...)` + `load_state_dict`：**缺失 0 / 多余 0**（302 键）。
>
> ### 完成度
>
> **rank 4 全部 9/9 完成**（3 臂 × 3 seeds）；**rank 8 未跑**（操作者停止）。
>
> ### rank 4 结果（3 seeds 平均）
>
> | 臂 | ΔCG | 可训 |
> |---|---|---|
> | **both** | **−0.4515** ± 0.0149 | 737,280 |
> | text_only | −0.3671 ± 0.0104 | 294,912 |
> | vision_only | −0.2927 ± 0.0022 | 442,368 |
>
> ### 🎯 四骨干 × rank 的排序（7 个配置）
>
> ```
> patch32 最佳臂: ['text_only']  → 一致（4 个配置：CLIP r4/r8、OpenCLIP r4/r8）
> patch16 最佳臂: ['both']       → 一致（3 个配置：SigLIP r4/r8、BioCLIP r4）
> ✅ 位置效应按 patch 尺寸分组
> ```
>
> **分析脚本 `tools/_pa_four_backbone_analysis.py`（数字与判定均由代码给出）**。
>
> ### ⚠️ 如实标注的边界
>
> - **BioCLIP 仅 rank 4**；
> - **BioCLIP 是域外模型**：生物域预训练，在自然图像上初始 CG **1.79**（B/32 为 0.81）→
>   **域偏移本身可能影响排序**，不能只归因 patch 尺寸；
> - **patch 尺寸与骨干数未解耦**（每个尺寸各 2 个骨干，n=4）。
>
> → **正文只能写"7 个配置按 patch 尺寸一致分组"，不能写"patch 尺寸导致"。**
>
> ### 抢救与缺陷
>
> `tools/_exp3_bioclip_strict.py` **只在全部 18 run 跑完后才写 JSON**——中途停止会丢全部结果。
> 已用 `tools/_exp3_bioclip_harvest.py` **从运行日志解析并落盘**（9 条记录 →
> `outputs/strict_freeze_bioclip/results_partial.json`，幂等可重跑）。
> **该"末尾才落盘"的设计缺陷已记录**：后续长任务应**每个 run 后即落盘**。
>
> ### 本轮踩的三个坑（均由"先冒烟测试"抓到，未浪费整晚）
>
> | # | 错误 | 发现时机 |
> |---|---|---|
> | ① | `'LoRA' object has no attribute 'weight'`（OpenCLIP 内部直接访问 `.weight`） | 冒烟 |
> | ② | **文本层 0 命中**——OpenCLIP 文本塔名为 **`transformer`** 而非 `text` | 冒烟 |
> | ③ | `NameError: torch`（作用域）+ **LoRA 注入在 `.to(dev)` 之后** → 设备不一致 | 实跑 |
>
> 已加防护：注入移到 `.to(dev)` **之前**，并**断言所有可训参数在目标设备上**。
>
> ### 另记：我的 ETA 第 4 次失真
>
> 我估 **12 分钟/run**，实际 **约 47 分钟/run**（约 4 倍）——因冒烟只跑 1280 样本 × 3 epochs，
> 而全程 5000 × 10。**教训：小规模冒烟可验证正确性，但外推耗时必须按数据量与 epochs 线性放大后再留余量。**

"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    rp = REPO / "docs" / "BIOCLIP_RESULT_20261006.md"
    io.open(rp, "w", encoding="utf-8", newline="").write(REPORT)
    t = io.open(rp, encoding="utf-8").read()
    for k in ("−0.4515", "−0.3671", "−0.2927", "patch32", "patch16", "1.79"):
        assert k in t, f"报告断言失败：缺 {k}"
    print(f"  ✅ 报告已写出 docs/{rp.name}（{len(t.splitlines())} 行）")

    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "BioCLIP 部分结果" not in h:
        anchor = "> **🧪 2026-10-05 晚 —— 补充实验"
        i = h.find(anchor)
        if i < 0:
            print("  ⚠ 未找到 HANDOFF 锚点")
            return 1
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ENTRY + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("BioCLIP 部分结果", "patch 尺寸", "−0.4515", "只写"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
