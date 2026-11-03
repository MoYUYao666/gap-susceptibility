# -*- coding: utf-8 -*-
r"""Record the upgrade-continuation round: P3 protocol clarification, A23 adapted-encoder certificate, extended transfer.

    python tools/_p1353_record_upgrade_round2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
PLAN = REPO / "docs" / "UPGRADE_PLAN_P3_A23_COMMENTARY_2026-10-19.md"
P3MEMO = REPO / "docs" / "P3_UPGRADE_MEMO_2026-10-19.md"
A23OBJ = REPO / "docs" / "A23_REVIEWER_OBJECTIONS.md"

PLAN_STATUS = """
---

## 执行状态·续（2026-10-19 18:50，第二轮补做）

| 项 | 状态 | 说明 |
|---|---|---|
| **P3-P0-2**（原"待裁决"）| ✅ **已解决并写入正文** | 追到 `paper3/scripts/run_full_sweep.py`：sweep 用 `run_training.py --epochs 3`，而 E2 族的轨迹在**同 rank 同 seed** 下完全不同（E0 3930.5 vs 3927，轨迹形状不同）⇒ 两族是**不同训练配置**、同一空白图协议。已在结论写入：dense 3-epoch sweep 的临界区间为 $[14,16]$，与 E2 的 $[5,6]$ 不同 ⇒ 临界 rank 连**超参**都随协议变，强化"属于协议不属于模型"的撤回表述 |
| **A23-P0-1**（原"负结果"）| ✅ **升级为适配模型实验并写入正文** | 发现本地其实有 **BioCLIP 基座 + OceanCLIP 权重**（`models/oceanclip-0.15b/`，open_clip 3.3.0）：在 67 类海洋子集与同一 gap-surgery 协议上，margin 质量与精度仅弱相关（$r=-0.35$ / $-0.56$），阈值跨编码器不迁移（BA 0.13–0.50）⇒ 作为"标量证书不能替代域内诊断"的证据写入，与论文结论一致 |
| **A23-P0-2**（扩展）| ✅ 已扩展并写入正文 | 从 8 个密集幅度臂扩到 **12 个归档域臂**（加 4 个 spectrum 臂）：跨域 BA 中位 **0.50**（机会）、范围 0.00–0.83；同时同域拟合降到 0.50–0.63 ⇒ 阈值需要足够幅度点才能拟合，进一步说明"绝对 gap 是各自测量网格的诊断" |
| **A1 的 checkpoint 复算** | ⏸ 不可行 | `outputs/a1_rr_ckpt/` 下无任何 `.pt`（目录为空）⇒ epoch-sweep 的逐 epoch margin 无法重算，监控声明的"内部最优点"验证仍留待未来 |
| P3-P2-7、C-P0-2 | ⏸ 仍暂缓（理由已记录） | 本地 CLIP 代理无法验证 LLaVA 协议；六实例表与 7 页上限冲突 |

**页数/状态**：P3 **10 页**、A23 **65 页**（+1 页）、Commentary **7 页**；均 0 错误 / 0 未定义 / 0 Overfull。P3 与 A23 复审 **READY/A**；Commentary 保持 READY/A。
"""

P3_NOTE = """
## 续：协议归属已澄清（2026-10-19 18:50）

追查 `paper3/scripts/run_full_sweep.py`：sweep 由 `run_training.py --rank R --seed S --epochs 3` 生成；E2 族在同一
rank/seed 下的轨迹不同（E0 3930.5 vs 3927，形状也不同），说明两族是**不同训练配置**、同一空白图协议。因此：
- E2 族：临界 bracket $[5,6]$（r=5 均值 3906 < 3927；r=6 均值 3989 > 3927）；
- dense 3-epoch sweep：$\\le14$ 收敛、r=16 两/三种子发散、r≥20 全部发散 ⇒ bracket $[14,16]$。
- 两族差异说明临界 rank 随**协议与超参**移动，正是论文"属于协议不属于模型"的撤回表述；已在 `sections/conclusion.tex`
  写入一句明确证据，不再有"未标注协议"的自相矛盾风险。
"""

A23_NOTE = """
## 续：适配模型证书与扩展阈值迁移（2026-10-19 18:50）

