# 项目说明 — Cross-Modal Alignment under PEFT


## ⛔ 自建侧边栏插件已废弃（2026-10-27，操作者要求删除）

> 操作者原话：**"插件删了吧，不要留了"**

`dsh-experiments-panel` 客户端插件**已彻底删除**（源码、tgz、隔离测试 profile `exptest`、两个 profile 的
node_modules 链接、桌面/包服务全部清理；`~/.dsh` 下已无任何 `dsh-experiments-panel` 痕迹）。
两次尝试（手改 profile、GUI 正规安装）都因**客户端条目激活失败**导致 `web boot: 1 entry did not activate`
——一个条目失败即整个 web boot 失败、应用打不开。**结论：这条路不走，也不再保留代码。**

**替代方案（已验证、零风险、操作者可自行开关）**：
- 监控服务：`tools/_p1777_progress_server.py` → `http://127.0.0.1:8787/`
- 开关：`tools/progress_monitor.ps1 -Action start|stop|status`，
  仓库根三个双击即用 `StartExperimentMonitor.cmd` / `StopExperimentMonitor.cmd` / `ExperimentMonitorStatus.cmd`，
  桌面快捷方式 `实验监控-开启/关闭/状态.lnk`；默认 30 分钟无人访问自动停；**不影响训练与应用**。
- 展示：Edge 分屏（`Ctrl+Shift+S`）把该页放右侧。

## 🔴🔴 执行节奏规则（用户明确要求，2026-10-26 立，长期有效）

> **"尽量一次性做完任务，除重大决策外不要时不时问我"** —— 2026-10-26 操作者原话

**铁律**：

1. **默认自主推进到底**：一个任务从开始到交付要在**尽量少的轮次**内完成，不允许把可自行完成的小步骤拆成
   反复请示（例：改代码 → 跑实验 → 取回 → 打分 → 写档 → 提交，应作为一次连续作业完成）。
2. **只在"重大决策"处停下来确认**，界定为：
   - 会产生**对外可见后果**（投稿/改投、DOI 与 tag 冻结、发布、公开仓库）；
   - **花钱或长时间占用云端资源**且范围未定（新开大实例、大规模扩实验）；
   - **科学结论方向**改变（例如负结果是否进正文、是否推翻某条既有主张）；
   - 违反既有规则或与已冻结记录冲突时的取舍。
   **其余一律自行决定并继续**，事后再汇报。
3. **失败也要一次做到位**：实验失败时先**自主定位并修复**，能重跑就重跑；只有在"缺外部凭据/需操作者开机"这类
   物理阻塞时才停下说明。
4. **汇报节奏**：过程中只在**关键节点**给一句话进度；不要每一步都问"要不要继续"。
5. **阻塞要一次说清**：若确实需要操作者动作，必须一次性给出**需要什么、为什么、给完我能做什么、预计多久**，
   不要分多轮挤牙膏。

## 🔴🔴 投稿目标必须是 SCI 期刊（用户明确要求，2026-10-24 立，长期有效）

> **"不管投哪，必须是SCI期刊，记录进规则"** —— 2026-10-24 操作者原话

**铁律**：

1. **任何稿件（研究论文、综述、Commentary/Perspective、Letter）的投稿目标，必须是 SCI(E) 收录期刊**
   （Web of Science Core Collection 的 **SCIE**；ESCI-only、Scopus-only、纯开放获取无 WoS 收录的刊物
   **一律不合格**）。
2. **投稿前必须核实并留痕**：在 `docs/VENUE_SCI_REGISTRY.md` 登记一行，含
   **刊名 / ISSN / 出版商 / 收录类型（SCIE）/ 核实来源 URL / 核实日期**。
   核实来源优先顺序：① Clarivate Master Journal List（mjl.clarivate.com）；
   ② 出版商官网的 "Abstracting & Indexing" 页；③ LetPub / MIAR 等第三方（仅作旁证，须与 ① 或 ② 交叉）。
3. **未核实的刊物视为不合格**：可以列在候选清单里，但必须标 `待核`，**不得**作为投稿目标写进任何方案、
   cover letter 或对外文档。
4. **替代出口只有两类**：(a) 合格的 SCIE 期刊；(b) **arXiv/Zenodo 预印本**（用于占位与引用，
   不计入"投稿目标"，也不能替代期刊发表的要求）。
5. **改投/被拒后的重新选择同样受本条约束**：包括 Commentary（`PRLETTERS-D-26-02402`）的备选刊物。
6. **例外只能由操作者书面同意**，并在 registry 里写明"经操作者同意"的日期与原话。

**当前五篇的目标刊物（均已核实 SCIE，登记在 registry）**：
Paper A → Neurocomputing（Elsevier）；A1 → Pattern Analysis and Applications（Springer）；
P3 → Pattern Recognition Letters（Elsevier）；A23 → IEEE Journal of Oceanic Engineering（IEEE）；
Commentary → Pattern Recognition Letters（Elsevier，`PRLETTERS-D-26-02402`，在审）。

