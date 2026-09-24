# -*- coding: utf-8 -*-
"""Record the submitted-version finding, the closed items, and the ap3 fix."""
import io
import os

ROOT = r"D:\Realdesktop\Wan\Important\New"

LOG = os.path.join(ROOT, "docs", "P1_REMEDIATION_LOG.md")
MARK = '## 十、提交版核对'
ADD = """
## 十、提交版核对（桌面 `PR-D-26-10149.pdf`，2026-09-20 提供）

操作者提供的提交版是 **Editorial Manager 2026-07-24 13:11 生成的合并快照**（40 页，iTextSharp 5.5.13.2），**早于 8-14 两次更正信，也早于本轮整改**。因此审稿人读的就是这一版。探测结果：

| 项 | 7-24 提交版 | 现稿 |
|---|---|---|
| 摘要零样本 | 24%、zero-shot 下降 **53.3%**、text-only 限 **+0.079** / **1.7%** | 23.3%±1.0%；ImageNet-1K 50k：frozen 59.28 / text-only 58.66（−0.62pp）/ both 59.67（+0.39）/ full-FT 2.6%（3 seeds）；DTD/Food101 在 ±0.8pp 内 |
| 零样本基准名 | **CIFAR-100**（DTD、Food101） | **ImageNet-1K**（DTD、Food101） |
| 模型计数 | four models (CLIP ViT-B/32, ViT-L/14, BLIP-1, SigLIP) | three model families (CLIP, BLIP-1, SigLIP) |
| 实验数 | 116（11 处） | 117 |
| DG/CG | r=−0.827 / −0.807（各 12 处） | −0.714 / −0.594 / 偏相关 −0.581；DG~CG +0.945 |
| 措辞 | first systematic study（6 处）、direct causal evidence（4 处） | 均已改（去 first、改为一臂严格对照） |

**结论：8-14 的两次更正显然没有替换掉 EM 里的稿件**（快照仍是 7-24 版，既不含 59.37/58.76 也不含 59.28/58.66）。→ 返修封面信已按 7-24 版重设基准（补丁 H）：新增本信针对哪一版的说明段、新增零样本声明行（53.3%/1.7%/+0.079 → 现 ImageNet 数字）、并把两行 8-14 和解行改写为 as submitted / 8-14 信 / 现稿三段式。**是否现在就在 EM 里补传修订版由操作者决定。**

## 十一、本轮其他非实验收尾

- `competing_interests.docx` **已核**（解包 docx XML 读正文）：仅为标准利益冲突声明，**无机构/日期信息** → 该项关闭。
- **ap3 侧 BLIP 命名已修**：`paper_ap3/` 把第三骨干写成 BLIP-2 (350M, Q-Former) 并引 `li2023blip2`，而它引用的数字（+0.047/+0.152、R@1 0.175）是 P1 的 **BLIP-1** 跑（P1 methodology 自述 cross-attention decoder / BERT text encoder / ITC+ITM+LM = BLIP-1）。已 6 处改为 BLIP-1 + `li2022blip`；ap3 全文现已无 BLIP-2 残留。
- **ap3 仍待办**（其投稿前的自身整改，非本轮）：`01_intro.tex` 等处仍引 P1 已撤销的 `r=−0.827`、以及 116 计数与 Adapter 旧基线值——ap3 准备投时要按 P1 修正后的口径整体重导。
- **Huang et al. ICCV 2025 引用仍缺**：`web_fetch` 被 VPN 劫持 DNS 挡住（ar5iv/arxiv 均解析到非公网 IP），搜索快照从不包含作者行。需关 VPN 后从 [CVF 页面](https://openaccess.thecvf.com//content/ICCV2025/html/Huang_Mind_the_Gap_Preserving_and_Compensating_for_the_Modality_Gap_ICCV_2025_paper.html) 复制 bibtex（arXiv 版为 2507.09118）。
"""

s = io.open(LOG, encoding="utf-8").read()
if MARK in s:
    print("log already has section 十")
else:
    io.open(LOG, "w", encoding="utf-8", newline="").write(s.rstrip() + ADD)
    print("log appended")

H = os.path.join(ROOT, "HANDOFF.md")
old = '③ **登录 EM 确认期刊手上是哪一版**（08-14 更正信所述 14,288 子集 vs 08-22 编译的 50k 协议）'
new = ('③ **已查明期刊手上是哪一版**：EM 里仍是 **2026-07-24 提交快照**（操作者提供的桌面 '
       '`PR-D-26-10149.pdf`，40 页 iTextSharp 合并产物；摘要为 24%/53.3%/1.7%/+0.079、基准写 '
       '**CIFAR-100**、含 116 与 −0.827/−0.807）→ **8-14 两次更正显然未替换成功**。返修封面信已按该版本'
       '重设基准（`paper/cover_letter_revision.tex`，4 页）。**是否现在就在 EM 补传修订版由操作者定**')
h = io.open(H, encoding="utf-8").read()
if old in h:
    io.open(H, "w", encoding="utf-8", newline="").write(h.replace(old, new, 1))
    print("handoff updated")
else:
    print("handoff anchor not found")
