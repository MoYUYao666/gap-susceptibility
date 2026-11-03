# -*- coding: utf-8 -*-
r"""Record the execution of the P3 / A23 / Commentary upgrade packages.

    python tools/_p1348_record_three_upgrades.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
PLAN = REPO / "docs" / "UPGRADE_PLAN_P3_A23_COMMENTARY_2026-10-19.md"

STATUS = """
---

## 执行状态（2026-10-19 18:20，全部本地）

| 项 | 状态 | 交付物 |
|---|---|---|
| P3-P0-1 配对区间 | ✅ 完成并**已入稿**：同种子同 rank 配对 $n{=}4$，guided 臂末端能量 $+11.5$，95% CI $[+6.8,+16.2]$（方向不利于 guided） | `outputs/analysis/p3_upgrade_analysis.json`；`sections/experiments.tex` |
| P3-P0-2 族内 r_c | ⚠️ **核验完成、未入稿**：E2 确认 $[5,6]$（r=5 均值 3906 < 3927；r=6 均值 3989 > 3927）；独立 sweep 给出 $[14,16]$（r≤14 收敛、r=16 两/三种子发散、r≥20 全部发散）。两族须在下一版**显式标注协议**后再写，避免自相矛盾 | `docs/P3_UPGRADE_MEMO_2026-10-19.md` |
| P3-P0-3 AdaLoRA | ✅ 核验：归档 $\Delta E=-1468.15$（$3\times10^{-4}$）与 $-757.30$（$10^{-3}$）与稿件**完全一致**，无需改 | `_p458_adalora_lr*.txt` |
| P3-P0-4 重编译+回复骨架 | ✅ 10 页 0/0/0；回复骨架见 `docs/P3_REVIEWER_OBJECTIONS.md` | `main.pdf` |
| P3-P1-5/6 | ✅ 意见包 8 条；死标签、未用 bib、PDF title 全部清掉 | `docs/P3_REVIEWER_OBJECTIONS.md` |
| P3-P2-7 本地 Γ 控制 | ⏸ **暂缓（有理由）**：通用 CLIP 代理无法验证 LLaVA 协议主张；记录于 memo | — |
| P3-P2-8 改投包 | ✅ `SUBMISSION/_venue_builds/P3_PRL_next/` | — |
| A23-P0-1 证书 | ⚠️ **负结果并记录**：通用 CLIP 在 fathomnet8/NKSID 上 margin 质量饱和（$M\approx1$，相关性不可定义），原因是从冻结模型精度仅 20–27%；OceanCLIP 权重本地缺失，改用归档 margins 不可行。作为 negative control 归档，不入正文 | `outputs/analysis/a23_certificate_control.json`；`docs/A23_REVIEWER_OBJECTIONS.md` |
| A23-P0-2 阈值迁移 | ✅ **已入稿**：同域 BA 0.83，跨域/跨模型 0.25–0.67（机会 0.50），双向报告 | `a23_threshold_transfer.json`；`ext_partII_domains.tex` |
| A23-P0-3 对称手术+CI | ✅ 归档核验：image-side 12 个幅度 + text-side $\lambda{=}1.0$（clip_frozen 与 sonar_ft 均有） | `sonar_protocol.json`；memo |
| A23-P0-4/P1-5…7 | ✅ 意见包 8 条；死标签引用、PDF title、1 条新引用；字体警告记录为 IEEEtran scit→it 替换（外观无损） | `docs/A23_REVIEWER_OBJECTIONS.md`；`main_ieee.pdf` 64 页 0/0/0 |
| A23-P2-8 域外复现 | ⚠️ 与 P0-1 同一控制，结论为负（饱和），已记录 | 同上 |
| C-P0-1 划界 | ✅ **已入稿**：3 条 2026 引用（Sharma/Yaras/Role-Ambard）+ 一句划界（"解释 gap 为何重要" vs "哪个数字可比"） | `MANUSCRIPT.md`；`_refs_used.json` 48 条 |
| C-P0-2 六实例表 | ⏸ 表格试加后**为守 7 页上限移除**；六实例仍为正文段落，逐条可核对 | `docs/COMMENTARY_REVIEWER_OBJECTIONS.md` |
| C-P0-3 POPE/MMBench 复核 | ✅ 两条头条数字均按原引用标注（LLaVA-1.5 表头三子集；MMBench circular 36.7→2.6），未新增未标注数字 | 同 memo |
| C-P1-4/5/6 | ✅ 意见包 6 条；死标签 `fig:decision` 由 builder 改为 `\\ref`；PDF title 元数据 | builder patch |
| C-P2-7 投稿包 | ✅ `SUBMISSION/_venue_builds/Commentary_PRL_next/` | — |
| **页数** | P3 **10 页**；A23 **64 页**；Commentary **7 页**（守上限）；均 0 错误 / 0 未定义 / 0 Overfull | 审计见 `docs/audits/` |

