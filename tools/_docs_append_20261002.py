# -*- coding: utf-8 -*-
r"""按项目规则，把本阶段（2026-10-02 Paper A 整改 + 补充实验）追加进 HANDOFF.md 顶部。

规则要求：**追加，不重写**；每条可复核（日期/路径/脚本/命令/结果）；诚实标注状态。

本阶段做的事（全部有脚本与产物）：
1. 修正正文两处**证据错误**（损失函数说法、R² 数据源）；
2. 跑完 SigLIP 严格冻结对照（发现方向相反）；
3. 换成 Elsevier `elsarticle` 模板并组建 Neurocomputing 投稿包；
4. 启动 OpenCLIP 严格冻结对照 + 排队补充实验。

    python tools\_docs_append_20261002.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "HANDOFF.md"

ENTRY = r"""> **🆕 2026-10-02 —— Paper A（`paper合`）整改收尾：换 Neurocomputing 模板 + 投稿包就绪 + 补实验**
>
> **本阶段主线**：把合并稿从 Springer 模板转为 Elsevier，组建可投稿的包；同时对全稿做**证据级复核**，
> 修掉两处**我自己先前引入/未察觉的错误**。所有改动落成 `tools/` 下带断言的幂等脚本。
>
> ### ① 两处证据错误（已修，提交 `1b59f20`）
>
> | # | 错误 | 证据 | 修法 |
> |---|---|---|---|
> | 1 | 正文称"SigLIP 的 **pairwise sigmoid** 目标不同于 CLIP 的 **InfoNCE**" | `src/trainer.py:418-428`：**所有模型微调都用同一个 InfoNCE**（`logit_scale * image @ text.T` + `cross_entropy`）。SigLIP 只是**预训练**用了 sigmoid | 改为"差在编码器与预训练，**微调损失相同**"；脚本 `tools/_pa_fix_loss_claim.py` |
> | 2 | 正文/摘要称 ODE "mean $R^2 > 0.96$" | **我的验证脚本查错了数据源**：按键名 `R2/r2/R^2` 全仓搜到的 13 处**全来自 `outputs/llava_*`（解码器）**，与主张无关。CLIP 侧拟合存在 `outputs/theory/**/beta_results.json` 的 **`exponential_fit.r_squared`** | 用正确来源重算：**仅 LoRA n=6，mean 0.9855（range 0.9777–0.9965）**；full_ft 组 mean 0.9223、最低 0.8629。全文 6 处表述统一为"**LoRA 子集** 0.986"，并把 full_ft 与 OpenCLIP BitFit(0.943) **明确标为低于该区间**。脚本 `tools/_pa_clip_ode_r2.py`、`_pa_fix_r2_source.py`、`_pa_unify_r2_wording.py`、`_pa_fix_last_r2.py`、`_pa_polish_r2_sentence.py`、`_pa_clean_r2_notes.py` |
>
> **教训**：`_pa_verify_core_claims.py` 的 R² 段原先按**键名**搜索而非按**实验来源**，抓到无关数字还报"✅"。
> 已于 `_pa_fix_r2_source.py` 改为读 `beta_results.json`，并在脚本内写明"不要再用全仓 R2 搜索"。
>
> ### ② SigLIP 严格冻结对照跑完（5 seeds × 2 臂）——**结论与预期相反**
>
> 产物 `outputs/siglip_strict/`；运行 `tools/_run_siglip_strict.py`；统计 `tools/_siglip_strict_stats.py`。
> 协议：5000 样本 / 10 epochs / batch 64 / rank8+α16 / seeds 42,123,456,789,1024。
> **严格冻结已验证**：text_only 可训 294,912（**视觉侧 0**）、both 可训 589,824。
>
> | 臂 | ΔCG（5 seeds） | 均值 ± sd | R@1 |
> |---|---|---|---|
> | text_only | +0.0565 +0.0678 +0.0719 +0.0661 +0.0698 | **+0.0664 ± 0.0060** | 0.432 |
> | both | −0.0180 −0.0125 −0.0020 −0.0136 −0.0108 | **−0.0114 ± 0.0059** | **0.619** |
>
> **配对差 −0.0778（sd 0.0033），t = −52.7，5/5 方向一致** → **SigLIP 上 both 显著更优，与 CLIP 相反**
> （CLIP：text_only −0.0465 vs both −0.0258，配对差 +0.0207，t=+10.0，见 `tools/_crossarch_strict_stats.py`）。
> **两架构都用同一个微调损失（InfoNCE），也都同预算同 seeds 同 rank。**
>
> **已据此改写**：`empirical.tex:124`（去掉"across architectures"普适声称）、`validation.tex:111`（写入反例）、
> `conclusion.tex:11`（"central message"去掉"and why it must"）、`introduction.tex:25`、
> 四处 "text-only superiority" → "text-only position" + 范围声明。摘要同步（**244 词**，从 367 压下来）。
> **诚实边界（已写入正文）**：ODE 预测的是"给定扰动分配下的轨迹"，**不预测分配本身**；两架构同时差着
> 骨干（patch16 vs 32）与预训练，**归因未分离**。
>
> ### ③ 换 Elsevier 模板 + 投稿包（提交 `03497e3`）
>
> 模板 `elsarticle`（`paper合/main_nc.tex`，由 `tools/_pa_to_elsarticle.py` 从 `main_springer.tex` 生成；
> **正文 8 个 `\input` 未改**）。**无损性已核**（`tools/_pa_compare_versions.py`）：
> labels 31/31、refs 22/22、cites 39/39、引用 key 集合完全一致、无重复 `\input`。
> 编译：**39 页、0 错误、0 未定义引用、41 条参考文献**。
>
> **新增三件（此前从未投稿，故一直没有）**：
> - `highlights_nc.txt/.pdf`（`tools/_pa_make_highlights.py`）：5 条、最长 59 字符
> - `cover_letter_nc.tex/.pdf`（`tools/_pa_make_cover_letter.py`）：2 页，**主动写明 SigLIP 反例**
> - 5 节声明（`tools/_pa_add_declarations.py`）：Data availability / Funding / Competing interests /
>   **CRediT（9 项）** / **生成式 AI**（措辞**经操作者 2026-10-02 确认**：Claude + DeepSeek V4，用于
>   起草修订正文与准备实验代码与图）；**位置在参考文献之前**（Guide 要求）
>
> **包**：`paper合/NC_submission/`（`tools/_pa_build_nc_package.py`）：Manuscript.pdf、Highlights.pdf/.txt、
> Cover Letter.pdf、latex_source.zip（52 文件）、README.md。
> **终检**（`tools/_pa_final_check_nc.py`，**从 PDF 实测**）：摘要 **244 词** ≤250 ✅、Highlights ✅、
> 声明齐备且位置正确 ✅、41 条文献 ✅。
>
> **⚠️ 终检抓到的一个真问题**：摘要初次实测 **252 词超限**——其中 **8 词是 `pdftotext` 把首页页脚
> （通讯作者信息）拼进了摘要正文流**。剔除后 244 词合规。**检查脚本已固化这一剔除逻辑**。
>
> ### ④ 补充实验（进行中）
>
> | 实验 | 目的 | 脚本/产物 | 状态 |
> |---|---|---|---|
> | **OpenCLIP B/32 (LAION-2B) 严格冻结** | 与 CLIP **同架构（patch32/768/151M）不同预训练** → 分离"骨干 vs 预训练" | `experiments/strict_freeze_control.py --model models/openclip --name oclip_`；`outputs/strict_freeze_openclip/` | 🏃 进行中（3 臂 × 5 seeds） |
> | **SigLIP vision_only** | 补全 SigLIP 三臂（CLIP 已有三臂） | `experiments/siglip_experiments.py --only s6_siglip_lora_vision_only`（**新增配置**） | ⏳ 排队 |
> | **严格冻结 rank sweep（4/16/32）** | 设计模式②"更低 rank 更保对齐"此前**只在 rank 8 验证过** | `strict_freeze_control.py --rank N`（**新增参数**）；`outputs/strict_freeze_rank/` | ⏳ 排队 |
>
> 排队执行：`tools/_run_extra_experiments.py --apply`（串行，避免 GPU 争用）。
> **脚本改动**：`strict_freeze_control.py` 新增 `--model/--out-dir/--name/--rank/--alpha-mult`（默认值不变，
> 既有产物语义不受影响）；`siglip_experiments.py` 新增 `s6_siglip_lora_vision_only` 配置。
>
> ### ⑤ 仍未解决（如实标注）
>
> - **`k = 0.043`**（`fig:falsification`/`fig:ers` 的 \|g_v\| 对 rank 斜率）：**无法从归档独立复算**
>   （`norm_g_v` 只在 LLaVA/adapter 数据里；CLIP rank sweep 结果缺该字段）。**待核**。
> - **`empirical.tex:28` 的 legacy 数值**（−0.064 vs −0.032）：与严格冻结不同协议，**本轮未动**，已在表注披露。
> - **`yi2025decipher` 的 ICML 出处**：保留。
> - **"162 ODE fits"与实测记录数（9）的对应关系**：未逐一重建。
> - **方向相反的归因**：骨干 / 预训练 / patch size 未分离（OpenCLIP 实验正在提供第一个分离点）。
>
> ### ⑥ 投稿时点（待操作者决定）
>
> `paper合` 的实证部分与**在审的 P1（`PR-D-26-10149`）同源**。**建议等 P1 决定**：
> P1 接收 → 需重新定位；P1 拒稿 → `paper合` 即成为该工作线主稿，可立即投稿。
> P1 已进入 Required Reviews Completed（2026-09-30），**预计 2026-10 上–中旬出结果**。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    anchor = "> **🆕 2026-10-01 下午"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到插入锚点（2026-10-01 下午 条目）")
        return 1
    print("  ✅ 找到锚点，新条目插在其前")
    if apply:
        new = t[:i] + ENTRY + "\n" + t[i:]
        # 更新头部时间
        new = new.replace("**更新时间**：2026-09-30（本次追加；文档内各历史条目保留其写作日期）",
                          "**更新时间**：2026-10-02（本次追加；文档内各历史条目保留其写作日期）", 1)
        io.open(F, "w", encoding="utf-8", newline="").write(new)
        t2 = io.open(F, encoding="utf-8").read()
        assert "2026-10-02 —— Paper A" in t2
        assert "更新时间**：2026-10-02" in t2
        assert "2026-10-01 下午" in t2, "旧条目必须保留"
        print(f"  ✅ 已追加（{len(t2.splitlines())} 行，原 {len(t.splitlines())} 行）")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