- **适配模型证书**（BioCLIP 基座 / OceanCLIP，67 类海洋子集，gap-surgery 同协议）：margin 质量与 top-1 相关仅
  $r=-0.35$（BioCLIP）/ $-0.56$（OceanCLIP，$\\varepsilon=0.05$）；阈值跨编码器迁移 BA $0.13$–$0.50$（机会 0.50）。
  ⇒ 标量证书不能替代域内诊断；已写入 `ext_partII_domains.tex` 并归档
  `outputs/analysis/a23_certificate_adapted.json`。
- **扩展阈值迁移**：12 个归档域臂（含 4 个 spectrum 臂）跨域 BA 中位 $0.50$、范围 $0.00$–$0.83$；同域拟合降至
  $0.50$–$0.63$ ⇒ 阈值需要足够幅度点才能拟合，已写入正文并归档 `a23_threshold_transfer_extended.json`。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    p = io.open(PLAN, encoding="utf-8").read()
    if "执行状态·续（2026-10-19 18:50" not in p:
        io.open(PLAN, "w", encoding="utf-8", newline="").write(p.rstrip() + "\n" + PLAN_STATUS)
        print("  plan status appended")
    m = io.open(P3MEMO, encoding="utf-8").read()
    if "协议归属已澄清" not in m:
        io.open(P3MEMO, "w", encoding="utf-8", newline="").write(m.rstrip() + "\n" + P3_NOTE)
        print("  p3 memo extended")
    o = io.open(A23OBJ, encoding="utf-8").read()
    if "适配模型证书与扩展阈值迁移" not in o:
        io.open(A23OBJ, "w", encoding="utf-8", newline="").write(o.rstrip() + "\n" + A23_NOTE)
        print("  a23 objections extended")
    h = io.open(HANDOFF, encoding="utf-8").read()
    ent = """> **🔁 2026-10-19 18:50 —— 升级继续：P3 协议归属查清并写入；A23 用本地 BioCLIP/OceanCLIP 补做证书实验**
>
> | 项 | 结果 |
> |---|---|
> | **P3** | 追到生成脚本：E2 族与 dense sweep 是**不同训练配置**（同 rank/seed 轨迹不同）⇒ 临界 bracket 从 $[5,6]$ 移到 $[14,16]$，正是"属于协议不属于模型"的更强证据；已写入 `conclusion.tex`；**10 页 0/0/0** |
> | **A23** | 发现本地有 **BioCLIP 基座 + OceanCLIP 权重**（open_clip 3.3.0）→ 完成原计划 P0-1：margin 质量与精度仅弱相关（$r=-0.35/-0.56$），阈值跨编码器不迁移（BA 0.13–0.50）⇒ 作为"标量证书不能替代域内诊断"写入；阈值迁移扩展至 **12 个域臂**（跨域 BA 中位 0.50，同域拟合降至 0.50–0.63）也写入；**65 页 0/0/0** |
> | **A1** | `outputs/a1_rr_ckpt/` 无 `.pt`，逐 epoch margin 无法重算 → 监控的内部最优点验证仍留待未来（已记录）|
> | 暂缓 | P3-P2-7 与 Commentary 六实例表维持暂缓（理由不变）|
>
> 归档：`a23_certificate_adapted.json`、`a23_threshold_transfer_extended.json`；P3/A23 复审 **READY/A**。
>

"""
    if "升级继续：P3 协议归属查清" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ent + h[j + 1:])
        print("  handoff entry added")
    mp = io.open(MAP, encoding="utf-8").read()
    row = ("112. 🔁 **升级继续（2026-10-19 18:50）** —— P3 协议归属查清（E2 与 sweep 为不同训练配置，临界 bracket [5,6]→[14,16] 已写入，"
           "强化协议依赖）；A23 用本地 BioCLIP/OceanCLIP 补做证书实验（弱相关 −0.35/−0.56、阈值不迁移 BA 0.13–0.50）并扩到 12 域臂"
           "（跨域 BA 中位 0.50）→ 均写入正文；P3 10 页、A23 65 页，0/0/0；A1 checkpoint 缺失已记录。\n")
    if "升级继续（2026-10-19 18:50）" not in mp:
        anchor = "111. ✅ **Paper A 进入 With Editor"
        idx = mp.find(anchor)
        assert idx >= 0
        end = mp.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp[: end + 1] + row + mp[end + 1:])
        print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
