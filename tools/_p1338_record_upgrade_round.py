# -*- coding: utf-8 -*-
r"""Record the upgrade round (P0-P2, all local) in HANDOFF and the file map.

    python tools/_p1338_record_upgrade_round.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

ENT = """> **🚀 2026-10-19 13:40 —— 升级包 14 项全部本地完成：A1 **60 页**、Paper A **72/52 页**；台账 **179/179、88/88、96/96**
>
> 按 `docs/UPGRADE_PLAN_2026-10-19.md` 执行（全程本地、峰值内存 <8 GB、未跑云端）：
>
> | 项 | 结果 |
> |---|---|
> | **P0-1 证书监控** | 18-run campaign 与 6-epoch 同域控制**均为单调下降**（无内部最优点）⇒ 如实改为"监控统计量 + 范围声明"，**不宣称**验证过的早停规则；within-run $r(M)=-0.99$ vs CG $-0.43$ |
> | **P0-2 模板稳健性** | 10 模板 × 5 骨干：CG 移动 0.025–0.094、$M(0.01)$ 仅 0.032–0.047；$r(M,\\text{top-1})=-0.91..-0.84$，CG 为 $-0.16..+0.20$ |
> | **P0-3 秩×位置** | 归档 ODE 拟合：秩扫描下 $\\alpha$ 基本平坦（Spearman −0.46/−0.18）⇒ 位置效应**不是容量假象**；家族分离在 $\\alpha$ 与 $R^2$ 上都可见 |
> | **P0-4 ODE 诊断** | 96 runs：均值 $R^2=0.858$、中位 0.94；LoRA text-only 100% >0.9，adapter 0.61–0.73 为失败集中区 |
> | **P1-5 定理推广** | 新增 **Corollary**：任意均值函数（非线性、非范数）同样被零均值扰动骗过 |
> | **P1-6 检索真实微调** | 400/136 划分，R@1 18.4→29.4，CG 0.95→0.49；$r(\\mathrm{CG})=-0.49$，$r(M_R)=-0.71$（证书更强）|
> | **P1-7 / P2-12 图** | A1 campaign 双联图、Paper A 机制示意图；均 CID TrueType（TNR/STIX）|
> | **P2-11 跨域** | fathomnet8 4 runs：top-1 44.4–54.6%，$r(M)=-0.59$、$r(\\mathrm{CG})=+0.75$（符号再次翻转）|
> | **P1-9 审稿包** | `docs/A1_REVIEWER_OBJECTIONS.md`、`docs/PAPERA_REVIEWER_OBJECTIONS.md` |
> | **P2-13 / P2-14** | `_p1336_build_venue_package.py`（dry-run 通过）、`docs/EVIDENCE_MAP_2026-10-19.md` |
>
> 编译：A1 **60 页**、Paper A NC **72** / Springer **52**，全部 0 错误 / 0 未定义 / 0 Overfull；
> 台账 **179/179、88/88、96/96**；冻结包未动（A1 审计预期保留 I-02：包 58 vs 本地 60 页）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "升级包 14 项全部本地完成" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff entry added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("104. 🚀 **升级包 14 项执行完成（2026-10-19 13:40）** —— P0-1…P2-14 全部本地完成（峰值内存 <8 GB）：A1 **60 页**、"
           "Paper A **72/52 页**；新增 Corollary、certificate/template/retrieval/cross-domain 归档与两图；台账 **179/179、88/88、96/96**；"
           "冻结包未动。详见 `docs/UPGRADE_PLAN_2026-10-19.md` 末节。\n")
    if "升级包 14 项执行完成" not in m:
        anchor = "103. 🗺️ **A1 + Paper A 升级包方案"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
