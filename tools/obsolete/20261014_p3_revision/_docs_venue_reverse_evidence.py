# -*- coding: utf-8 -*-
r"""选项 3：反查"这类论文实际发在哪"——写入决策文档（2026-10-07）。

## 本轮方法（第 5、6 轮，逐轮修正）

| 轮 | 脚本 | 方法 | 问题 / 收获 |
|---|---|---|---|
| 5 | `_venue_reverse_lookup.py` | 全文 `search=` | ⚠️ 总命中 **3–4 万** → 松匹配，计数不可信 |
| 6 | `_venue_modality_gap_venues.py` | **`title.search=`（仅标题）** | ✅ 总量合理（99 / 352 / 257 篇），**信号干净** |

## 第 6 轮结果（标题级精确）

| 标题短语 | 总量（2023 起） | 第一梯队 |
|---|---|---|
| `modality gap` | **99 篇** | Zenodo **20**（预印本库，非期刊）｜**EAAI 3**｜IEEE RA-L 2｜IEEE TMM 2｜**ESWA 2**｜**PR 1** |
| `cross-modal alignment` | **352 篇** | **Neurocomputing 7**｜IEEE TCSVT 6｜ACM TOMM 6｜IEEE Access 5｜**KBS 5**｜**IF 5**｜**PR 4** |
| `parameter-efficient fine-tuning` | **257 篇** | **Neurocomputing 8**｜**IEEE TPAMI 6**｜**IJCV 5**｜**Neural Networks 5**｜**PR 3** |

（🆓 = 在 `docs/OA_FUNDING_ROUTES.md` 免 APC 清单内）

## 两个决定性结论

### ① 主题本身**很窄**
`modality gap` 三年仅 **99 篇**（且 **20/99 在 Zenodo 预印本库**）——**这不是一个拥挤的领域**。
好处：**没有"已被做烂"的风险**；坏处：**没有稳定的对口刊**，各刊都是零散收录。

### ② 最优 scope 的刊 ↔ **免 APC 清单，几乎不重叠**

| 主题第一梯队 | 是否免 APC | 有无障碍 |
|---|---|---|
| IEEE TPAMI / IJCV / IEEE TCSVT / IEEE TMM | ❌ **IEEE 明确不覆盖** | 自付 US$2,645（JOE 官方价） |
| Zenodo（20/99） | — | **不是期刊**（预印本库） |
| **Neurocomputing**（7 + 8 篇，两榜第一） | ✅ | ⚠️ **P1 曾桌面拒**；且 **A1 在此在审** |
| **Pattern Recognition**（4 + 3 篇） | ✅ | ⚠️ **P1 在此在审**（`PR-D-26-10149`） |
| **Neural Networks**（5 篇） | ✅ | ⚠️ **P1 曾桌面拒** |
| **KBS**（5 篇） | ✅ | ⚠️ Guide *"preferably ≤20 double line spaced pages"*（我们约 2.2 倍） |
| **Information Fusion**（5 篇） | ✅ | ⚠️ 页数硬上限 **10–35**（我们约 45–52） |
| **ESWA**（2 篇） | ✅ | ⚠️ 双盲；**scope 偏系统/应用** |
| **EAAI**（3 篇，`modality gap` 榜第二） | ❓ **未逐刊核实** | 见下 |

**→ 免 APC 且有主题先例的刊，全部带一项实质障碍**（拒稿史 / 在审冲突 / 篇幅 / 口径）。

### ③ 新发现：`Engineering Applications of AI`（EAAI）

- `modality gap` 标题级 **3 篇**，在**非预印本期刊中排第二**（仅次于若干 IEEE 刊）；
- **但**：抽看其论文形态仍是 **"方法 + 任务"**
  （*"Denoising diffusion bridge for cross-modal alignment in **3D scene understanding**"*、
  *"A universal parameter-efficient fine-tuning approach for **stereo image super-resolution**"*）
  → **与第 1–4 轮的结论一致：这些刊要"落到任务"**；
- **且 EAAI 不在** `docs/OA_FUNDING_ROUTES.md` 的"① 确定覆盖"9 刊清单里
  → 属**"② 需逐刊核实"**（它虽是 Elsevier hybrid，非 fully-OA，但**未逐刊实测**）。

## ⚠️ 本轮局限（诚实标注）

1. **样本小**：`modality gap` 三年仅 99 篇，各刊计数为个位数 → **统计噪声大**；
2. **`title.search` 仍是 OpenAlex 的匹配**，非权威目录（ScienceDirect 全程 403）；
3. **Zenodo 20/99** 说明该主题相当比例尚未正式发表 → **venue 信号本身偏弱**；
4. **未读正文**，形态判断依标题。

**→ 结论：这是"方向性"证据，足以否掉"某个免 APC 刊是天然对口"的想法，但不足以指定唯一目标刊。**
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "docs" / "PAPERA_VENUE_DECISION.md"


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "选项 3" in t:
        print("  已写入，跳过")
        return 0
    if not apply:
        print("  （预演）")
        return 0
    body = __doc__
    i = body.find("## 本轮方法")
    j = body.find("from __future__")
    sec = "\n\n---\n\n## 六、选项 3：反查「这类论文实际发在哪」（2026-10-07 追加）\n\n" + body[i:j].rstrip() + "\n"
    io.open(F, "w", encoding="utf-8", newline="").write(t.rstrip() + sec)
    t2 = io.open(F, encoding="utf-8").read()
    for k in ("选项 3", "title.search", "99 篇", "几乎不重叠", "EAAI", "方向性"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ 已写入（{len(t2.splitlines())} 行）")

    # HANDOFF
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    ent = r"""> **🔎 2026-10-07 —— 选项 3（反查"这类论文实际发在哪"）：**最优 scope 的刊基本都不在免 APC 清单内****
>
> **交付件**：`docs/PAPERA_VENUE_DECISION.md` §六。
>
> ### 方法（第 5、6 轮；第 5 轮有缺陷已弃）
>
> 第 5 轮用全文 `search=` → 总命中 **3–4 万**（松匹配，计数不可信）。
> 第 6 轮改用 **`title.search=`（仅标题）** → 总量合理，**信号干净**。
>
> ### 结果（标题级精确，2023 起）
>
> | 标题短语 | 总量 | 第一梯队 |
> |---|---|---|
> | `modality gap` | **99 篇** | Zenodo **20**（预印本库）｜**EAAI 3**｜**ESWA 2**｜**PR 1** |
> | `cross-modal alignment` | **352 篇** | **Neurocomputing 7**｜**KBS 5**｜**IF 5**｜**PR 4** |
> | `parameter-efficient fine-tuning` | **257 篇** | **Neurocomputing 8**｜**IEEE TPAMI 6**｜**IJCV 5**｜**Neural Networks 5**｜**PR 3** |
>
> ### 两个决定性结论
>
> **① 主题很窄**：`modality gap` 三年仅 **99 篇**，其中 **20 篇在 Zenodo 预印本库**
> → **不是拥挤领域**（无"做烂"风险），但**也没有稳定对口刊**，各刊零散收录。
>
> **② 最优 scope 的刊 ↔ 免 APC 清单几乎不重叠**：
>
> | 主题第一梯队 | 免 APC | 障碍 |
> |---|---|---|
> | IEEE TPAMI / IJCV / TCSVT / TMM | ❌ **IEEE 明确不覆盖** | 自付 US$2,645 |
> | Zenodo（20/99） | — | **不是期刊** |
> | **Neurocomputing**（两榜第一） | ✅ | ⚠️ **P1 曾桌面拒** + **A1 在审** |
> | **Pattern Recognition** | ✅ | ⚠️ **P1 在审**（`PR-D-26-10149`） |
> | **Neural Networks** | ✅ | ⚠️ **P1 曾桌面拒** |
> | **KBS** | ✅ | ⚠️ *preferably ≤20 双倍行距页*（我们约 2.2 倍） |
> | **Information Fusion** | ✅ | ⚠️ 硬上限 **10–35 页**（我们约 45–52） |
>
> **→ 免 APC 且有主题先例的刊，全部带一项实质障碍**（拒稿史／在审冲突／篇幅／口径）。
>
> ### 新发现 EAAI（Engineering Applications of AI）
>
> `modality gap` 标题级 **3 篇**，在**非预印本期刊中排第二**。**但**：
> ① 抽看形态仍是"方法+任务"（*3D scene understanding*、*stereo image super-resolution*）→ **与前四轮结论一致**；
> ② **不在** `OA_FUNDING_ROUTES.md` 的"① 确定覆盖"9 刊内 → 属**"② 需逐刊核实"**。
>
> ### ⚠️ 局限
>
> 样本小（99 篇，各刊个位数 → 噪声大）｜ `title.search` 仍非权威目录（**ScienceDirect 全程 403**）｜
> **Zenodo 20/99** 说明该主题相当部分未正式发表 → **venue 信号本身偏弱** ｜ 未读正文。
> **→ 足以否掉"某免 APC 刊天然对口"，但不足以指定唯一目标刊。**
>
> ### ⏭ 待操作者决定
>
> 走到这里，**"免 APC" 与 "scope 对口" 两条约束没有交集**。可选：
> **A. 改包装投 ESWA**（无篇幅上限，落到"practical guidelines"）｜
> **B. 改包装投 CVIU**（无篇幅上限 + 单盲 + 首轮 3.7 月，视觉侧前置）｜
> **C. 放弃 £0 约束**，投 scope 真正对口的刊（需先确认预算）｜
> **D. 核实 EAAI 是否在协议内 + 要其 Guide**。
"""
    if "选项 3（反查" not in h:
        anchor = "> **🔬 2026-10-07 —— 实证明查候选刊"
        i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 锚点"
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ent + "\n" + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("title.search", "几乎不重叠", "免 APC", "EAAI", "PAPERA_VENUE_DECISION.md"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
