# -*- coding: utf-8 -*-
r"""Record novelty items 1-7 (second round) and update the status documents.

Delivered in this round:
  1  prompt-template control: five backbones, ten templates, gap moves by 0.025-0.094 while accuracy moves 2.3-4.9 pts
  2  threshold transfer: frozen gap spans 0.791-1.116 (x1.41); 20 cross-setting transfers, median balanced accuracy
     0.458, 10/20 below chance, worst 0.188
  3  Proposition 3 (text-side confound, identifiable only with the prompt vocabulary fixed) + proof
  4  tau at k = 5 and k = 10 archived for every template (a1_prompt_template_gap.json::tau5/tau10)
  5  two more benchmarks: iNaturalist-wild (spread 2.6, gain 3.2) and rare species (spread 21.0, gain 9.9)
  6  bootstrap intervals: flagship spread 32.7 [31.3, 33.9]; contraction +19.0 [17.8, 20.2]; etc.
  7  five-item minimum reporting standard (Table standard)

Infrastructure: CLIP ViT-L/14 fetched from ModelScope (hf-mirror and huggingface.co time out on this machine; the rule is
to probe and use the source that answers). Archives: a1_prompt_template_gap.json, a1_threshold_transfer.json,
a1_more_benchmarks.json. Scripts: _p1262-_p1267 (plus the fetch script _p1261).

    python tools/_p1268_record_novelty_round3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
WHICH = REPO / "哪篇是哪篇.md"
NOVDOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"

NOVSEC = """

---

## 第 7 步（2026-10-18 18:15）：第 1–7 项全部落地，A1 **51 页**

| 项 | 落地内容 | 归档 |
|---|---|---|
| **1** | **提示词模板控制**：固定 5,000 张 ImageNet-5k 图像，只换 10 个模板。CG 变动 **0.025–0.094**（最大 OpenCLIP），而 top-1 变动仅 **2.3–4.9 点**。旗舰匹配对里 **0.028** 的 gap 差伴随 **32.7 点**精度崩塌 ⇒ 一次 prompt 选择把 gap 推走 **3.4 倍**，精度却几乎不动 | `a1_prompt_template_gap.json`（5 骨干）|
| **2** | **阈值不可迁移**：各设置**冻结** gap 跨 **0.791–1.116（×1.41）**；SigLIP 冻结 gap 最大（1.116）却精度最高（73.3%）；20 次跨设置迁移的 balanced accuracy **中位 0.458**、**10/20 低于随机**、最差 **0.188** | `a1_threshold_transfer.json` |
| **3** | **Proposition 3（文本侧混杂 / 可识别性）**：文本侧变动（prompt/类名）只动 gap、不动行序 ⇒ 不报告 prompt 词表时 gap 不可归因到图像侧；附证明 | `main.tex` §3.1 |
| **4** | **τ 的 k 依赖**：每个模板同时归档 τ@5 与 τ@10（τ@10 系统性略高，见归档）| `a1_prompt_template_gap.json` |
| **5** | **再加两个基准**：iNaturalist-wild（50 物种，spread **2.6**、收缩 **+3.2**）、rare-species（398 类，spread **21.0**、收缩 **+9.9**）| `a1_more_benchmarks.json` |
| **6** | **bootstrap 区间**（500 次图像重采样）：旗舰 spread **32.7 [31.3, 33.9]**；收缩 **+19.0 [17.8, 20.2]**；新基准区间全部排除 0 | 同上 |
| **7** | **最低报告标准**（5 项清单表）：gap+序统计量、prompt/词表、匹配 gap 对照、校准设置、逐次记录 | `main.tex` Discussion `tab:standard` |

**骨干扩展**：新下载 **CLIP ViT-L/14**（ModelScope，`models/clip-vit-large-patch14`）。
实测：`hf-mirror.com` 与 `huggingface.co` 本机**超时不可达**（0 B/s），ModelScope **可达**（~10 MB/s 实测下载）
⇒ 按"以实测为准"走 ModelScope，权重直下数据盘，无本地上传。提示词控制因此覆盖 **5 个骨干**（B/32、B/16、OpenCLIP、SigLIP、L/14）。

