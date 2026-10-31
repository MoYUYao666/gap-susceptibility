# P1 今晚要跑的 GPU 任务（操作者执行）

> 前提：**GPU 串行**，跑之前确认没有别的训练在跑（`nvidia-smi`）。
> 目的只有一个：补上严格冻结对照缺失的 **joint 臂**，让 §5 的"一臂对照"限制消失。

## 一、要跑什么，代价多少

| 命令 | 内容 | 实测代价 |
|---|---|---|
| `python experiments/strict_freeze_control.py --tags both --seeds 42` | joint 臂 **1 seed** | **~52 min** |
| `python experiments/strict_freeze_control.py --tags both` | joint 臂 **5 seeds**（与 text-only 同规格） | **~4.3 h** |
| `python experiments/strict_freeze_control.py --tags vision_only` | vision-only 臂 5 seeds（可选） | **~3.5 h** |
| `python experiments/strict_freeze_control.py --tags both --smoke` | 1 epoch/512 样本冒烟（写进 `outputs/strict_freeze_smoke/`，不会污染正式目录） | ~2 min |

**为什么这么慢**：joint 臂把可训参数放进视觉塔 → 必须做完整视觉反向传播。实测 **312–326 s/epoch**（text-only 严格跑仅 ~30 s/epoch，因为它整棵视觉塔的反向被跳过），10 epoch ≈ 52 min/seed。

**建议**：先跑 `--seeds 42` 单种子（52 min）看方向；若方向符合预期且你有时间，再跑满 5 seeds。**单种子请不要写进正文**（脚本会记录 `n_seeds=1`，`tools/_p1_add_joint_rows.py` 会照实写 1，正文里"5 seeds"的对照是 text-only 那一行）。

## 二、跑完之后（三步，全部已备好）

```powershell
# 1) 汇总（幂等，可随时重跑）
D:\Anaconda\envs\pytorch\python.exe tools\p1_strict_control_summary.py

# 2) 把 joint 行插进已写好的 strict_control.tex，并自动改写"一臂对照"的那两句话
D:\Anaconda\envs\pytorch\python.exe tools\_p1_add_joint_rows.py

# 3) 重编译（两遍）
cd paper
D:\texlive\2025\bin\windows\pdflatex.exe -interaction=nonstopmode main_nn.tex
D:\texlive\2025\bin\windows\pdflatex.exe -interaction=nonstopmode main_nn.tex
```

`_p1_add_joint_rows.py` 是**幂等**的：没有 joint 数据时它只报告缺什么、不改任何文件；有数据时插入表格行并把 §5 里"the control is one-armed"那段改写成对照版。

## 三、跑完后请核对三件事

1. **joint 严格跑的视觉张量非零数应 > 0**（因为视觉塔有适配器）——若仍为 0，说明配置没生效，别采信。
2. joint 的 CGΔ 若**显著差于** text-only（预期的方向）→ §5 的"适配器放哪里才是变量"这一结论得到直接支持，可以把"one-armed"的保留意见删掉。
3. joint 的 CGΔ 若**与 text-only 差不多** → 那"放在哪一侧"也不是原因，机理问题需要重新表述；**这种情况务必告诉我**，不要自行改稿。

## 四、不要重跑的东西（会覆盖已修好的产物）

- `paper/generate_figures.py`、`paper/scripts/generate_figures.py`：**已在文件头加弃用警示**——它们含审计发现的选择器缺陷，重跑会把 fig1/2/3/5/7 覆盖回错的。
- `paper/scripts/gsnr_analysis.py`：**已可重跑**（已加固定种子 42、面板 B 标题已修），但会覆盖 `outputs/gsnr_results.json`（旧值已存档为 `gsnr_results_pre_fix.json`）与 fig11，图注里的 1.4×/4.16/0.61 是当前值。
- 其余重画脚本：`paper/scripts/plot_fig{1,2,3,5,7}_*.py`，都是幂等的、可安全重跑。

## 五、当前状态速记

- 严格冻结 **text-only（5 seeds）已完成**：CGΔ −0.0465±0.0027、R@1 0.6238±0.0049、可训 196,608、`vision_model.*` 张量改动 **0/199**。
- 混合 text-only（历史）5-seed：CGΔ −0.0458±0.0021、R@1 0.621 → 两者 **Welch p=0.70**，这是"视觉侧附带更新是惰性的"这一结论的依据。
- 半成品 joint 跑（4/10 epoch）的产物**已删除**，避免被误当成结果。
