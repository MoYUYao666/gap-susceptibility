# Paper A 投稿前审核报告

> 审核日期：**2026-10-05** ｜ 对象：`paper合/`（目标 Neurocomputing）｜ 审核人：本会话
> 复跑命令：见文末「复核入口」

## 一、结论

**可以投稿。** 发现并修复 **1 项实质缺陷** + **4 项审计工具自身缺陷**；全部机械面与实质面检查通过。

| 类别 | 结果 |
|---|---|
| 编译 | ✅ NC **50 页** / Springer **33 页**，**0 错误、0 未定义引用** |
| 引用 | ✅ cites **44** / bib **44**，缺失 0、未使用 0；PDF 中作者-年份引用 **51 处** |
| 交叉引用 | ✅ 32 个 label、23 个 `\ref`，**悬空 0**；PDF 无 `??` |
| 重复 label | ✅ 0 |
| 占位符 | ✅ 0（TODO/FIXME/XXX/TBD 全无） |
| 图文件 | ✅ 引用的 12 个全部存在 |
| 图/表编号 | ✅ 图 12 环境 / 12 label；表 7 table + 1 longtable / 8 label |
| 摘要 | ✅ **244 词** ≤ 250 ｜ 摘要数字与正文一致（0.986 / 0.946 / 0.71 / 0.59） |
| 声明 | ✅ Data / Funding / Competing / CRediT / 生成式 AI 齐备且位于文献之前 |
| Highlights | ✅ 5 条、最长 59 字符 |
| 核心主张复算 | ✅ 严格冻结 5-seed 方向一致；ODE R²（仅 LoRA）0.986；α_pred \|差\| ≤ 0.0026 |

## 二、修复的实质缺陷（1 项）

### `introduction.tex`：残留的过度声称

| | 内容 |
|---|---|
| **原文** | "text-only fine-tuning **overwhelmingly preserves** cross-modal alignment better than joint-modality, a phenomenon this paper **confirms across 117 experiments on five architectures**" |
| **问题** | ① 无条件声称，而正文已记录 **SigLIP 上 both 更降间隙**；② 那 117 个实验多在 **legacy 约定**下跑（text-only 臂实际训练约 1.45 亿参数），**未隔离"适配位置"** |
| **为何此前漏掉** | 本会话改过 `empirical/validation/conclusion` 的设计模式与结论段，**但 introduction 这句用"Regularity"措辞**，按关键词搜索时未被捞出 |
| **修法** | 改为"**examines that suggestion … finds it holds where the comparison isolates the adaptation site, but not universally**" |
| **发现方式** | 本次新增的**范围词扫描**（`tools/_extract_claims.py`） |
| **脚本** | `tools/_pa_fix_intro_regularity.py` |

## 三、修复的审计工具缺陷（4 项，**均非稿件问题**）

| # | 工具 | 缺陷 | 后果 | 修法 |
|---|---|---|---|---|
| 1 | `_pa_final_check_nc.py` | 引用计数只认数字制 `[n]` | 在 44 条文献的稿子上报"**0 处引用**" | 改为两种制式都认（`tools/_fix_preflight` 前先手工改，见该文件注释） |
| 2 | `_audit_paperA_preflight.py`① | 用 `(fig\|tab)` 把两类 label 一起数 | 报"图 12 vs 20、表 7 vs 20"两个**假问题** | 分类计数 |
| 3 | `_audit_paperA_preflight.py`② | 只数 `\begin{table}`，漏 `longtable` | 报"表 7 vs 8"不明所以 | 环境正则含 `(long)?table` |
| 4 | 本报告作者的快速断言（见下） | 未等数据齐就下结论 | 三次错误结论，其中一次**写进正文** | 分析固化为脚本 + 配对检验 |

## 四、审核过程中我自己的错误（记录在案）

| # | 错误 | 发现方式 |
|---|---|---|
| 1 | 把 CLIP 的"更负"与 SigLIP 的"更小"当成**相反方向** | 配对检验 |
| 2 | 仅凭 2 个骨干断言"rank 效应**跨骨干成立**"（**已写入正文**） | OpenCLIP 跑完后推翻 |
| 3 | 断言"OpenCLIP 两臂都与另两个骨干相反" | 其中一臂 **t=+1.09 不显著** |

**共同根因**：数据未齐、未做检验、手工读数字。**对策**：`tools/_pa_rank_analysis.py`（所有数字由代码算、断言由配对检验给）。

## 五、已知边界（**如实标注，不掩盖**）

| 项 | 状态 |
|---|---|
| `k = 0.043` | **已从全稿清除**（5 处），改为实测区间（10% vs √r 预测 8 倍）；`docs/K043_INVESTIGATION.md` |
| 图来源 | 12 张中 **3 张**本轮重绘（来源明确）；**7 张**数据源在、可重绘；**2 张**（falsification / effective_rank）依赖已重测的 `k`，**待重绘** |
| rank 方向 | 5/6 组合同向且显著；**OpenCLIP both 例外（t=+1.09 不显著）** |
| 位置效应 | **按骨干分组**（CLIP 6/6、OpenCLIP 2/2 为 text-only；SigLIP 2/2 为 both） |
| 与 `yaras2026explaining` 的表面冲突 | **已在相关工作写辨析**（预训练 vs 微调阶段不同） |
| `162 ODE fits` | 与归档实测记录数（9）的对应关系**未逐一重建** |

## 六、复核入口

```powershell
python tools\audit\check_paperA.py            # 引用键匹配 / 伪造残留
python tools\_pa_final_check_nc.py            # NC 合规（页数/摘要/声明/引用计数）
python tools\_audit_paperA_preflight.py       # 新面审计（悬空 ref/重复 label/占位符/图文件/编号）
python tools\_pa_verify_core_claims.py        # 核心主张复算
python tools\_pa_rank_analysis.py             # 三骨干 rank 分析（配对检验）
python tools\_pa_rank_matrix.py               # 骨干 × rank 矩阵
python tools\_extract_claims.py --apply       # 主张提取（措辞审核用）
python tools\_pa_build_nc_package.py --apply  # 重建投稿包
```

## 七、最终确认（2026-10-05，本文件撰写后）

本报告初稿完成后又做了三轮复核，**发现并修正 3 处真问题**（两版 `main*.tex` 摘要残留旧计数 278；目录表 `Total` 误用全文字口径 374 而与表内求和 212 不符；附录说明把严格冻结重复计数），并**重绘全部 9 张来源不明的图**（`docs/PAPERA_FIGURE_PROVENANCE.md`）。**当前实测**：NC **50 页**、Springer **33 页**、0 错误、0 未定义引用、cites 44 = bib 44、目录表求和 = Total = **212**、全文 **374**、图来源 **12/12**。详见 `docs/PAPERA_REVISION_SPEC.md` §7.7。
