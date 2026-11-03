# -*- coding: utf-8 -*-
r"""Record the upgrade-round phase (Round 1-3, provenance, package fix) in the hand-off documents.

    python tools/_p1446_record_upgrade_phase.py --apply
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")
EVID = os.path.join(REPO, "docs", "EVIDENCE_MAP_2026-10-19.md")

ENTRY = """> **🧪 2026-10-20 19:30 —— 五稿升级轮（Round 1–3）+ 溯源硬规则落地 + 修回包独立编译修复**
>
> | 项 | 结果 |
> |---|---|
> | **溯源硬规则** | 写入 `AGENTS.md`/`CLAUDE.md`；`docs/provenance_manifest.json` 覆盖 **98 floats（95 verified + 3 exempt）**；门禁 `tools/_p1428_provenance_gate.py` **PASS**；A1/A23/PaperA 各加 `Data and code provenance` 附录，P3 补充材料 **S13** |
> | **页数变化** | A1 61→**63**、A23 66→**68**、Paper A NC 72→**74**（Springer 52→**53**）、P3 正文仍 **10** + 补充 **6**；全部 0 错 0 overfull；cover letter 自动同步 |
> | **Round 1** | A1 检索监控（regret 0.7 vs 末轮 2.9）；训练集 mass **负结果**（1.43 vs 留出 1.04，非解法）；早停省 **2.6 epoch**、代价 +0.06；A23 n_eval 下限（<100 张不可靠）；Paper A ODE 拟合范围（LoRA 95% runs R²>0.9、full-FT 64%、adapter 仅 7%）；跨稿一致性报告（33 shared numbers、页数/DOI 一致）|
> | **Round 2** | P3 补 seeds（目标 5/rank）与 num-samples 消融**进行中**；A1 双塔 LoRA **待跑**（GPU 被 P3 占用）|
> | **Round 3** | 五包 staged 编译 **1:1 通过**（修复打包器：递归收 sections/supplementary、图收 png/jpg/eps、staged 加 bibtex）；A23/Commentary 回复骨架写好；Commentary 文献刷新（arXiv:2603.09095，**未入正文**，规避 7 页限制）|
> | **A23 water-tank96 复跑** | 两编码器 top-1 8.9–18.5 / 4.3–17.5（机会 9.1%），r 为负 ⇒ **OOD 边界**，归档 `outputs/analysis/a23_watertank_domain.json`，**未入稿**（与既有 water-tank 行重复，避免误导）|
> | **DeepInfer** | 仅支持 DeepSeek-V4.1-Flash、需 SM100/昇腾950，本地 4060 不可运行、无 VLM 支持 ⇒ 无直接价值，notes 见 `docs/DEEPINFER_NOTES_2026-10-20.md` |
> | **镜像** | git mirror `e8e2f16` 之后新增内容尚未推送（按"修回包确认后再推"的既有规则）|
>
> 待办：P3 5-seed 统计与消融入稿（可能新增补充表 S14）、A1 双塔 LoRA、六稿终检、mirror push、**v2.1 release（只列包含部分、无论文细节）**。
>

"""

ROW = ("125. 🧪 **五稿升级轮 + 溯源硬规则 + 包修复（2026-10-20 19:30）** —— provenance manifest 98 floats/gate PASS、"
       "四稿 provenance 附录入稿（A1 63、A23 68、PaperA 74/53、P3 10+6）；Round 1 三项分析入稿 + 负结果如实；"
       "Round 3 五包 staged 编译 1:1（修打包器缺 sections/supplementary/PNG 图）；A23/Commentary 回复骨架；"
       "P3 seeds/消融与 A1 双塔 LoRA 仍在跑；v2.1 待终检后发布。\n")

EVID_ROWS = """| `a1_monitor_trainmass.json` | A1 训练集 margin 监测（4 域 × 10 epoch） | `tools/_p1410_a1_trainmass.py` |
| `a1_monitor_bothtower.json` | A1 双塔 LoRA 监测（dtd/food101） | `tools/_p1411_a1_bothtower.py` |
| `a1_retrieval_monitor.json` | A1 检索监控（marine captions 400/137） | `tools/_p1412_a1_retrieval_monitor.py` |
| `a1_round1_analysis.json` | A1 Round-1 汇总（规则 regret / 省 epoch） | `tools/_p1434_a1_round1_analysis.py` |
| `a23_watertank_domain.json` | water-tank96 gap-surgery（OOD 边界） | `tools/_p1414_a23_watertank.py` |
| `a23_neval_sensitivity.json` | A23 n_eval 敏感性（32/64/128/256/all） | `tools/_p1415_a23_neval.py` |
| `paperA_ode_residuals.json` | Paper A ODE 拟合残差结构 | `tools/_p1440_paperA_ode_residuals.py` |
| `cross_paper_consistency.json` | 五稿共享数字/页数/DOI 一致性 | `tools/_p1442_cross_paper_consistency.py` |
| `staged_package_check.json` | 五个修回包独立编译 1:1 校验 | `tools/_p1444_staged_package_check.py` |
| `provenance_manifest.json` | 98 float → 脚本 → JSON 清单 | `tools/_p1428_provenance_gate.py` |
| `p3_rerun_seeds.json` / `p3_numsamples_ablation.json` | P3 补 seeds / 协议消融（进行中） | `tools/_p1416_p3_seeds.py` / `tools/_p1417_p3_numsamples.py` |
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "五稿升级轮（Round 1–3）" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENTRY + h[j + 1:])
        print("  handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    if "五稿升级轮 + 溯源硬规则" not in m:
        anchor = "124. 🧹 **Tier A+B 升级"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + ROW + m[end + 1:])
        print("  map updated")
    if os.path.exists(EVID):
        e = io.open(EVID, encoding="utf-8").read()
        if "a1_monitor_trainmass.json" not in e:
            io.open(EVID, "w", encoding="utf-8", newline="").write(e.rstrip() + "\n" + EVID_ROWS)
            print("  evidence map updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
