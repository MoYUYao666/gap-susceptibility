# P1 — Round-2 review of submission artefacts against the manuscript

**Manuscript**: P1, *Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models* (sole author Hongrui Wan), Pattern Recognition **PR-D-26-10149**, under review since 2026-08-23.
**Review type**: read-only consistency review of the submission artefacts against the manuscript (and against the archived experimental records where an artefact quotes a number). The only file written is this report.

## 0. What was reviewed, and the exact revision this report describes

| Artefact | Size (B) | Last write | SHA-256 (16) |
|---|---|---|---|
| `paper/main_nn.pdf` (manuscript, 41 pp.) | 2 703 220 | 2026-09-20 13:50:36 | `3BA4BD77FAB9D48B` |
| `paper/highlights.tex` | 579 | 2026-09-20 12:46:30 | `DE9A18C2682AB2F6` |
| `paper/highlights.pdf` | 24 867 | 2026-09-20 12:46:35 | `8110FD984A11E4EC` |
| `paper/cover_letter_revision.tex` | 6 418 | 2026-09-20 13:49:13 | `A7205D8BA3EBC111` |
| `paper/cover_letter.tex` | 2 271 | 2026-08-14 11:10:40 | `85326D3DF5FF54F2` |
| `paper/cover_letter_zeroshot_correction.tex` | 3 641 | 2026-08-14 11:47:58 | `6EC855DC96290379` |
| `paper/cover_letter.pdf` | 95 287 | 2026-08-05 21:24:02 | `1DE335AE6527AD0C` |
| `paper/abstract.pdf` | 46 306 | 2026-07-04 14:30:49 | `3D9EC7929F530763` |
| `paper/title_page.tex` / `declaration.tex` | 672 / 376 | 2026-08-14 11:09–11:10 | `76BF95481869D664` / `C80CBBB86296901D` |
| `paper/title_page.docx` / `declaration.docx` / `declaration.pdf` / `competing_interests.docx` / `declarationStatement.docx` | — | 2026-08-05 / 07-17 / 07-04 / 07-17 / 07-24 | — |

⚠️ **The tree was being modified by another agent while this review ran.** Between my first listing and my last check, `paper/sections/*.tex` were rewritten at **13:49:13**, `tools/_p1_patch_c.py` ran at 13:49:09, and `main_nn.pdf` was rebuilt twice (13:40:12 → 13:49:21 → 13:50:36). Findings below are stated against the revision in the table above; where a defect existed in the 13:40 build but was fixed by the patch-C rebuild I say so explicitly in §8. Anything that needs to ship must be re-verified against the **final** build.

**Counts**: **6 must-fix · 6 should-fix · 9 note** (21 findings). Nothing was found fabricated; the defects are reporting/consistency defects in the artefact set.

---

## 1. Do the highlights agree with the manuscript? (brief item 1)

Source: `paper/highlights.tex:8–12`.

| # | Highlight (verbatim) | Manuscript evidence | Verdict |
|---|---|---|---|
| 1 | `117 PEFT experiments trace modality-gap evolution across three model families` | `main_nn.tex:39–40` "Through **117 experiments** spanning two PEFT methods, **three model families**, two retrieval datasets, and three zero-shot benchmarks"; `paper/sections/supplementary.tex` sections I–XIII total 117 | **Supported on the count and the families; the word "PEFT" is not** (see N1) |
| 2 | `Text-only adaptation preserves cross-modal alignment better than joint adaptation` | `main_nn.tex:42–45` "text-only fine-tuning preserves cross-modal alignment better than joint modality fine-tuning … **with a few exceptions (e.g., COCO both-position, SigLIP both-position, Adapter vision-only and ViT-B all-layer text-only)**"; `introduction.tex:15` "On COCO, both-position achieves a marginally better CG$\Delta$ ($-0.052$ vs.\ $-0.041$)"; Table 2 (`experiments.tex:77–78`) COCO column: text-only **−0.041**, both **−0.052** | **Supported as the paper's headline; the bullet drops the manuscript's own four named exceptions** (N2) |
| 3 | `Full fine-tuning raises the gap by 23.3% over five seeds and collapses zero-shot` | `main_nn.tex:45–47` "Full fine-tuning increases the Centroid Gap by **23.3% ± 1.0% over five seeds** and collapses zero-shot accuracy to near-chance levels (mean 2.6% over 3 retrained seeds, vs. 59.3% frozen)"; `experiments.tex:86` "+0.191 ± 0.008 … five seeds" | **Supported** |
| 4 | `Gap magnitude predicts retrieval; Centroid and Distribution Gap are interchangeable` | `experiments.tex:158` "the two statistics are **close to** interchangeable here"; `experiments.tex:244` "we therefore treat them as interchangeable"; `main_nn.tex:56–58` "r = −0.71 (partial r = −0.58 …, the two measures being strongly collinear at r = +0.95)" | **Supported, with the manuscript's "close to" elided** (N3) |
| 5 | `A strict control shows text-only adapters leave the visual encoder untouched` | `strict_control.tex:29–33` "the vision encoder of the text-only configuration receives *no* updates: **0 of 199** vision-side backbone tensors change"; `strict_control.tex:24` Table 8 "196,608 … −0.047 ± 0.003 … 0/199" | **Supported** |

**No bullet contradicts the manuscript on a number.** The three qualifications above are about wording strength, not value disagreement. Stated in full:

- **N1 · note — "117 PEFT experiments" is not what the catalogue holds.** The 117 rows of `supplementary.tex` sections I–XIII include **six frozen baselines that are not fine-tuning runs at all** — `baseline_frozen` (`:36`), `coco_frozen` (`:71`), `blip_frozen` (`:82`), `vitl_frozen` (`:92`), `imagenet_zs_frozen` (`:127`), `siglip_frozen` (`:162`) — plus **three post-hoc analyses with no training**: Noise sensitivity, GSNR gradient analysis, Effective rank tracking (`:154–156`). The manuscript itself is careful ("117 experiments spanning two PEFT methods…", `main_nn.tex:39`; "117 experimental observations", `visual_fragility.tex`), and Table 1's counts include those same rows. 117 is the paper's own count, so the bullet is not *wrong*, but "117 PEFT experiments" overstates what was run; "117 experiments" would be exact.
- **N2 · note — bullet 2 states the finding without the manuscript's own exception list.** The abstract, Introduction finding 2 and Discussion §7.1 all carry "with a few exceptions (e.g., COCO both-position, SigLIP both-position, Adapter vision-only and ViT-B all-layer text-only)" (`main_nn.tex:44–45`, `introduction.tex:15`, `discussion.tex:6`), and Table 2's COCO column has both-position better than text-only (−0.052 vs −0.041, `experiments.tex:77–78`). The bullet's flat form is standard highlight practice, but it is the strongest unqualified form of a claim the body qualifies four times.
- **N3 · note — bullet 4 drops the manuscript's hedge and one half of its finding.** The manuscript says "close to interchangeable" (`experiments.tex:158`, `discussion.tex:36`) and adds a null result the bullet omits: change measures are at best weakly predictive (DG∆ r = +0.134, p = 0.055). "Interchangeable" unqualified is what a reader will remember if the −0.581 partial correlation becomes contentious.
- **N4 · note — highlights PDF furniture.** The compiled `highlights.pdf` carries a footer page number ("1") and the heading "Highlights"; Elsevier's file is normally a plain bullet list. Harmless, occasional copy-desk nit.

---

## 2. The 85-character limit (brief item 2)

`highlights.tex` was compiled in a scratch directory (self-contained; produces a byte-identical `highlights.pdf`: **24 867 B**, matching the on-disk file). `pdftotext` of the compiled PDF:

```
• 117 PEFT experiments trace modality-gap evolution across three model families
• Text-only adaptation preserves cross-modal alignment better than joint adaptation
• Full fine-tuning raises the gap by 23.3% over five seeds and collapses zeroshot
• Gap magnitude predicts retrieval; Centroid and Distribution Gap are interchangeable
• A strict control shows text-only adapters leave the visual encoder untouched
```

| # | Authored text (LaTeX source) | Rendered text (PDF) | Rendered + `"• "` |
|---|---|---|---|
| 1 | 77 | 77 | 79 |
| 2 | 81 | 81 | 83 |
| 3 | **80** | 79 (pdftotext drops the line-break hyphen in "zero-shot") | 82 |
| 4 | **83** | 83 | **85** |
| 5 | 76 | 76 | 78 |

**Result: PASS on every reading.** Elsevier's rule ("3–5 bullet points, maximum 85 characters, including spaces, per bullet point") is met with the largest bullet at 83 characters of text. Bullet 3 line-wraps onto a second line in the PDF because "zero-shot" does not fit; that is a typesetting wrap, not a breach of the 85-character rule. Note only: if one counts the bullet glyph and its following space (the strictest possible reading), bullet 4 lands on **exactly 85** — zero margin. Trimming it slightly would remove any doubt. There are 5 bullets, within the 3–5 requirement.

---

## 3. The revision cover letter's corrections table (brief item 3)

### 3.1 Is the "previously reported" column accurate? — **Yes, for all 7 rows** (verified against the pre-remediation sources, which are recoverable from the patch scripts in `tools/`).

| Row | Letter's "previously reported" | Submitted-version source (recovered) | Verdict |
|---|---|---|---|
| Training convention | "LoRA runs described as 'text-only / both' fine-tuning without stating the parameter budget" | `tools/_p1_patch_a.py:158–160` (the disclosure was inserted into `methodology.tex` by that patch; `docs/P1_ADVERSARIAL_REVIEW.md` [M15]: "PDF 全文 0 处 LayerNorm/embedding/trainable-param 披露") | ✅ |
| Adapter comparison | "mean CGΔ = −0.100 … F = 13.37, p = 5×10⁻⁴" | `_p1_patch_a.py:104,106`: old Table 4 row `Adapter & $-$0.100 & 0.173 & $d$=64, text-only`; old ANOVA text "…$F = 13.37$, $p = 5 \times 10^{-4}$ … mean CGΔ = −0.100 vs. −0.004 for LoRA" | ✅ |
| Gap–retrieval | "DG → R@1 r = −0.827 versus CG r = −0.683, partial −0.807 (n = 81)" | `_p1_patch_a.py:76,108,116–120`: old intro "achieving a Pearson correlation of $r=-0.827$ … (vs. $r=-0.683$ for CG, $n=81$), and maintaining $r=-0.807$ in partial correlation analysis"; old Table 5 cells `−0.827` / `−0.683` / `−0.807` | ✅ |
| Full fine-tuning | "'increases the Centroid Gap by 24%' (single run)" | `_p1_patch_a.py:60`: old abstract "Full fine-tuning increases the Centroid Gap by 24\% and collapses" | ✅ |
| Experiment count | "116 experiments" | `_p1_patch_a.py:55,100,138–144`: 116 → 117 in abstract, intro, Table 1, `supplementary.tex` | ✅ |
| Figures | "Figure 1 mixed COCO curves with a Flickr30k seed band; … Figure 5 labelled a text-only run as 'Both-LoRA'; Figure 7 showed the superseded correlation values" | `docs/P1_ADVERSARIAL_REVIEW.md` [M3], [M6], [M11]; `_p1_patch_a.py:110` shows the submitted DG-vs-CG scatter caption still printing "$r=-0.827$ … $r=-0.683$" | ✅ (but see 3.3 on "Figure 2") |
| Effective rank | `"text-only preserves visual embedding geometry"` | `_p1_patch_b.py:149` (old intro finding 7): "…and effective rank tracking confirms **text-only preserves visual embedding geometry**" — verbatim | ✅ |