**已因本条被剔除的候选**：Frontiers in Artificial Intelligence、Frontiers in Big Data（ESCI/Scopus，非 SCIE）。
`Patterns`（Cell Press）与 `Nature Machine Intelligence`（Comment/Commentary 栏目）在 registry 中标 `待核`，
核实通过才可用。

## 🔴🔴 下载源优先级（用户明确要求，最高优先级）

> **"立规矩，云端hf速度慢优先国内源ModelScope之类的"** —— 2026-10-16 操作者原话

**云主机上取模型/数据集/依赖包，一律按此顺序选源**：

> **"规矩改了，走镜像最快"** —— 2026-10-16 操作者最新指示（**取代**此前的"用国内源就不要hf"；该条已作废，见下）

| 顺序 | 源 | 用途 | 实测（2026-10-16，AutoDL 主机）|
|---|---|---|---|
| **1** ⭐ | **`hf-mirror.com`**（`HF_ENDPOINT` + `snapshot_download`）| **模型、数据集** | **主机 3：15 GB / 6–8 分钟（≈30–40 MB/s）** ✅ 首选 |
| **2** | **pypi.tuna.tsinghua.edu.cn** | Python 包 | **3.1–4.6 MB/s** ✅ |
| **3** | **ModelScope** `modelscope.cn` | 模型、数据集兜底 | 单连接 ~1 MB/s；**多连接 13–18 MB/s** |
| 4 | 阿里云 pypi 镜像 | Python 包备用 | 探针 531 kB/s |
| ❌ | `huggingface.co`（直连）| — | **不可达** |
| ❌ | `download.pytorch.org` | — | **0 B/s，卡死**（476 MB 处停住）|

> ⚠️ **同一天两台机的镜像速度差 60 倍**：主机 3 走镜像 **30–40 MB/s**；另一台新实例同样方法**只有 0.5 MB/s**。
> ⇒ **每台新机先探速再定源**（12 秒即可测），不要凭上一次的经验；**镜像优先，但以实测为准**。

**取模型的标准姿势（镜像优先）**：

1. **首选镜像**：`export HF_ENDPOINT=https://hf-mirror.com`、`export HF_HOME=/root/autodl-tmp/hf`
   （放数据盘），然后 `snapshot_download('仓库名')`；
2. **兜底**：镜像若慢，换 ModelScope；ModelScope 单连被限速时用**多连接分块下载器**
   （`tools/_p1083_parallel_fetch.py`，已验证把 1 MB/s 提到 13–18 MB/s）；
3. **别用 `HF_ENDPOINT` 之外的方式直连 `huggingface.co`**（本环境不可达）；
4. **慢 ≠ 卡死**：连续 30–60 秒零增长才判卡死；判卡死后**先测单连 vs 多连**，再换源。

**执行要点**：

1. **先探速再下载**：新主机上手第一件事是量各源吞吐（`curl -m 12 -o /dev/null -w '%{speed_download}'`），
   按实测选源，**不要凭习惯直接 `hf download`**；
2. **ModelScope 仓库名必须用 API 核实**，不要猜：`HubApi().get_model_files(repo)`；
   本次教训：猜的 `AI-ModelScope/llava-1.5-7b-hf` **不存在**（404），实际是 **`llava-hf/llava-1.5-7b-hf`**；
3. **pip 一律带 `-i https://pypi.tuna.tsinghua.edu.cn/simple`**，并设
   `PIP_INDEX_URL` / `PIP_CACHE_DIR=/root/autodl-tmp/pipcache`；
4. **下载放后台并记录速率**（`setsid ... > log 2>&1 &`），便于判断是"慢"还是"卡死"；
5. **慢 ≠ 卡死**：连续 30–60 秒零增长才判定卡死；判卡死后**先测多连接**，再换源；
6. **模型权重仍然只在服务器端下载**（既有规则），本规则不改变这一点；
7. **ModelScope 单连接 633 kB/s 偏慢时先测并行**（多连接聚合），再决定是否需要换数据集侧方案。

## 🔴 模型获取规则（用户明确要求，最高优先级）

**所有模型权重一律直接在服务器（autodl）上下载，禁止"本地下载 → 上传服务器"流程。**

- 原因：本地下载再上传耗时且易错（曾发生 GPTQ 模型上传 + 版本不兼容问题）
- 服务器下载命令（**镜像优先**，见上方源优先级表）：
  - **首选**：`export HF_ENDPOINT=https://hf-mirror.com; export HF_HOME=/root/autodl-tmp/hf`，
    然后 `python -c "from huggingface_hub import snapshot_download; print(snapshot_download('llava-hf/llava-1.5-7b-hf'))"`
    —— 主机 3 实测 **15 GB / 6–8 分钟**；`HF_HOME` 必须指向 50 GB 数据盘（根盘只有 30 GB）
  - **兜底**：ModelScope，`modelscope.snapshot_download`（缓存目录用 `MODELSCOPE_CACHE`，同样放数据盘）；
    **仓库名必须先用 `HubApi().get_model_files('<repo>')` 核实**——猜名会 404
    （已踩过：`AI-ModelScope/llava-1.5-7b-hf` 不存在，实际是 `llava-hf/llava-1.5-7b-hf`）
  - **单连慢时不要换源就先试多连接**：`tools/_p1083_parallel_fetch.py` 实测把 ModelScope 的 1 MB/s 提到 **13–18 MB/s**
  - 运行 `transformers`/`peft` 时可只用本地缓存（`HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`），避免下载后再联网解析
