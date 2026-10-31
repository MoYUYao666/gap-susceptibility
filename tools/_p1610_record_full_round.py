# -*- coding: utf-8 -*-
"""Record the full 2026-10-24 statistics/evidence round before creating v2.4."""
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

entry = """> **📊 2026-10-24 17:30 —— 全篇提升轮：统计加固 + 三处内容缺口闭合；六 profile READY(A)、final_verify ALL PASS**
>
> - **Paper A（NC 77 页 / Springer 54 页）**：
>   ① **新增 H.1「只变 loss 的对照」**——同一 Qwen2-VL-2B、同数据/预算/位点（160 对、batch 4、1 epoch、bf16、both 臂），
>   **对比目标 Δ=−73.5%**（DG* 1.0703→0.2832）vs **生成目标 Δ=−14.2%**（→0.9180）：**两者都缩小、目标只改幅度不改符号**
>   ⇒ 把 H 节从"无法归因"升级为"目标不是符号来源"（归档 `outputs/analysis/qwen_objective_control_{contrastive,generative}_both_seed42.json`，脚本 `tools/_p1595_qwen_objective_control.py`）；
>   ② 种子级 bootstrap CI 入稿（CLIP B/32 r8 text−vision −0.057[−0.063,−0.052]、SigLIP 反转 +0.014[+0.008,+0.018]）；
>   ③ 修正两处 caption 缺陷：`tab:position_strict` 的 sd 范围不再覆盖 BioCLIP（单列 0.002/0.010/0.015）；`tab:vlm`/`tab:llava` 明示为**总体 sd (ddof=0)**；
>   ④ `tab:llava` 补配对结果 both−vision **−25.81[−33.25,−13.48]**（保留非配对保留意见）；页数 75→77，cover letter 同步；
> - **P3（supplement 17→18 页，main 仍 10 页）**：S33 用**精确** 15 对置换矩阵（14/15 分离、10 对取到最小可达 p=1.08e-5；唯一不分离 **r7-vs-r8 p=0.0709**，并声明以精确检验为准）；
>   **r=5 TOST 限定**：十种子组**不等于零**（p=0.652，95% [−71.43,−15.97]），只是负侧最小；S28 加 VQA 等价（token F1 TOST p=0.0074；准确率 r5−r6 反转 +0.0433[0.0033,0.0833] 且不达等价）；
>   **F6 修正**：1434/4302 → 归档支持的 **1793 pairs / 3 epochs**（步数如实记为"未归档"）；S29 caption 补全 torch2.6 两行文件全名；S17 行同步；`+1478` 舍入更正为 **+1477**（3 处，门禁 needle 同步）；
> - **A1（64 页）**：① 溯源附录 `tab:monitor_regret` 由"一个 archive 覆盖 10 格"改为**逐格指名**（`a1_monitor_combined.json::per_run` 等）；
>   ② 监测不确定度改写为 **run 级 bootstrap**（0.58[0.28,0.93]、3.55[2.42,4.71]、0.52[0.26,0.79]、配对 +0.06[−0.34,+0.50] 不排除零），并说明 0.37/1.08 只是 run 内二项 SE；
> - **A23（70→72 页）**：细 ε 网格重算推翻"证书失效"的表述——**饱和来自网格太粗**：ε=0.001 时 32/32 配置脱离饱和，pooled r **−0.98（控制）/ −0.90（适配）**；
>   域相对分辨率（ε=c·median margin，c=0.01–0.02）使四域内部 r∈[−1.00,−0.87]，但**跨域阈值仍不迁移**（BA≤0.55）；
>   稿内删去已为假的"which we have not performed"，加 Source 行；附录新增归档卫生 (iv)（7 类非 8 类、chance 14.29%、NKSID `tire` 834 张在根目录被静默跳过、`M(0.01)` 键从未测过）；
>   **并修掉 `_p1472` 的 reproduction 空转 bug**（键名 `mass_0p02` vs 归档 `mass_0.02`）：现控制臂 42 对**逐位一致**、适配臂 ≤0.00995，稿内据实表述；
> - **Commentary（7 页，余量增大）**：13 处经校验的精简（**−198 词**）+ 新增**"两个决策 × 方法族"表**（每行带出处）+ **撤掉 Figure 1**（其两处 placement 无出处；同时消除 F1 裸"1"引用）；重建后末页行数 118→70，构建门禁全过；
> - **门禁**：六 profile **READY(A)、0 fail/0 warn**；provenance **PASS**；台账 96/96、A1 216/216、Paper A 88/88；staged 包 5/5 编译一致（PaperA 77/77）；`final_verification` **ALL PASS**（页数 64/77/54/10/72/7）。
>
"""

h = io.open("HANDOFF.md", encoding="utf-8").read()
if "全篇提升轮" not in h:
    i = h.find("# 项目交接文档")
    j = h.find("\n", i)
    io.open("HANDOFF.md", "w", encoding="utf-8", newline="").write(h[:j + 1] + "\n" + entry + h[j + 1:])
    print("handoff updated")

m = io.open("文件地图.md", encoding="utf-8").read()
row = ('162. 📊 **2026-10-24 17:30 —— 全篇提升轮**：Paper A 加"只变 loss"对照（对比 −73.5% vs 生成 −14.2%）与 bootstrap；'
       'P3 精确 15 对矩阵 + TOST + VQA 等价；A1 溯源逐格 + run 级 bootstrap；A23 细 ε 网格（饱和系网格所致、域内可用、跨域不迁移）；'
       'Commentary −198 词 + 两决策表 + 撤 Figure 1；六 profile READY、final_verify ALL PASS。\n')
if "全篇提升轮" not in m:
    i = m.find("161. 🧩 **2026-10-24 15:15")
    e = m.find("\n", i)
    m = m[:e + 1] + row + m[e + 1:]
    io.open("文件地图.md", "w", encoding="utf-8", newline="").write(m)
    print("map updated")
print("done")