### 3.2 Is the "corrected" column what the manuscript now says?

| Row | Verdict |
|---|---|
| Training convention | ✅ "145,170,177" = `methodology.tex:22` and `strict_control.tex:7`; "196,608 … 0.13%" = `strict_control.tex:11–12` and Table 8 (`strict_control.tex:24`); "the visual encoder receives exactly zero updates" = `0/199` (`strict_control.tex:30–31`). |
| Adapter comparison | ⚠️ **Partly.** `experiments.tex:126` and Table 4 (`experiments.tex:138`) do say "no Adapter configuration reduces the gap: the best (d=64) still ends at +0.064" / "mean +0.229". **But Table 1 still prints the retired convention**: `experiments.tex:30` `Adapter & 7 & $-$0.217 & 0.574` under the caption `experiments.tex:17` "CG$\Delta_{\text{best}}$ = best gap change (**relative to frozen baseline for each category**)" — see **M4**. |
| Gap–retrieval | ✅ `experiments.tex:158` and Table 5 (`:168–173`): −0.714 / −0.594 / −0.581 / +0.945. The claim "no longer claims that DG substantially outperforms CG" holds (`:158`, `:244`, `discussion.tex:36`). |
| Full fine-tuning | ✅ `main_nn.tex:45` "23.3% ± 1.0% over five seeds"; `experiments.tex:86` "+0.191 ± 0.008". The letter's "+0.191 ± 0.008 … i.e. 23.3%" is arithmetically the same claim (0.1906/0.8184 = 23.3%). |
| Experiment count | ✅ 117 in `main_nn.tex:39`, `experiments.tex:6,49`, `supplementary.tex:5`, `conclusion.tex`; section XIII now headed "8 experiments" and Table 1's SigLIP row is 6 (see §8), so the rows sum to the printed total of 117. |
| Figures | ⚠️ See 3.3 (**M-numbering fixed at 13:49**, residual wording issue S2). |
| Effective rank | ✅ "9.43 to 6.16–7.02 in three of four" = `supplementary.tex:261` verbatim; "the strict control leaves it unchanged" = `supplementary.tex:261` + `strict_control.tex:32–33`. |

### 3.3 Two rows that mis-described a side (now one fixed, one not)

**M4 · must-fix — Table 1 still reports the retired Adapter convention, contradicting the letter's own row 2 and the manuscript's §4.5/Table 4.**
- Artefact (letter, current): *"Recomputed against the frozen baseline, **no Adapter configuration reduces the gap** (best +0.064, mean +0.229)"* — `cover_letter_revision.tex:86–87`.
- Manuscript: `experiments.tex:30` `Adapter & 7 & $-$0.217 & 0.574` under the caption `experiments.tex:17` *"best gap change (**relative to frozen baseline for each category**)"*; `supplementary.tex:65` `adapter\_d64\_text & $d$=64 & text\_only & $-$0.217 & 0.574`.
- The archive agrees with the letter, not with Table 1: `outputs/analysis/adapter_common_baseline.json` → `adapter_d64_text: delta_old −0.2167, delta_common +0.0636`.
- **Fix**: the Adapter cell must carry the frozen-relative best (`+0.064`, R@1 0.574) or the caption's "relative to frozen baseline for each category" must be qualified for that one row. (The Table 2 caption and the `supplementary.tex:5` note were both given Adapter-convention caveats during this review — see §8 — so Table 1 is now the only place where the old convention survives unreconciled.)

**Fixed during this review:** the letter's row 6 previously read *"**Figure 2** carried an $n=81$ title over a 17–30 point scatter"*, while the manuscript's Figure 2 is the Cross-validation chart (`experiments.tex:92–93`; printed caption "Figure 2: Cross-validation: text-only yields the smallest alignment degradation…") and the $n=81$ scatter was printed as **Figure 4** (`experiments.tex:153–156`; printed caption "Figure 4: Distribution Gap vs. Centroid Gap as retrieval performance predictors over the reproducible archive of n = 204 runs"). "Figure 2" was the **file name** (`figures/fig2.png` maps to printed Figure 4 because the include order is fig1→fig3→fig4→fig2). Patch C rewrote it to *"the figure printed as Figure 4 carried an n=81 title"* (`cover_letter_revision.tex:103`). **Verify the final letter still says this** — an editor will look up whatever number is printed.