- 完整实验流程见 `exp/README.md`

## 项目结构速览

- `paper/` Paper 1（PR，elsarticle，`PR-D-26-10149`）；`paper_a1/` A1（Neurocomputing，`NEUCOM-D-26-20952`）；`paper_a2/` A23（海洋/声呐，IEEE JOE `26-0663`）；**`paper合/` Paper A = P1+P2（当前主稿，目标 Neurocomputing）**；`弃用/06_归档稿件/paper_ap3/` ap3（P1+P2+P3，**因含 P3 不可投**，已归档）；`paper3/paper_ieee/` Paper 3（TNNLS 已拒 → 改投 PRL `PRLETTERS-D-26-02378`）
- `exp/` 补实验脚本（llava-hf / Qwen2-VL 云端跑）；`outputs/` 全部论文数字的溯源来源（**别动**）
- 交接文档：`HANDOFF.md`（状态表 + 数据溯源 + 审计记录）；**`文件地图.md`（"谁是谁" + 当前待办，冲突时以它为准）**；`docs/`（决策、审计、投稿记录）
> **⚠️ 本节已于 2026-10-06 更正（原条目过期）**
> 原记："已归档、不再推进：`弃用/06_归档稿件/paper合/`（Paper A，**已弃用**）、`paper_a4/`"
> **实况**：`paper合/` **在根目录且为当前主稿**——2026-09-24 曾决定弃用（改以 ap3 为合并主线），
> 但 **2026-10-01 起恢复为主稿**；截至 2026-10-06 编译 **49 页**，`NC_submission/` 投稿包齐备。
> 反而 **`paper_ap3/` 已在 `弃用/06_归档稿件/`**——因其**含 P3 内容**（P3 正投 PRL），
> 合并投出构成重复投稿。权威状态见 `文件地图.md`（冲突时以它为准）。
> **仍未推进**：`paper_a4/`。

## 🔴🔴 唯一原则（用户明确要求，最高优先级）

> **"所有数据必须要可复现有来源。"** —— 2026-10-07 操作者原话

**含义（无例外）**：

1. 稿件/报告里的**每一个数字**，都必须能**指名**：(a) 产出它的**脚本**，(b) 承载它的**归档文件与字段**；
2. **"看起来对"不等于"有来源"**：不得用近似、推断、他人转述、或"应该是这个量级"来填数；
3. **无法给出来源的数字，一律删除**（而非保留待查）——因为读者无法区分"暂时没找到"与"编造"；
4. **第三方数字**（如审稿周期）**必须标注来源**（官网/社区/第三方），不得与自有实测混列；
5. **自动模糊匹配不算验证**：归档规模大时任何数字都能随机命中（本项目已有一次假门禁的教训：
   `tools/_reproducibility_gate.py` 以 0.5% 容差在 122,161 个归档数值里搜 → 145/145 通过，**纯属假象**）。
   **正确做法**：`tools/_claim_ledger.py` —— **人工指名出处 + 逐条断言**。

**门禁**：`python tools\_claim_ledger.py --apply`（24 条关键主张，全通过才算过）。

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

## 🔴 语言规则（用户明确要求，最高优先级）

> **"后续的实验与结果等等都直接用英文来写，你给我输出的结论用中文即可"** —— 2026-10-14 操作者原话

**产出物一律英文**（写进文件的东西）：

| 范围 | 要求 |
|---|---|
| **代码** | 变量名、函数名、注释、docstring、`print`/`argparse` 消息 **全英文** |
| **实验结果与归档** | JSON 的**键与值**、字段说明、`note`/`desc` 类字段 **全英文** |
| **脚本输出** | 控制台/日志文字 **全英文** |
| **文档** | `README.md`、`docs/*.md`、报告、清单 **全英文**（若该文档面向外部或长期留存） |
| **稿件** | 本来就是英文，**不得出现中文**（含注释、宏定义、`%` 注释） |
| **GitHub 发布库** | **全英文**；**唯一例外**见下 |

**唯一例外（必须保留中文）——"功能数据"**：

- **真实存在的文件/目录名**（如 `paper合/`、`outputs/_serial_logs/同秩对照_*.log`）
  ⇒ **翻译会打断路径**，必须原样保留
- **检测/匹配用的正则模式与字符串列表**（如占位符检测器里的 `待补|待填`、
  审计工具的禁止串 `公开仓库`）⇒ 属**功能**而非文字
- **shell 命令里作为参数的文件名**（如 `zip 结果.zip`）

**⇒ 判据：改它会不会让程序找不到文件、或改变匹配语义？会 ⇒ 不改；不会 ⇒ 必须改英文。**

