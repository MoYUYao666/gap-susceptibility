# A23 — Round-3 pre-submission review of `paper_a2/` (fresh adversarial read)

**Engagement**: independent third review of the manuscript in `paper_a2/` (target journal *Ocean Engineering*,
Elsevier, hybrid/subscription route) before submission. Read-only: **no file under `paper_a2/` or `outputs/` was
modified**; this report is the only file written.

**Relationship to the two earlier rounds.** `docs/A23_TABLE_TRACE.md` verified 24 tables cell-by-cell
(register D1–D14) and `docs/A23_REAUDIT.md` re-verified the corrections (19 PASS / 8 FAIL). This round
deliberately does **not** re-run that trace. It covers what the two earlier rounds did not look at:
(a) the manuscript's argument (abstract ↔ body ↔ cover letter ↔ highlights), (b) the archived **figures**
(the D-round audited tables only), (c) *prose* numbers inside the extension parts, (d) the *test* of a cell
against the convention its own caption declares, rather than against whichever convention happened to match,
and (e) submission compliance. Where a Round-1/Round-2 item is still open it is marked **[carried over]**
and not counted as new.

**Verification rule applied**: every number relied on below was recomputed from a named JSON key path or
read from the archived figure/PDF artefact. One Round-2 conclusion is *corrected* here — its "±"-convention
verdict on `tab:dynamics` (finding **A3**, which also establishes that Round 2's prescribed fix would have
introduced a new error).

**Compilation** (run in this round, from `paper_a2/`, source and artefacts unchanged in size):

| build | command | exit codes | pages | errors | undefined refs/cites |
|---|---|---|---|---|---|
| English | `pdflatex main.tex` ×2 | **0, 0** | **62** (`Output written on main.pdf (62 pages, 1497414 bytes)`) | none (`!` none) | none (`bibcite` 28/28; no `LaTeX Warning: Reference/Citation`) |
| Chinese | `xelatex main_zh.tex` ×2 | **0, 0** | **43** | none | none (`bibcite` 28/28) |

