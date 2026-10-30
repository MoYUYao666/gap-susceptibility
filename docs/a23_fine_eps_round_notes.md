# A23 fine-epsilon 证书入稿记录（2026-10-24）

**本轮范围**：只改 `paper_a2/` 与本文档。`HANDOFF.md`、`文件地图.md`、`docs/provenance_manifest.json`、
`SUBMISSION/**`、`docs/a23_fine_eps_text.md` 及其他论文**未动**。
**依据**：`docs/a23_fine_eps_text.md` §3.1（主替换文本）/ §4（归档卫生附录）；归档
`outputs/analysis/a23_fine_eps_certificate.json`；脚本 `tools/_p1472_a23_fine_eps.py`。

---

## 1. 改了什么（文件 / 行号）

| 文件 | 行号（改后） | 改动 |
|---|---|---|
| `paper_a2/ext_partII_domains.tex` | **105–120** | 删掉结尾已为假的负面对照句（原 105–107："We therefore report the certificate as a negative control … which we have not performed"），换成 §3.1 的正面表述 |
| 同上 | **121–123** | 新增 Source 行：`tools/_p1472_a23_fine_eps.py`；`outputs/analysis/a23_fine_eps_certificate.json` |
| 同上 | 123–126 | 其后的 "Both controls are archived …" 句、ImageNet-5k 句、adapted-encoder 句**原样保留**（§3.1 §3.4 要求） |
| `paper_a2/main_ieee.tex` | **866–868** | `app:probes` 引言 "Two probes …" → "The probes below …"，并声明第 (iv) 项是归档审计（原文写 "Two probes" 但已有 (i)–(iii) 三项，属既存不一致） |
| `paper_a2/main_ieee.tex` | **945–963** | 新增 `(iv) Archive hygiene of the margin-mass control`：三条披露（a）语料 7 类不是 8 类、chance 14.29%；（b）NKSID 第 8 类 `tire` 的 834 张在语料根目录、loader 静默丢弃、控制只用 1,783/2,617；（c）`correlation["M(0.01)"]` 实为 `mass_0.05` 的重复、M(0.01) 从未测过，真值取 `-0.488`/`-0.512` |
| `paper_a2/verify_a23_fix.py` | 6–7、29、92、127、142–143 | 页数常量 `PAGES = 72`（原硬编码 70，散在 3 处）；不改则 a23_joe profile 的 gate 必红（见 §4.3） |

改后正文（PDF 第 37–38 页）与附录（第 66–67 页）均已复核；`"which we have not performed"`、
`"negative control at this operating point"` **已从 PDF 文本层彻底消失**。

### 1.1 正文新段用到的数字与字段（逐条已核）

| 数字 | 字段 |
|---|---|
| 32 行在 ε=0.001 去饱和（M<1） | `arms.control.verdict.n_rows_where_fine_grid_separates`=14、`arms.adapted…`=18；`coarsest_required_eps`=0.001 |
| r=−0.98 / −0.90（ε=0.001） | `arms.control.pooled.with_top1.mass_0p001.r`=−0.98075、`arms.adapted…`=−0.89980 |
| r=−0.49 / −0.51（ε=0.01） | `…mass_0p01.r`=−0.48757 / −0.51217 |
| r=−0.39 ↔ +0.82（marine，0.001/0.005） | `arms.control.correlations.marine_optical.with_top1.{mass_0p001,mass_0p005}.r` |
| 四个域 margin 中位数为负 | `arms.<arm>.domains.<domain>.rows[λ=0].margin_median` = −0.0161/−0.0125/−0.0412/−0.0189 |
| 域相对 r∈[−1.00,−0.87]（c=0.01–0.02） | `arms.<arm>.domain_relative_variants.<domain>.median_margin_relative.rows[].r_with_top1` |
| 绝对网格跨域 BA 不超过 0.50 | `arms.<arm>.threshold_transfer_cross_domain.by_statistic.<key>.*.test_BA`（控制臂最大 0.5；adapted 最大 0.5） |
| 最佳域相对校准 0.875 单向、反向为 chance | `…threshold_transfer_cross_domain_domain_relative.by_calibration.q10`（a→b 0.875 / b→a 0.500） |