**纪律**：`SUBMISSION/` 冻结包与 `_frozen_submitted/` 未动；新包只写入 `SUBMISSION/_venue_builds/`；全部本地，GPU 仅 A23 控制 ~2 min 与检索无关任务，峰值内存 <4 GB。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    p = io.open(PLAN, encoding="utf-8").read()
    if "执行状态（2026-10-19 18:20" not in p:
        io.open(PLAN, "w", encoding="utf-8", newline="").write(p.rstrip() + "\n" + STATUS)
        print("  plan status appended")
    h = io.open(HANDOFF, encoding="utf-8").read()
    ent = """> **🚀 2026-10-19 18:20 —— P3/A23/Commentary 三稿升级包执行完毕（本地）：P3 10 页、A23 64 页、Commentary 7 页，均 0/0/0**
>
> 按 `docs/UPGRADE_PLAN_P3_A23_COMMENTARY_2026-10-19.md` 全部执行，结果分三类：
>
> | 稿 | 已入稿的升级 | 核验后不改/负结果 | 交付 |
> |---|---|---|---|
> | **P3** | 配对区间（$+11.5$，CI $[6.8,16.2]$，方向不利于 guided）；死标签/未用 bib/PDF title 清掉 | AdaLoRA $-1468.15$/$-757.30$ 与稿件**一致**；E2 确认 $r_c\\in[5,6]$，独立 sweep 为 $[14,16]$ → **协议标注待作者裁决**，本轮不写 | 10 页 0/0/0；`docs/P3_REVIEWER_OBJECTIONS.md`、`docs/P3_UPGRADE_MEMO_2026-10-19.md`、`_venue_builds/P3_PRL_next/` |
> | **A23** | **跨域阈值迁移已入稿**（同域 BA 0.83 → 跨域 0.25–0.67，双向）；对称手术核验；死标签/title/引用 | margin 证书在通用 CLIP 上**饱和失效**（$M\\approx1$，冻结精度仅 20–27%）→ 记为 negative control，不入正文 | 64 页 0/0/0；`docs/A23_REVIEWER_OBJECTIONS.md`、`_venue_builds/A23_JOE_next/` |
> | **Commentary** | 3 条 2026 引用 + 划界句已入稿；`fig:decision` 死标签由 builder 修好；PDF title | 六实例汇总表试加后**为守 7 页上限移除**；正文压缩 4 处、参考文献 `\\footnotesize` | **7 页**、builder 检查全过；`docs/COMMENTARY_REVIEWER_OBJECTIONS.md`、`_venue_builds/Commentary_PRL_next/` |
>
> 冻结包与 `_frozen_submitted/` 未动；新包只在 `SUBMISSION/_venue_builds/`。三稿审计仅剩 `A-01`（提交后消除）与各自 pakcage 差异。
>

"""
    if "P3/A23/Commentary 三稿升级包执行完毕" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ent.replace("\\n", "\n") + h[j + 1:])
        print("  handoff entry added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("109. 🚀 **P3/A23/Commentary 升级包执行（2026-10-19 18:20）** —— P3 **10 页**（配对区间入稿；AdaLoRA 核验一致；"
           "r_c 协议标注待裁决）、A23 **64 页**（跨域阈值迁移入稿；证书负结果记录）、Commentary **7 页**（3 条 2026 引用+划界；"
           "死标签与 title 修复；六实例表为页限移除）；均 0/0/0；新包在 `SUBMISSION/_venue_builds/`，冻结包未动。\n")
    if "P3/A23/Commentary 升级包执行（2026-10-19 18:20）" not in m:
        anchor = "108. ✅ **A1 状态更新：With editor"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
