# Decoder 阶梯轮记录（2026-10-24b）：Paper A Section H 改写

本轮把云端跑完的**匹配阶梯**（objective control ladder）写进 Paper A 附录 Section H，并更正本地控制的图像
token 上限描述。所有数字均逐一核对过 `outputs/analysis/decoder_attribution_*.json` 与
`outputs/analysis/qwen_objective_control_*.json`，未使用任何未归档数字。

## 1. 改了什么（文件 + 行号）

| 文件 | 位置 | 改动 |
|---|---|---|
| `paper合/sections/supplement.tex` | L429–440 | Section H 引言：把"五因素同时不同 ⇒ 无法归因"限定为"仅凭这两个实验无法归因"，并新增指向 H.2 的句子（同一 LLaVA 权重在对比损失下收窄） |
| 同上 | L445–477 | H.1（本地控制）：**保留**归档数字（1.0703 → 0.2832 = −73.5%；1.0703 → 0.9180 = −14.2%），新增更正段 L461–477，说明该控制从未真正生效其宣称的图像 token 上限，并改引两个**公开**脚本路径（见 §6 第 0 条） |
| 同上 | L478–564 | **新增 H.2**「A matched ladder over family and scale」+ 表 `tab:decoderladder`（L498–522，`\label` 在 L509）+ `Source:` 行（L524–533）+ 三条判读（L535–546）+ 四条限制（L548–564） |
| `docs/provenance_manifest.json` | L1403–1421 | 新增浮标条目 `tab:decoderladder`：script = `tools/_p1612_objective_control_multimodel.py`，archive = 五份 `outputs/analysis/decoder_attribution_*.json`，status = `verified`（仅因路径存在且数字取自其中） |
| `tools/_p1454_final_verify.py` | L28 | `PAGES`：`paper合/main_nc.pdf` 77 → **79**，`paper合/main_springer.pdf` 54 → **56** |
| 同上 | L32–39 | 新增 `LADDER_RUNGS`（五级，按表序）与 `LADDER_3B` 路径常量 |
| 同上 | L125–135 | 写范围守卫**反转**：上一轮（bootstrap，2026-10-24a）要求"Section H 不得改动"，本轮要求"改动必须落在 Section H 之内"（每一处 hunk 的 `+起始行 ≥ Section H 标题行`） |
| 同上 | L140–231 | 新增 `check_decoder_ladder_integration()`：**35 项断言**（表内容逐行回算归档、四条 caveat 的措辞、3B 未跑与归档缺失一致、本地控制归档未被改动、稿件不得引用公开镜像里不存在的 `docs/` 路径等） |
| 同上 | L295–298、L308 | main 接线，并计入 `all_pass` |
| `tools/_p1181_verify_paperA_consistency.py` | L53–58 | 新增 4 条：「H.2 存在」「`sec:decoderladder` 标签存在」「真实分辨率语句在」「旧措辞 `at a reduced image resolution` 不在」 |
| `paper合/cover_letter_nc.tex`、`paper合/cover_letter.tex` | L26 | 页数 77 → 79（构建脚本自动写入），两份 PDF 已重建 |
| `docs/decoder_ladder_round_notes.md` | 本文 | 本轮记录 |

**未改**：Section A–G（写范围守卫反转后仍逐 hunk 约束）、`main_nc.tex` / `main_springer.tex` 正文（Data
availability 行未动，见 §6）、`SUBMISSION/**` 源文件（仅按指定脚本刷新了包副本）、`HANDOFF.md`、`文件地图.md`。

## 2. 页数与构建

| 文件 | 改前 | 改后 | errors | undef refs/cites | overfull | float too large |
|---|---|---|---|---|---|---|
| `paper合/main_nc.pdf` | 77 | **79** | 0 | 0 | 0 | 0 |
| `paper合/main_springer.pdf` | 54 | **56** | 0 | 0 | 0 | 0 |
| `paper合/cover_letter_nc.pdf` | 3 | 3 | 0 | 0 | 0 | 0 |
| `paper合/cover_letter.pdf` | 3 | 3 | 0 | 0 | 0 | 0 |
| `paper合/highlights_nc.pdf` | 1 | 1 | 0 | 0 | 0 | 0 |

- 构建方式：`python tools/_p1174_build_paperA_editorial.py --apply`（三遍 pdflatex + bibtex + 收敛遍，含逐文档审计）。
  第一次构建时 Springer 出现 2 处 `Overfull \hbox`（`Source:` 行的长文件名），在文件名各段之间插入
  `\allowbreak` 后归零。