---

## 2. 编译与日志健康

命令（在 `paper_a2/`）：`pdflatex -interaction=nonstopmode main_ieee.tex` **×2**；**无需 bibtex**
（参考文献是内联 `thebibliography`）。

- **页数 72**（改前 70）
- LaTeX 错误 **0**；undefined reference **0**；undefined citation **0**；`Rerun to get` **0**
- Overfull hbox **0**、Overfull vbox **0**；Underfull hbox 30（`\sloppy` 下的既存现象，改前同量级）
- LaTeX Warning **0**、Font Warning **0**、Missing character **0**
- PDF 文本层抽检：新段 37–38 页；Source 行 38 页；附录 (iv) 66–67 页；chance `14.29%` 66 页
- `python paper_a2/verify_a23_fix.py` → **ALL CHECKS PASSED**（含"冻结归档 37 个 SHA-256 全未变"）

---

## 3. 审计结论

`python -m tools.paper_audit audit --profile a23_joe --fail-on NONE`

```
A23 - IEEE JOE (IEEEtran)  BLOCKED  grade D  pass=56 fail=1 warn=1 manual=9 skip=19 error=0
  BLOCKER A-01  P1  uncommitted changes under paper_a2
```

报告落在 `%TEMP%\a23_audit_20261024d\AUD-a23_joe-20261024T084812Z.{json,md}`——**故意没写进 `docs/audits/`**，
以免越出本轮写范围；lead 可原样重跑落到默认位置。

**非 PASS 项（全部）**：

1. **A-01（P1 FAIL）**「Git working tree is clean」——预期内：`M paper_a2/ext_partII_domains.tex`、
   `M paper_a2/main_ieee.tex`、`M paper_a2/verify_a23_fix.py` 未提交，lead 提交即消。
2. **J-01（P1 WARN）**「claim-ledger evidence older than the manuscript sources」——**与内容无关**：
   `outputs/analysis/claim_ledger{,_a1,_paperA}.json` 16:39:48 生成，早于本轮 16:42+ 的稿件改动；
   改完稿后重跑 `python tools\_claim_ledger.py --apply` 即消。
3. **9 条 MANUAL**（审计工具不自动判，需人工）：A-07、D-10、E-04、E-06、E-09、E-10、G-07、G-08、J-03。
4. **19 条 SKIP**：本 profile 未配置（投稿包 / 盲审 / highlights / claim-ledger 门禁），或 `--staged`
   未请求（B-10 clean-room 重建未跑）。

**其余 56 条全 PASS**，含 LaTeX 告警、字体替换、页数一致性、题名 / 摘要 / 关键词一致性等。

---

## 4. 偏离 §3.1 的地方 + 发现的缺陷（需要 lead 决策）

### 4.1 ⚠️ `reproduction` 检查是空转，§3.1 的"精确复现"句不能写进稿

- `arms.<arm>.domains.<domain>.reproduction.pairs_checked` **四个域块全部为 0**，即
  `max_abs_diff = 0.0` / `reproduced = true` 是**一对都没比**得到的空结论。
- 根因：`tools/_p1472_a23_fine_eps.py:65-66` 的 `eps_key()` 产出 `mass_0p02`，而两个既有归档
  （`a23_certificate_control.json`、`a23_certificate_adapted.json`）用的键是 `mass_0.02`/`mass_0.05`/`mass_0.1`
  ⇒ `reproduction_check()` 里 `if k in ref` 永不成立（脚本 425–431 行）。
- **按归档键名独立逐对比对**（96 对）：**control 42 对全 0.0（精确复现）**；
  **adapted 54 对中 29 对不一致，max |diff| = 0.00995（= 16/1608）**。
