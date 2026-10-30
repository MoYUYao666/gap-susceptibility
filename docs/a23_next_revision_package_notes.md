# A23 下一修订包（staged next revision，JOE `26-0663`）记录（2026-10-25）

> **参见（A23 同一轮共 6 份笔记，按时间序）**：`a23_multiencoder_round_notes.md`（2026-10-24 上一轮）→
> `a23_multiencoder_rerun_notes.md`（重跑口径）→ `a23_multiencoder_cloud_notes.md`（云端多编码器）→
> `a23_21unit_switch_notes.md`（21 单元切换）→ `a23_transfer_claim_rewrite_notes.md`（迁移主张改写）→
> **本文件**（下一版修订包，最新）。**冲突时以本文件为准**；更早的 `a23_fine_eps_round_notes.md` 属另一主题（细 ε 证书）。

## 1. 建了什么

- **包路径**：`SUBMISSION/A23_JOE_next_revision/`（新建）。投稿包 `SUBMISSION/A23_JOE/` 与冻结副本
  `SUBMISSION/_frozen_submitted/` **一个字节都没改**（证据见 §3）。
- **稿件**：`paper_a2/main_ieee.pdf`（**73 页**，2026-10-25 08:11 构建）。包内 `Manuscript.pdf` 与它逐字节相同。
- **构建脚本**：`tools/_p1631_a23_next_revision.py`（新写的 A23 驱动）→ 调用 P3 用的同一个通用构建器
  `tools/_p1336_build_venue_package.py`。包内文件名 / README 表 / `SHA256SUMS.txt` 约定照抄 P3 的
  `SUBMISSION/P3_PRL_next_revision/`（由 `tools/_p1627_rebuild_next_revision.py` 构建）。
- **上传文件名全部不含 `_`**（驱动内断言，7 个文件名逐一检查）。
- 两次连续重建产出**逐字节相同**的包（`rebuild byte-reproducible: True`）。

## 2. 源 → 包 映射（大小 + sha256，2026-10-25 终态）

| 包内文件 | 源 | 大小 (B) | sha256 |
|---|---|---|---|
| `Manuscript.pdf` | `paper_a2/main_ieee.pdf`（73 页） | 1,275,901 | `f5a3725e95c842c86198dc798184d4fa6a0cdf5bd46b6e2790503e668ae22856` |
| `Supplementary.pdf` | `SUBMISSION/A23_JOE/supplementary/SUPPLEMENTARY_FOR_REVIEWERS.pdf`（43 页，**只读复制**） | 1,065,101 | `5a9c624e106ec7d06eed8163cb4a4a48e1dbdc545c47d20d10c2c63f3d840f77` |
| `Highlights.pdf` | `paper_a2/highlights.pdf`（1 页） | 72,213 | `15ca97d1ca574e0141ca2e75ef41e23de1aca93e17dcde3bad9ec9cfc6f5a69c` |
| `DeclarationOfInterest.docx` | `paper_a2/declaration_of_interest.docx` | 5,700 | `99bbb817697652a048d691785fcaca9006c08f5c5132760549da103d97d8b1bd` |
| `LaTeXSource.zip` | 构建器从 `paper_a2/` 打包，主文件改名 `root.tex` | 964,664 | `e92b0a91b5274640d808bbaa7af6110a82f71e78a9933ae35d8879b26bbac49f` |
| `README.md` | 构建器生成 + 驱动追加冻结记录 | 2,606 | `d072b03193ac74bbc6b1ced8c16d871b9740ba57531248401efe9288c7565512` |
| `SHA256SUMS.txt` | 上列 6 个文件的 sha256 | 497 | `96873223bdde05b62f9c2f24925f444daaae38aac701c3bd753bd5ac065fd490` |

- `Supplementary.pdf` / `Highlights.pdf` / `DeclarationOfInterest.docx` 与**投稿件逐字节相同**（sha256 等于
  `paper_a2/verify_a23_fix.py` 冻结清单里的对应值），即**本次修订未改**这三件。
- `LaTeXSource.zip` 内含 13 项：`root.tex` + `ext_partI..V.tex` + `figures/fig1..7.png`。主文件必须叫
  `root.tex`（JOE 门户硬要求，见 `SUBMISSION/A23_JOE/supplementary/README.txt`）。独立校验：解压到临时目录、
  连跑两次 `pdflatex root.tex` → **73 页 / 0 error / 0 undefined ref-cite / 0 overfull hbox**。
- 包内不含 `main_zh.*` / `zh_ext_*.tex` / 封面信 / 摘要 / highlights 源码（只留编译该稿真正需要的文件）。

## 3. 冻结证明（本轮实测）

| 检查 | 命令 | 结果 |
|---|---|---|
| 37 个冻结哈希 | `python paper_a2/verify_a23_fix.py` | **ALL CHECKS PASSED**（29 项 PASS，含 `frozen archive: all 37 SHA-256 hashes unchanged`） |
| 建包**前后**逐文件快照 | 37 个 `SUBMISSION/A23_JOE/**` + 14 个 `SUBMISSION/_frozen_submitted/**` | 前后**逐文件相同**；清单摘要 sha256：`A23_JOE 39c0d4499e72ba06f9eab9b7ffb26808221d1c570bff6c54f3f5d35f6db091f1`、`_frozen_submitted 0e6e784be5e4238e2a20f116d39ab22ef7214d1d61a91c36107c74e0377e8aab` |
| `git status --porcelain SUBMISSION/` | 同左 | **输出为空**（见下方说明；对 SUBMISSION 不构成证据） |
| `git status --porcelain SUBMISSION/A23_JOE/ SUBMISSION/_frozen_submitted/` | 同左 | 同样为空（同上） |
| `git check-ignore -v` | `SUBMISSION/A23_JOE_next_revision/`、`SUBMISSION/A23_JOE/`、`SUBMISSION/_frozen_submitted/` | 三者都命中 `.gitignore:74:SUBMISSION/` |

