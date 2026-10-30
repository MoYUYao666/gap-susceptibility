# A2A3 合并稿实验结果汇总（2026-08-27 执行轮）

> 数据源：`outputs/sonar_protocol_full.json`、`ocean_rank1_bound.json`、`direction_operator.json` 等。
> 全部数字以 JSON 为准；本文档为合并稿写作的快照。

## ① A3 全量 NKSID 复跑（`sonar_protocol_full.json`，2617 图/8 类，无 cap）
类分布：floats 951, tire 834, cylinder 288, big_propeller 203, soft_pipeline 115, iron_pipeline 112, small_propeller 94, fishing_net 20。

| 模型 | σ_m | gap_norm | top1_0 | τ@λ=1 (pred=meas) | τ@λ=0.5 | τ@λ=2 | τ文本侧 | CG@λ=1 |
|---|---|---|---|---|---|---|---|---|
| CLIP frozen | 0.0247 | 1.0911 | 14.94 | **−0.0807** | 0.1631 | −0.2031 | −0.0228 | 0.0377 |
| SonarCLIP (全量 FullFT 10ep) | **0.0136** | 1.1445 | **99.89** | **0.7202** | 0.8028 | 0.5839 | 0.7261 | 0.0970 |
| CLIP+FlickrFT (陆地对照) | 0.0222 | 1.1342 | 27.97 | −0.0906 | 0.1444 | −0.2267 | −0.0392 | 0.0811 |

- **Theorem 1 全量零偏差**：3 模型 × 6λ 全部 pred=meas 逐位一致（另 3 文本侧条件）。
- **压平率（全量口径）**：frozen→SonarCLIP 0.0247/0.0136 = **1.82×**；陆地 1.11× → **1.6× 更深**（子集 650 平衡口径为 3.8× vs 1.1× = 3.4×）。幅度受类分布调制（floats+tire = 68% 长尾）。
- **τ 免疫性**：τ@λ=1 0.720（子集 0.896 时）——免疫性随训练集规模/类分布下降；top-1 保留 99.9%（λ=1 时 top1 99.89）。
- 对称化：frozen Δτ=0.058（|−0.0807−(−0.0228)|）；SonarCLIP Δτ=0.006；flickrft Δτ=0.051。
- 谱系（NCC 平坦）子集口径数字保留（96.8/96.2/94.8 @λ=0/0.5/1 → 87.2 @λ=2）。

## ② Theorem 3 海洋版（`ocean_rank1_bound.json`，4 模型族 × 8λ）
字段：exact(3a) / corr_gauss(3c) / weak_bound / meas_keep_loss(实测保失率)。

| 模型族 | σ_m | λ=0.5 exact/corr/meas | λ=1 exact/corr/meas | λ=2 exact/corr/meas |
|---|---|---|---|---|
| bioclip | 0.0075* | 0.225/0.279/0.097 | 0.351/0.450/0.169 | 0.475/0.606/0.312 |
| oceanclip | 0.0078* | 0.194/0.235/（−0.010 top1 微升） | 0.357/0.373/**0.033** | 0.556/**0.518**/0.188 |
| openclip_tf | 0.0739 | 0.639/0.698/0.531 | 0.735/0.750/0.628 | 0.793/0.776/0.602 |
| siglip | 0.0299 | 0.580/0.598/0.139 | 0.787/0.697/0.539 | 0.882/0.750/0.861 |

- 弱界 5(1−τ̄) **32/32 全部成立**（通常平凡：λ=0.25 时 1.1–2.6，λ=2 时 3.4–5.5）。
- 高斯相关结构界在 σ_m 适中模型（bioclip/siglip/openclip）上成上界（corr > exact > meas 常见）；**σ_m 极小时失效**（oceanclip λ=2: exact 0.556 > corr 0.518——高斯尾假设在 σ_m=0.0078 饱和）→ 诚实披露"高斯界仅适用于 σ_m 适度域；σ_m 极小的海洋专用模型需用确定性 3(a)"。
- λ<0 时 corr 对称（公式对称）而 exact 轻微不对称——真实 (d,b) 分布所致。

## ③ 方向解析算子 v1（`direction_operator.json`，mean-方向 vs PCA-方向 + 残差占比）
| 域/退化 | τ_meas | err_gap(基线) | err_mean | err_pca | resid_mean | resid_pca |
|---|---|---|---|---|---|---|
| marine haze_t0.60 | 0.4803 | 0.4626 | **0.3167** | 0.4348 | 0.9543 | 0.9797 |
| marine haze_t0.30 | 0.2881 | 0.6155 | **0.3623** | 0.5591 | 0.9387 | 0.9829 |
| marine uw_cast | 0.3990 | 0.5328 | **0.3254** | 0.4021 | 0.9522 | 0.9711 |
| sonar speckle_p20 | 0.5252 | 0.4178 | **0.2898** | 0.3809 | 0.7028 | 0.9282 |
| sonar speckle_p40 | 0.4751 | 0.4658 | **0.2843** | 0.3702 | 0.7216 | 0.9301 |
| sonar blur_r2 | 0.1843 | 0.7243 | **0.1769** | 0.4320 | 0.8097 | 0.8837 |
| sonar shadow_strip | 0.6200 | 0.3622 | **0.1772** | 0.3243 | 0.9031 | 0.9379 |

