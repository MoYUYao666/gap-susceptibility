# -*- coding: utf-8 -*-
r"""Record the cloud round (2026-10-24 evening) in the hand-off documents."""
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

entry = """> **☁️ 2026-10-24 19:30 —— 云端轮完成：解码器匹配阶梯（决定性）、451 题 VQA、A23 多编码器；实例已按规矩关机**
>
> - **云端实例**：AutoDL RTX 4080 SUPER 32 GB / torch 2.12.1+cu130；门禁 `cloud_next/verify_cloud_artifacts.py`
>   对 phase1、phase3 均 **PASS** → 产物全部取回本地并校验 → `shutdown` 已执行 → **端口探测 `False`（已关机）**。
>   phase2（torch 2.6 栈）是**本地**作业（云端没有 2.6 环境），phase4（A23 多编码器）本轮**缓办**（需 2.1 GB 语料 + ~7 GB 权重）。
> - **Paper A 新增 H.2「匹配阶梯」**（决定性）：同一协议（`marine_captions`、320 对、3 epochs、LoRA r8/a16、both 位点、seed 42）
>   只变目标函数与骨干：**Qwen2-VL-2B 对比 −88.79% / 生成 −3.64%（冻结 DG* 双臂完全一致）**；
>   **LLaVA-1.5-7B 对比 −65.07% / 生成 +16.12%**（生成臂轨迹 第1轮 −14.2% → 第2轮 +6.7% → 第3轮 +16.1% 过零）；
>   **Qwen2.5-VL-7B 生成 −34.42%**。⇒ **只变损失不能决定符号**：对比臂在两个骨干都缩小；扩大只出现在 LLaVA 家族 + 生成损失。
>   四条如实限定写进正文：单种子；4-bit 训练后不可逐位复现；LLaVA 对比臂因 1e-4 第 3 轮 NaN 改用 5e-5（A/B 冻结基线差 5.73%，`meta.ab_check` 记为 MISMATCH）；
>   3B 梯级未跑（磁盘）。页数 **NC 77→79 / Springer 54→56**，cover letter 与投稿包已同步。
> - **发现并更正的旧缺陷**：本地 2B 控制（`_p1595`）宣称的 64-token 图像上限在 transformers 5.x 下**被静默丢弃**，
>   实际跑在处理器默认分辨率（≈1200–2500 tokens/图）；归档保留不动，论文 H.1 已改为"默认分辨率下测得"并改引新的匹配阶梯。
>   更正记录 `docs/DECODER_CONTROL_CAP_CORRECTION_2026-10-24.md`；新脚本会记录 `image_token_budget_applied_via` 并在未生效时**中止**。
> - **P3 S28 全 451 题**（推理，复用机上 `r5_step`/`r6_step` 适配器，未重训）：token F1 两秩均优于 base；
>   accuracy 仅 r=5 解析（−0.0577 [−0.0976,−0.0177]）、r=6 与 base **等价**（TOST p=0.0057）；
>   **r5−r6 accuracy 反转 +0.0532 [+0.0222,+0.0865] 全测试集下更清晰、不成立等价**，token F1 仍等价（+0.0233，TOST p=0.0396）。
>   门禁 needle 同步更新（26 条须存在 + 20 条 300 题旧值须缺席）；supplement 仍 18 页。
> - **A23 多编码器迁移**（本地部分）：3 编码器 × 3 语料 = 5 单元、25 有序对、260 条跨单元条目；**7 条名义高于 chance、0 条通过图像 bootstrap**；
>   且**逐位复现**归档证书（4 单元 `max|Δ|=0`，128 个比较值）。正文负结论已按"仅本次选择所支持"放宽；页数仍 72。
> - **门禁总览**：六 profile **READY(A) 0 fail / 0 warn**；provenance **PASS**；台账 96/96、216/216、88/88；`final_verification` **ALL PASS**
>   （页数 **64 / 79 / 56 / 10 / 72 / 7**；新增 `decoder ladder integration` 35/35）。发布库 main 已含本轮全部脚本/归档/笔记（`1215fa0`），
>   `RELEASE_NOTES_v2.5.md` 已备但**未打 tag**（是否铸 v2.5 DOI 属对外可见决定，等操作者定）。
> - **仍在跑**：本地 torch 2.6 栈补种子（r5/r6 × seeds 7/123/999，约 55–65 min/run，预计 6 runs）；跑完用
>   `tools/_p1613_p3_cloud_runner.py --job env-seeds --aggregate --strict` 生成 `outputs/analysis/p3_env_stack_seeds.json` 再改 S29/S37。
>
"""

h = io.open("HANDOFF.md", encoding="utf-8").read()
if "云端轮完成" not in h:
    i = h.find("# 项目交接文档")
    j = h.find("\n", i)
    io.open("HANDOFF.md", "w", encoding="utf-8", newline="").write(h[:j + 1] + "\n" + entry + h[j + 1:])
    print("handoff updated")

m = io.open("文件地图.md", encoding="utf-8").read()
row = ("164. ☁️ **2026-10-24 19:30 —— 云端轮**：Paper A 新增 H.2 匹配阶梯（对比 −88.8/−65.1% vs 生成 −3.6/+16.1/−34.4%，"
       "只变损失不决定符号）；P3 S28 全 451 题（r5−r6 accuracy 反转 +0.0532 更清晰）；A23 多编码器 0/260 迁移存活且逐位复现归档；"
       "实例门禁 PASS→取回→关机；本地 torch26 补种子仍在跑。页数 NC 79 / Springer 56 / supp 18 / A23 72。\n")
if "云端轮" not in m:
    i = m.find("163. 🔖 **2026-10-24 17:45")
    e = m.find("\n", i)
    m = m[:e + 1] + row + m[e + 1:]
    io.open("文件地图.md", "w", encoding="utf-8", newline="").write(m)
    print("map updated")
print("done")