**对话回复用中文**（说给操作者听的东西）：结论、进度、决策、报错解释 —— **中文**。
**报告与消息里的技术名词、文件名、代码片段照原样**（不硬译）。

**⚠️ 引用既有中文文档时**：可以引用，但**新建的产出物一律英文**。
**⚠️ 反例（本项目已发生）**：用 PowerShell `Add-Content` 往 UTF-8 文件追加中文 ⇒ **GBK 字节混入、文件非法 UTF-8**
⇒ **向已存在文件追加内容，必须用 Python 显式 `encoding="utf-8"`**。

### 范围裁决（2026-10-14）

> 操作者在四个选项中选定：**"只管今后，存量不动"**

| 对象 | 语言 | 说明 |
|---|---|---|
| **今后新建的产出物** | **英文** | 代码/注释/docstring/print、结果 JSON、报告、清单、README |
| **已有存量脚本**（`tools/` 下 1,320 个含中文 `.py`，328,521 字符） | **保持原样** | 它们是**历史记录**（每个会话的修订脚本），不是维护目标；**不要为了统一语言去翻改** |
| **交接文档**（`HANDOFF.md`、`文件地图.md`、`docs/` 工作笔记） | **中文** | 它们的用途是**向操作者汇报**，而操作者读中文 |
| **对话回复** | **中文** | 结论、进度、决策、报错解释 |
| **稿件 / 修订包 / GitHub 发布库** | **英文** | 面向外部；**已全部完成**（`SUBMISSION/P3_PRL_revision/` 的答复件与 `publish_clean/` 均已英文化） |

**⇒ 判据（判断某文件该用哪种语言）**：**它写给谁看？**
给**外部**（期刊/审稿人/公众）⇒ **英文**；
给**操作者**（汇报、导航、决策记录）⇒ **中文**；
给**机器**（路径、匹配模式）⇒ **按原样**。

**⚠️ 存量豁免的理由**：`tools/_p4xx_*.py` 这类脚本是**一次性修订脚本**，
其价值在于"记录当时怎么做的"，**改动它们既无收益、又会让 HANDOFF 的按行号引用失效**。

### 🔴🔴 DOI / tag 冻结纪律（2026-10-14 立，因我的操作失误）

> **教训**：Zenodo 归档建好之后，我**又反复强制移动 tag、删除并重建 GitHub Release**
> （`cc9bdac` → `5e1da98` → `e320e75` …）。**Zenodo 把每一次都当成新版本** ⇒
> **同一份快照被铸出了两个 DOI**（`10.5281/zenodo.23341083` 与 `10.5281/zenodo.23341223`），
> 操作者看到的就是"每更新一次 DOI 就变"。

**⇒ 铁律**：

1. **一旦 Zenodo 抓取了某个 tag，该 tag 就冻结** —— **不得** `git tag -d` + 重打，
   **不得** `git push :refs/tags/<tag>`，**不得**删除并重建对应的 GitHub Release。
   （三者都会让 Zenodo 认为是新版本 ⇒ 铸新 DOI。）
2. **要出新版本，就用新 tag**（`v1.1`、`v1.2`…）⇒ Zenodo 会在**同一个概念 DOI**下
   新增一个版本 DOI，DOI 不会"漂移"。
3. **引用规则**：**引用具体版本的 DOI**（Zenodo 官方建议），
   **概念 DOI 用于"始终指向最新版"**。稿件的 Data statement 写具体版本 DOI。
4. **改 README / 元数据这类小修，不值得新铸 DOI**：
   在 Zenodo 记录页直接改描述即可，不动 tag。
5. **需要改 tag 之前，先问操作者** —— 因为这会产生一个新的 DOI，属于对外可见的后果。



> ⚠️ **补充铁律（2026-10-25 立，因 v2.5 漏发 Release）**：**打 tag 之后必须再建 GitHub Release** ——
> Zenodo 的 GitHub 集成摄取的是 **Release**，**不是裸 tag**。本次实测：`git push ssh-origin v2.5` 成功后远端
> tag 列表已含 `v2.5`，但 `gh release list` 最新仍是 `v2.4`，因此 **Zenodo 没有铸出新版本 DOI**。
> 正确顺序：`push main` → `tag -a <tag>` → `push <tag>` → **`gh release create <tag> --verify-tag`**
> （用 `--verify-tag` 复用已存在的 tag，**绝不用 `--target` 去移动 tag**）→ 等 Zenodo 摄取后核对 DOI。
> 判据：`gh release list --repo <owner>/<repo>` 里必须出现新 tag 且标为 `Latest`，否则不算发布完成。

**⏸ 当前状态**：`v1.0-prl-revision` **已冻结在 `e320e75`**（对应 Zenodo `23341223`）；
**在操作者决定用哪个 DOI 之前，不再有任何 tag / Release 操作。**

## 🔴 发布边界（用户明确要求）

**当前 GitHub 仓库只放代码与结果，不放论文。** 后续新增内容按此边界处理：