⚠️ **`git status` 这条要如实读**：`SUBMISSION/` 整目录被 `.gitignore` 第 74 行忽略
（`git ls-files SUBMISSION/` = **0** 个文件），所以该命令**无论有没有新建包都打印空**——它既不能证明包新建了、
也不能证明冻结件没被改。**真正的冻结证据是上面两条**：37 哈希门禁 + 建包前后快照逐文件一致。

## 4. 修订信必须披露的内容

1. **迁移主张收窄为有界陈述**：`5 units / 25 pairs / 0 survivors` → **`21 units / 441 pairs / 29 survivors`**，
   29 条幸存者的目标语料**全部是声呐**（`12` SigLIP + `10` OceanCLIP + `6` RemoteCLIP + `1` CLIP-L/14）；
   27/29 是 σ 相对族 `M(ε/σ_D)`；最强一条 BioCLIP(sonar) → SigLIP(sonar)：目标 BA `0.900`、源拟合 BA `0.500`
   ⇒ 迁移的是**方向**（M 低 = 健康），不是可移植的绝对阈值。
   来源：`outputs/analysis/a23_multiencoder_transfer.json`（`conclusion.n_units` / `n_ordered_pairs` /
   `n_entries_surviving_bootstrap` 等），脚本 `tools/_p1614_a23_multi_encoder_transfer.py`。
   **诚实标注（重要）**：这段主张**在投稿件里根本不存在**——对冻结的 64 页 `SUBMISSION/A23_JOE/current/main_ieee.pdf`
   做 `pdftotext` 检索，`21 units` / `no threshold` / `multi-encoder` / `acoustic-sonar` **均 0 命中**。
   `5 units / 25 pairs / 0 survivors` 是**投稿之后本地草稿**的状态（`docs/a23_multiencoder_round_notes.md`），
   今天还短暂出现过 `18 units / 324 pairs / 19 survivors` 的中间态（`docs/a23_transfer_claim_rewrite_notes.md` §9）。
   ⇒ 修订信应按"**新增**了多编码器迁移段落（现为有界声呐域陈述）"披露，并给出现行数字；不要把 5 单元口径
   说成审稿人读到的版本。
2. **页数**：投稿件 **64 页** → 当前草稿 **73 页**；其中最后一步 **72 → 73** 就是今天这次改写（新句比旧句长
   ≈1,073 字符 + Source 行字段路径再长 ≈600 字符，跨了分页边界）。依据：`paper_a2/verify_a23_fix.py` 的
   `PAGES = 73`、`docs/a23_transfer_claim_rewrite_notes.md` §5。
3. **新增第五条限制**：本次扩格引入的 RemoteCLIP 是遥感微调编码器，其 top-1 在这三个语料上**都落在 chance 的
   两倍以内**（`12.83 / 11.27 / 2.43 %` 对 `14.29 / 14.29 / 1.49 %` chance），而 29 条幸存者中 **6 条**的目标
   取自它（`paper_a2/ext_partII_domains.tex` 该段 limits 列表第 5 条；RemoteCLIP 权重身份/加载/非随机权重
   四组复验见 `docs/a23_21unit_switch_notes.md` §2）。

## 5. 没建 / 待决定（诚实清单）

- `CoverLetter.pdf`：**未建**。P3 的 next-revision 包同样不含封面信（其 README 记 `not supplied`）；且
  `paper_a2/cover_letter.pdf` 是**投稿件**的封面信（2026-10-17），描述的是投稿版内容 ⇒ 修订封面信 / 答复信
  必须新写（披露清单见 §4）。
- `TitlePage.pdf`：**未建**（JOE 单盲、作者块在正文里；投稿包也没有单独 title page）。
- `Abstract.pdf`：**未建**（P3 包不含该件）。`paper_a2/abstract.pdf` 是当前的（1 页，`verify_a23_fix.py`
  已验证 `abstract.tex` == `main_ieee.tex` 的摘要/关键词/标题），门户若要可随时补。
- `SUBMISSION/A23_JOE/abstract_plaintext.txt` **已过期**：它是投稿时的纯文本摘要（1,438 字符），与当前
  `paper_a2/abstract.tex` 从第 200 字符起就不一致（当前作 "the Describable Textures Dataset (DTD)"，冻结版作
  "DTD"；当前 1,572 字符）。若门户要求重填摘要字段，需按当前摘要重新生成；冻结包内那份**不能改**。
- P3 包里的 `EM_FIELDS.md` 是 PRL 专用字段清单，A23 **没有对应文件**（门户字段来源：`paper_a2/abstract.tex`
  与正文声明节）。
- 包内 `Supplementary.pdf` 是**投稿时的审稿人补充材料**（43 页：索引页 + OE 决定信 + A1 同期稿），本次修订
  **未改**；若 JOE 要求更新补充材料，需另建。

## 6. 复核命令

```powershell
python tools/_p1631_a23_next_revision.py                  # dry run
python tools/_p1631_a23_next_revision.py --apply --verify-tex   # 建包 + 独立编译校验 + 写 SHA256SUMS
python paper_a2/verify_a23_fix.py                         # 必须 ALL CHECKS PASSED（37 哈希全绿）
git status --porcelain SUBMISSION/                        # 空（SUBMISSION/ 被 .gitignore:74 忽略，非证据）
```