- 共构建 3 轮：第 1 轮（修正 overfull 前）NC 79 / Springer 56 且 Springer 有 2 处 overfull；第 2 轮 overfull 归零；
  第 3 轮（把 `docs/` 内部路径改引公开脚本后）页数不变，仍 **NC 79 / Springer 56**，errors 0 / undef 0 / overfull 0 /
  float 0 / rerun False。
- 表落位：`tab:decoderladder` 在 NC 第 70 页（H.2 标题在第 69 页，`Source:` 行与表同页），Springer 第 49 页。
- 包刷新：`python tools/_p1576_refresh_a1_papera_packages.py --apply`（页数变化后跑了一次，第 3 轮构建后又跑一次）
  → `SUBMISSION/PaperA_Neurocomputing` 的 Manuscript/Cover Letter/Highlights 与 live 文件 **sha256 逐一相同**
  （79/3/1 页），`latex_source.zip` 重建（45 项，内含最终版 `sections/supplement.tex`），README 实测事实更新为
  **79 页 / 242 词**。

## 3. 五级数字（表 ↔ 归档字段，逐条核对）

表内 `DG^*` 保留 4 位小数、变化保留 1 位（单种子 + 4bit，1 位是诚实分辨率；原始值见下）。

| backbone | objective | 归档文件（`outputs/analysis/`） | `frozen_dg_star` | `dg_star[-1]` | `delta_DG_percent` |
|---|---|---|---|---|---|
| Qwen2-VL-2B | contrastive | `decoder_attribution_qwen2vl-2b_contrastive_seed42.json` | 0.64453125 | 0.072265625 | −88.7878787878788 |
| Qwen2-VL-2B | generative | `decoder_attribution_qwen2vl-2b_generative_seed42.json` | 0.64453125 | 0.62109375 | −3.6363636363636362 |
| LLaVA-1.5-7B | contrastive | `decoder_attribution_llava15-7b_contrastive_seed42.json` | 0.48193359375 | 0.1683349609375 | −65.0709219858156 |
| LLaVA-1.5-7B | generative | `decoder_attribution_llava15-7b_generative_seed42.json` | 0.455810546875 | 0.529296875 | +16.12212104981253 |
| Qwen2.5-VL-7B | generative | `decoder_attribution_qwen25vl-7b_generative_seed42.json` | 1.078125 | 0.70703125 | −34.42028985507246 |

五份记录共同字段：`meta.mode = "apply"`、`meta.protocol = "match"`、`meta.seed = 42`、`meta.arm = "both"`、
`meta.num_samples = 320`、`meta.epochs = 3`、`meta.lr = 1e-4`（LLaVA contrastive 除外，见 caveat ii）、
`meta.precision = "4-bit nf4"`、`meta.lora = {r:8, alpha:16, dropout:0.05}`、
`meta.dataset = "data/marine_captions"`、`meta.image_token_budget_applied_via = "size.longest_edge"`、
`meta.image_tokens_realised = 164`（Qwen，上限 196）/ `1152`（LLaVA，即 576×batch 2）。

## 4. 四条 caveat 的稿件原文

稿件里是 (i)–(iv) 四句，原文如下（英文为稿件实际措辞）：

1. 单种子 / 4bit 不可复现：
   > "(i) Each rung is a single seed, and in four-bit precision the trained value is not bit-reproducible
   > --- repeated identical-seed runs moved $DG^*$ by about $1\%$ of the frozen value at the smoke scale,
   > through quantisation and CUDA nondeterminism --- so the ladder is read as a direction and not as an
   > effect size, and no spread across seeds is claimed."

2. LLaVA 学习率 / 冻结基线不一致 / 过零：
   > "(ii) The LLaVA contrastive rung was run at $5\times10^{-5}$ rather than the ladder's $10^{-4}$: a first
   > attempt at $10^{-4}$ diverged to non-finite losses in its third epoch and produced no record, an outcome
   > the producing script guards against by skipping non-finite steps and refusing to report a history that
   > is not finite. The re-made run records its rate in \texttt{meta.lr} ($5\times10^{-5}$ against $10^{-4}$
   > in the other four rungs). The LLaVA A/B pair therefore differs in learning rate, and its two frozen
   > baselines differ as well, by $5.7\%$ ($0.4819$ against $0.4558$); \texttt{meta.ab\_check.verdict} in the
   > contrastive record reads \texttt{MISMATCH} and the record is kept rather than discarded. The LLaVA
   > generation trajectory also crosses zero between its first and second epochs --- $-14.2\%$, then $+6.7\%$,
   > then $+16.1\%$ against its own frozen baseline, from \texttt{dg\_star} --- so the sign of that rung is a
   > property of where training stops as much as of the loss."

