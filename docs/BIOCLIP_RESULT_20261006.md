# BioCLIP 严格冻结对照：部分结果与四骨干分析

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
