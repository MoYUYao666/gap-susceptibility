# 可复制提示词：创建 Paper Audit Mode

> 直接整段复制到「创造模式」会话；完整规格、86 条检查表、profile 矩阵、验收标准与已知坑见
> docs/PAPER_AUDIT_MODE_HANDOVER.md。

```text
你在仓库 D:\Realdesktop\Wan\Important\New（Cross-Modal Alignment under PEFT，Windows + PowerShell 7 + Python 3.14 + TeX Live 2025）中创建一个名为 Paper Audit Mode 的"论文审核模式"。

目标：把"审一篇稿子"固化成可复跑、可追溯、有判定标准的流程。审核轮不改稿；修复另开修复轮并留证据。全程离线，不依赖第三方 Python 包。

必须交付：
1. tools/paper_audit/ Python 包（可用 `python -m tools.paper_audit` 调用），文件包括：
   __init__.py、__main__.py、cli.py、model.py、registry.py、profiles.py、texutil.py、checks.py、report.py、README.md、templates/、freeze/。
2. 检查注册表：86 条检查，分 A-J 十个维度（A 可复现/取证，B 构建，C 结构，D 期刊合规，E 文献，F 数字溯源与一致性，G 排版渲染，H 数据/伦理/声明，I 投稿包与冻结安全，J 证据与交接）。每条检查必须有唯一 id、维度、严重度（P0/P1/P2/P3）、标题、方法说明；能自动化的必须实现，不能自动化的标 MANUAL 并写清需要什么证据。
3. 9 个 profile：paperA_nc（Paper A/Neurocomputing）、paperA_springer、p3_prl（P3/PRL）、a1_nn（A1/Neural Networks）、a23_joe（A23/IEEE JOE）、prl_commentary（PRL Commentary），以及 generic_elsevier / generic_ieee / generic_prl 三个模板。每个 profile 至少配置：manuscript 路径、tex/pdfs/logs、页数/摘要词数/关键词/highlights/盲审等 limits、required_sections、required_declarations、forbidden_strings、key_numbers、claim ledger 与一致性门禁命令（供 F-04/F-05 执行并校验预期字符串）、freeze_paths、包目录与门户名映射、build_command、staged_command。
4. CLI 契约：
   - `python -m tools.paper_audit list-profiles`
   - `python -m tools.paper_audit list-checks [--dimension A] [--json]`
   - `python -m tools.paper_audit freeze --profile <id> [--write]`
   - `python -m tools.paper_audit audit --profile <id> [--staged] [--out DIR] [--fail-on P0|P1|NONE] [--command-timeout N]`
   - `python -m tools.paper_audit selftest`
   - `python -m tools.paper_audit render-template --kind audit|fix|readiness`
   - audit 默认写 docs/audits/AUD-<profile>-<UTC>.md 和 .json；默认 --fail-on P1，有 P0/P1 FAIL 时退出码 1。
5. 报告：JSON 是机器可读的单一真相源，至少含 audit_id、profile、manuscript、generated_at、git_commit、git_branch、git_dirty、verdict、grade、counts、environment、commands、artifacts（SHA-256）、findings（check_id/dimension/severity/title/status/message/evidence/remediation）、checks（注册表快照）；Markdown 报告含判定、blocker、十维覆盖表、逐条 findings、命令、环境、哈希。
6. 判定规则：P0/P1 FAIL 或 ERROR = BLOCKED（grade D）；仅 P2 FAIL = READY-WITH-MINOR（B）；否则 READY（A）。SKIP 不等于 PASS；MANUAL 必须具名审核人签收。
7. 冻结机制：freeze --write 为冻结件（SUBMISSION/、PRL 的 UPLOAD/）记录逐文件 SHA-256；audit 的 I-04 重新计算并报告 added/removed/changed，任何变化都是 P0。不得改动已投出的冻结件。
8. 三套模板：审核报告（AUDIT_REPORT_TEMPLATE.md）、修复证据（FIX_EVIDENCE_TEMPLATE.md，要求 check id + file:line before/after + 验证命令 + 冻结哈希）、投稿就绪清单（SUBMISSION_READINESS_TEMPLATE.md）。
9. 中文协议文档 docs/PAPER_AUDIT_MODE.md：核心原则（证据优先、冻结优先、不自我认证、修复与审核分离、文档收尾）、严重度/判定、A-J 维度表、86 条检查全表、9 阶段流程（冻结基线→加载→采集→构建验证→数字溯源→包/冻结→报告→修复轮→签收复跑→归档）、角色分离、命令速查、新增稿件/检查/模板的方法、禁止事项、口径变更记录、当前基线。
10. 一个可被 DSH 加载的 skill：~/.dsh/skills/paper-audit/SKILL.md（YAML frontmatter：name/description/compatibility/metadata；正文写触发词、首步命令、profile 表、判定、冻结纪律、修复轮、自检与报告要求；触发词包含"论文审核/复审/投稿前终检/在审稿冻结检查/逐条核对"）。
11. 把首轮全量审核报告归档到 docs/audits/ 并生成 README.md 索引；运行 selftest 并记录结果。

硬性约束：
- 不修改任何稿件；不改冻结件；不为了让门禁通过而修改检查口径/严重度。
- 离线：只用标准库 + TeX Live 的 pdfinfo/pdftotext/pdffonts/pdflatex。
- Windows/UTF-8 兼容；命令输出英文（报告与代码英文，协议文档中文）。
- 每条 PASS/FAIL 必须可指到证据（文件、日志计数、命令输出、SHA-256）；禁止"应该没问题"。
- 实现前先读本仓库已有参考实现（若存在）：tools/paper_audit/ 与 docs/PAPER_AUDIT_MODE.md；逐文件对比并说明复刻差异。

验收（必须逐条执行并贴输出）：
1) python -m tools.paper_audit selftest → 注册表 86 条、9 个 profile、模板齐全、冻结文件哈希全部校验通过；
2) 对 6 个稿件 profile 跑 audit --fail-on NONE → 0 个 P0/P1 FAIL，判定全部 READY 或 READY-WITH-MINOR，报告 JSON/MD 落盘；
3) 对 paperA_nc 跑 audit --staged → 独立编译检查（I-03）PASS；
4) 报告归档 docs/audits/ 并有 README 索引；
5) git status 干净（除报告/工具/文档外无稿件改动）；
6) 输出最终验收表：profile / audit id / verdict / pass / fail / warn / manual / skip / 报告路径。
```

> 使用提示：若创造模式所在会话看不到本仓库历史，把本文件一起发过去；§3–§14 是它的规格书，
> §15 是已知坑，§16 是当前实现的基线，§17 是扩展方式。