- **可以推**：`tools/`（分析、审计、绘图、校验脚本）、`outputs/`（结果 JSON）、`src/`、`exp/`、`experiments/`、必要的 `docs/`（方法与审计记录）
- **不要推**：任何**稿件本体**（`main*.tex` / `main*.pdf`）、**封面信**、**declaration / title_page / highlights**、以及**在审稿件的任何衍生版本**（含中文镜像——JOE 的投稿认证覆盖"任何语言"）
- **✅ 已于 2026-09-24 完成**：操作者**删除并重建**了 GitHub 仓库，随后把本地 `publish_clean`（`1ca7744`）force push 上去
  （`+ aa76b48...1ca7744  main -> main (forced update)`）。**远端现状（实测）**：仅 `refs/heads/main = 1ca7744`，**1303 文件**：
  `outputs/` 842、`tools/` 332、`docs/` 78、`experiments/` 25、`exp/` 12、`src/` 11 + 根目录 3；**稿件类 / 权重 / `paper*` / 交接文档 = 0**。
  因是**重建**而非改写历史，**论文与旧对象已从远端彻底消失**（不再有"不可达对象待 GC"的问题）。
- **发布凭据**：`~/.ssh/id_ed25519_github` = `SHA256:pQ1OeDjfHSII20yycl6NW2Uf6VRn88REkvXb2VcP/Ww`（`~/.ssh/config` 已把 github.com 指到它），身份 `MoYUYao666`，实测可用。
- **推送入口已改为独立仓库 `publish_clean/`**（不在 `.worktrees/publish-main` 里改索引——`git rm -r --cached .` 在本机沙箱会**静默失效**）。更新流程：改 live 文件 → 复制进 `publish_clean/` → `git -C publish_clean add -A` → `commit` → `git -C publish_clean push ssh-origin main`。重建脚本 `tools/build_publish_repo.ps1`（可重跑）。
- ✅ **根目录 `.gitignore` 已于 2026-09-24 重建并提交（`fb1fa2f`）**。**更正先前误判**：它并非"UTF-16 乱码"，
  而是**两处 em dash 尾字节被写坏**（`E2 80 3F`，应为 `E2 80 94`，只在两条注释里），**规则一直有效**——
  `outputs/` 的 negation 生效（root 已跟踪 **713** 个 `outputs/` 文件、未跟踪 JSON = **0**）。重建后 `git check-ignore` 逐条验证 **14/14 一致**。
- 📌 **判编码的规矩**：先看**字节**（hex 头、NUL 计数、严格 UTF-8 解码、定位非法字节偏移），
  **不要**凭 PowerShell 的显示或某一种误解码就下结论——本次就是因此在文档里留下了两条错误结论。
- ❓ **仓库可见性未核实**（无凭据；匿名 API 对私有仓库与不存在的仓库都返回 404）。**若准备公开，先确认 `main` 干净**——当前已确认干净。

## 🔴 备份与发布操作纪律

- **备份**：`tools/_make_backup_snapshot.py` 生成 `backups/snapshot_FULL_<日期>.zip` + `.sha256` + `.manifest.txt`。
  默认**排除** `data`/`models`/`coco`/`flickr30k`（可再下载）与 `backups/` 自身（防套娃）；**包含** `outputs/` 与 `.git/`。
  建完必须复核：`sha256` 一致、条目数与 manifest 一致、`zipfile.testzip()` 无损坏。
- ⚠️ **备份 ≠ git 历史**：若 master 有未提交改动，zip 里是**当前文件**，但 `.git` 里没有对应提交记录。
  要"连历史都完整"，先提交再备份。
- **推送前**：在 `publish_clean/` 里核对——`git add -A` 后确认**稿件类 0 个、≥100 MB 文件 0 个**，再 `commit` + `push`。
- **网络前提**：`git push/ls-remote` 需要**允许派生 ssh 子进程的权限**（受限沙箱下会报 `sh.exe … signal pipe`，此时须以更宽权限重试或由操作者执行）。2026-09-24 的推送是在放宽权限后完成的；**别再假设"一定推不了"**，先试一次、按报错判断。

## 🔴 门禁脚本必须用 base 解释器跑（2026-10-25 立，实测）

> 发现经过：2026-10-25 的发布收尾中，用 `D:\Anaconda\envs\pytorch\python.exe` 跑门禁，
> `paperA_nc` / `paperA_springer` / `a23_joe` 三个 profile 直接 **BLOCKED（F-05 consistency gate failed）**，
> `paper_a2/verify_a23_fix.py` 报 `ModuleNotFoundError: pdfplumber`，`tools/_p1454_final_verify.py`
> 报 `No module named 'pypdf'` 后崩溃；换 **`D:\Anaconda\python.exe`（base）** 后全部转绿。

**规矩**：

1. **门禁/审计/复现脚本一律用 base 解释器** `D:\Anaconda\python.exe`
   （不要用 `envs\pytorch`、`envs\torch24`、`envs\torch26` 等训练环境）；
