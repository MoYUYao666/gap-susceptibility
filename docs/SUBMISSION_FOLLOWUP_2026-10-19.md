# 投稿后续跟踪（2026-10-19 记录）

> 依据：Springer Nature Snapp 官方页 "How to submit → What happens after submission"（2026-10-19 读取），
> 以及各投稿门户当前状态。**只记录事实**；拿不到的字段写"待邮件"。

## 一、当前状态（2026-10-19 14:05）

| 稿件 | 期刊 / 平台 | 编号 | 状态（门户实测）| 下一步 |
|---|---|---|---|---|
| **A1** | Pattern Analysis and Applications（Snapp）| Submission ID `0a4629f0-0a6d-45d8-b5b1-3681cc4adc8b`；**PAA 稿号待邮件** | **With editor（2026-10-19）**：Submission received ✓、Technical check ✓、Editorial assignment ✓；v.1.0；审稿文件 `latex_source.pdf` | 等编辑决定：送审（Reviewer invited）或直接要求修改 |
| **Paper A** | Neurocomputing（Elsevier EM）| **`NEUCOM-D-26-23760`** | **With Editor**（状态变更 2026-10-19 12:08；提交 2026-10-18 9:19）| 等送审 → 出现 Under Review / 收到审稿意见 |
| P3 | Pattern Recognition Letters | `PRLETTERS-D-26-02378R1` | **Decision in Process**（2026-10-19）| deadline **2026-11-02**；等决定邮件 |
| A23 | IEEE JOE | `26-0663` | 在审 | 等决定 |
| Commentary | PRL | `PRLETTERS-D-26-02402` | 在审 | 等决定 |

## 二、Snapp 投稿后的正式阶段（官方页面，逐条对应我们的动作）

| # | 状态 | 含义 | 我们的动作 |
|---|---|---|---|
| 1 | **Technical check**（进行中）| 检查可读性、格式、声明（伦理/利益冲突）、作者身份；AI 查重 | 保持邮箱 `hw4c24@soton.ac.uk` 畅通；若要求澄清，**只改本地稿**、不改冻结包，等明确替换许可 |
| 2 | Editorial assignment | 通过技术检查后，编辑团队指派编辑；会分配 **PAA 稿号** | 收到邮件后：把稿号写入 `HANDOFF.md`、`哪篇是哪篇.md`、`文件地图.md`、`AUTOMATION_HANDOVER.md` 与每周提醒 prompt |
| 3 | With editor | 编辑评估是否符合期刊；可能要求修改或直接送审 | 等；不主动催稿（首次投稿 <1 周属正常）|
| 4 | Peer review | 送审：Reviewer(s) invited → accepted → report(s) received | 收到意见 → 用 `docs/A1_REVIEWER_OBJECTIONS.md` 与 `docs/REVISION_CITATION_BACKLOG_2026-10-19.md` 起草逐点回复 |
| 5 | Revision requested | 官方数据：约 **97%** 的录用稿至少需一轮修回；**必须同时提交修订稿 + 逐点回复** | 从**本地工作副本**重建投稿包（已含升级包 14 项与补引），新建对应 `SUBMISSION/` 包，保留 `_frozen_submitted/` 原件 |
| 6 | Revision received | 修订件再过技术检查，编辑评估 | 同上；多轮修回属正常流程 |
| 7 | Final decision | 录用或拒稿 | 录用 → 授权/校对；拒稿 → **Transfer Desk** 可能推荐同系列期刊（Springer）或改投 |
| 8 | Transfer Desk（若拒）| Springer 内部转投建议 | 用 `tools/_p1336_build_venue_package.py` 一键重建目标刊包（本地，无需重跑实验）|

## 三、检查节奏（写进每周提醒）

- **每天**：看一次邮箱（技术检查问题常以邮件形式出现）；
- **每周一**（现有文献检索提醒）：顺带核对两个门户的状态——PAA 的 Snapp 详情页、Elsevier EM 的 `NEUCOM-D-26-23760`；状态变化立即落账；
- **2026-11-02 前**：P3 的 R1 审稿截止，优先处理 P3；
- **不做**：不主动重传文件、不在审稿期替换冻结件。

## 四、落账位置（状态一变就改这几处）

1. `HANDOFF.md`（顶部按日期追加）；
2. `哪篇是哪篇.md`（状态列）；
3. `文件地图.md`（状态表 + 追加条目）；
4. `AUTOMATION_HANDOVER.md`（各稿标题行）；
5. 每周提醒 prompt（本周已含 Paper A 稿号与 A1 状态）。

## 五、状态历史

- **2026-10-18 19:5x**：投稿（提交 v1.0）；
- 2026-10-19 上午：Submission received → Technical check in progress；
- **2026-10-19 15:25**：Technical check ✓、Editorial assignment ✓ → **With editor**。

- **2026-10-19 12:08（EM）**：Paper A 状态 **With Editor**。

- **2026-10-19（EM）**：P3 `PRLETTERS-D-26-02378R1` 状态变为 **Decision in Process**（2026-10-13 投出）。