---

## 4. The two 2026-08-14 letters the journal already holds (brief item 3, second half)

Both letters are dated **August 14, 2026** (`cover_letter.tex:19`, `cover_letter_zeroshot_correction.tex:19`). The revision letter contains **no reference to either of them** — that is the finding.

**M5 · must-fix — the revision letter silently supersedes numbers the editor has already been told were *corrected*, and never reconciles with the two letters on file.**

1. **Zero-shot values and their protocol.** The letter on file says:
   > `cover_letter_zeroshot_correction.tex:42` — "**frozen 59.37%, text-only LoRA 58.76% (−0.6pp), both-position LoRA 59.67% (+0.3pp), full fine-tuning 0.13% (−59.2pp)**. The measurements use the single-template protocol … on a **14,288-image ImageNet validation subset**, stated in the table footnote."
   
   The manuscript now says (`experiments.tex:227–230`; identical in the PDF):
   > `Frozen … 59.28%` / `Text-only, r=8 … 58.66%` / `Both, r=8 … 59.67%` / `Full fine-tuning … 2.6%`, under `experiments.tex:220` "…on the **full 50,000-image** ImageNet validation set".
   
   Four of the four headline numbers moved (58.76→58.66; 59.37→59.28; 0.13→2.6) and the stated *n* changed by a factor of 3.5. The corrections table has **no row for this**, and `docs/P1_REMEDIATION_LOG.md:54` records that the intended handling was exactly this: "处理方式不是改稿件，而是**在返修信里更正协议描述**". **Fix**: add a row (or a paragraph) stating the two protocols, which is now authoritative, and why the 08-14 figures differ.
2. **The change-score correlations.** `cover_letter.tex:46` told the editor this had been *corrected*: "Table 4: the two change-score correlations (DG Δ → R@1, CG Δ → R@1) **corrected to the recorded values (r = −0.042, p = 0.713; r = +0.012, p = 0.915)**". The manuscript now says (`experiments.tex:158,172–173`): `DG Δ → R@1  +0.134  0.055 (NS)` and `CG Δ → R@1  +0.190  0.007`. Row 3 of the new table covers only the *level* correlations; a reader with the August letter in hand sees a second unexplained revision of the same two cells — with the sign flipped on DGΔ.
3. **Figure 7.** `cover_letter.tex:47` said Fig. 7 had been *regenerated* at the verified values "(r = −0.827 / −0.683 / −0.807)"; the new table's row 6 now calls those readings "**the superseded correlation values**". The retraction is correct, but the reversal needs one explicit sentence referencing the August letter, otherwise the file reads as two contradictory self-corrections.

**Other items in the 08-14 letters that still check out** (so they can be cited as unchanged): SigLIP five R@1 entries 0.479/0.468/0.463/0.455/0.454 = `supplementary.tex:163–167` (siglip_lora_r4/r8/r16, siglip_text_only, siglip_both); layered catalog ViT-B vis-L2 −0.009, vis-L4 −0.002, both +0.209 = `supplementary.tex:136–138` and Adapter text-only −0.045 / both −0.044 = `supplementary.tex:149–150`; BLIP-1 rank-4 R@1 0.175 = `supplementary.tex:84` and `experiments.tex:31`.

**S1 · should-fix — the PDF in the folder is not the letter on file.** `paper/cover_letter.pdf` renders **"August 5, 2026"** and is otherwise word-for-word identical to `cover_letter.tex` (whose date reads "August 14, 2026"). Anyone re-uploading "the cover letter" from `paper/` would ship a differently dated rendering of a letter the editor already has.

**M6 · must-fix — the companion-work disclosure claims a "Prefix comparison" that the manuscript says was never run.**
- Artefact: `cover_letter_revision.tex:57–58` — "the present manuscript reports a separate programme of PEFT experiments, **the Adapter and Prefix comparisons**, the layered fine-tuning results, the zero-shot benchmarks and the monitoring application."
- Manuscript: `conclusion.tex:16` — "**Fifth, other PEFT methods (prefix tuning, prompt tuning, IA3) remain unexplored under our framework.**" The only other occurrence of "Prefix" in the package is `methodology.tex:22`, and it is a statement about *code paths*, not results: "The **Adapter and Prefix paths** freeze the backbone before injection and are unaffected." The experiment catalog (`supplementary.tex` sections I–XIII) lists **no prefix-tuning run**.
- This matters because the paragraph's whole purpose is to draw the boundary between the two manuscripts: telling the editor that this paper contains prefix comparisons that it does not contain is exactly the kind of statement an overlap check will test. **Fix**: delete "and Prefix" (or "the Adapter comparison"), and if a Prefix result does exist, add it to the catalog.

---

## 5. Dates, title page, declaration, ORCID, funding, competing interests (brief item 4)

### 5.1 The `.tex` set (what should be on file) is internally consistent — one issue

`title_page.tex`: title `Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models` (= `main_nn.tex:25`), `University of Southampton`, `hw4c24@soton.ac.uk`, `ORCID: 0009-0003-8649-7504`, `Submitted to **Pattern Recognition**`, `August 14, 2026`.
`declaration.tex:6`: "The author declares that he has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper." + `University of Southampton` + `August 14, 2026`.

