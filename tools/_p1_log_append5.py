# -*- coding: utf-8 -*-
"""Append the round-2 artefact-review entry to docs/P1_REMEDIATION_LOG.md (idempotent)."""
import io
import os

P = os.path.join(r"D:\Realdesktop\Wan\Important\New", "docs", "P1_REMEDIATION_LOG.md")
MARK = "## 九、第二轮复查（四份）"
ADD = """
## 九、第二轮复查（四份）与补丁 C–G

第二轮派出四个与"验证修复"不同的攻击面：`docs/P1_REVIEW2_{FIXVERIFY,NUMBERS,MECHANISM,ARTEFACTS}.md`。汇总：fix-verify 4 must/6 should（31/34 项已落盘、构建产物 43 页 0 undefined）；numbers 34 PASS/9 INCONSISTENT/2 UNSUPPORTED；mechanism **7 must**/10 should；artefacts 6 must/6 should/9 note。

### 补丁 C（20 处）
Table 1 SigLIP 5→6（使单元格和 = 印出的 117）；n=204 规则补写"排除严格对照"；Table 2 表注写明 Adapter 列用各自注入后基线并交叉引用 Table 4；fig4 图注改为三面板（rank｜α｜模块，原写"α（左）"）；fig1 去掉"monotonic"；`+0.237` 补注 (d=16)；五种子标准差统一为样本标准差（→1.0%）；supplementary 的 "Table 9" 改用 `\\ref`；`vitl_frozen` 的 R@1 由 0.000 改 `---`（存档无该值）；full-FT CGΔ 上界 +0.67→+0.66（实测 0.6646/0.2609/0.2672）；结论补回具名例外；相关/讨论各处 yi2025 "证明"→"归因"；删除 `paper/main_nn.abs`；fig11 重生成后图注 1.4×/4.16/0.61。

### 补丁 D/D2（机理重构，**影响结论**）
严格对照的结果**反过来否掉了视觉脆弱性解释**：历史混合 text-only 训了 **95.96%** 的参数（含全部 199 个 `vision_model.*` 张量、视觉秩 9.43→6.16–7.02）却与严格对照（0/199、可训 196,608）结果无差异（−0.0458±0.0021 vs −0.0465±0.0027，**Welch p=0.7017**）→ 视觉侧附带更新**惰性**，真正变量是**适配器放在哪一侧**。摘要/intro/conclusion/§5 全部改写：明确对照为**一臂**、有效秩"不变"降级为**冻结一致性检查**（循环）、不再把梯度分析当收敛证据（视觉梯度 1.4× **更大**）。

### 补丁 E（M4/M5）
分层微调族的 text-only/both 是**未冻结**配置且已发散（CG 1.29、R@1 0.01），而 Text+Vis-L1/L2/L4 冻结 → 引言/讨论/图注补"协议警告"；图 8 面板 (B) 由**只含适配器**的重建算出、与冻结必然重合 → 注明是适配器一致性检查，面板 (D)（实测训练跑）才有效。

### 补丁 F/G（投稿件）
- **稿件原本没有 Funding 与生成式 AI 声明**（A1 有）→ 已补（Elsevier 要求；作者确用 Claude/DeepSeek）。
- Table 1 的 Adapter 最佳 CGΔ 由 −0.217 改 **+0.064**（该表图注承诺"相对冻结基线"）。
- 两条 bib 注改为单行（多行 + 保护括号是排版异常的来源）。
- 2026-08-14 那封更正信里 `$\\text{CG}$` 未加载 amsmath → **LaTeX 报错但仍产出 PDF，交上去的那份在该处是残缺的**；已修源码并重编译。
- 返修封面信：删掉"Prefix comparisons"（正文列出 prefix 为未探索），并**新增两行** reconciled 两封 08-14 信（零样本协议 14,288 vs 50k；变化相关性 −0.042/+0.012 → +0.134/+0.190）→ 现 4 页。
- **归档改前遗留物**到 `paper/_superseded_2026/`：`abstract.pdf`（与稿件 9 处矛盾）、`title_page.docx`（Neural Networks／哈工程／旧 ORCID）、`declaration.docx`、`declarationStatement.docx`；并重生成过期的 `declaration.pdf`（原 7-04 哈工程）与 `cover_letter.pdf`（原 8-05）。

### 被否掉的代理结论（第二轮）
- "p = 0.70 应为 0.66–0.67"：**误报**。用样本标准差（0.00303）复算 t=−0.398、**p=0.7017**。
- 第一轮的 [M5]"fig2/fig3 对调"依旧为误报（已目视确认）。

### 我自己的错误（记录）
`re.subn` 的**替换串会处理转义**：`\\a`→BEL、`\\b`→退格、`\\\\`→单反斜杠，导致插入的两行表格丢掉 `\\addlinespace`/`\\bottomrule`。**教训：LaTeX 文本一律用 lambda 作替换**（`re.sub(pat, lambda m: text, s)`），或改用 `str.replace`。

### 仍未完成
① joint 严格臂（今晚，`docs/P1_TONIGHT_RUN.md`）；② Huang et al. ICCV 2025 作者列表（需 VPN）；③ 登录 EM 确认期刊手上是哪一版（08-14 的 14,288 子集 vs 08-22 的 50k 协议）；④ `competing_interests.docx` 内容未核（无法直读二进制，交前请打开确认机构信息）。
"""

s = io.open(P, encoding="utf-8").read()
if MARK in s:
    print("already present, skipping")
else:
    io.open(P, "w", encoding="utf-8", newline="").write(s.rstrip() + ADD)
    print("appended")