Remaining log noise: 5 `Overfull \hbox` (≤18.8 pt) in the English build at main.tex 181–198 (=long-panel
figure), 428–441 (tab:dir-op), 713–724 (tab:eng), and two extension tables; `hyperref` "Token not allowed in a
PDF string" ×4 (math in section titles/PDF bookmarks — cosmetic); Chinese build: `Font shape TU/SimSun(0)/b/it
undefined` ×1 (cosmetic).

---

## 1. Findings, ordered by severity

Numbers in **[brackets]** are the report's own finding ids; they are referenced by the verdict in §5.

### 1.1 Must fix before submission

---

**[A1] — Figure 1 (`fig3_taupred.png`) was drawn from a different condition set than the text claims; the title claims 52, the code plots 38, and the caption's own breakdown sums to 34.**

*Evidence (artefact → code → text)*
- `paper_a2/figures/fig3_taupred.png` (read directly): axes titles `max |diff| = 0.0001 (38 conditions)`, `predicted τ (exact inversion condition)` vs `measured τ`.
- `tools/clip_a2_figures.py:121–132` builds the point list: 4 families × 7 λ = 28 (`ocean_margins.json`, `ocean_margins_x.json`), +2 (`ocean_fauna_margins.json`), +2 (`ocean_inat_wild.json`), +6 (`ocean_nsweep.json`, N ∈ {20,40,67}) = **38**. There is no 52-point source.
- `paper_a2/main.tex:174–179` (figure float) and `main.tex:177`: caption "**across all 52 conditions** (four model families, three class-set sizes, two image sources, λ∈[−1,2])".
- `paper_a2/main.tex:170`: "Fig.~\ref{fig:tau} plots predicted versus measured $\tau$ for all **52 conditions** (four families × seven $\lambda$; $\lambda{=}1$ on the three class sets; and class-set sizes $\{20,40,67\}$ for the BioCLIP pair)" — and that enumeration is **28 + 3 + 3 = 34**, which is neither 52 nor 38.
- `main.tex:54` (contribution 1, "all 52 marine conditions"), `main.tex:32` (abstract, "10^{-4} in every cell"), `main.tex:761` (conclusions, "marine 52 conditions ≤10^{-4}") and `cover_letter.tex:26` all inherit "52".

*Why it matters*: a reviewer who opens the figure sees a condition count that contradicts the figure caption in
the same float; the number is load-bearing (it is the paper's headline claim). Both prior rounds audited tables
only and did not open the PNG.

*Fix*: rebuild the figure with the full condition list, or (cheaper) change `main.tex:177`, `main.tex:170`,
`main.tex:54`, `main.tex:761` and `cover_letter.tex:26` to "**38 conditions**" and fix the enumeration in line 170
to the four families × seven λ + three class-set sizes + the three N-sweep points, i.e. the list the script
actually plots. The max-deviation claim (0.0001) is unaffected.

---

**[A2] — Abstract and conclusions claim exactness "in every cell", but the paper's own Table 10 and §3.7 report a 3-of-6 exception with deviations up to 0.016.** **[new; Round 2 saw the row but graded the sentence PASS]**

*Evidence*
- `main.tex:32` (abstract): "the exact predictor is verified to $10^{-4}$ **in every cell**".
- `main.tex:761` (conclusions): "machine-precision verified **in every cell** of the domain--model matrix (marine 52 conditions ≤10^{-4}; sonar 18/18 zero deviation; ImageNet-5k, DTD, Food101 exact)". `main_zh.tex` mirrors this verbatim ("每一格达到机器精度验证").
- `main.tex:499` (tab:watertank, UATD domainft row): exact τ `3/6^{\dagger}`; `main.tex:520–521`: "the sole exception is the collapsed UATD domain fine-tune, **exact in 3 of 6 λ with deviations ≤0.016**".
- JSON: `outputs/uatd_protocol.json :: domainft.rows[3].tau_pred 0.8095` vs `.tau_meas 0.8186` (Δ 0.0091); `rows[4]` 0.1371 vs 0.1532 (Δ 0.0161); `rows[5]` −0.9187 vs −0.9248 (Δ 0.0061).
- `paper_a2/highlights.tex:10` / `highlights.docx` bullet 1 and `cover_letter.tex:26` repeat the unrestricted claim (the cover letter at least scopes it to "the domain–model matrix", which the replication instruments sit outside — defensible; the abstract is not).

*Fix*: in the abstract and §7, change "in every cell" to "in every cell except the collapsed UATD domain fine-tune
(3 of 6 λ)", or move the UATD exception into the abstract's sentence as a parenthetical. A referee who reads
§3.7 after the abstract currently finds an internal contradiction.

---

**[A3] — `tab:dynamics`' `±` convention is stated wrongly in *both* directions: the caption says population sd "throughout", two cells are sample sd, one cell is population sd, and one cell is the sample sd of a *different quantity*.** **[corrects Round 2 finding A21/B4]**

*Evidence (recomputed from JSON this round)*

Seeds per the caption (`ext_partIII_dynamics.tex:35–41`): BioCLIP+Marine = `bio_marine_s0`, `bio_marine_s1`,
`ocean_tautraj.marine`; CLIP+Sonar = `dynamics_matrix.clip_sonar` (s42), `clip_sonar_s0`, `clip_sonar_s1`.

| cell (`ext_partIII_dynamics.tex:26–27`) | paper | pop sd (ddof 0) | sample sd (ddof 1) | matches |
|---|---|---|---|---|
| BioCLIP+Marine τ@1 0.178±**0.006** | 0.006 | 0.0063 | 0.0077 | pop ✓ |
| BioCLIP+Marine τ@10 0.184±**0.009** | 0.009 | 0.0088 | 0.0108 | pop ✓ |
| BioCLIP+Marine σm@1 0.0092±**0.001** | 0.001 | 0.0014 | 0.0020 | neither |
| CLIP+Sonar τ@1 0.436±**0.171** | 0.171 | 0.1709 | 0.2093 | pop ✓ |
| CLIP+Sonar τ@10 0.278±**0.112** | 0.112 | 0.1123 | 0.1375 | **pop** ✓ |
| CLIP+Sonar σm@1 0.0094±**0.007** | 0.007 | 0.0070 | **0.0086** | pop ✓ |
| CLIP+Sonar σm@10 0.0050±**0.001** | 0.001 | 0.0011 | 0.0013 | pop ✓ |
| CLIP+Sonar top-1@10 98.5±**1.3** | 1.3 | 1.2893 | **1.5790** | pop ✓ |

- JSON key paths: `outputs/dynamics_matrix.json :: clip_sonar[0].{tau,sigma_m}`, `:: clip_sonar[9].{tau,sigma_m,top1}`; `outputs/dynamics_seed.json :: clip_sonar_s0[0]`, `:: clip_sonar_s0[9]`, `:: clip_sonar_s1[0]`, `:: clip_sonar_s1[9]`, `:: bio_marine_s0[0]/[9]`, `:: bio_marine_s1[0]/[9]`; `outputs/ocean_tautraj.json :: marine[0]`, `:: marine[9]`.
- Caption, `ext_partIII_dynamics.tex:38–39`: "``$\pm$'' is the **population** standard deviation over the archived seeds (**the convention used throughout this paper**)".
- Counter-example *inside the same table*: the CLIP+Sonar **τ@10** cell prints 0.112 (population). Round 2 (`A23_REAUDIT.md` A21, B4, §3) declared this cell FAIL because the *sample* sd is 0.137, and declared the paper's ±-convention "split" (dynamics = sample, sonar-peft = population). Both verdicts are wrong: this cell is population-sd-correct, and the cells that are genuinely sample-sd (or wrong) are the *other* two.
- Cells that do not follow the declared convention: `σm@1 = 0.0094±0.007` (0.0070 pop → should be **0.007**; 0.0086 sample → 0.009); `top-1@10 = 98.5±1.3` (1.2893 pop → **1.3**; 1.5790 sample → 1.6). Both printed values equal the *sample* sd, so those two cells do use ddof 1 while the rest use ddof 0. `σm@1 = 0.0092±0.001` is the sample sd of the *two-seed* σm set but the population sd of the three-seed τ set — it cannot be both.
- The Chinese mirror repeats all eight cells unchanged (`zh_ext_partIII_dynamics.tex:19–20`, caption line 28).

*Fix*: pick one convention (population, to match `tab:sonar-peft` at `main.tex:264` and `tab:peft` at
`main.tex:374–380`, both of which this round reproduced cell-for-cell under ddof 0), recompute the eight `±`
values in `ext_partIII_dynamics.tex:26–27`, and delete the "used throughout this paper" clause — it is *true*
for the other two tables but false for this one. Note that Round 2's instruction to change `0.138 → 0.137`
(A21) must **not** be applied: that cell is 0.112 and correct under the convention the caption declares.

---

**[A4] — The abstract's second finding ("removes the protective text/image asymmetry") is contradicted by the paper's own text-type-discrimination result, which is one of its selling points.**

*Evidence*
- `main.tex:32` (abstract): "domain adaptation flattens the class bias field in a domain-specific, saturating way (…) **and removes the protective text/image asymmetry**" — stated for domain adaptation in general.
- `main.tex:586–588` (§3.7): "the replica **keeps a protective text-side asymmetry** ($\Delta\tau$ $+0.061$, reduced from BioCLIP's $+0.246$ but not erased as in OceanCLIP's $+0.007$), so symmetrization is **specific to taxonomy-text adaptation**".
- JSON: `outputs/ocean_replica.json :: marine.tau_text1 0.2781` − `:: marine.rows[5].tau_meas 0.2174` = +0.0607 → +0.061 ✓ (matches `tab:replica`, `main.tex:560`).
- The Chinese abstract (`main_zh.tex:37`) carries the same over-general sentence, and the Chinese §3.7 carries the same correction.

*Fix*: scope the abstract clause: "…and, for taxonomy-text adaptation, removes the protective text/image
asymmetry (a natural-text fine-tune retains it: $\Delta\tau$ +0.061)".

---

**[A5] — The Introduction runs a conclusion-first argument: it defines the test's success condition as the result it is about to report.**

*Evidence*
- `main.tex:48`: "**If the diagnostic survives that transfer at the same precision, the alignment-health laws are modality-general and should be assumed to structure any future non-optical contrastive model** (side-scan, LiDAR, polarimetric)." The same sentence appears in `main_zh.tex:49`.
- `main.tex:761` restates it unconditionally: "The diagnostic is therefore a property of contrastive alignment structure, not of a single modality or benchmark, and **should be assumed to structure future non-optical contrastive models**."
- What the paper actually tests: one acoustic backbone family (frozen CLIP ViT-B/32 → SonarCLIP, plus SonarCLIP seeds), NKSID + three replication sets, of which **one** is a failed adaptation (UATD). No side-scan, LiDAR or polarimetric data were tested — §5 (Future work, `main.tex:756`) says the side-scan multi-class set is "exhausted" and remains a data-availability item.

*Why it matters*: the claim being asserted ("should be assumed to structure") is the paper's headline
generalisation, and stating it as the pre-committed consequence of the test performed on one modality is exactly
the pattern a careful reviewer flags. The body is appropriately hedged (`main.tex:752`, `main.tex:761`
"narrowing the remaining modality risk to class-set scale and composition rather than acoustic modality").

*Fix*: at `main.tex:48`, replace "should be assumed to structure any future non-optical contrastive model" with
"transfers to at least one non-optical channel with the same precision"; keep the unconditional statement only in
§5/§7 where the evidence summary justifies it, or weaken it to "is expected to transfer" there as well.

---

### 1.2 Should fix (a reviewer is likely to raise these)

---

**[B1] — The abstract/highlights' "full fine-tuning destroys zero-shot" is contradicted by the paper's own tiered recommendation; the abstract also drops the qualifier the cover letter keeps.**

- `main.tex:32` (abstract) and `highlights.tex:12` / `highlights.docx` bullet 3: "while full fine-tuning destroys it (−15% to −62%)".
- `main.tex:761` (conclusions): "full fine-tuning **legitimate in strongly OOD regimes if variance is budgeted**".
- `main.tex:253` (§3.3): "In the strong-OOD small-class regime, full fine-tuning is therefore **not automatically disqualifying**".
- `main.tex:633` (§4 rule 4): "full fine-tuning is a **hard veto** for deployment in data-scarce marine settings" — the marine-only scope is present here but absent from the abstract and highlights.
- `cover_letter.tex:26` gets it right: "the adaptation recipe is domain-relative: … whereas in the strongly out-of-distribution acoustic regime full fine-tuning attains the best ordering health".

*Fix*: add "in the marine domain" to the abstract and highlight-3 sentences (the numbers −15%/−62% only describe
the marine sweep, `tab:peft`; the sonar FullFT row is `+` best-τ), so the abstract matches the letter and §4.

---

**[B2] — The abstract's own second finding promises a "saturating" flattening; the paper's quantitative saturation
claim is contradicted by the 650→2,617 image step.**

- `main.tex:32`: "flattens the class bias field in a domain-specific, **saturating** way (3.6× marine, 1.8×–3.8× sonar vs 1.1× terrestrial)".
- Saturation is demonstrated only for the marine 50-epoch checkpoint (`main.tex:295`: 0.0078 at 50 ep = 0.0064 at 10 ep).
- In sonar the flattening is *not* stable with scale: balanced 650 → 0.0239/0.0063 = **3.79×** but full 2,617 → 0.0247/0.0136 = **1.82×** (`outputs/sonar_protocol.json :: clip_frozen.sigma_m 0.0239`, `:: sonar_ft.sigma_m 0.0063`; `outputs/sonar_protocol_full.json :: clip_frozen.sigma_m 0.0247`, `:: sonar_ft_full.sigma_m 0.0136`), and the τ-immunity falls 0.896 → 0.720 (`main.tex:233`, explicitly "immunity is data-scale-dependent").
- The same sentence appears in `main_zh.tex:37`.

*Fix*: in the abstract, replace "saturating way" with "in a domain-specific way that saturates with training dose
but is modulated by data scale (3.6× marine; sonar 3.8× at 650 images, 1.8× at 2,617)".

---

**[B3] — Figure 7's caption describes a composition the figure does not have, and the reader cannot know what the three plotted models are.**

- `main.tex:274` caption: "(a) $\sigma_m$ of **frozen versus sonar-adapted models (balanced and full protocols)** against the terrestrial control".
- `figures/fig7_sonar_sigma.png` (read directly): panel (a) is a grouped bar chart with groups "balanced 650" and "full 2,617" and **two series only** — "CLIP frozen" (0.0239 / 0.0247) and "+ Sonar" (0.0063 / 0.0136) — plus a stray "+ Flickr" legend entry (0.0216) that appears in neither bar; panel (b) plots three flattening ratios (3.8×, 1.8×, 1.1×) for "sonar balanced 650 / sonar full 2,617 / terrestrial (full 2,617)".
- The "frozen" bars are **not labelled** as balanced vs full in the caption or by any annotation; the caption's "(balanced and full protocols)" is the only hint, and the "+Flickr" legend entry has no bar.
- Round 2 walked the sonar block (A11–A16) but did not open the figure.

*Fix*: caption → "(a) σm of CLIP frozen and SonarCLIP under the balanced 650-image and full 2,617-image protocols;
(b) matched-scale flattening ratios for the two sonar protocols against the terrestrial control"; either add the
terrestrial bar to panel (a) or drop the "+ Flickr" legend entry.

---

**[B4] — `tab:rank1`'s caption still names only 2 of the 7 bold cells, and the two cells it names are not the two largest violations.**

- `main.tex:411` `OceanCLIP & 2 & 0.5560 & \textbf{0.5178}`, `main.tex:414` `SigLIP & 1 & 0.7867 & \textbf{0.6969}`, `main.tex:405` BioCLIP λ=−1 `\textbf{0.5106} & \textbf{0.4500}`, `main.tex:407` BioCLIP λ=2 `\textbf{0.4745} & \textbf{0.6059}` (bold cell is only the first column of that row).
- Caption, `main.tex:417`: "Bold: **violations of the Gaussian bound (OceanCLIP, λ=2; SigLIP, λ=1)**" — omits BioCLIP λ=−1, −0.5, −0.25 and SigLIP λ=2, all of which the prose at `main.tex:397` lists and which the bold markup flags.
- Round 2 (A17/A18) verified the *count* (7 cells) and the prose list, and graded the caption PASS; the caption itself was not re-read.

*Fix*: caption → "Bold: the seven cells where the correlated-structure bound is violated (BioCLIP λ=−1, −0.5, −0.25; OceanCLIP λ=2; OpenCLIP λ=2; SigLIP λ=1, 2; listed in the text)."

---

**[B5] — `tab:degmap`'s two "optical rows" sentence does not describe the table it sits in.** **[carried over — Round 2 §4 observation 3, still uncorrected]**

- `ext_partIV_degradation.tex:43–45`: "Note that blur is available only for the acoustic domain; **the two optical rows per domain are the two haze levels** ($t{=}0.6$ and $t{=}0.3$)."
- The table (`ext_partIV_degradation.tex:28–38`) has **five** rows per optical domain (haze t=0.6, haze t=0.3, shadow, speckle 20%, speckle 40%). The caption's own "Intensities are monotone within family" and the "three laws" paragraph depend on all five.
- Mirrored in `zh_ext_partIV_degradation.tex:39`.

*Fix*: "the two **haze** rows per optical domain are the two haze levels".

---

**[B6] — The same caption asserts "every condition has |λ_eff| ≤ 0.11" while the table prints 0.111.** **[carried over — Round 2 §4 observation 2, still uncorrected]**

- `ext_partIV_degradation.tex:41–43` vs `ext_partIV_degradation.tex:32` (marine-67 speckle 40%: $\lambda_{\rm eff}$ 0.111).
- JSON: `outputs/degradation_matrix.json :: marine_bioclip.rows[4].lam_eff 0.1108` — so the printed cell is right and the bound is wrong for the rounded grid.

*Fix*: "|λ_eff| ≤ 0.12" or "|λ_eff| ≤ 1.2×10^{-1} (max 0.1108, marine speckle 40%)".

---

**[B7] — The `tab:calib` caption still claims a bootstrap that the result file does not contain.** **[carried over — Round 1 D14 / Round 2 B3, never corrected]**

- `main.tex:740–741`: "Tripwire calibration (118 matrix grid points, five domains, four model families; **2{,}000-fold bootstrap over points**, 95% CI in brackets)."
- JSON: `outputs/threshold_calibration.json` top-level keys are exactly `n_points` (=118), `cells`, `cutoffs`; the `cutoffs` object holds `sensitivity/specificity/precision/sens_lo/sens_hi/spec_lo/spec_hi` per cutoff — no replicate count, and the strings `boot`/`2000` do not occur in the file. The CI bounds are present; their provenance is not archived.
- `main_zh.tex` mirrors the caption ("2{,}000 次自举" appears in the mirror's table caption region).

*Fix*: either delete "2,000-fold bootstrap over points" and write "95% CI from the archived per-point
calibration", or archive the bootstrap replicates and keep the count. Also: the `τ≥0.8 / retention≥83%` row
prints `1.000` with no bracket while the caption promises brackets (`main.tex:735`).

---

**[B8] — `main.tex:631` anchors the recommended τ ≥ 0.8 band at λ=1, where the paper's *best* adapted model shows τ = 0.454 — the recommendation would fail its own flagship model.**

- `main.tex:631`: "We recommend the $\tau>0.8$ band as the ``safe'' operating region when adapting marine VLMs", then, in the same paragraph, "The band should therefore be read as an operating-region declaration at $\lambda\in\{0.25,0.5\}$ … rather than at $\lambda{=}1$".
- `main.tex:717` (tab:eng, "Pre-deployment audit of a marine VLM"): "**$\tau@\lambda{=}1$ (predicted vs measured)**; $\sigma_m$ & **$\tau\ge0.8$ safe**".
- Data: OceanCLIP τ@λ=1 = 0.454 — `outputs/ocean_spectrum.json :: oceanclip.rows[2].{NCC 62.065, top1 23.383, R1 0.199}` (the spectrum file's rows carry `NCC/top1/R1/CG`, not τ) and `outputs/ocean_nsweep.json :: oceanclip["67"].tau_meas_1 0.4539`; the same 0.454 appears in `tab:portrait` (`main.tex:335`) and `tab:spectrum` (`main.tex:314`). Retention at that point is **96.7%** (`main.tex:335`). So the operational table's rule flags the healthiest adapted checkpoint as unsafe.
- `ext_partV_mechanisms.tex:110–111` repeats "Safe band: $\tau@\lambda{=}1\ge0.8$".

*Fix*: change both the tab:eng row and the protocol step to "τ ≥ 0.8 at the **deployment-matched λ** (λ∈{0.25,0.5} for
marine checkpoints; τ@λ=1 is a stress column, not a pass/fail gate)" — this is exactly what §4's prose already argues.

---

**[B9] — Internal contradiction: §5 declares the co-trained-branch question closed; §5's own "remaining open validation" list reopens it.**

- `main.tex:754` (limitations 1): "The text-type discrimination (Section~\ref{sec:replica}) **bounds the curriculum question** … so the residual, honest doubt is only about the *magnitude* of OceanCLIP's specific adaptation".
- Same line, end: "the remaining open validation is MarineGPT-scale (7B+) instruction tuning **and co-trained bilingual branches**".
- Same line, limitation 6 area: "the remaining scope limits are honest and specific: … SCTD … remains **un used**; FathomNet's API **is retired**" → two defects in one clause: (i) "un used" is a typo for "unused"; (ii) "FathomNet's API is retired" contradicts `main.tex:810` ("the provided API key is valid, and the API is fully functional---at the correct host database.fathomnet.org") and `main_zh.tex:754`.
- JSON: the co-training negative itself is correctly reported (`outputs/bioclip_joint_training.json :: marine.top1_0 83.52`, `:: marine.top1_heldout 9.583`, `:: marine.tau_l1 0.3918`, `:: marine.tau_text1 0.5823`, `:: retrieval.q_ans.video_R1 13.052` — all match `main.tex:606–611`).

*Fix*: split the limitation into "curriculum question (settled by §3.7)" and "branch-sharing objective (open)";
fix "un used" → "unused"; correct the FathomNet clause to "FathomNet's signed-URL frames require credentials
(the API itself is functional)" to match Appendix B.

---

**[B10] — `tab:subspace` reports k = 1…5 but §2.9 defines only k = 1, 2, 3.**

- `ext_partIV_degradation.tex:82–85`: "reports the direction-resolved operator at subspace dimension $k=1,2,3$ (Section~\ref{sec:dir-method} generalized: the first direction is the supervised mean degradation direction, **the next two** are orthogonalized principal components of the paired shifts)".
- The table (`ext_partIV_degradation.tex:91`) has columns `err k=1 … err k=5`, and §3.6's takeaway depends on k=5 ("residuals 0.12–0.28 at k=5", `main.tex:756`; `ext_partIV_degradation.tex:174`).
- Verified against JSON: `outputs/direction_subspace.json` `err_k1..err_k5` reproduce all 40 printed cells (e.g. `:: marine_bioclip[0].{err_k1 0.2572 … err_k5 0.1866}` → 0.257/0.187 ✓).
- Mirrored in `zh_ext_partIV_degradation.tex:52`.

*Fix*: "at subspace dimension $k=1,\dots,5$ (the first direction is the supervised mean degradation direction;
the next four are orthogonalized principal components)".

---

**[B11] — The Qwen exactness claim is a single-λ number presented as the operator's accuracy.**

- `ext_partIII_dynamics.tex:69–70`: "same gap-surgery protocol---**exact to $7\times10^{-4}$ at $\lambda{=}1$** on the frozen baseline".
- JSON: `outputs/vlm_instruction_dynamics.json :: frozen.rows` → |τ_pred − τ_meas| = 0.0000 (λ=0), 0.0006 (λ=0.5), **0.0007 (λ=1)**, 0.0016 (λ=−0.5), 0.0020 (λ=2), **0.0030 (λ=−1)**. The maximum over the six λ is 3×10^{-3}, i.e. ~4× the quoted figure.
- The Chinese mirror repeats "在 $\lambda{=}1$ 处精确至 $7\times10^{-4}$" (`zh_ext_partIII_dynamics.tex:40`).

*Fix*: "exact to 7×10^{-4} at λ=1 (3×10^{-3} worst-case over the grid)".

---

**[B12] — `tab:ml16k`'s caption reports the frame count as the query count.**

- `main.tex:464`: "Natural-text retrieval on MarineLife-16K (**3{,}440 queries**, 427 videos; …)".
- JSON: `outputs/ocean_ml16k_retrieval.json :: meta.n_frames 3416`, `:: meta.n_queries 3440`; every `retrieval.*.n` is 3440. §2.11 counts 3,440 QA items and §2.10 counts 3,416 frames. So the caption prints the *frame* number where it means the *query* number (a reader comparing the two sections will see 3,440 vs 3,416 and suspect drift).

*Fix*: "3,440 queries over 3,416 frames (427 videos)".

---

### 1.3 Minor / hygiene

**[C1]** `main.tex:424` ranks the residual fractions across domains: "speckle 0.70 < blur 0.81 < shadow 0.90 < marine haze/colour cast 0.94–0.95". Within sonar the ordering holds (`outputs/direction_operator.json :: sonar_frozen[0].resid_frac_mean 0.7028`, `[2] 0.8097`, `[3] 0.9031`), but "shadow 0.90" is *sonar* shadow while the next term is marine — the chain silently changes domain. Fix: prefix each term ("sonar speckle … sonar shadow … marine haze/cast …").

**[C2]** `main.tex:632` and `main.tex:668–673` interleave `τ` values to three decimals (0.18/0.07) with table values to three decimals (0.177/0.069) for the *same* runs, and `main.tex:632` says the marine run gives τ=0.18 "while zero-shot top-1 rises to 58.4%" whereas `tab:monitor` (line 665) gives top-1 58.40 → the JSON `outputs/ocean_tautraj.json :: marine[0].{tau 0.1765, top1 58.396}` matches the table. Align the prose to the table's digits (0.177 / 0.069).

**[C3]** `ext_partV_mechanisms.tex:48`: "each **check point** keeps a different, measurable slice" → "checkpoint" (the paper uses "checkpoint" 15× elsewhere).

**[C4]** `main.tex:754` "un used" → "unused" (see B9).

**[C5]** `ext_partI_theory.tex:187` (tab:theory-stack, Thm 1 row) claims validation "**9/9 ≤0.002**". The archived artefact for the canonical model gives |pred − meas| = 0.0000, 0.0016, 0.0030, 0.0072, 0.0100, 0.0236, 0.0374, 0.0591, **0.0624** over λ ∈ {0.25, 0.5, 1, 2, 4, −2, −1, −0.5, −0.25} (`outputs/a1_theory_verify.json :: predicted_tau_orthogonal` vs `:: measured_tau_orthogonal`), and the adjacent prose in the same section quotes the honest figure ("the operator predicts the orthogonal-family τ curve within 0.075, within 0.039 for |λ|≤1", `ext_partI_theory.tex:112–114`, verified ✓). Either the table cell is wrong or it refers to a different quantity; if the latter it must be named. Also `tab:theory-stack` row order ("Lemma 1 = pairwise inversion, Lemma 2 = affine representation") does not match the appendix numbering (Lemma 1 = affine, Lemma 2 = inversion) — harmless because everything is `\ref`-resolved, but the table's "Lemma/Thm/Cor" column is the only place a reader sees the two orderings.

**[C6]** `main.tex:86` and `main.tex:806` state that in the local network environment "**only NKSID was retrievable**" / "we therefore report single-dataset acoustic evidence"; §3.6 (`main.tex:474–481`) and §5 (limitation 6) report four acoustic datasets acquired. Both statements survive in the same PDF (`main_zh.tex:84` mirrors the first). Fix: mark §2.5/Appendix B as "as of the first acquisition attempt (2026-08)" and cross-reference the retry log, so the two passages do not read as contradictory.

**[C7]** `ext_partI_theory.tex:155–157` reports the contraction column values to four decimals ("predicted top-1 70.32/78.58 and τ 0.7598/0.615 match measured values *exactly*"), verified ✓ against `outputs/a1_theory_verify.json :: class_contraction.{0.25,0.5}` and `:: measured`. But the source artefact is `outputs/a1_full_results.json :: [7].top1 55.96` for the λ=0.25 image-side surgery — a *different* experiment with a different top-1. The "exactly" claim is correct for the JSON pair named; it should name `a1_theory_verify.json` explicitly in §A.2 so a reader cannot pair it with the λ-curve rows. (Reported as hygiene only: no contradiction found.)

**[C8 — carried over, not new]** `ext_partIII_dynamics.tex:54` says "in every direction--seed pair τ drops from 1 to **0.13**--0.67 in one training step", but the six archived pairs the caption names span **0.17–0.67** (`dynamics_seed.json :: bio_marine_s0[0].tau 0.1867`, `:: bio_marine_s1[0].tau 0.1715`, `ocean_tautraj.json :: marine[0].tau 0.1765`, `dynamics_matrix.json :: clip_sonar[0].tau 0.2757`, `dynamics_seed.json :: clip_sonar_s0[0].tau 0.36`, `:: clip_sonar_s1[0].tau 0.6729`); 0.13 is the deliberately excluded collapsed seed (`:: clip_sonar_s99[0].tau 0.132`), which the *next* clause correctly reports separately. Round 1 B5 raised this; it remains. The companion convergence claim "0.13–0.40 sonar" **is** consistent (the three matched seeds converge at 0.3083 / 0.1274 / 0.3972).

**[C9]** The Qwen range in `ext_partIII_dynamics.tex:71–72` is stated as "τ stays in **0.93**–0.97 across all 10 epochs"; the trajectory is 0.926, 0.9363, 0.9413, 0.9436, 0.9436, 0.9496, 0.9499, 0.9536, 0.9682, 0.9436 (`outputs/vlm_instruction_dynamics.json :: traj[*].tau_l1`), so the true span is **0.926–0.968** and the epoch-1 value (0.926, the one the same paragraph highlights) sits *below* the quoted floor. Same paragraph, `:73`: "settles near **0.075**" while the epoch-10 value is 0.0755. Cosmetic, but these are exactly the digits a re-audit re-derives.

---

## 2. Cross-file consistency (English ↔ Chinese ↔ cover letter ↔ highlights ↔ Word files)

| # | Item | Result |
|---|---|---|
| 1 | Title identical in `main.tex:20`, `cover_letter.tex:20`, `declaration_of_interest.docx` ("Manuscript:" line) | **PASS** (`main_zh.tex:18` is a translation, as the mirror banner declares) |
| 2 | Abstract ↔ body claims | **FAIL** — A2 (every cell), A4 (asymmetry removed), B1 (full-FT destroys), B2 (saturating) |
| 3 | Cover letter ↔ manuscript | **PASS on numbers** (see §3): the letter's five domains, 52-condition claim (fails only via A1), 3.6×/1.8×–3.8×/1.1×, −2.8%…−8.1%, −15%…−62%, 0.881±0.016, 72.8±36.1, 21.8%, 27.65% vs 0.26%, four acoustic instruments + FathomNet, companion-work disclosure (PRLETTERS-D-26-01941, PR-D-26-10149) all match the body. The letter is **better scoped than the abstract** on B1 and A2 ("acoustic regime full fine-tuning attains the best ordering health"; "domain–model matrix"). No overstatement found that the manuscript does not already make. |
| 4 | Highlights ↔ manuscript | **PASS on numbers** (all five bullets traceable, §3), **1 overstatement** (bullet 3, finding B1); bullet 5 (27.65% vs 0.26%) matches `ocean_replica.json` / `ocean_ml16k_retrieval.json` exactly |
| 5 | Highlights ↔ `highlights.docx` | **PASS** — same five bullets, same order; docx has 5 paragraphs, `highlights.tex` has 5 `\item`s |
| 6 | Chinese mirror numeric fidelity | **PASS** — a token-level diff of every numeric token in the six ZH files vs the six EN files found **no** differences (1,763 EN / 1,800 ZH tokens; the only asymmetric token is `17`, which is the `4.17` / `17.33` table cells written with the `{,}` separator and therefore not tokenised identically). |
| 7 | Chinese mirror claim of full consistency (`main_zh.tex:30–31`: "全部数字、图表、公式与参考文献与英文版一致") | **FAIL (minor)** — (a) `radford2021` is `\bibitem`-defined but **never `\cite`d** in the Chinese file (26 unique cites vs 27 in English, where `main.tex:93` cites it); (b) `main_zh.tex` has an **extra Introduction paragraph** (line 47) with no English counterpart; (c) the conclusions diverge in framing (EN: an em-dash aside "—and the fourth acquisition contributes…"; ZH: a main clause "而第四个获取贡献首个适配失败案例"), and ZH omits the EN's "narrowing the remaining modality risk…" clause wording; (d) `main_zh.tex:22` is dated 2026-09-02 against the English/cover-letter date of 2026-09-14. |
| 8 | `declaration_of_interest.docx` ↔ `main.tex:821–822` | **PASS** — both carry the "no known competing financial interests" sentence and the "no specific grant" sentence; the docx also carries title/author/date, as the Elsevier tool requires |

**C7b (figures, not covered by either earlier round):** all seven PNGs exist, all seven are `\ref`-cited
(`fig:tau` ×2, `fig:lambda` ×2, `fig:sonar-tau` ×1, `fig:sonar-sigma` ×1, `fig:sigma` ×2, `fig:peft` ×1,
`fig:degrad` ×1). Two caption/figure mismatches were found (A1, B3) plus one loose term: `main.tex:184` calls
panel (c) an "**inset**" while it is a third side-by-side panel (`fig1_lambda.png`: "(a) Order preservation,
image side / (b) Zero-shot retention / (c) Text side"). The remaining four captions were checked against the
images and are accurate.

---

## 3. Submission-compliance checklist (against the journal's stated requirements, `_oe_guide.txt` lines 588–618 and 298–337)

| # | Requirement (source) | Manuscript | Verdict |
|---|---|---|---|
| 1 | Abstract ≤ 200 words (`_oe_guide.txt:589`) | 187 words (`main.tex:31–33`, token count after stripping LaTeX) — the Chinese mirror is the same text | **PASS** |
| 2 | Abstract must stand alone; avoid references, define non-standard abbreviations (`:592`, `:597`) | **no citations** ✓; but `PEFT` (line 32) and `top-1` are used without expansion in the abstract; `PEFT` is expanded only in §1.2 (`main.tex:75`) | **PARTIAL** — expand "parameter-efficient fine-tuning (PEFT)" at first use in the abstract |
| 3 | 1–7 keywords, English (`:602`) | 7 keywords (`main.tex:36`); ZH mirror also 7 (`main_zh.tex:34`) | **PASS** (edge of range) |
| 4 | Highlights: 3–5 bullets, ≤85 characters incl. spaces (`:617`) | 5 bullets; measured character counts 82 / 78 / 72 / 71 / 72 → max 82 (**PASS**). `highlights.docx` also carries 5 | **PASS** |
| 5 | Highlights as a separate editable file whose name contains "highlights" (`:615`) | `highlights.docx` (+`highlights.tex`) | **PASS** |
| 6 | Declaration of competing interests as a **Word** file uploaded at submission (`:336–337`) | `declaration_of_interest.docx`, `.docx` format, author signature not required (absent) | **PASS** |
| 7 | Declarations tool completed ("I have nothing to declare" option) (`:334`) | manuscript-level statement present (`main.tex:821–822`) | **PASS** (submission-system action remains for the author) |
| 8 | Figure/table captions complete (each float self-explanatory) | 24/24 tables and 7/7 figures have captions; **but** `fig:tau` caption contradicts its own panel title (A1), `fig:sonar-sigma` caption mis-describes panel (a) (B3), `tab:rank1`/`tab:degmap`/`tab:calib` captions contain the errors B4/B5/B7 | **FAIL** (4 captions) |
| 9 | Every float cited in the text | 24/24 tables ≥1 `\ref`; 7/7 figures ≥1 `\ref` | **PASS** |
| 10 | Reference completeness: every `\cite` defined, every `\bibitem` cited | all 27 English cites resolve to `\bibitem`s; **`qwen2vl2024` is defined but never cited** (the model is named in `main.tex:754` and the acknowledgements `main.tex:831`). Chinese: all 26 cites resolve; **`qwen2vl2024` and `radford2021` uncited** | **PARTIAL** — cite `\citep{qwen2vl2024}` where Qwen2-VL-2B first appears (`main.tex:754`), and add the `radford2021` citation to `main_zh.tex` |
| 11 | Bibliography ordering | first-author surname order verified in `main.tex:834–889` (Alawode, Bi, Biderman, Chen, Chowers, Christensen, Grassucci, Jian, Kamal, Levi, Liang, Maione, Mistretta, NKSID, Qin, Qwen Team, Radford, Sofer, survey, Valdenegro-Toro, Wan, Wan, Wortsman, Xie, Yamaguchi, Yi, Zheng, zjunlp) — the two Wan entries at 874–877 and Valdenegro-Toro at 872–873 are correct | **PASS** (`elsarticle` `authoryear` style; the mixed `\bibitem[…]{}` label format is the template's own) |
| 12 | Data-availability statement | present (`main.tex:814–816`), names repository and every dataset | **PASS** |
| 13 | Funding statement | present (`main.tex:818–819`) | **PASS** |
| 14 | CRediT author contributions | present (`main.tex:824–825`) | **PASS** |
| 15 | Generative-AI disclosure | present (`main.tex:827–828`) | **PASS** |
| 16 | Title page: corresponding author + e-mail included (`_oe_guide.txt:580–581`) | `main.tex:22–29` (author, affiliation, `\cortext`, `\ead`) | **PASS** |
| 17 | World-readable English | body is clean; `highlights.docx` uses non-ASCII sub/superscripts (`10⁻⁴`, `3.6×`) — render fine in Word, but plain-text submission fields can mangle them | **PASS (note)** — consider `10^-4` / `3.6x` if the portal pastes highlights as text |
| 18 | No word limit for research papers | 62 pp. in `elsarticle[review]` (double-spaced), 43 pp. Chinese | **PASS** |

---

## 4. Numbers spot-checked this round (JSON path = value)

Every entry was recomputed from the named key path in this round; ✓ = paper agrees, ✗ = disagrees.

**Manuscript figures (opened and read)**
- `figures/fig3_taupred.png` panel title "max |diff| = 0.0001 (**38** conditions)" ↔ `main.tex:170,177` "52 conditions" — ✗ (**A1**); 0.0001 ↔ `main.tex:170` "10^{-4}" ✓
- `figures/fig7_sonar_sigma.png` panel (a) bars 0.0239/0.0063/0.0216 and 0.0247/0.0136/0.0222 ↔ `outputs/sonar_protocol.json :: clip_frozen.sigma_m 0.0239`, `:: sonar_ft.sigma_m 0.0063`, `:: clip_flickrft.sigma_m 0.0216`; `outputs/sonar_protocol_full.json :: clip_frozen.sigma_m 0.0247`, `:: sonar_ft_full.sigma_m 0.0136`, `:: clip_flickrft.sigma_m 0.0222` ✓; caption describes different series — ✗ (**B3**)
- `figures/fig1_lambda.png`, `fig2_sigma.png`, `fig4_peft.png`, `fig5_degradation.png`, `fig6_sonar_lambda.png` — captions ✓ (fig6 curves match `sonar_protocol_full.json :: clip_frozen.rows[*].tau_meas`, `:: sonar_ft_full.rows[*]`, `:: clip_flickrft.rows[*]`)

**`tab:dynamics` (recomputed sd table, §1.1 A3)**
- `outputs/dynamics_matrix.json :: clip_sonar[0].{tau 0.2757, sigma_m 0.0104}`, `:: clip_sonar[9].{tau 0.3083, sigma_m 0.0063, top1 96.769}`
- `outputs/dynamics_seed.json :: clip_sonar_s0[0].{tau 0.36, sigma_m 0.0003}`, `:: clip_sonar_s0[9].{tau 0.1274, sigma_m 0.0037, top1 98.923}`, `:: clip_sonar_s1[0].{tau 0.6729, sigma_m 0.0174}`, `:: clip_sonar_s1[9].{tau 0.3972, sigma_m 0.0051, top1 99.846}`
- `outputs/dynamics_seed.json :: bio_marine_s0[0]/[9].{tau 0.1867/0.1929, sigma_m 0.0078/0.0054, top1 59.017/100.0}`, `:: bio_marine_s1[0]/[9].{tau 0.1715/0.1867, sigma_m 0.0106/0.0081, top1 46.517/99.813}`
- `outputs/ocean_tautraj.json :: marine[0].{tau 0.1765, top1 58.396, CG 1.1002}`, `:: marine[9].{tau 0.1719, top1 100.0, CG 1.0615}`
- `outputs/dynamics_seed.json :: clip_sonar_s99[0].tau 0.132` (the excluded collapsed seed) ↔ `ext_partIII_dynamics.tex:54` "0.13–0.67" ✗ — the six archived direction–seed pairs span 0.17–0.67 (**C8**, carried over from Round 1 B5)
- `outputs/dynamics_seed.json :: clip_sonar_50ep[9].{tau 0.3166, sigma_m 0.0062, top1 67.846}`, `:: [49].{tau 0.1548, sigma_m 0.0046, top1 100.0}` ↔ `ext_partIII_dynamics.tex:109–111` "0.317 → 0.155, 0.0062 → 0.0046, top-1 100%" ✓
- `outputs/dynamics_fathomnet.json :: traj[0].{tau 0.0542, sigma_m 0.009}`, `:: traj[9].{tau 0.1, sigma_m 0.0097, top1 100.0}`, `:: frozen_info.{sigma_m 0.0264}`, `:: flickrft_info.{sigma_m 0.0119, tau_l1 0.6292}` ↔ `ext_partIII_dynamics.tex:121–126` ✓ (note: that JSON's `meta.dataset` string says "8 concepts × 30" while `meta.classes` has 6 entries and `meta.n` = 144 = 6×24 — the paper's "6-concept subset … 24 frames each" is the correct one; **repository metadata defect**, worth correcting before the JSONs are published as supplementary material)
- `outputs/vlm_instruction_dynamics.json :: traj[0].{tau_l1 0.926, sigma_m 0.0839}`, `:: traj[9].{tau_l1 0.9436, sigma_m 0.0755}`; frozen `:: frozen.rows` deviations 0.0000–0.0030 ↔ `ext_partIII_dynamics.tex:71–73` ✓ (with **B11**)
- `outputs/vlm_vision_instruction_dynamics.json :: traj[0].{tau_l1 0.8823, sigma_m 0.1413, mean_cos 0.3485}`, `:: traj[9].{tau_l1 0.8813, sigma_m 0.0823, mean_cos 0.1886}` ↔ `ext_partIII_dynamics.tex:81–83` ✓

**Other cells re-verified because they carry a finding**
- `outputs/degradation_matrix.json :: marine_bioclip.rows[4].lam_eff 0.1108` ↔ `ext_partIV_degradation.tex:32,41–43` (**B6**); `:: rows[0].tau_meas 0.6498`, `:: rows[1].tau_meas 0.4041`, `:: rows[4].tau_meas 0.3322` ✓
- `outputs/direction_subspace.json :: marine_bioclip[0].err_k1 0.2572 … err_k5 0.1866`; `:: sonar_frozen[2].{err_k1 0.1769, err_k4 0.1437, err_k5 0.1388}` ✓ (all 40 cells)
- `outputs/perimage_operator.json :: *.err_same_def 0.0` and `tau_pred_perimage == tau_meas_tauA == tau_meas_tauB` for all eight conditions ✓ (`ext_partIV_degradation.tex:150–158`)
- `outputs/direction_operator.json :: sonar_frozen[2].{err_gap 0.7243, err_mean 0.1769, resid_frac_mean 0.8097, err_pca 0.432}` ↔ `main.tex:437,424` ✓
- `outputs/uatd_protocol.json :: domainft.rows[3].{tau_pred 0.8095, tau_meas 0.8186}`, `:: rows[4].{tau_pred 0.1371, tau_meas 0.1532}`, `:: rows[5].{tau_pred −0.9187, tau_meas −0.9248}`, `:: domainft.sigma_m 0.0002`, `:: domainft.top1_0 4.438` ↔ `main.tex:499,505–512` ✓ (**A2** is about the abstract, not this row)
- `outputs/watertank_protocol.json :: frozen.{sigma_m 0.0287, top1_0 17.33, rows[4].tau_meas −0.1074, rows[6].tau_meas −0.079}`, `:: riku_protocol.json :: frozen.{sigma_m 0.0286, top1_0 6.796, rows[4].tau_meas −0.3252}` ✓
- `outputs/threshold_calibration.json :: n_points 118`, `:: cutoffs.ret_ge_0.96["0.8"].{sensitivity 0.229, specificity 0.988, precision 0.889}`, `:: cutoffs.ret_ge_0.83["0.5"].{sensitivity 0.559, specificity 0.864}` ↔ `main.tex:631,734–737` ✓; no `boot`/`2000` key (**B7**)
- `outputs/ocean_spectrum.json :: oceanclip.rows[2].{NCC 62.065, top1 23.383, R1 0.199, CG 0.1359}`, `:: bioclip.rows[*]` ↔ `tab:spectrum` (main.tex:307–315) ✓
- `outputs/ocean_peft_ms.json` (18 keys, seeds {s1, s42, s99}) → **all 18 cells of `tab:peft` reproduce** under the population sd, and every retention percentage recomputes: `:: bioclip__lora_text__s{1,42,99}.{flickr_R1 0.1148/0.1179/0.1089 → 0.1139 → 0.114, pop sd 0.0037 → 0.004; marine_top1 23.197/22.948/22.699 → 22.948, pop sd 0.203 → 0.20}`, `:: bioclip__fullft__s{1,42,99}.{flickr_R1 0.4072/0.3231/0.2891 → 0.3398 → 0.340, pop 0.0542 → 0.054; marine_top1 10.137/9.453/5.409 → 8.333, pop 1.317 → 1.32}` (retention −61.60% → −61.6% ✓), `:: oceanclip__lora_text__*.{23.383/23.197/23.507 → 23.362 ± 0.127}`, `:: oceanclip__lora_both__*.{22.264/22.637/21.766 → 22.222 ± 0.357}`, `:: oceanclip__bitfit__*.{23.507/23.570/23.445 → 23.507 ± 0.051}` (retention −2.83% → −2.8% ✓), `:: oceanclip__fullft__*.{19.527/20.896/21.144 → 20.522 ± 0.711}`, `:: oceanclip__fullft__*.flickr_R1 {0.5672/0.6038/0.5901 → 0.5870 ± 0.0151}`. `tab:peft` therefore uses the **population** sd convention — the same as `tab:sonar-peft` — which is what A3 measures `tab:dynamics` against. (Do **not** be misled, as this round briefly was, by the single-seed duplicate keys in `ocean_peft.json` — e.g. `:: bioclip__fullft.marine_top1 9.453` is the *seed-42* value, not the 3-seed mean.)
- `outputs/ocean_replica.json :: marine.{sigma_m 0.0167, top1_0 2.861, rows[5].tau_meas 0.2174, tau_text1 0.2781}`, `:: retrieval.q_ans.video_R1 27.645` ✓; `outputs/bioclip_lora_instruction.json :: marine.{sigma_m 0.0598, top1_0 19.963, tau_l1 0.3435, tau_text1 0.5458}`, `:: retrieval.q_ans.video_R1 11.657` ✓ (note `main.tex:560` prints Δτ +0.061 while `main.tex:586` and `main.tex:561` print +0.202 — both are correct for their rows, but the two sentences sit 25 lines apart and read as a contradiction on first pass; consider echoing the row labels)
- `outputs/bioclip_joint_training.json :: marine.{top1_0 83.52, top1_heldout 9.583, tau_l1 0.3918, tau_text1 0.5823}`, `:: retrieval.q_ans.video_R1 13.052` ↔ `main.tex:606–611` ✓
- `outputs/ml16k_qa_layers.json :: bioclip.lighting.videoR1 0.0`, `:: oceanclip.lighting.videoR1 0.581` ↔ `tab:qa-layers` (ext_partV:29–30) ✓ — but the adjacent prose (`ext_partV_mechanisms.tex:42–43`) lists "lighting 0.00" among the scene queries where "BioCLIP collapses to chance", silently dropping that **OceanCLIP retains 0.58% there (2.5× chance) while the other scene cells are at 0.00/0.235/0.24**; the row that makes the "re-allocation, not erosion" story is in the table but not in the reading paragraph (minor).
- `outputs/ocean_ml16k_retrieval.json :: meta.{n_frames 3416, n_queries 3440}`, `:: openclip_tf.q_ans.video_R1 1.919` ↔ `tab:ml16k` and `main.tex:448` ✓ (with **B12**)
- `outputs/a1_full_results.json :: [11].top1 32.01`, `:: [6].top1 59.28` → 54.0% ↔ `tab:portrait` last row ✓; `:: [6].tau_top5 0.2887` ↔ τ@λ=1 0.289 ✓
- `outputs/domain_matrix.json :: imagenet5k.openclip_tf.{sigma_m 0.0666, rows[4].tau_meas 0.3689, ncc_0 48.26}`, `:: dtd.openclip_tf.ncc_0 68.6/75.7/79.4/66.3`, `:: food101.openclip_tf.ncc_0 80.9/82.0/89.4/57.8` ↔ `tab:matrix` ✓
- `outputs/mechanism_summary.json :: sources.{nsweep, class_set, sonar, domain_matrix, degradation_sonar, direction_operator}` — the SonarCLIP balanced σm 0.0063 and τ@λ=1 0.896 appear only in `sonar_spectrum.json`/`sonar_protocol.json`, **not** in `mechanism_summary.sources.sonar` (which holds the full-protocol triple) — the `tab:sonar-sigma` balanced row is traceable but via a different file than the summary; note for the data-availability statement.
- Abstract's `27.65%` / `0.26%` ↔ `ocean_replica.json :: retrieval.q_ans.video_R1 27.645` / `ocean_ml16k_retrieval.json :: oceanclip.q_ans.video_R1 0.262` ✓; abstract's `−2.8%`…`−8.1%` and `−15%`…`−62%` ↔ `tab:peft` ✓; abstract's `10^{-4}` ↔ `figures/fig3_taupred.png` "0.0001" ✓; abstract's `1.8–3.8×` ↔ sonar protocols ✓

---

## 5. Verdict

**Not ready to submit as-is.** The manuscript is numerically sound in the places the two earlier rounds
checked, and in the places this round sampled: all 24 tables were traced by Round 1, and every load-bearing
cell re-sampled this round (across `dynamics_*`, `direction_*`, `perimage_operator`, `ocean_peft*`,
`uatd/riku/watertank_protocol`, `ocean_replica`, `bioclip_joint_training`, `ml16k_qa_layers`,
`threshold_calibration`, `domain_matrix`, `degradation_matrix`, `a1_theory_verify`) reproduces from the named
JSON key path, including all 18 cells of `tab:peft` and all 40 error cells of `tab:subspace`; both language
versions compile cleanly with no undefined references or citations (English 62 pp., Chinese 43 pp., exit 0/0
for both). What blocks submission is not arithmetic but **the paper's own framing of that arithmetic**:
Figure 1's condition count contradicts its caption and its own source code (52 vs 38 vs 34) and that count
carries the headline claim; the abstract's "in every cell" and "removes the protective asymmetry" both
contradict results the paper itself reports later (UATD 3/6; the +0.061 replica asymmetry); the "±" convention
is declared wrongly in both directions in `tab:dynamics` (and Round 2's fix instruction for that table would
introduce a new error); the Introduction pre-commits to the generalisation it is about to test; and `tab:eng`'s
τ ≥ 0.8 gate would fail the paper's own best model. **Minimum set of changes**: (1) fix or regenerate Figure 1
and correct the five "52 conditions" statements; (2) qualify the abstract's "every cell" and "removes the
asymmetry" clauses and add "in the marine domain" to the full-fine-tuning claim; (3) recompute the eight `±`
cells of `tab:dynamics` under a single declared convention and delete the "convention used throughout" clause;
(4) correct B4/B5/B6/B7 captions and B8's deployment gate; (5) soften the Introduction's "should be assumed to
structure any future non-optical contrastive model" and fix the §5 co-training/FathomNet/"un used" clause;
(6) cite `qwen2vl2024` (and add `radford2021` to the Chinese mirror) and fix the mirror's two content
divergences. Items 1–4 are reviewer-visible in the abstract, the first figure and the two most-read tables;
with 1–6 done the remaining risk is ordinary copy-editing rather than a credibility gap.

---

## 6. Files read / written

**Read**: `paper_a2/main.tex` (892 lines), `main_zh.tex` (756), `ext_partI..V_*.tex`, `zh_ext_partI..V_*.tex`,
`cover_letter.tex`, `highlights.tex`, `highlights.docx`, `declaration_of_interest.docx`,
`figures/*.png` (all 7, opened), `docs/A23_TABLE_TRACE.md`, `docs/A23_REAUDIT.md`, `_oe_guide.txt`;
JSONs read in full or by key path: `outputs/dynamics_matrix.json`, `dynamics_seed.json`,
`vlm_instruction_dynamics.json`, `vlm_vision_instruction_dynamics.json`, `dynamics_fathomnet.json`,
`degradation_matrix.json`, `direction_subspace.json`, `direction_operator.json`, `perimage_operator.json`,
`ocean_spectrum.json`, `ocean_peft.json`, `ocean_peft_ms.json`, `ocean_nsweep.json`, `ocean_margins.json`,
`ocean_replica.json`, `bioclip_lora_instruction.json`, `bioclip_joint_training.json`,
`ml16k_qa_layers.json`, `ocean_ml16k_retrieval.json`, `watertank_protocol.json`, `riku_protocol.json`,
`uatd_protocol.json`, `sonar_protocol.json`, `sonar_protocol_full.json`, `sonar_spectrum.json`,
`domain_matrix.json`, `threshold_calibration.json`, `mechanism_summary.json`, `a1_full_results.json`,
`a1_theory_verify.json`; build artefacts `main.log`, `main.aux`, `main_zh.log`, `main_zh.aux`, `main.pdf`,
`main_zh.pdf`.

**Written**: `docs/A23_ROUND3_REVIEW.md` (this file) — only.

**Not modified**: every file under `paper_a2/` and `outputs/`. The two `pdflatex` runs and two `xelatex` runs
regenerated `main.pdf/main.aux/main.log` and `main_zh.pdf/main_zh.aux/main_zh.log` in place from unchanged
sources; `main.pdf` came out byte-identical in size to the pre-existing build (1,497,414 bytes).
