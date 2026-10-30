# 海洋视觉模型候选池盘点（阶段 0 结论）

**日期**：2026-08-25 ｜ 参照 `docs/OCEAN_VISION_VALIDATION_PLAN.md`

## 候选模型

| 模型 | 判定 | 说明 |
|---|---|---|
| **OceanCLIP-0.15B**（[zjunlp/OceanCLIP-0.15B](https://huggingface.co/zjunlp/OceanCLIP-0.15B?library=open_clip)）| ✅ **采用** | BioCLIP 基座（ViT-B/16, 512 维）+ 海洋微调 50 epoch；`open_clip` 格式，权重已本地化 `models/oceanclip-0.15b/`（bioclip 570MB + oceanclip-bio 1.71GB + terms.txt 1001 物种名） |
| **AquaticCLIP**（arXiv 2502.01785 / IEEE 11380196）| ❌ 不可得 | arXiv 摘要中 GitHub 链接为占位符 "xxx"（原文如此），无公开权重；降级 |
| **MarineGPT**（hkust-vgd, arXiv 2310.13596）| ⏸ 暂缓 | VLM 型（需 LLM 算力，用户要求尽量不云端）；留作后续 |
| WaterBench / MARINER 基准 | ⏸ 暂缓 | 阶段 2 VLM 诊断用，目前无算力需求 |

## 权重结构（重要发现）

- `epoch_50.pt` 是**完整训练 checkpoint**：`{epoch, name: 'taxon_v211', state_dict, optimizer}`（1.71GB 含 Adam 状态）。
- 正确的加载方式= README 里的示例**有误**：需取 `ck['state_dict']`（302 键，标准 OpenCLIP 结构 `visual.*`/`transformer.*`/`logit_scale`），`model.load_state_dict(inner, strict=False)` → **missing 0 / unexpected 0**。
- `logit_scale = 4.537`；terms.txt = 1001 个物种拉丁名（含 `A abramis` 这类单字母缩写条目）。

## 评测集（采用 BioCLIP 官方基准 rare-species）

- **imageomics/rare-species**（HF，cc0，w/o 独立文本列）：TreeOfLife-10M 附带，BioCLIP 作者组生成；11983 条 = 图像 + 完整分类学（kingdom→sciName）。
- 海洋子集：`class ∈ {Actinopterygii, Chondrichthyes, Coelacanthi}` → 2009 行 → 过滤 ≥8 图/类 → **67 类 / 1608 图**（类名 = sciName 拉丁名，与 terms.txt 风格一致）。
- 无文本列 → gap 方向 d̂ 自估（类文本模板 `a photo of a {sciName}` + 图像质心），**与 A1 用 Flickr30k 自然对估计 d̂ 的口径不同**（协议偏差，报告中披露）。

## 运行环境

- GPU 实验环境：conda `pytorch`（torch 2.9.1+cu130, open_clip 3.3.0, transformers 5.9.0）——RTX 4060 Laptop 8GB。
- 系统 python 为 CPU 版 torch（勿用）；下载走 `HF_ENDPOINT=https://hf-mirror.com`（全局环境变量）。