- 结论：§3.1 的括注"the recomputation reproduces every archived value at ε∈{0.02,0.05,0.10} **exactly**"
  **对 adapted 臂不成立**，故本轮**删去该括注**，只保留"same corpora and the same frozen weights"这一可核事实
  （`n_images`/`n_classes` 与归档一致）。
- **建议修复**（在 `tools/` 与 `outputs/`，超出本轮写范围）：`reproduction_check()` 改用归档键名匹配；
  重跑 `python tools\_p1472_a23_fine_eps.py --arm analyze`；随后可恢复定量表述
  "control 精确复现 / adapted ≤0.01"。
- **连带**：`docs/a23_fine_eps_text.md` §2 与 §3.1 的"max |diff| = 0.0 over all 24 rows × 3 eps"同样需订正
  （该文档不在本轮写范围）。

### 4.2 §3.1 的"任何校准都不能迁移"属过度概括 → 稿中已限定

`threshold_transfer_cross_domain_domain_relative.by_calibration.q10` 在控制臂 a→b 上
`test_BA = 0.875`（反向 0.500）。§3.1 原句"no ε and no calibration we tested transfers …（best 0.50–0.55）"
与之矛盾。稿中改为：**绝对网格**不超过 chance（两侧最大 0.50），**最佳域相对校准** 0.875 单向、
反向为 chance，因此仍不构成可迁移阈值。

### 4.3 `verify_a23_fix.py` 的页数硬编码 70 → 72

该脚本是 a23_joe profile 的 gate（profile 里 `expect: ALL CHECKS PASSED`）。加两处内容后页数 70 → 72，
三处硬编码（第 86、121、136 行）必红，故改为常量 `PAGES = 72` 并在注释里记录 64→70→72 的沿革。
**这是门槛值而非质量标准**；若 lead 不同意，回退一行即可（但 gate 会红）。

---

## 5. 建议的 `docs/provenance_manifest.json` 条目（**未修改 manifest 本体**）

`manuscripts.A23.floats` 追加一项（键名与既有条目一致；`_p1428_provenance_gate.py` 只扫描浮动体，
正文段落不加也不会让 gate 变红，但按 2026-10-20 规则应登记）：

```json
{
  "label": "text:fine-eps-certificate",
  "kind": "text",
  "script": "tools/_p1472_a23_fine_eps.py",
  "archive": "outputs/analysis/a23_fine_eps_certificate.json",
  "archives": ["outputs/analysis/a23_fine_eps_certificate.json"],
  "status": "verified",
  "note": "Body paragraph in ext_partII_domains.tex (margin-mass certificate), plus appendix item (iv). Fields: arms.<arm>.pooled.with_top1.mass_0p001.r / mass_0p01.r; arms.<arm>.verdict.n_rows_where_fine_grid_separates; arms.<arm>.domain_relative_variants.<domain>.median_margin_relative; arms.<arm>.threshold_transfer_cross_domain*.by_*.test_BA; archive_only_derivations.{class_count_note,archived_correlation_block}. Control arm reproduces the archived coarse-grid values exactly (42/42 pairs, max |diff| = 0.0, re-checked independently); adapted arm agrees to max |diff| = 0.00995. The archive's own reproduction block is vacuous (pairs_checked = 0) - see docs/a23_fine_eps_round_notes.md."
}
```

若 lead 选择先修 4.1 再登记，则把 `status` 先记 `pending`，修完改 `verified` 并补上 adapted 臂的真实界。

---

## 6. 未做 / 可选后续

- 未跑 `--staged` clean-room 重建（B-10 因此 SKIP）；需要更强证据时补
  `python -m tools.paper_audit audit --profile a23_joe --staged`。
- 未改 `main.tex`（elsarticle 旧变体，2026-09-22）与 `main_zh.tex`（中文镜像，2026-09-18）：
  两者都**不含**被删的假句（已 grep 确认），且 a23_joe profile 只编译 `main_ieee.tex`。
- 未改 `docs/a23_fine_eps_text.md`（§4.1 的订正留待 lead）。