**编译与审计**：A1 **51 页**、0 错误 / 0 未定义 / 0 Overfull；`a1_paa` **READY grade A：pass=61 fail=0 warn=0**；
PAA 包已重建（Manuscript 51 页、源码 14 文件）。
"""

ENT = """> **🧪 2026-10-18 18:15 —— A1 第 1–7 项全部落地（48 → **51 页**），并新增第 5 个骨干 CLIP ViT-L/14**
>
> 1. **提示词模板控制**（真实文本侧干预）：5 骨干 × 10 模板，CG 变动 **0.025–0.094**、top-1 仅动 **2.3–4.9 点**；
>    旗舰对里 0.028 的 gap 差伴随 32.7 点崩塌 ⇒ prompt 一次选择把 gap 推走 **3.4 倍**而精度几乎不变。
> 2. **阈值不可迁移**：冻结 gap 跨 0.791–1.116（×1.41），SigLIP gap 最大却精度最高；20 次迁移 BA **中位 0.458**、10/20 低于随机。
> 3. **Proposition 3（文本侧混杂/可识别性）** + 证明；4. τ@5/τ@10 双口径归档；
> 5. **再加两基准**：iNat-wild（spread 2.6 / +3.2）、rare-species（21.0 / +9.9）；
> 6. **bootstrap 区间**：旗舰 32.7 [31.3, 33.9]、收缩 +19.0 [17.8, 20.2]；
> 7. **最低报告标准表**（5 项）。
>
> **下载来源实测**：hf-mirror / huggingface.co **超时**，ModelScope **可达（~10 MB/s）** ⇒ 新骨干 **CLIP ViT-L/14** 走
> ModelScope 直下 `models/clip-vit-large-patch14`。归档 `a1_prompt_template_gap.json`、`a1_threshold_transfer.json`、
> `a1_more_benchmarks.json`；脚本 `_p1261`–`_p1267`。
>
> **A1 现状**：**51 页**、0/0/0；PAA 包重建；审计 `a1_paa` **READY grade A：pass=61 fail=0 warn=0**。仍待投（Springer EM）。
>


"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    n = io.open(NOVDOC, encoding="utf-8").read()
    if "第 7 步" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 第 1–7 项全部落地" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")
    w = io.open(WHICH, encoding="utf-8").read()
    old = "**已加定理（Prop 1/Cor 1/Prop 2）+ 无标签监控协议 + 第二数据集复现** | 48 + 1 title page |"
    new = ("**已加定理（Prop 1–3/Cor 1）+ 监控协议 + 提示词混杂控制（5 骨干，含新下载 ViT-L/14）+ 阈值迁移 + "
           "5 基准复现** | 51 + 1 title page |")
    print(f"  which A1 row: {w.count(old)}")
    if w.count(old) == 1:
        io.open(WHICH, "w", encoding="utf-8", newline="").write(w.replace(old, new, 1))
    m = io.open(MAP, encoding="utf-8").read()
    row = ("84. 🧪 **A1 第 1–7 项（2026-10-18 18:15）** —— 48→**51 页**、0/0/0，审计 READY/A pass=61 fail=0 warn=0。"
           "提示词模板控制（5 骨干：CG 动 0.025–0.094、top-1 仅 2.3–4.9 点）；阈值迁移失败（冻结 gap ×1.41、迁移 BA 中位 0.458）；"
           "Prop 3 文本侧混杂；iNat/rare-species 复现（2.6 / 21.0）；bootstrap CI（32.7 [31.3,33.9]）；最低报告标准表。"
           "新骨干 CLIP ViT-L/14 走 ModelScope（hf-mirror/hf.co 本机超时）。\n")
    if "A1 第 1–7 项" not in m:
        anchor = "83. 🧪 **A1 六项新颖性增强"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
