# -*- coding: utf-8 -*-
"""Record the final integration round (Paper A decoder confound + A23 margin control) and extend the mirror list."""
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

entry = """> **🧩 2026-10-24 15:15 —— 两个内容缺口闭合：Paper A 解码器符号冲突（新 H 节）+ A23 margin 负对照（重写）**
>
> - **Paper A：新增补充材料 H 节**「What the two decoder experiments do and do not separate」（`paper合/sections/supplement.tex` 末尾，label `sec:decoderconfound`）：
>   Qwen2-VL-2B（对比目标，13 seeds，三臂 **−98.57/−96.74/−89.41%**，39/39 缩小、seed 区间互不重叠）与
>   LLaVA-1.5-7B（生成目标，3 seeds，**+73.27/+121.48/+95.66%**，9/9 扩大）符号相反；
>   各自符号内部稳定（LLaVA 换 text-side 约定仍同号；Qwen 三种归档构造全为缩小），但**五个因素同时变化**
>   （目标/规模 2B vs 7B/预训练家族/数据集/训练与评测规模），故不能归因；隔离需固定 model+data+budget+site 只变 loss，归档没有。
>   证据：`outputs/analysis/paperA_decoder_confound.json`、`docs/paperA_decoder_confound_paragraph.md`、只读脚本 `tools/_p1580_paperA_decoder_confound.py`；
> - **顺带修三个隐患**：① 表 E/表 G 的 `+` 号在两表里指相反方向 → 两处 caption 明确「正号=更小/更大」；
>   ② **溯源清单错配**：`tab:vlm`/`tab:llava` 原指向 τ-vs-λ 探针文件却标 verified → 改为
>   `outputs/vlm_clean_summary.json`（脚本 `_p1164_verify_pull_analyze_e.py`）与 `outputs/canonical_caption_metric.json`（脚本 `_p1145_clean_gap_measure.py`），
>   `docs/provenance_manifest.json`、`tools/_p1432_provenance_map_paperA.py`、`docs/PROVENANCE_MANIFEST_2026-10-20.md` 三处同步；重跑时被误删的 `tab:odefit` 已补回（`_p1589`）→ provenance gate **PASS（paperA 31/31）**；
>   ③ 正文页数 **NC 74→75、Springer 53→54**（H 节成本 1 页）→ cover letter 页数声明同步 75，`final_verify` 期望页数更新；
> - **A23：margin 负对照按归档重写**（`paper_a2/ext_partII_domains.tex`，Results 内，自 2026-10-19 已在正文）：
>   删去**无归档支持的因果句**「因为冻结精度只有 20–27%」——59.1% 精度的 ImageNet-5k 参照在 ε≥0.05 同样饱和（66/66 臂 M(0.10)=1.0）；
>   新增有效工作点（ImageNet-5k：margin 中位 0.0063、M(0.01)=0.681、r=−0.996）、通用 CLIP 饱和（14/14 配置 M(0.05)=1.0、相关性不可定义、阈值退化到 0.50）、
>   适配编码器弱相关（BioCLIP −0.346 / OceanCLIP −0.564，阈值迁移 BA 0.125）与「不主张任何优势」的边界；
>   归档 `a23_margin_negative_control.json` + 说明 `docs/a23_margin_negative_control_paragraph.md`；同时更正 `HANDOFF.md` 过期条目与 `docs/A23_REVIEWER_OBJECTIONS.md` 两处因果句；
> - **门禁**：六 profile **READY(A)、0 fail / 0 warn**；provenance **PASS**；台账 96/96、A1 216/216、Paper A 88/88；`final_verification` **ALL PASS**（页数 64/75/54/10/70/7）。
>
"""

h = io.open("HANDOFF.md", encoding="utf-8").read()
if "两个内容缺口闭合" not in h:
    i = h.find("# 项目交接文档")
    j = h.find("\n", i)
    io.open("HANDOFF.md", "w", encoding="utf-8", newline="").write(h[:j + 1] + "\n" + entry + h[j + 1:])
    print("handoff updated")

m = io.open("文件地图.md", encoding="utf-8").read()
row = ("161. 🧩 **2026-10-24 15:15 —— 内容缺口闭合**：Paper A 补 H 节（解码器符号冲突，五因素混淆，不可归因）；"
       "A23 负对照重写并删去无据因果句；溯源错配修正、`tab:odefit` 补回；NC 75/Springer 54 页；六 profile READY。\n")
if "内容缺口闭合" not in m:
    i = m.find("160. 🔖 **2026-10-24 15:00")
    e = m.find("\n", i)
    m = m[:e + 1] + row + m[e + 1:]
    io.open("文件地图.md", "w", encoding="utf-8", newline="").write(m)
    print("map updated")

# --- mirror list -------------------------------------------------------------
add = [
    "tools/_p1580_paperA_decoder_confound.py", "tools/_p1583_update_doi_to_v23.py",
    "tools/_p1584_commentary_headroom.py", "tools/_p1585_a23_margin_negative_control.py",
    "tools/_p1586_record_doi_round.py", "tools/_p1587_integrate_a23_margin_text.py",
    "tools/_p1588_integrate_paperA_decoder_confound.py", "tools/_p1589_restore_odefit_provenance.py",
    "tools/_p1590_sync_paperA_pagecounts.py", "tools/_p1591_correct_a23_records.py",
    "tools/_p1593_fix_a23_objections.py",
    "outputs/analysis/paperA_decoder_confound.json", "outputs/analysis/a23_margin_negative_control.json",
    "docs/paperA_decoder_confound_paragraph.md", "docs/a23_margin_negative_control_paragraph.md",
    "docs/PAGE_LENGTH_REVIEW_2026-10-24.md",
]
p = "tools/_p1284_prepare_public_mirror.py"
t = io.open(p, encoding="utf-8").read()
anchor = '    "cloud_p3/run_cloud_final.sh",\n'
need = [x for x in add if x not in t and os.path.exists(x)]
if need and t.count(anchor) == 1:
    io.open(p, "w", encoding="utf-8", newline="").write(
        t.replace(anchor, anchor + "".join('    "%s",\n' % x for x in need), 1))
    print("mirror list += %d entries" % len(need))
else:
    print("mirror anchor count", t.count(anchor), "need", len(need))