3. 本地控制的 token 上限从未生效（H.1 正文另有一整段）：
   > "(iii) The local control of Section~\ref{sec:objectivecontrol} never enforced the image-token budget it
   > advertised and is therefore not a rung of this ladder, and its magnitudes are not comparable with these."
   >
   > H.1 更正段（关键句）："The attribute the script set in order to apply the cap is discarded by the
   > installed \texttt{transformers} release (5.16.1), so the runs proceeded at the image processor's default
   > resolution, at roughly $1200$--$2500$ image tokens per image."（同段还点出协议块自相矛盾：
   > `meta.max_image_tokens` = 12 而 `meta.reduced_budget_note` 写 "64 image tokens/image"）

4. 3B 未跑：
   > "(iv) The $3$B rung of the Qwen2.5-VL family was not run, because its weights did not fit the data disk
   > available on the instance, so the Qwen scale comparison rests on $2$B and $7$B rather than on three points."

另有三条**判读**（H.2 L535–546）：匹配协议下 objective 不决定符号（对比损失在两个 backbone 上都收窄：2B
−88.8%、LLaVA-7B −65.1%）；生成损失在 Qwen2-VL-2B（−3.6%）与 Qwen2.5-VL-7B（−34.4%）收窄、在 LLaVA-1.5-7B
（+16.1%）放宽，因此放宽跟随的是**backbone family**（LLaVA-1.5 的冻结 CLIP-L/14-336 + 576-token splice）而非
生成损失本身；原"五因素同时不同因此无法归因"被**收窄而非推翻**——objective 已分离且不是放宽的原因，仍混淆的
是 family、scale 与数据规模（含固定 576-token splice 造成的图像 token 预算差异）。

## 5. 门禁结果（全部实测，命令照抄）

| 门禁 | 结果 |
|---|---|
| `python tools/_p1181_verify_paperA_consistency.py` | **0 failure(s)** |
| `python tools/_p1428_provenance_gate.py` | **PASS**：paperA floats 31 → 32，missing 0 / pending 0 / broken_paths 0 |
| `python -m tools.paper_audit audit --profile paperA_nc --fail-on NONE` | **READY grade A**，pass=67 fail=0 warn=0 manual=9 skip=10 error=0 |
| `python -m tools.paper_audit audit --profile paperA_springer --fail-on NONE` | **READY grade A**，pass=56 fail=0 warn=0 manual=9 skip=21 error=0 |
| `python tools/_p1454_final_verify.py --apply` | 见 §5.1 |
| 新增断言自检 | `check_decoder_ladder_integration()` **35/35** 通过；表行解析做过反向对照（把 0.6211 改成 0.6212、改 LLaVA 行单元格 ⇒ 断言即失败） |

### 5.1 `_p1454_final_verify.py --apply` 逐项（最终版文本，实测）

```
  frozen: True 12 files, bad=0
  provenance gate: True
  A1 ledger: 216 pass / 0 fail / 216 total
  audit a1_paa: READY fail=0 warn=0 ok=True
  audit paperA_nc: READY fail=0 warn=0 ok=True
  audit paperA_springer: READY fail=0 warn=0 ok=True
  audit p3_prl: READY fail=0 warn=0 ok=True
  audit a23_joe: READY fail=0 warn=0 ok=True
  audit prl_commentary: READY fail=0 warn=0 ok=True
  p3_audit_check: True        p3_audit_pdf: True
  A23 verify: True            Commentary final check: True
  staged packages: True []
  pages: {'paper_a1/main.pdf': 64, 'paper合/main_nc.pdf': 79, 'paper合/main_springer.pdf': 56,
          'paper3/paper_ieee/main.pdf': 10, 'paper_a2/main_ieee.pdf': 72, 'paper_review_prl/main_prl.pdf': 7} pass: True
  bootstrap integration: True failed: []
  decoder ladder integration: True failed: []
  git clean: False
  ALL: PASS
```