**N5 · note** — the submission is recorded as **2026-08-23** (`HANDOFF.md:8,189,196`: "P1（PR）**Under Review**（08-23）"; `docs/P1_ADVERSARIAL_REVIEW.md:3`: "自 2026-08-23 起 Under Review"), but the title page and declaration are dated **August 14, 2026** (the date of the two correction letters), and `title_page.tex` still reads "Submitted to Pattern Recognition". For the revision, all three (title page, declaration, cover letter) need one consistent date; `cover_letter_revision.tex` currently carries **no date at all** (`:3` internal note: "DRAFT 2026-09-18 — to be finalised and dated when the decision arrives").

**S4 · should-fix — no funding statement, no acknowledgements and no generative-AI disclosure anywhere in the P1 package; no competing-interest section inside the manuscript.** A recursive search of `paper/**/*.tex` for `Funding|Acknowledg|generative AI|Declaration of` returns exactly one hit: `declaration.tex:4`. Compare the author's own sibling submission, `SUBMISSION/A1_Neurocomputing/declaration.tex`, which carries all of: "Declaration of competing interests", "**Funding** — This research did not receive any specific grant from funding agencies…", and "**Declaration of generative AI and AI-assisted technologies in the manuscript preparation process**" — and whose line 31 states the requirement explicitly: *"In accordance with the journal's guide for authors, this statement is also required to appear in the manuscript itself, in a new section immediately before the reference list."* `main_nn.tex` has only `\section*{Data availability}` (`:83–84`). An editorial office that has seen the A1 package will notice the asymmetry.

### 5.2 The non-`.tex` artefacts in `paper/` are stale — two of them contradict the manuscript on identity

**M2 · must-fix — `title_page.docx` (2026-08-05) is a different paper's title page.** Extracted text vs the manuscript:

| Field | `title_page.docx` (extracted) | Current submission |
|---|---|---|
| Title | "Protect, Don't Perturb: **An Empirical Study of** Cross-Modal Alignment under **Parameter-Efficient Fine-Tuning** of Vision-Language Models" | `main_nn.tex:25` / `title_page.tex:10` "Protect, Don't Perturb: Cross-Modal Alignment under **PEFT** of Vision-Language Models" |
| Affiliation | "**Harbin Engineering University, Harbin, China**" | `title_page.tex:16–17` "University of Southampton / Southampton, UK" |
| E-mail | "**2024282101@hrbeu.edu.cn**" | `title_page.tex:20` "hw4c24@soton.ac.uk" |
| ORCID | "**0009-0008-3346-0114**" | `title_page.tex:23` "0009-0003-8649-7504" |
| Journal | "Submitted to **Neural Networks**" | `title_page.tex:29` "Submitted to **Pattern Recognition**" |
| Date | "June 11, 2026" | `title_page.tex:32` "August 14, 2026" |

`HANDOFF.md:218` records that this file is already known to be a leftover: "**title_page.docx 是 Neural Networks 时代残留（Harbin 大学/旧邮箱）——废弃不用**", and that ORCID `0009-0008-3346-0114` is "旧号（旧号！与 Paper 3 同源错误）" whose replacement is `0009-0003-8649-7504`. It is still sitting in the submission folder next to `title_page.tex`; the same page also records that a *previous* cover letter was shipped from a stale file in this folder (item ④). **Fix**: delete or move the stale `.docx` files out of `paper/` before packaging.

**M3 · must-fix — `declaration.pdf` (2026-07-04) names the wrong institution; `declaration.docx` (2026-07-17) names the wrong title.**
> `declaration.pdf` (pdftotext): "Declaration of competing interests … Hongrui Wan / **Harbin Engineering University** / **July 4, 2026**"
> `declaration.tex:11`: "Hongrui Wan / **University of Southampton** / **August 14, 2026**"
> `declaration.docx` (extracted): "…the manuscript entitled **Protect, Don't Perturb: An Empirical Study of Cross-Modal Alignment under Parameter-Efficient Fine-Tuning of Vision-Language Models** … Date: **July 17, 2026**" (affiliation is Southampton here, so this file contradicts the manuscript only in title and date).

Two different institutional affiliations for one author across one submission folder is the single most likely thing for a production office to query, because it concerns authorship identity, not content.

*No conflict in the remaining two files*: `competing_interests.docx` (2026-07-17) and `declarationStatement.docx` (2026-07-24) agree word-for-word with the Elsevier standard text in `declaration.tex:6` ("The author declares that he has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper."); neither carries a name/affiliation/date block, so neither contradicts the manuscript.

---

## 6. Artefacts that still promise something the manuscript no longer contains (brief item 5)

**M1 · must-fix — `paper/abstract.pdf` (2026-07-04) is a pre-remediation abstract and contradicts the manuscript on nine counts.** It is a standalone, uploadable-looking PDF sitting in the submission folder. Full text vs the manuscript:

