# -*- coding: utf-8 -*-
"""Record the cloud round, the cleanup and the final revision re-check."""
import io
import json
import os

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
GAPS = "docs/P3_REMAINING_GAPS_2026-10-22.md"
AUD = "docs/P3_RESUBMISSION_AUDIT_2026-10-21.md"
EXP = "paper3/scripts/outputs/experiments"
AN = "outputs/analysis"


def jl(p):
    return json.load(io.open(p, encoding="utf-8"))


def main() -> int:
    lr = {r: jl(os.path.join(EXP, f"verify_r{r}_s42.json")) for r in (5, 6)}
    crop = jl(os.path.join(AN, "p3_rerun_protocol.json"))["runs"]
    cl = {r: jl(os.path.join(EXP, f"cloud_verify_r{r}_s42.json")) for r in (5, 6)}
    vqa = {k: jl(os.path.join(AN, f"cloud_p3_vqa_downstream_{k}.json")) for k in ("base", "5", "6")}
    q7 = []
    import glob
    for f in sorted(glob.glob(os.path.join(EXP, "*cloud_q25_7b*.json"))):
        d = jl(f)
        q7.append((d["rank"], d["seed"], d["delta_E"]))
    entry = """> **☁️ 2026-10-22 19:30 —— 云端跑完：第二环境复现 + 7B 新族 + per-step VQA；并清理 44 GB 本地冗余**
>
> **云端结果（RTX 4080 SUPER，torch 2.12.1+cu130）**
>
> | 任务 | 结果 |
> |---|---|
> | R3.18 第二环境复现（r5/r6 seed42）| 本地 −10.5/+115.0（E0 3921.0）vs 云端 **−33.5/+81.5**（E0 3926.0）→ **符号模式保持**，E0 差 0.1% |
> | R1.4 新族（Qwen2.5-VL-7B）| r5 **−2112/−2112**、r6 **−2176/−2048**（两个 seed）→ **两 rank 均负，无 crossing**（3B 亦无）|
> | R2.3/R3.16 VQA（per-step 80 训练对）| base **0.340/0.354**、r5 **0.320/0.328**、r6 **0.340/0.348** → 两个 rank 都**没有提升** |
>
> 论文：新增 **S29**（第二环境表）、S20 增加 7B 表、S28 改为 per-step 数字；S17 增加"环境符号保持"行；
> 补充 **S1–S29（12 页）**、正文 10 页；`audit_check`/`audit_pdf` 0/0；provenance gate PASS（P3 floats=21）。
>
> **清理**：本地删除 llava-hf `.git` LFS 副本、`_modelscope_cache`、重复权重格式、Qwen 2B/3B 模型、dtd tar 等，
> 共释放 **约 44 GB**（models 65→21.6 GB）；云端删除不完整 hf LLaVA、旧 `/root/p3` 数据/输出等约 **9 GB**。
>
> **最终 revision 复核**：33 条全部有实测/归档/稿内位置（R3.18 已闭环）；仅剩说明项：S27 为块级再实现（非官方代码）、
> S28 VQA 训练规模 80 对。**0 条未解决。**
>

"""
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "云端跑完：第二环境复现" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + entry + h[j + 1:])
        print("handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("148. ☁️ **云端结果 + 清理（2026-10-22 19:30）** —— 第二环境：本地 −10.5/+115 vs 云端 −33.5/+81.5（符号保持）；"
           "Qwen2.5-7B 两 rank 均负（无 crossing）；VQA per-step 无提升；新增 S29；本地清理 44GB。\n")
    if "云端结果 + 清理" not in m:
        i = m.find("147. 🐞 **代码审计/修 bug")
        if i < 0:
            i = m.find("146. 🧾 **本地完成/云端待实例")
        assert i >= 0
        end = m.find("\n", i)
        m = m[: end + 1] + row + m[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(m)
        print("map updated")
    g = io.open(GAPS, encoding="utf-8").read()
    final = """

## 十、最终状态（2026-10-22 19:30，云端完成）

- 33 条 R1 意见：**全部有实测/归档/稿内位置（33/33）**；R3.18 由第二环境复现闭环（本地 −10.5/+115 vs 云端 −33.5/+81.5，符号保持）。
- 剩余仅为说明项、不是缺实验：
  1. S27 的 HALoRA/IGU/Shap 规则是块级再实现（论文如实写明，不冒充官方代码）；
  2. S28 的 VQA 为 per-step 80 训练对的小规模检查（非 benchmark 规模）；
  3. 云端与本地 CUDA 相同（13.0）、torch/GPU 不同（2.9 vs 2.12；4060 vs 4080 SUPER）。
"""
    if "## 十、最终状态" not in g:
        io.open(GAPS, "w", encoding="utf-8", newline="").write(g.rstrip() + final)
        print("gaps updated")
    a = io.open(AUD, encoding="utf-8").read()
    if "云端收尾" not in a:
        a = a.rstrip() + "\n\n## 十二、云端收尾（2026-10-22 19:30）\n\n新增 S29（第二环境）、S20 7B 表、S28 per-step 数字；补充 S1–S29（12 页）；audit 0/0；provenance PASS（P3 floats=21）。\n"
        io.open(AUD, "w", encoding="utf-8", newline="").write(a)
        print("audit updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
