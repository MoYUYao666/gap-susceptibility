# -*- coding: utf-8 -*-
"""Record round-3 (allocation-rule baselines + VQA-RAD downstream) in the hand-off documents."""
import io
import json
import os

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
GAPS = "docs/P3_REMAINING_GAPS_2026-10-22.md"
AUD = "docs/P3_RESUBMISSION_AUDIT_2026-10-21.md"
AN = "outputs/analysis"


def load(name):
    p = os.path.join(AN, name)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def main() -> int:
    rules = load("p3_baseline_rules.json")
    vqa = {k: load(f"p3_vqa_downstream_{k}.json") for k in ("base", "5", "6")}
    v = {k: x for k, x in vqa.items() if x}
    vqa_line = "; ".join("%s acc=%.3f F1=%.3f" % (k, x["accuracy"], x["token_f1"]) for k, x in v.items())
    entry = """> **🧪 2026-10-22 15:40 —— R1 剩余项第三轮：分配规则基线（S27）与 VQA-RAD 下游**
>
> | 缺口 | 新内容 | 结果 |
> |---|---|---|
> | R2.4/R3.9 HALoRA/IGU/Shap 样式 | **S27** `tab:rules` + `tab:rulearms` | 规则分配：HALoRA (2/4/6/4)、IGU (11/1/3/1)、Shap (10/2/3/1)；训练 arm ΔE 分别为 **+284.0 / +333.0 / +444.0**（均为正、未改善）|
> | R2.3/R3.16/R3.23 VQA-RAD | **S28** `tab:vqa` | %(vqa)s（base 与训练 arm 对比；VQA-RAD 是检索/描述/指令之外的第二个任务族）|
>
> 补充材料 **S1–S28**、正文 10 页；`audit_check`/`audit_pdf` 0/0（编译通过后更新页数）。
> **云端待办**：第二环境复现（R3.18）与 VQA 扩大样本（200 train）——本地已通过冒烟测试，
> 云包在 `cloud_p3/`，运行手册 `docs/P3_CLOUD_RUNBOOK_2026-10-22.md`；AutoDL 实例当前关机，需操作者开机并给新 SSH 端口/密码。
>

""" % {"vqa": vqa_line or "running"}
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "R1 剩余项第三轮" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + entry + h[j + 1:])
        print("handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("145. 🧪 **R1 剩余项第三轮（2026-10-22 15:40）** —— S27 分配规则基线（HALoRA/IGU/Shap 样式，"
           "训练 arm +284/+333/+444）；S28 VQA-RAD 下游（%s）；云包 `cloud_p3/` 就绪，待实例。\n" % (vqa_line or ""))
    anchor = "144. 🧪 **R1 剩余项第二轮"
    if "R1 剩余项第三轮" not in m:
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        m = m[: end + 1] + row + m[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(m)
        print("map updated")
    g = io.open(GAPS, encoding="utf-8").read()
    add = """

## 八、第三轮补充后（2026-10-22 15:40）

- **R2.4/R3.9**：HALoRA/IGU/Shap 样式的块级规则已实现并训练（S27，arm ΔE +284/+333/+444）；
  仍非官方实现（这是唯一保留的说明，而不是缺失实验）。
- **R2.3/R3.16/R3.23**：VQA-RAD 下游已跑（S28），第二个任务族与数据族均已覆盖。
- **R3.18**：第二环境复现仍需云端；云包与 runbook 已备好，等 AutoDL 实例开机。
"""
    if "## 八、第三轮补充后" not in g:
        io.open(GAPS, "w", encoding="utf-8", newline="").write(g.rstrip() + add)
        print("gaps updated")
    a = io.open(AUD, encoding="utf-8").read()
    if "第三轮补充" not in a:
        a = a.rstrip() + "\n\n## 十一、第三轮补充（2026-10-22，S27–S28）\n\n分配规则基线（S27）与 VQA-RAD 下游（S28）已入稿；补充材料 S1–S28。\n"
        io.open(AUD, "w", encoding="utf-8", newline="").write(a)
        print("audit updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