| `abstract.pdf` (verbatim) | Manuscript now |
|---|---|
| "Through **116** experiments" | `main_nn.tex:39` "Through **117** experiments" |
| "we conduct the **first** systematic study" | `main_nn.tex:41` "we conduct a systematic study" (the "first" flag was removed in the remediation) |
| "three model **architectures**" | `main_nn.tex:39` "three model **families**" |
| "increases the Centroid Gap by **24%**" | `main_nn.tex:45` "**23.3% ± 1.0%** over five seeds" |
| "**destroys zero-shot accuracy by 53.3%**" | `main_nn.tex:47` "collapses zero-shot accuracy to near-chance levels (mean **2.6%** over 3 retrained seeds)" |
| "text-only LoRA limits the gap increase to **+0.079** and zero-shot degradation to **1.7%**" | `main_nn.tex:47–48` "text-only LoRA largely contains the gap increase and limits zero-shot degradation to **0.6** percentage points"; +0.079 is a Route D configuration only (`experiments.tex:33`) |
| "provide **direct causal evidence** through noise sensitivity, gradient analysis, and effective rank tracking" | `main_nn.tex:53–55` the causal wording was replaced by the strict control |
| "Distribution Gap **predicts retrieval performance at r = −0.827 (partial r = −0.807** controlling for Centroid Gap)" | `main_nn.tex:56–58` "**r = −0.71 (partial r = −0.58** …, collinear at r = +0.95)" |
| "across LoRA, Adapter, BLIP-1, and **SigLIP** configurations" with no exceptions | `main_nn.tex:43–45` "…and ViT-L configurations, **with a few exceptions**" |

Every one of those nine statements is a claim the remediation deliberately retired (verified: the retracted strings `53.3`, `1.7%`, `direct causal`, `first systematic`, `0.807`, `24\%` return **0 hits** in the current `main_nn.pdf` text). **Nothing in the workspace references `abstract.pdf`** (a recursive search of `root/*.md`, `docs/**`, `paper/**`, `tools/**` for `abstract.pdf` returns nothing) — it is an orphan, which makes deleting it free. The identical text also existed as `paper/main_nn.abs`; patch C deleted that file at 13:49 ("deletes paper/main_nn.abs, a pre-remediation build artefact still printing 116/24%"). **`abstract.pdf` was not deleted.**

**S5 · should-fix — the manuscript promises released code/data that has no address.** `experiments.tex:149`: *"…(the strict control of Section 5 is held out, giving n = 204; **the rule, the script and the complete row list are released with the code**, and Table 5 reports the result)"*, and the revision letter repeats it ("releases the row list", `cover_letter_revision.tex:94`). A search of `paper/**/*.tex` for `github|zenodo|Code availability|code and data` returns **only that sentence**. `main_nn.tex:83–84` offers just "Data will be made available on request." Either add the repository URL (the sibling papers do — e.g. `SUBMISSION/A1_Neurocomputing/main.tex:578` ends with "Code and data: `github.com/MoYUYao666/gap-susceptibility`") or soften the promise.

---

## 7. Other things a production or editorial office would flag (brief item 6)

**S6 · should-fix — two references print as garbled strings** (adjacent bibliography fields concatenated with no separator), still present in the current build:
> `[4] L. Yi, R. Douady, C. Chen, Decipher the modality gap …, arXiv preprint arXiv:**2510.03268The Convergent Representation of Contrastive Vision-Language Models: Geometry, Modality Gap and Shared Space Alignment (ICML 2026 version)** (2025).`
> `[28] J. Zhang, N. Liu, K. Wang, GTMA …, arXiv preprint arXiv:**2512.18504Published version: IEEE Xplore, document 11463397** (title: GTMA: Dynamic Representation Optimization for OOD VLMs) (2025).`
Cause: the `note = {…}` field (`references.bib:153` for Yi et al., `references.bib:351` for GTMA) renders immediately after the `journal` field under `elsarticle-num`, with no separator. A copy-editor will bounce these.

**S3 · should-fix — the revision letter promises an accompanying response that does not exist.** `cover_letter_revision.tex:43–44`: "**The point-by-point response to the reviewers accompanies this letter.**" A recursive search of the workspace for reviewer-response material returns only A1 documents (`docs/A1_REVIEWER_RESPONSE_PLAN.md`, `docs/A1_REVIEWER_EXPERIMENTS.md`) and `paper3/paper_ieee/Reviewer.pdf` — nothing for P1. (`paper/REVIEW_DEFENSE.md` is a pre-submission defence memo, not a response.) Because the letter is a draft pending the decision this is a scheduling issue, not a falsehood — but the sentence must not survive into the sent version unless the response is in the same envelope.

**N8 · note — non-submission material is interleaved with submission material, and some of it is stale.** `paper/FOR_ADVISOR.md:5,14` still says "Hongrui Wan · **Harbin Engineering University** · Submitted **June 11, 2026**", "| 期刊 | **Neural Networks** (SCI 一区, IF~10) |", "116 实验", and `:26,55,58` still carry `r=-0.979→-0.827`, "CG +24%, zero-shot -53.3%", "r=-0.827, partial r=-0.807, n=81". `paper/1.md` is a pasted editor's e-mail ("…the review process will start ASAP… Kind regards, Riza Cadayday"). `paper/REVIEW_DEFENSE.md:42,90–97` still frames the defence around "r = -0.827 … (94 experiments, 79 clusters)". None of these should be in an upload bundle.

**N7 · note — attribution in the letter is narrower than in the manuscript.** `cover_letter_revision.tex:59–60`: "The two share the Centroid Gap / Distribution Gap measurement framework, which both attribute to the work that introduced the CG/DG decomposition (**Liu et al.**)". The manuscript adopts it as "the terminology of [10, 43]" — `methodology.tex:6`: "adopting the terminology of~\cite{liu2026tpc,cheng2026maab}". Consider matching the manuscript.

