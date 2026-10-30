# 篇幅复核与压缩方案（非 P3，2026-10-24）

> 目的：把"篇幅"这一项从"感觉偏长"变成**可核查的事实 + 可执行的选项**。
> 事实来自本地编译产物（`pdftotext`/`pypdf` 实测），外部期刊政策一律标注"待核"，不推测。

## 一、实测篇幅

| 稿件 | 主稿页数 | 实测锚点 | 期刊硬性上限 | 备注 |
|---|---|---|---|---|
| Paper A（Neurocomputing, elsarticle）| **74** | References 起于第 70 页；正文+附录 ≈ 69 页 | 无（Guide 未给带数字的篇幅上限）| 另有 Springer 变体 **53** 页（References 起于第 48 页）|
| A1（Pattern Analysis and Applications, Springer）| **64** | References 起于第 61 页 | 无 | 摘要 241/250 词（已留 9 词余量）|
| A23（IEEE JOE）| **70** | References 起于第 55 页；补充材料 **43** 页 | **待核**：JOE 的版面费/超页规则未在本地留证 | 提交版本为 64 页（`SUBMISSION/_frozen_submitted` 未动）|
| Commentary（PRL）| **7** | 上限 7；参考文献在第 7 页 | **7 页（硬上限）** | 本轮已精简 82 词，末页行数 126→118，留出约 6% 余量 |

## 二、可压缩的候选（需操作者决定，未擅自改稿）

| 稿件 | 候选动作 | 预计节省 | 代价 |
|---|---|---|---|
| Paper A（NC 74 页）| 把附录 E/G（解码器 VLM 两节）整体移入补充材料，主稿只留结论段 + 指向补充 | **约 6–9 页** | 主稿自洽性略降；需同步改引用与 provenance 清单 |
| Paper A | 把附录 A–D 的逐表明细改放补充材料 | 约 4–6 页 | 同上 |
| A23（70 页）| 把逐域 CI 明细/负对照表移入已有的 43 页补充材料 | 约 4–6 页 | 需重排附录编号 |
| A1（64 页）| 把监测评估的逐运行表移入补充材料 | 约 3–5 页 | 同上 |
| Commentary | 已到 7 页上限；任何新增必须等量删减 | — | 本轮已建 6% 余量 |

## 三、判定

- **Neurocomputing 与 PAA 没有硬性页数上限**，所以 Paper A/A1 的"偏长"是**审稿体验**问题而非合规问题；
  **JOE 的超页费用规则需要操作者核实**（本地无来源，按项目规则记为待核，不填数字）。
- 因此本轮**不做大删减**：改稿属于编辑决策，且两篇都在审稿中；本地只做了无争议的瘦身（A1 摘要、Commentary 文字）。
- 一旦决定压缩，按上表执行即可；每一次移动都必须同步：① 稿件编号与交叉引用；② `docs/PROVENANCE_MANIFEST_2026-10-20.md` 的 label 归属；③ 重新编译 + 全部门禁。

## 四、复核命令

```
python -c "from pypdf import PdfReader; print(len(PdfReader('paper合/main_nc.pdf').pages))"
python tools/_p1181_verify_paperA_consistency.py
python -m tools.paper_audit audit --profile paperA_nc --fail-on NONE
```