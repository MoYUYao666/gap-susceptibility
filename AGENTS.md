# 项目说明 — Cross-Modal Alignment under PEFT

## 🔴 模型获取规则（用户明确要求，最高优先级）

**所有模型权重一律直接在服务器（autodl）上下载，禁止"本地下载 → 上传服务器"流程。**

- 原因：本地下载再上传耗时且易错（曾发生 GPTQ 模型上传 + 版本不兼容问题）
- 服务器下载命令（国内网络环境）：
  - ModelScope（推荐，国内快）：`python -c "from modelscope import snapshot_download; snapshot_download('模型名', local_dir='/root/...')"`
  - HuggingFace 镜像：`HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_XET=1 python -c "from huggingface_hub import snapshot_download; ..."`
- 完整实验流程见 `exp/README.md`

## 项目结构速览

- `paper/` Paper 1（PR，elsarticle）；`paper_a1/` A1（Neurocomputing）；`paper_a2/` A23（海洋/声呐，IEEE JOE `26-0663`）；`paper_ap3/` ap3（**唯一合并主线**，P1+P2+P3，待 P1 出决定）；`paper3/paper_ieee/` Paper 3（TNNLS，已拒）
- `exp/` 补实验脚本（llava-hf / Qwen2-VL 云端跑）；`outputs/` 全部论文数字的溯源来源（**别动**）
- 交接文档：`HANDOFF.md`（状态表 + 数据溯源 + 审计记录）；**`文件地图.md`（"谁是谁" + 当前待办，冲突时以它为准）**；`docs/`（决策、审计、投稿记录）
- 已归档、不再推进：`备选/06_归档稿件/paper合/`（Paper A，**已弃用**）、`paper_a4/`

## 🔴 阶段收尾规则（用户明确要求，最高优先级）

**每完成一个阶段的任务，必须同步更新交接类文档，然后才算"做完"。**

- **每一次会话收尾都算一个阶段**：回答"还剩什么 / 进度如何"之前，先按下方三件同步文档——**不要在聊天里报新状态而文件里还是旧的**。
- **投递类事实（新稿号、状态变更、拒稿/接收）第一时间落账**：这类信息只存在于邮件或投稿系统里，不写进文档就等于丢失；拿不到的字段**记为待核**，不许推测填数。
- **必更三件（按此顺序）**：
  1. `HANDOFF.md` —— 在顶部按日期追加该阶段条目：**做了什么 → 结果是什么 → 还差什么**。
  2. `文件地图.md` —— 涉及"谁是谁 / 当前待办 / 状态"变化时必改（它是导航与待办的唯一入口）。
  3. 该阶段的交付件/决策文档（`docs/*.md`）—— 报告、清单、决策记录；有对应交付件就更新，不要另开一份平行文档。
- **追加，不重写**：历史条目保留；过期结论要**标注过期并给出新结论**，不要静默覆盖（本仓库多次因"旧条目未标注"而误读状态）。
- **每条记录必须可复核**：写明日期、文件路径、脚本名、命令与结果；数字要能给出来源 JSON 或实测命令，禁止只写结论。
- **必须诚实标注状态**：区分"已完成（附证据）/ 进行中（附交付件与阻塞项）/ 待操作者决定（列出选项）"。**交付件尚未落地时，不得写成"已核""已完成"。**
- **改动用脚本、可重跑**：批量修改要落成 `tools/` 下的幂等脚本并带断言，便于日后复核与重放。
- **收尾自检三问**：① 这阶段的结论落到文件了吗？② 有没有哪个文档的数字与之矛盾（尤其页数、计数、投稿状态）？③ 待办列表是否已按新事实更新？

## 🔴 发布边界（用户明确要求）

**当前 GitHub 仓库只放代码与结果，不放论文。** 后续新增内容按此边界处理：

- **可以推**：`tools/`（分析、审计、绘图、校验脚本）、`outputs/`（结果 JSON）、`src/`、`exp/`、`experiments/`、必要的 `docs/`（方法与审计记录）
- **不要推**：任何**稿件本体**（`main*.tex` / `main*.pdf`）、**封面信**、**declaration / title_page / highlights**、以及**在审稿件的任何衍生版本**（含中文镜像——JOE 的投稿认证覆盖"任何语言"）
- **待清理（需操作者决定，勿擅自改）**：`publish` 分支当前仍跟踪稿件类文件（`paper/` 71、`paper_a1/` 38、`paper_ap3/` 30、`paper_a2/` 30，含 `paper/main_nn.pdf` 与各 cover letter）。这是历史推送遗留，**与实际策略不符**；移除需改 `tools/_sync_publish*.py` 的路径白名单，且**远端 git 历史里已存在这些内容**，删除当前文件不等于抹除历史。
- **清空重传的现成工具**：`tools/push_code_only_to_github.ps1` —— 默认**只读预览**（不改工作树、不提交、不推送），`-Execute` 才执行（建 `publish/code-only` → 清零索引 → 按白名单加入 → 提交 → force push 覆盖远端 `main`）。白名单 = `tools` `src` `exp` `experiments` `outputs` `docs` + 根目录四个文件；`outputs/` 下的 `.pt/.pth/.ckpt/.bin/.safetensors/.onnx` 一律排除（GitHub 单文件 100 MB 上限）。实测：保留 1384 个、移出 403 个稿件类 + 20 个权重类。

## 🔴 备份与发布操作纪律

- **备份**：`tools/_make_backup_snapshot.py` 生成 `backups/snapshot_FULL_<日期>.zip` + `.sha256` + `.manifest.txt`。
  默认**排除** `data`/`models`/`coco`/`flickr30k`（可再下载）与 `backups/` 自身（防套娃）；**包含** `outputs/` 与 `.git/`。
  建完必须复核：`sha256` 一致、条目数与 manifest 一致、`zipfile.testzip()` 无损坏。
- ⚠️ **备份 ≠ git 历史**：若 master 有未提交改动，zip 里是**当前文件**，但 `.git` 里没有对应提交记录。
  要"连历史都完整"，先提交再备份。
- **推送 GitHub 前**：先跑上面的**只读预览**核对保留/移出清单，确认"保留清单内稿件类 = 0 且无 ≥100 MB 文件"。
- **本机沙箱内 git 不能联网**（`ls-remote`/`push` 会报 `sh.exe signal pipe` 权限错）——**推送一律由操作者执行**，
  不要试图绕过或改用其它方式。

## 关键约束

- 论文所有数字必须来自真实 JSON（`outputs/`、`paper3/scripts/outputs/experiments/`），禁止编造
- 投稿前跑 `paper3/paper_ieee/audit_check.py` + `audit_pdf.py` 审计
- TNNLS 合规：10 页限制、双盲匿名（作者信息只在 title_page）、AI 披露（K 条）