**N6 · note — the "Welch p=0.70" quoted in the revision letter and now in the manuscript is not reproducible from the archived per-seed data.** `cover_letter_revision.tex:79–80`: "…the gap reduction it produces is within noise of the mixed runs (five seeds, **Welch $p=0.70$**)", and `paper/sections/strict_control.tex:41` (patch D2, 13:51:25): "…$-0.0458 \pm 0.0021$ against $-0.0465 \pm 0.0027$ (**$p = 0.70$**, Welch)". Recomputed from the same archive: strict-freeze text-only per-seed CGΔ (`outputs/strict_freeze/text_only/seed{42,123,456,789,1024}/results.json`, `final_gap.centroid_gap − initial_gap.centroid_gap`) = −0.044293, −0.049649, −0.049182, −0.046685, −0.042715 → mean −0.046505, sd 0.003014; legacy 5-seed text-only (`outputs/flickr30k_seeds/summary.json` → `rq2_text_only`: mean −0.045817, sd 0.002099) → Welch **t = 0.450, df ≈ 7.55, two-sided p ≈ 0.67**; using the printed rounded sds (0.0021 / 0.0027) → **p ≈ 0.66**; using the per-seed values printed in Table 11 (−0.048/−0.044/−0.048/−0.043/−0.047, sd 0.002345) → **p ≈ 0.78**. The qualitative claim ("within noise") is safe — the two means differ by 0.0007 against a pooled SE of 0.0015 — but "p = 0.70" should be recomputed and aligned across the letter and the manuscript, or written as "p ≈ 0.7".

**N9 · note — the supplementary catalog labels the three Route E runs by different keys.** `supplementary.tex:114–116` labels `e2_dges_text_alpha4` as "text, α=4, DG-ES" and `e3_dges_text_r8` as "text, r=8, DG-ES", while the Figure 5 caption calls the third run "the **α=16** text-only run" (`experiments.tex:187`). Both are right (`paper/scripts/dges_improved.py:273–275`: `both_r8 = rank 8, alpha 16`; `text_alpha4 = rank 8, alpha 4`; `text_r8 = rank 8, alpha 16`), but a reader cannot tell that "r=8" and "α=16" name the same run. Cosmetic.

---

## 8. What changed while this review was running (for the parent agent)

`tools/_p1_patch_c.py` ran at 13:49:09 and `main_nn.pdf` was rebuilt at 13:49:21 and again at 13:50:36. It resolved **five** items I had verified as defects in the 13:40:12 build:

| Item | 13:40 build | Current (13:50:36) build |
|---|---|---|
| Fig. 11 embedded image | Old PNG: panel B title read "**B: Text-only matches Both (Vis grads contribute <640% to loss reduction)**" (extracted from the PDF and read as an image) — contradicting `supplementary.tex`'s own caption and footnote *b* ("text-only converges to a higher final loss") | Regenerated PNG embedded: "**B: Text-only converges to a higher loss (4.16 vs. 0.61) yet preserves alignment**", matching `supplementary.tex:286` and footnote *b* |
| Fig. 11 numbers | caption "1.5× … 4.15 vs. 0.56" | `supplementary.tex:286` "1.4× … 4.16 vs. 0.61" (patch C12) |
| Discussion §7.3 Adapter guideline | `discussion.tex:28` "Use text-only with large bottleneck dimension ($d=64$, CG$\Delta = -0.217$)" — contradicted §4.5 | patched to "+0.064 … versus +0.259 at d=4" (patch C9) |
| Revision letter, training-convention row | "the **ordering of the positions is unchanged** and the visual encoder receives exactly zero updates in that control" — unsupported: `outputs/analysis/strict_control_summary.json` has **only** `text_only` (5 seeds); the log's own note says the joint rows were not run | replaced by "the visual encoder receives exactly zero updates in that control, and the gap reduction it produces is within noise of the mixed runs (five seeds, Welch p=0.70)" (patch C15) |
| Revision letter, figures row | "Figure 2 carried an n=81 title" (file name, not printed number) | "the figure printed as Figure 4 carried an n=81 title" (patch C15) |
| Table 1 row sum | SigLIP row = 5 → the category rows summed to 116 under a printed total of 117 | SigLIP = 6 → rows sum to 117 (patch C1) |
| Table 2 caption | no Adapter-convention note | convention stated + cross-reference to Table 4 (patch C2) |
| `supplementary.tex:5` | no Adapter caveat | Adapter-row caveat added (patch C11) |
| `paper/main_nn.abs` | present, printing 116/24%/direct-causal/r=−0.827 | deleted |

