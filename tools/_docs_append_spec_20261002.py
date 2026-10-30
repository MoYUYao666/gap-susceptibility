# -*- coding: utf-8 -*-
r"""把 2026-10-02 阶段追加进 `docs/PAPERA_REVISION_SPEC.md`（规格文档是本稿的工作依据）。

    python tools\_docs_append_spec_20261002.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "docs" / "PAPERA_REVISION_SPEC.md"

ADD = r"""

### 7.5 2026-10-02 追加：换模板 + 两处证据错误 + 新实验

**① 两处证据错误（已修，提交 `1b59f20`）**

| # | 错误 | 证据 | 修法 |
|---|---|---|---|
| 1 | 称 SigLIP 的 pairwise sigmoid 目标不同于 CLIP 的 InfoNCE | `src/trainer.py:418-428`：**所有模型微调都用同一 InfoNCE**（`logit_scale * image @ text.T` + `cross_entropy`） | 改为"差在编码器与预训练，**微调损失相同**"；`tools/_pa_fix_loss_claim.py` |
| 2 | ODE "mean $R^2 > 0.96$" | **我的验证脚本查错了来源**：按 `R2/r2/R^2` 全仓搜到的 13 处**全来自 `outputs/llava_*`（解码器）**；CLIP 侧拟合在 `outputs/theory/**/beta_results.json` 的 **`exponential_fit.r_squared`** | 用正确来源重算：**仅 LoRA n=6，mean 0.9855（range 0.9777–0.9965）**；full_ft 组 0.9223、最低 0.8629。全文 6 处统一为"LoRA 子集 0.986"，并把 full_ft 与 OpenCLIP BitFit(0.943) **明确标为低于该区间** |

**② SigLIP 严格冻结对照（新，产物 `outputs/siglip_strict/`）**

- 协议：5000 样本 / 10 epochs / batch 64 / rank8+α16 / seeds 42,123,456,789,1024
- 严格冻结已验证：text_only 可训 **294,912**（**视觉侧 0**）；both 可训 **589,824**
- **text_only +0.0664 ± 0.0060**（R@1 0.432）vs **both −0.0114 ± 0.0059**（R@1 **0.619**）
- **配对差 −0.0778（sd 0.0033），t = −52.7，5/5 seeds 方向一致**
- CLIP 同协议对照：text_only −0.0465 vs both −0.0258，配对差 +0.0207，t = +10.0
- → **两架构方向相反**；且两者**同预算、同 seeds、同 rank、同一微调损失**
- 统计脚本：`tools/_siglip_strict_stats.py`、`tools/_crossarch_strict_stats.py`

**③ 已据此改写的正文位置**

| 文件 | 改动 |
|---|---|
| `empirical.tex:124` | 设计模式①去掉"across architectures"普适声称 |
| `validation.tex:111` | 写入 SigLIP 反例及两点后果（含"ODE 不预测分配方向"的范围声明） |
| `conclusion.tex:11` | "central message"去掉"and why it must" |
| `introduction.tex:25` | 同一处方加架构限定 |
| 四处 "text-only superiority" | 改为 "text-only position" + 范围声明 |
| 摘要 | **367 → 244 词**，去循环引用与旧值，写入架构依赖 |

**④ 模板与投稿包（提交 `03497e3`）**

- Elsevier `elsarticle`：`paper合/main_nc.tex`（`tools/_pa_to_elsarticle.py` 生成；**正文 8 个 `\input` 未改**）
- **无损性已核**（`tools/_pa_compare_versions.py`）：labels 31/31、refs 22/22、cites 39/39、引用 key 集合完全一致、无重复 input
- 编译：**39 页、0 错误、0 未定义引用、41 条参考文献**
- 新增：Highlights（5 条，最长 59 字符）、Cover Letter（2 页）、5 节声明（CRediT 9 项 + 生成式 AI，**位置在参考文献之前**）
- 投稿包：`paper合/NC_submission/`（Manuscript / Highlights.pdf+.txt / Cover Letter / latex_source.zip / README）
- 终检：`tools/_pa_final_check_nc.py`（**从 PDF 实测**）全绿；摘要 **244 词** ≤250
- ⚠️ 终检抓到：初次实测 252 词，其中 **8 词是 `pdftotext` 把首页页脚拼进摘要正文流**；剔除后合规，脚本已固化该逻辑

**⑤ 补充实验**

| 实验 | 目的 | 脚本 | 状态 |
|---|---|---|---|
| OpenCLIP B/32 (LAION-2B) 严格冻结 | 与 CLIP **同架构（patch32/768/151M）不同预训练** → 分离"骨干 vs 预训练" | `strict_freeze_control.py --model models/openclip --name oclip_` | 🏃 进行中 |
| SigLIP vision_only | 补全 SigLIP 三臂（CLIP 已有三臂） | `siglip_experiments.py --only s6_siglip_lora_vision_only`（**新增配置**） | ⏳ 排队 |
| 严格冻结 rank sweep（rank 4/16/32） | 设计模式②"更低 rank 更保对齐"此前**只在 rank 8 验证过** | `strict_freeze_control.py --rank N`（**新增参数**） | ⏳ 排队 |

排队执行：`tools/_run_extra_experiments.py --apply`（串行，避免 GPU 争用）

**脚本改动（默认值不变，既有产物语义不受影响）**：
`strict_freeze_control.py` 新增 `--model/--out-dir/--name/--rank/--alpha-mult`；
`siglip_experiments.py` 新增 `s6_siglip_lora_vision_only` 配置。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "7.5 2026-10-02 追加" in t:
        print("  已含 §7.5，跳过")
        return 0
    print(f"  将追加 {len(ADD.splitlines())} 行")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.rstrip() + ADD)
        t2 = io.open(F, encoding="utf-8").read()
        for k in ("7.5 2026-10-02", "exponential_fit.r_squared", "t = −52.7", "NC_submission"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ 已追加并断言通过（{len(t2.splitlines())} 行）")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