- **方向解析首次部分成功**：mean 方向手术误差平均减半（声呐 0.36–0.72 → 0.18–0.29；海洋 0.46–0.62 → 0.32–0.36）。
- **残差占比 = 退化可解析性层级**：散斑 0.70 < 模糊 0.81 < 阴影 0.90 < 海洋(雾化/色偏) 0.94–0.95——合成噪声单体方向性最强，结构性退化最弱。
- **PCA 方向劣于均值方向**（PCA 被类间变异主导）——方向估计需用退化对的差分均值（监督式），不能用无监督主成分。
- 结论语言："单方向解析是下限；完整解析需多方向/子空间算子"——正文从"open problem"升级为"原型 v1 + 量化层级"。

## ⑥ MarineLife-16K 自然文本检索（`ocean_ml16k_retrieval.json`，终版）
- 数据事实：HF 实际发布 **427 视频组/3416 帧/3440 QA**（README 声称 2000 视频+16080 QA 未完整发布；metadata/attributes_captions.csv 缺失）——如实披露。QA 为人工自然语言（question+answer_text），"真实自然文本"性质成立。
- **终版结果（随机基线 video_R1 = 1/427 = 0.234%）**：

| 模型 | q_ans R1(video) | q_ans R5 | q_only R1 | ans R1 | obj R1 |
|---|---|---|---|---|---|
| openclip_tf | **1.92%** | — | 0.96% | 2.33% | — |
| bioclip | 0.87% | 3.20% | 0.49% | 0.47% | 0.44% |
| oceanclip | **0.26%** | 1.60% | 0.29% | 0.29% | 0.23% |

- **结论（与 D 互补且更锐利）**：通用 CLIP 最好（1.92% ≈ 8×随机）；海洋物种编码器 bioclip 3.7×；**OceanCLIP ≈ 随机（1.1×）**——海洋专用微调在自然场景文本上的检索对齐被摧毁（特化代价的极端形态：物种分类模板 67 类精确 vs 自然 QA 近随机）。与 D（BLIP 生成字幕，海洋模型 ≤1.4%）一致。
- **数据质量警示**：初跑（下载未完整,86 视频假口径）曾给出"oceanclip>bioclip"反转结论——经核验为残缺数据 artifact；完整口径下 bioclip>oceanclip 成立。最终数字一律以本表为准。
- 修 bug 记录:vids 需 site/video 组合（目录名跨 site 重复）；查询视频集 ⊂ 帧视频集（有一视频无 QA）。

## ⑦ 第二个声呐数据集 —— ❌ 作废（2026-08-27 核验,诚实记录）
- **尝试记录**（全部失败）：SeabedObjects-KLSG（SSS 385+62 图）GitHub SSH/HTTPS/codeload/jsDelivr 均不可达；SCTD/S3Simulator/XingYZhu FLS 均 GitHub 系;UATD（Xie/Yang/Qiu, Sci Data 2022, 多波束 FLS）figshare API 404、OpenI 仅存 README、OneDrive 短链无法解析到文件、百度网盘需账号;**HF 12 轮搜索**（sonar/side-scan/imaging/acoustic camera/didson/fls/atr/mine-like/nksid/sonar-image/sonar-vision/underwater-sonar）无带标注声呐成像数据集（sonar-rock-mine=60 维信号表、URPC 镜像=**光学**海参/海胆/扇贝/海星、NOSIBLE=金融 NLP、Lake-Swimmer=无标注 .avi、mvaldenegro=GitHub）。
- **关键澄清**：`fuhao7i/URPC` 为**水下光学图像**（URPC2021 抓取竞赛,4 类海洋生物）**非声呐**——17:00 曾出错跑完（frozen top1 22.75/τ 0.38,类别=holothurian/echinus/scallop/starfish,与 NKSID 无关),结果已作废不录入。
- **论文表述**（merge 稿）：数据可得性章节 + Future work——"跨数据集/跨声呐类型(SSS)验证是本框架的自然扩展；公开声呐数据集的典型分发渠道(GitHub/Figshare/云盘)在若干网络环境下不可达,我们未能获得带标注的第二声呐成像集；相关尝试记录于附注"。同时 ① 的全量 vs 平衡子集双口径已提供"样本选择敏感性"的内部稳健性证据。
- **S3Simulator**（Springer Pattern Recognition 2024, 仿真 SSS）为最可行后续候选（本环境不可达）。
