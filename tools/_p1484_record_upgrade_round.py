# -*- coding: utf-8 -*-
r"""Record the five-paper claim-upgrade round."""
from __future__ import annotations

import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")
EVID = os.path.join(REPO, "docs", "EVIDENCE_MAP_2026-10-19.md")

ENTRY = """> **⬆️ 2026-10-21 14:05 —— 五篇"升级主张"落地（新论文只记录、暂不启动）**
>
> | 稿 | 新增升级 | 结果 |
> |---|---|---|
> | **Paper A** | 新段落 **Protocol dependence**：同模型/数据/seed/site，只改梯度累积（有效 batch $32\\to128$）| $\\alpha$ 近翻倍（$-0.0345\\to-0.0669$）、$\\beta$ 降 35%（$0.1091\\to0.0713$）⇒ $\\alpha,\\beta$ 是协议泛函；abstract 加一句 |
> | **A1** | 新附录 **Risk–compute frontier**（20 个大留出集 runs，ε 网格）| ε=0.005：省 **4.2 epoch**、regret 0.74；ε=0.05：省 0、0.50；小留出集 4 runs 在 ε=0.01 下 regret **16.5** ⇒ 小 split 禁用早停 |
> | **A23** | 新附录 probe (iii) **leave-one-domain-out 校准**（106 条件、5 域）| slope $+33$~$+51$、held-out $r$ 0.38–0.64，但 MAE **13.5–27.8** ⇒ 关系可迁移、绝对校准不可 |
> | **P3** | 新补充 **S16 protocol shift** + 正文/abstract | r=5 在 n=12 测到 **−39.5**（r=6 +40.5），与默认 n=20（−10.5/+115.0）对比：**符号边界稳定、幅度变化 2.8×**；abstract 加 "exact permutation $p=0.008$"；n=64 因单 run >95 min 中断（记录未用）|
> | **Commentary** | §4 增 **From aspiration to acceptance test** 段 + 参考文献 scriptsize | 仍 **7 页**、0 错、0 overfull、引用完整 |
>
> 页数：A1 **64**、A23 **70**、PaperA **74/53**、P3 **10+7**、Commentary **7**；五包 staged **1:1**（64/70/10/74/7）。
> 新论文想法：`docs/NEW_PAPER_IDEAS_2026-10-21.md`（提案 A–E，按指示**仅记录**，等升级/审核完毕再定）。
>

"""

ROW = ("131. ⬆️ **五篇升级主张（2026-10-21 14:05）** —— Paper A 加 protocol-dependence（α/β 随有效 batch 变 2×/35%）；"
       "A1 加 risk–compute frontier 附录（省 4.2 epoch @ 0.74；小 split 16.5 禁用）；A23 加 leave-one-domain-out 校准"
       "（slope +33~+51、MAE 13.5–27.8）；P3 加 S16（r5 n=12 −39.5 vs r6 +40.5，符号稳定、幅度 2.8×）+ abstract p=0.008；"
       "Commentary 加 acceptance-test 段并保持 7 页；新论文想法仅记录。页数 64/70/74-53/10+7/7，五包 staged 1:1。\n")

EVID_ROWS = """| `a1_monitor_frontier.json` | A1 risk–compute frontier（ε 网格） | `tools/_p1480_a1_frontier.py` |
| `a23_calib_lodo.json` | A23 leave-one-domain-out 校准 | `tools/_p1478_a23_lodo_calibration.py` |
| `p3_protocol_shift.json` | P3 r=5 在 n=12 的协议移动测量 | `tools/_p1476_p3_protocol_shift.py` |
| `docs/NEW_PAPER_IDEAS_2026-10-21.md` | 新论文提案 A–E（仅记录） | — |
"""


def main() -> int:
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "五篇“升级主张”落地" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENTRY + h[j + 1:])
        print("  handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    if "五篇升级主张（2026-10-21 14:05）" not in m:
        anchor = "130. 📦 **GitHub v2.2 release"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + ROW + m[end + 1:])
        print("  file map updated")
    e = io.open(EVID, encoding="utf-8").read()
    if "a1_monitor_frontier.json" not in e:
        io.open(EVID, "w", encoding="utf-8", newline="").write(e.rstrip() + "\n" + EVID_ROWS)
        print("  evidence map updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