**Still outstanding after that rebuild**: M1 (`abstract.pdf`), M2/M3 (stale `.docx`/`declaration.pdf`), M4 (Table 1's Adapter cell), M5 (no reconciliation with the 08-14 letters), S1–S6, N1–N9. Re-verify M4 and the letter rows against whatever build finally ships.

**A further patch wave landed after this report was drafted** (observed at 13:50:25–13:51:49): `tools/_p1_patch_d2.py`, `tools/_p1_patch_e.py`, `tools/_p1_add_joint_rows.py`, and another rebuild (`main_nn.pdf` 2 706 964 B at 13:51:33). These are *mechanism*-scope edits, not artefact-scope: D2 rewrites `strict_control.tex`'s conclusion to "the control is one-armed … we do not claim that vision-side perturbation is what makes joint adaptation costlier", E relabels "0 of 199" to `vision_model.*` tensors and flags the layered-family confound, and `_p1_add_joint_rows.py` is a turnkey updater for when the joint strict-freeze arm is actually run. Two consequences for this report:
- The **"ordering of the positions is unchanged"** defect (fixed in the letter by patch C15) is now also fixed in the manuscript by an explicit one-armed caveat — good; keep the two consistent.
- **N6 now applies to the manuscript as well as the letter** (`strict_control.tex:41` "p = 0.70, Welch"), so it is worth resolving rather than dropping.
None of M1–M5, S1–S6 or N1–N5, N7–N9 is touched by that wave.

---

## 9. Prioritised action list

**Before anything is sent to the editor**
1. **M5** — add a paragraph to the revision letter naming the two 2026-08-14 letters and stating, in one place, which of their numbers stand and which are superseded (zero-shot protocol/n; the two change-score correlations; Fig. 7).
2. **M6** — remove "and Prefix" from the companion-work disclosure (`cover_letter_revision.tex:57–58`): the manuscript states prefix tuning is unexplored.
3. **M4** — fix `experiments.tex:30` (or its caption): Table 1's Adapter "Best CGΔ" must be frozen-relative (+0.064) to match Table 4, §4.5 and the letter.
4. **M1** — delete `paper/abstract.pdf` (orphan; nine retracted claims).
5. **M2/M3** — move `title_page.docx`, `declaration.docx`, `declaration.pdf` out of `paper/` (or replace with the Southampton / Pattern Recognition / 2026 versions). Confirm which ORCID is on file: `0009-0003-8649-7504` (`title_page.tex`), not `0009-0008-3346-0114`.
6. **S4** — add Funding / acknowledgements / generative-AI disclosure to the manuscript and re-date `title_page.tex` + `declaration.tex` for the revision.
7. **S3** — either write the point-by-point response or remove the sentence promising it.
8. **S5/S6** — add the code/data URL; fix the two concatenated bibliography entries.

**Housekeeping that removes real shipping risk**
9. **N8/S1** — quarantine non-submission material (`FOR_ADVISOR.md`, `1.md`, `REVIEW_DEFENSE.md`, `_p1pdf.txt`, `*.aux/.log/.out/.spl`, `cover_letter.pdf` with the 5 August date) so the next upload is picked from the `.tex` sources only.
10. **N5** — one consistent date across title page, declaration and cover letter; date the revision letter when it is finalised.
11. **N1–N4, N6, N7, N9** — wording-level: qualify "117 PEFT experiments", keep the manuscript's exceptions with bullet 2, restore "close to" in bullet 4, fix "p=0.70" in both the manuscript and the letter, match the CG/DG attribution, trim bullet 4 below 85 characters of text if any doubt remains, and decide whether the highlights PDF should carry a page number.

---

## 10. Evidence log (how each comparison was produced)

- Manuscript text: `pdftotext -enc UTF-8 paper/main_nn.pdf` (41 pp., CreationDate 2026-09-20 13:50:33) — the checked-in `paper/_p1pdf.txt` is a **stale** dump of the 13:40:12 build and does not contain the patch-C wording.
- `highlights.tex`: compiled in a scratch directory with `D:\texlive\2025\bin\windows\pdflatex.exe` (0 errors); output 24 867 B = byte-identical size to `paper/highlights.pdf`; text and lengths taken from `pdftotext` of that build and cross-checked against the `.tex` source.
- Pre-remediation ("previously reported") values: recovered from the remediation patch scripts themselves — `tools/_p1_patch_a.py` (abstract/intro/conclusion/experiments/supplementary/methodology/disclosure), `_p1_patch_a2.py` (+0.237 vs +0.500), `_p1_patch_a4.py` (fig 7 caption), `_p1_patch_a5.py` (Table 4 means), `_p1_patch_a6.py`/`_p1_patch_a7.py` (DG numbers, "81 experiments"), `_p1_patch_b.py` (the verbatim "text-only preserves visual embedding geometry"), plus `docs/P1_ADVERSARIAL_REVIEW.md` [M1]–[M26] and `docs/P1_REVIEW_NUMBERS.md`/`docs/P1_REVIEW_CONSISTENCY.md`.
- Archive checks: `outputs/analysis/adapter_common_baseline.json` (`delta_old` vs `delta_common` per run), `outputs/analysis/strict_control_summary.json` (only `text_only`), `outputs/flickr30k_seeds/summary.json`, `outputs/strict_freeze/text_only/seed*/results.json`, `outputs/route_e/e{1,2,3}_*/` (checkpoint sizes 1 955 KB / 787 KB / 787 KB).
- Figure mapping: `\includegraphics` order in `paper/sections/experiments.tex` (fig1→Fig 1, fig3→Fig 2, fig4→Fig 3, fig2→Fig 4, fig5→Fig 5, fig6→Fig 6, fig7→Fig 7), cross-checked against the printed captions in the PDF.
- Embedded-figure check: `pdfimages -list` + `pdfimages -png -f 37 -l 37` + pixel crop read as an image, to compare what the PDF actually embeds with `paper/figures/*.png`.
- `.docx` extraction: `Expand-Archive` on the file, then `word/document.xml` stripped of tags.
- No network access was used for verification (the two ORCID strings were not resolvable from public sources in this environment; they are compared between artefacts only).
