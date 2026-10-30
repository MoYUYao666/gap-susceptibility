# -*- coding: utf-8 -*-
"""Final revision re-check after the third gap-fill round; record the cloud hand-off state."""
import io
import json

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
GAPS = "docs/P3_REMAINING_GAPS_2026-10-22.md"

FINAL = """

## 九、最终 re-check（2026-10-22 16:00，本地全部完成）

按 R1 的 33 条逐条复核（当前下一版草稿：正文 10 页 + 补充 11 页 S1–S28）：

- **32 条已解决**（有实测/归档/稿内位置）；
- **1 条待云端**：R3.18 第二环境复现——本地已做 5 seed + transformers 4.57/5.16 对照，剩 CUDA/PyTorch/硬件矩阵，
  云包 `cloud_p3/` 与 `docs/P3_CLOUD_RUNBOOK_2026-10-22.md` 已备好，AutoDL 实例需操作者开机并提供新 SSH 端口/密码；
- **0 条未处理**。

现在剩下的"非证据性说明"只有三条，且都不是缺实验：
1. R3.18 的云端机器差异（待跑，不是限制）；
2. S27 的 HALoRA/IGU/Shap 是块级再实现（论文里如实写明，不冒充官方实现）；
3. S28 的 VQA-RAD 训练样本为 40（本地冒烟尺度）；云端 runbook 已给 200 样本版本用于放大。
"""


def main() -> int:
    g = io.open(GAPS, encoding="utf-8").read()
    if "## 九、最终 re-check" not in g:
        io.open(GAPS, "w", encoding="utf-8", newline="").write(g.rstrip() + FINAL)
        print("gaps final updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    entry = """> **🧾 2026-10-22 16:00 —— 本地全部完成 + 冒烟测试通过；云端待实例**
>
> - 第三轮补齐：S27 分配规则基线（HALoRA/IGU/Shap 样式训练 arm +284/+333/+444）、S28 VQA-RAD 下游
>   （base/r5/r6 accuracy 0.340、F1 0.354，无提升）；
> - 补充 S1–S28（11 页）、正文 10 页；`audit_check`/`audit_pdf` 0/0；provenance gate PASS（19 floats）；final verify ALL PASS；
> - 冒烟测试：VQA base + 12-sample 训练 arm 通过；云包 `cloud_p3/` 编译通过；
> - 按 revision 33 条最终复核：**32 已解决、1 待云端（R3.18）、0 未处理**；说明项仅"再实现非官方/样本尺度/云机差异"三条；
> - 云端运行手册 `docs/P3_CLOUD_RUNBOOK_2026-10-22.md`；**待操作者开机 AutoDL 并提供新 SSH 端口/密码**。
>

"""
    if "本地全部完成 + 冒烟测试通过" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + entry + h[j + 1:])
        print("handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("146. 🧾 **本地完成/云端待实例（2026-10-22 16:00）** —— S27 规则基线 + S28 VQA-RAD；补充 S1–S28；"
           "33 条复核 32 解 1 待云；`cloud_p3/` + runbook 就绪。\n")
    anchor = "145. 🧪 **R1 剩余项第三轮"
    if "本地完成/云端待实例" not in m:
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        m = m[: end + 1] + row + m[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(m)
        print("map updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