2. 训练/编码/推理脚本仍用对应的训练环境（`envs\pytorch` 等）——**两套解释器分工不同**；
3. **判断"门禁失败"之前，先确认解释器对了**：缺 `pypdf` / `pdfplumber` 一类依赖会把"环境缺件"
   伪装成"稿件不一致"，是**假 BLOCKED**；
4. 该差异**与改动无关**，属既有环境分工；写入本条以便后来者不再误判。

## 🔴🔴 审核范围规则（用户明确要求，2026-10-25 立，长期有效）

> **"之后只需要审核最新稿，旧稿或已归档的不参与审核"** —— 2026-10-25 操作者原话

**铁律**：

1. **审核/门禁/复现只覆盖"最新稿"**：`paper_a1/`、`paper_a2/`、`paper3/paper_ieee/`、`paper合/`、
   `paper_review_prl/` 这五个活跃稿树，以及它们引用的归档与提交包（`SUBMISSION/` 中对应的**冻结件**只做
   **哈希级不改动校验**，不做内容审核）；
2. **`弃用/` 一律不参与审核**：其中任何内容（旧稿、旧云轮目录、历史归档、临时脚本）**都不进入**
   `paper_audit` 各 profile、`_p1454_final_verify.py`、`_p1428_provenance_gate.py`、台账与复现账本；
3. **旧稿/归档只作为溯源证据**被引用（例如冻结哈希清单），**不再作为被审对象**；
4. **新增审核对象前先确认它是最新稿**：若某目录属于弃用范围，**不得**把它加进任何 profile 或清单；
5. **三个例外已于 2026-10-25 移入 `弃用/`（本条取代下方原条目）。** 先纠正一个**假阳性**：早先的守卫用
   **朴素子串**匹配，把 `SUBMISSION/_archive/...` 误判成对根级 `_archive/` 的引用；改用**根锚定**匹配重查后，
   53 个门禁脚本里对这三个目录的**根级引用为 0** ⇒ 迁移安全：
   - **`_archive/`（251 文件）→ `弃用/08_历史归档/_archive/`**：`tools/paper_audit/profiles.py` 与五份
     `tools/paper_audit/freeze/*.json` 里的 46 处 `_archive/` **全部是 `SUBMISSION/_archive/...`**（冻结路径，
     未动），与本目录无关 ⇒ **无需改任何引用**，133 条冻结哈希不受影响；
   - **`paper/`（111 文件）→ `弃用/06_归档稿件/paper/`**：引用仅为**冻结** `SUBMISSION/_archive/*/README.md`
     的历史叙述（按冻结规则**未修改**，仅在本文件与此处记录）与 `paper3/README_是哪篇.md` 的一句目录清单
     （**已更新**）；
   - **`paper_review/`（30 文件）→ `弃用/06_归档稿件/paper_review/`**：Commentary 活跃文档 5 处引用**已更新**
     （`MANUSCRIPT.md` ×2、`DRAFT_OUTLINE.md` ×1、`FIXES_2026-10-18.md` ×2，另 `docs/commentary_compression_and_table.md` ×1）。
   ⇒ **顶层不再有例外**；`弃用/` 内一切内容仍**不参与**任何审核/门禁/账本。
   <原条目（2026-10-25 早间，已被本条取代，保留供追溯）：三个因路径被门禁引用而留在顶层的例外 ——
   `_archive/`（被 `tools/paper_audit/profiles.py` 与两份 freeze manifest 引用 ⇒ 涉及 133 条冻结哈希）、
   `paper/`（被 `SUBMISSION/_archive/*/README.md` 归档记录引用）、`paper_review/`（被 Commentary 的活跃文档引用）；
   三者的处理意见需操作者决定。>

（目录 `弃用/` 于 2026-10-25 由 `备选/` 改名而来，历史文档里出现的 `备选` 均指此目录。）

## 关键约束

- 论文所有数字必须来自真实 JSON（`outputs/`、`paper3/scripts/outputs/experiments/`），禁止编造
- 投稿前跑 `paper3/paper_ieee/audit_check.py` + `audit_pdf.py` 审计
- TNNLS 合规：10 页限制、双盲匿名（作者信息只在 title_page）、AI 披露（K 条）

## 💻 内联命令的引号规则（2026-10-17 立，工具 shell = PowerShell 7.6.7 + UTF-8）