退出码 0，报告落在 `outputs/analysis/final_verification.json`（`all_pass: true`，
`decoder_ladder_integration.checks` 共 **35** 项、失败 0 项）。**`git clean: False` 属预期**：本轮 6 个受跟踪文件的
改动、本文档与 `docs/audits/*`（跑门禁的副产物）尚未提交（任务说明由 lead 提交后该项才转绿）。

## 6. 未核实 / 待 lead 决定

0. **（已在轮内修掉，但值得记账）稿件一度引用了公开镜像里不存在的路径。** 我最初把更正段的出处写成
   `docs/DECODER_CONTROL_CAP_CORRECTION_2026-10-24.md`，随后核实 `publish_clean/.gitignore` L57 整目录忽略 `docs/`：
   该文件在根仓库受跟踪、在公开镜像里**不可达**（`git -C publish_clean ls-files` 无此文件，
   `git -C publish_clean check-ignore -v` 命中 `.gitignore:57:docs/`）。已改为引用两个公开脚本
   （`tools/_p1595_qwen_objective_control.py`、`tools/_p1612_objective_control_multimodel.py`，二者在 publish_clean
   均受跟踪），并在 `_p1454` 新增 `cap_correction_cites_public_paths` 断言（稿件任何位置不得出现 `docs/` 路径）。
   同类风险请 lead 留意：**稿件里引用的每个路径都应能在公开镜像取到**；`outputs/analysis/*.json` 与 `tools/*.py`
   本轮抽查均在 publish_clean 受跟踪。

1. **LLaVA 首次 1e-4 的云端 run log 未取回本地**（`outputs/_logs/`、`cloud_next/` 下都没有本轮阶梯日志）。
   稿件因此**没有**引用"run log"，只依赖两处本地可核对证据：JSON 的 `meta.lr`（5e-05 vs 1e-04）与产出脚本
   自身的守卫注释/逻辑（`tools/_p1612_objective_control_multimodel.py` L835–842 跳过非有限步、L866–867
   "every epoch measured non-finite; nothing to report"、L956–957 非有限历史拒绝写出、L836–837 注释
   "the first attempt at this arm went NaN in epoch 3 and lost the run"）。若要把"run log 记录"写进稿件，需先取回日志。
2. **`paper合/sections/provenance_appendix.tex` 未加 `tab:decoderladder` 一行**（该文件不在本轮写范围）。
   附录表自称"列出每个报告自有结果的图表"，现在缺这一行 → 建议 lead 授权后补一行：
   `tab:decoderladder & tools/_p1612_objective_control_multimodel.py & decoder_attribution_*.json & verified`。
   `docs/provenance_manifest.json` 已登记（门禁不查附录表）。
3. **Data availability / cover letter 的枚举仍是 "Appendix Sections E and G"**（`main_nc.tex` L87、
   `main_springer.tex` L87、两份 cover letter）。本轮五份阶梯记录已随 `publish_clean` 提交（HEAD `1215fa0`），
   但稿件引用的 DOI 快照是 v2.3（`10.5281/zenodo.23609295`），而 `publish_clean` README 已指向 v2.4
   （`10.5281/zenodo.23614290`）。是否把 Section H 纳入 Data availability 枚举、以及用哪个版本 DOI，属于
   DOI/tag 冻结纪律下的对外可见决定 → **留给 lead/操作者**，本轮未动这两个文件。
4. **`docs/provenance_manifest.json` 中 `tab:vlm` / `tab:llava` 的映射是本轮之前就存在的问题**：
   `outputs/analysis/paperA_decoder_confound.json` 的 `provenance_findings.mapping_is_correct = false`
   （真实产出脚本应是 `tools/_p1150_qwen_clean_sweep.py` / `tools/_p1145_clean_gap_measure.py`），且
   `tab:llava` 在 manifest（`canonical_caption_metric.json`）与附录（`llava_instruction_dynamics.json`）里
   归档不一致。本轮只新增条目、未改这两条（不在"本轮文本触及"的范围内）。
5. **`paper合/sections/empirical.tex` L15 的 "decoder-model controls (Appendix Sections E and G) use batch size 2"**
   字面上仍成立（明确限定 E、G），但阶梯里 Qwen 是 batch 4、LLaVA 是 batch 2；如需在正文补一句，注意
   `_p1181` 正在断言该整句，两者要一起改。

## 7. 构建/门禁输出

见 §2（构建）与 §5（门禁）；`_p1454_final_verify.py --apply` 的结果落在
`outputs/analysis/final_verification.json`，其中 `decoder_ladder_integration.checks` 为本轮新增的 **35** 项断言。