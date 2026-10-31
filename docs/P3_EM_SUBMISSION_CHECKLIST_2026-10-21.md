# P3 PRL 新投稿：EM 提交清单（2026-10-21）

> 用途：PRL Editorial Manager 新投稿（new submission）逐步填写清单。
> **固定流程见 `docs/EM_SUBMISSION_SOP_2026-10-21.md`；可粘贴字段见 `SUBMISSION/P3_PRL_resubmission/EM_FIELDS.md`。**文件均在
> `SUBMISSION/_venue_builds/P3_PRL_next/`；投稿动作由操作者在 EM 完成。

## 0. 前置

- [ ] 登录 Editorial Manager（PRL）。
- [ ] 选择 **Submit New Manuscript**（不是 "Revise Submission"）。
- [ ] 在 cover letter 中保留前稿号披露：`PRLETTERS-D-26-02378R1`（已被拒，2026-10-21）。

## 1. Article type

- 选 **Research paper / Full-length article**（按 PRL EM 下拉项；若只有 "Research Paper" 选它）。

## 2. Title

```
Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry: Identifiability, Negative Results, and Protocol Dependence
```

## 3. Authors / affiliations

- Hongrui Wan（University of Southampton, Southampton, SO17 1BJ, UK; hw4c24@soton.ac.uk; ORCID 0009-0003-8649-7504）。
- 通讯作者：本人。

## 4. Abstract

从 `paper3/paper_ieee/main.pdf` 第 1 页复制（**246 词，≤250**）；不要用旧版摘要。
关键词：`PEFT Allocation; Representation Theorem; Phase Transition; Cross-Architecture Transfer; Multimodal Fine-tuning`。


## 4b. Contributor roles（CRediT，单作者勾 11 项）

```
Conceptualization; Data curation; Formal analysis; Investigation; Methodology; Project administration;
Software; Validation; Visualization; Writing – original draft; Writing – review & editing
```

不勾 Funding acquisition / Supervision / Resources（单作者）。

## 5. 文件上传（按顺序；**文件名无下划线**）

| 文件 | 路径 | 备注 |
|---|---|---|
| Manuscript | `P3_PRL_next/Manuscript.pdf` | 10 页 |
| Supplementary | `P3_PRL_next/Supplementary.pdf` | 8 页（S1–S17）|
| Cover letter | `P3_PRL_next/CoverLetter.pdf` | 2 页，含前稿披露与 5 项改动 |
| Title page | `P3_PRL_next/TitlePage.pdf` | 1 页，含新副标题 |
| Highlights | `P3_PRL_next/highlights.pdf` | 5 条，各 ≤85 字符 |
| LaTeX source | `P3_PRL_next/LaTeXSource.zip` | 独立编译通过 |

## 6. 声明

- Competing interests: none.
- Funding: none.
- Data availability: public repository + version DOI `10.5281/zenodo.23341223`（正文已写）。
- Generative-AI declaration: 按 PRL 要求勾选/填写（正文已含声明段）。

## 7. 需要在 cover letter 之外口头说明的（EM 备注栏，可选）

"New submission replacing rejected manuscript PRLETTERS-D-26-02378R1 (21 Oct 2026). The revision is substantive:
claim-status table (S17), five-seed statistics (p=0.008), protocol-window measurements (S16), real-image control numbers,
and a corrected data/code availability statement. We request consideration as a new submission."

## 8. 提交后

- [ ] 记录新稿号；更新 `HANDOFF.md` / `文件地图.md`（投递类事实第一时间落账）。
- [ ] 若 EM 要求推荐审稿人：避开近期合作者；可填 2–3 位跨模态 PEFT/评测方向的独立研究者。