**编码已是 UTF-8，但双引号字面量里 `` ` `` 仍是转义符、`$` 仍是变量前缀** ⇒
**内联命令（`python -c`、远端命令）一律用 PowerShell 单引号包裹**：

```powershell
python -c 'import re; print(len(re.findall(r"\d+", s)))'   # 单引号：反引号/美元/双引号都原样
```

含正则、`$`、反引号、嵌套双引号时尤其必要；中文输出已正常。

## 🧰 科研技能与环境清单（2026-10-17 录入）

完整清单见 **`docs/skills_environment_2026-10-17.md`**（事实来源：`D:\Realdesktop\Wan\Important\DSH-技能交接卡-完整版.md`）。
**环境**：PowerShell 7.6.7（UTF-8）· Python 3.14.6（`D:\Anaconda`，**本项目 torch 在 `envs\pytorch`**）· TeX Live 2025 · Node 24 · Edge + CDP 代理。
**技能 43 个**（`~/.dsh/skills` 33 + `~/.agents/skills` 10）。

本项目最相关的几个，**用之前先 `skill` 加载**：

| 任务 | 技能 |
|---|---|
| 改写/重构稿件章节 | `nature-writing` |
| 润色、精简、LaTeX 排版 | `nature-polishing` |
| 统计报告审查（均值±离散度、重复数、不确定性）| `nature-statistics` |
| 引文逐字段核对 | `nature-ref-verifier` |
| 检索 / DOI / 引文格式 | `nature-academic-search`（或 MCP `mcp__academic-search__*`）|
| 投稿前自审 | `nature-reviewer` |
| 数据/代码可用性声明 | `nature-data` |
| 期刊级配图 | `nature-figure` |

**边界**：无 Elsevier API（`search_scopus`/`search_sciencedirect` 会报错）· arXiv 源常 30 s 超时 · 全文下载必须走已登录的 Edge（Elsevier/Springer/IEEE 加 `--route web_access`）· `cordis.patch.yml` 新增条目必须包在 `insert:` 下。

## 🔴🔴 云端主机收尾规则（用户明确要求，2026-10-17 立）

> **"云端全部跑完并确认无误就关机哈，我就不手动关了，记录这个规则"** —— 2026-10-17 操作者原话

**云端任务结束后由 agent 负责关机，操作者不再手动关。**

**必须按此顺序（顺序不可颠倒）**：

1. **确认跑完**：进程已退出、没有 `ARM_FAILURES` / traceback；
2. **确认无误**：跑该阶段的全项校验（记录数、字段、样本量、适配器非空、分塔隔离等），**断言通过**；
3. **取回产物**：记录 JSON、适配器、分析结果**全部拉到本地**并逐文件校验大小；**任何还需要的东西都不能只留在云端**
   （数据盘未必随实例保留，旧实例已出现过"机器失联"）；
4. **只有以上三步完成后**才关机：
   ```bash
   sync && ( shutdown -h now || poweroff || /usr/bin/shutdown -h now )
   ```
   若容器内无权关机，则如实报告"需在 AutoDL 控制台停止"，**不得假装已关**；
5. **关机后验证**：端口探测应失败（`Test-NetConnection <host> -Port <port>` 返回 False），并在交接文档记一条"已关机"及时间。

**禁止**：结果未取回就关机；校验未过就关机；把"我以为跑完了"当成跑完。


## 🔴🔴 云端并行规则（用户明确要求，2026-10-25 立，长期有效）

> **"只要是云端，先确认实验是否有无bug，然后依据显存选择并行，能并行必须并行提高效率"** —— 2026-10-25 操作者原话

**三步，顺序不可颠倒**：

### 第一步：先确认实验没有 bug（不许"先跑起来再说"）

云端 GPU 按时计费，跑错一轮的代价是钱 + 时间 + 可能的错误结论。开跑前必须**逐项留痕**：

1. **本地先跑三件**：脚本的 `--plan`（输入/环境/公平性检查）、`--self-test`（断言集）、`--dry-run`
   （打印将要执行的全部命令与将写出的全部数字），三者都必须 exit 0；
2. **最小单元冒烟**：先用 1 个单元/1 个臂/1 个样本量级在云端真跑一遍，确认产物结构、命名、字段与断言
   都符合预期，再放全量；
3. **契约检查**：确认脚本会"缺输入就 exit 非 0 并打印精确取数命令"，而不是**在缺件时给出数字**；
   确认预声明判定规则（等价 margin、决策阈值）在跑之前就已经写死；
4. **命名冲突检查**：列出每个并发单元将要写的**文件名**，确认并发集合内**没有重名**
   （本项目踩过：按种子命名的臂若种子相同会互相覆盖 `verify_r*_s<seed>_*.json`）；
5. **留痕**：把上面每一步的命令与结果写进该轮的 `docs/*notes.md`，没有留痕视为没做。

### 第二步：按显存实测决定并发度（不靠猜）

1. **先量再定**：跑**第一批**（1 个进程）并用 `nvidia-smi` 记录峰值显存，再据卡容量决定每批进程数
   （经验值：4-bit 7B LoRA 训练约 4–8 GB/进程；4-bit 7B 推理约 4–8 GB/进程；32 GB 卡通常可放 **2–3** 个）；
2. **安全边界**：总量不超过卡容量的 **~85%**（32 GB 卡 ⇒ 上限约 27–28 GB），并给 CUDA 上下文/碎片留余量；
3. **计量口径**：并发度按 **显存** 定，不按 CPU 核数；单进程若本身就是显存大户（如全参微调、长上下文推理），
   并发度为 1 也是合法结论——但必须在笔记里写明**实测的峰值显存**作为依据。

### 第三步：能并行就必须并行（否则要给出理由）

1. **默认并行**：只要第一步的命名冲突与第二步的显存都通过，**必须拆分并发**，不得因为"习惯串行"而排队；
   典型做法：把 N 个独立单元（臂/种子/语料/配置）拆成**互不相交**的批次，每批一个 detached 进程
   （`setsid nohup ... > logs/<batch>.log 2>&1 &`），并把确切命令写进 `logs/parallel_plan.txt`；
2. **降级条件（必须记录实测依据）**：显存超限、进程异常退出、或**单单元耗时比串行翻倍以上**（说明在抢同一
   计算资源、总吞吐反而下降）⇒ 回退串行，并把实测数字写进笔记；
3. **禁止重复作业**：并发前先 `ps aux` 确认**没有别的会话/agent 已经在跑同一作业**；两个进程写同一批产物
   比慢十倍更糟（会静默覆盖归档）；
4. **并发不等于放松验收**：每个单元仍要独立通过自己的断言与归档校验；取回、校验、关机顺序不变；
5. **收尾必产出**：该轮笔记里要有一行"并发度 = X（依据：峰值显存 Y GB / 命名冲突检查 Z）"，
   以及"并行 vs 串行实测耗时对比"。

## 🔴 生图字体规则（用户明确要求，2026-10-18 立，长期有效）

> **"图片的字体也得是 times new roman，以后生图里面的文字都得是这个字体"** —— 操作者原话

**所有生成图（论文插图、graphical abstract、示意图、补充材料图）里的文字一律 Times New Roman**，数学符号用 STIX
（Times 兼容字形）。这条规则对**今后所有新图**生效，不只是当前稿件的图。

**matplotlib 统一设置（每个生图脚本开头必须加）：**

```python
import matplotlib as mpl
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
})
```

**交付前检查（硬判据）**：`pdffonts figure.pdf` 只应出现 `TimesNewRoman*`（数学允许 `STIXGeneral*`）。
出现 `DejaVu*`、`Arial*`、`Helvetica*` 即未达标，必须重生成。

**已按此修复（2026-10-18）**：`tools/_p1210_figure_matched_gap.py`（fig5）与 `tools/_p1276_graphical_abstract.py`
（graphical abstract）原本用 DejaVu Sans，已由 `tools/_p1288_fix_figure_fonts.py` 插入样式块并重生成；
fig1–fig4 本来就是 Times New Roman，未改。核验结果：六张图（含裁边版）只含 TimesNewRoman 与 STIXGeneral。

**嵌入类型要求（同日追加）**：字体必须嵌为 **CID TrueType**（`pdf.fonttype=42`）；**Type 3 不被接受**——
出版社排版会拒收 Type 3。`pdffonts` 检查时同时看 `type` 列，出现 `Type 3` 即需重生成。

**已按此修复的第二批（2026-10-18 晚间）**：fig1–fig4 原为 **Type 3**（`clip_a1_figures.py` / `clip_a1_fig4.py`
只设了字体族、未设 `pdf.fonttype`），已由 `tools/_p1290_regen_legacy_figures.py` 插入样式块并重生成；
六张图（含裁边版）现均为 **CID TrueType**：TimesNewRomanPSMT / TimesNewRomanPS-BoldMT / STIXGeneral。

## 🔴🔴 结果溯源硬规则（2026-10-20 立，长期有效）

> 操作者原话："从现在起论文里每个表格或者别的需要体现我们结果的都要有详细的脚本来源路径和json路径，没有的就补全"。

- **适用范围**：五篇稿件（A1 / Paper A / P3 / A23 / Commentary）中所有报告**我们自身结果**的表与图；纯文献表、示意图可豁免，但必须在清单中显式标注 `exempt` 及理由。
- **落地形式**：`docs/PROVENANCE_MANIFEST_2026-10-20.md` 逐项登记 `label → 生成脚本 → 结果 JSON（含字段路径）`；稿件中以 caption 末尾 `Source:` 行或正文 `Data and code provenance` 节给出对应路径。
- **门禁**：`python tools/_p1428_provenance_gate.py` —— manifest 中任何一项缺失/未验证即失败；`paper_audit` 各 profile 增加该门禁。
- **新表/新图**：生成时必须同步写 manifest 与 caption Source 行，否则不得入稿。
- **历史条目**：按轮次补齐；每轮收尾时把 `pending` 数量写进 HANDOFF。

## 🔴🔴 投稿文件名规则（2026-10-21 立，长期有效）

> 操作者原话："所有投搞的文件名称不要有 '_'"

- **适用范围**：所有向期刊/会议系统上传的文件名（Manuscript、Supplementary、CoverLetter、TitlePage、Abstract、
  Highlights、LaTeXSource 等），**一律不含下划线**；用驼峰（`CoverLetter.pdf`）或连字符。
- 实现：`tools/_p1336_build_venue_package.py` 统一重命名为 `Manuscript.pdf`、`Supplementary.pdf`、
  `CoverLetter.pdf`、`TitlePage.pdf`、`Abstract.pdf`、`Highlights.pdf`、`LaTeXSource.zip`；
  `tools/_p1445_rebuild_packages.py` 重建时自动生效。
- 本地源文件/脚本名不受此规则约束（只在**上传文件名**层面执行）。
