# A23 — Round-3 fixes applied to `paper_a2/`

**Scope**: fixes for the five must-fix and the twelve should-fix items of `docs/A23_ROUND3_REVIEW.md`,
plus the compliance items and a full Chinese-mirror sync.
**Authoritative input**: `docs/A23_ROUND3_REVIEW.md`. Every finding was independently re-verified
against the archived artefacts before any edit; two of the review's own instructions were **not** applied
and one of its prescriptions was corrected (see §3 and §B4).
**Untouched**: everything under `outputs/`. No result JSON, figure PNG or table cell was modified.

---

## 1. MUST-FIX

### 1.1 — Figure-1 condition count: **38**, not 52

**Where the true count comes from.** `tools/clip_a2_figures.py:121–132` builds the point list as
4 families × 7 λ = 28, plus fauna (2), plus iNaturalist-wild (2), plus 2 models × 3 class-set sizes (6)
= **38**. I re-ran that exact construction against the JSONs and reproduced **38 points** with
`max |diff| = 0.000124` (the figure title's `0.0001`):

| block | JSON key path | n |
|---|---|---|
| 4 families × 7 λ | `ocean_margins.json :: {bioclip,oceanclip}.predicted_tau_exact[λ]` / `:: .measured[λ].tau`; `ocean_margins_x.json :: {openclip_tf,siglip}.`same | 28 |
| fauna @ λ=1 | `ocean_fauna_margins.json :: {bioclip,oceanclip}.predicted_tau_exact["1.0"]` / `:: .measured["1.0"].tau` | 2 |
| iNat-wild @ λ=1 | `ocean_inat_wild.json :: {bioclip,oceanclip}.{tau_pred_1,tau_meas_1}` | 2 |
| N-sweep | `ocean_nsweep.json :: {bioclip,oceanclip}["20"\|"40"\|"67"].{tau_pred_1,tau_meas_1}` | 6 |
| | **total plotted** | **38** |

**No archived JSON yields 52.** The only two counts the artefacts support are 38 (plotted points) and
**42** — the same set *plus* the four λ=0 cells of the 8-value grid
(`ocean_margins.json :: {bioclip,oceanclip}.predicted_tau_exact["0.0"] = 1.0` and `:: .measured["0.0"].tau = 1.0`,
likewise `ocean_margins_x.json`), i.e. 4 × 8 = 32 λ-matrix cells (max |dev| = 0.000124) + 2 + 2 + 6 = 42.
The old line-170 enumeration (28 + 3 + 3 = 34) matches neither. As the task allowed, the text now states
**both** counts explicitly so a reader cannot be confused.

| file:line | before → after |
|---|---|
| `main.tex:54` | "across all **52** marine conditions (four model families, three class-set sizes, two image sources)" → "across all **38** marine conditions (four model families × seven non-trivial λ; two further class sets at λ=1; and the class-set-size sweep {20,40,67} for the BioCLIP pair)" |
| `main.tex:170` | "for all **52** conditions (four families × seven λ; λ=1 on the three class sets; and class-set sizes {20,40,67} for the BioCLIP pair)" → explicit 38-point breakdown + "The trivial λ=0 slice … is omitted from the figure but included in the underlying verification, so the marine exactness result covers **42** (model, condition, λ) cells in total; **the count plotted here is therefore 38, not the 52 stated in earlier drafts of this work.**" |
| `main.tex:177` (caption `fig:tau`) | "across all **52** conditions (…)" → "across the **38** conditions plotted (…)"; + sentence "The trivial λ=0 slice is excluded from this summary figure and included in the underlying verification, which covers **42** marine cells in all." |
| `main.tex:766` (was 761, conclusions) | "marine **52** conditions ≤10⁻⁴" → "marine **38 plotted** conditions ≤10⁻⁴" |
| `cover_letter.tex:26` | "(**52** marine conditions; …)" → "(**38** marine conditions; …)" |
| `ext_partII_domains.tex:59` | "the marine **52**-condition and sonar 18/18 verifications" → "the marine **38**-condition and sonar 18/18 verifications" |
| `main_zh.tex:53, 169, 176, 654`; `zh_ext_partII_domains.tex:45` | mirrored (全部 52 → 38, plus the 42-cell note) |

### 1.2 — Abstract/conclusions "in every cell": qualified to match Results

*Evidence* — `outputs/uatd_protocol.json :: domainft.rows[*]`:
`rows[3]` 0.8095 vs 0.8186 (Δ 0.0091), `rows[4]` 0.1371 vs 0.1532 (Δ 0.0161),
`rows[5]` −0.9187 vs −0.9248 (Δ 0.0061), `rows[0..2]` Δ 0.0000 → **3 of 6 λ exact**.

| file:line | before → after |
|---|---|
| `main.tex:32` (abstract) | "verified to 10⁻⁴ **in every cell**, so τ … is the quantity to monitor" → "verified to 10⁻⁴ **in every cell of the domain–model matrix except the collapsed UATD fine-tune (3 of 6 λ; deviations ≤0.016)**, so τ … is what to monitor" |
| `main.tex:766` (conclusions) | "machine-precision verified **in every cell** of the domain–model matrix (marine 38 …)" → "… **except one** (… ; the collapsed UATD domain fine-tune is exact in 3 of 6 λ with deviations ≤0.016)" |
| `main_zh.tex:37, 654` | mirrored |
| `highlights.tex:10` + `highlights.docx` bullet 1 | "…is verified to 10⁻⁴ **in every cell of the matrix**" → "…**verified to 10⁻⁴ across five domains**" (extra fix: the review flagged this bullet in §2 row 4 too) |

The cover letter was already scoped to "the domain–model matrix", which the review itself calls
defensible; it was changed only for the 52→38 count.

### 1.3 — `tab:dynamics` ± convention: **no cell was wrong; no cell was changed**

Full recomputation over the seed sets the caption names. BioCLIP+Marine = seeds 0, 1, 42
(`dynamics_seed.json :: bio_marine_s0`, `:: bio_marine_s1`, `ocean_tautraj.json :: marine` — the last has
**no** `sigma_m` key, hence the caption's "two for BioCLIP+Marine"); CLIP+Sonar = seeds 42, 0, 1
(`dynamics_matrix.json :: clip_sonar`, `dynamics_seed.json :: clip_sonar_s0`, `:: clip_sonar_s1`).

| cell | printed | ddof=0 (population) | ddof=1 (sample) | rounds to | verdict |
|---|---|---|---|---|---|
| BM τ@1 0.178±**0.006** | 0.006 | 0.006279 | 0.007690 | 0.006 / 0.008 | **pop ✓** |
| BM τ@10 0.184±**0.009** | 0.009 | 0.008803 | 0.010779 | 0.009 / 0.011 | **pop ✓** |
| BM σm@1 0.0092±**0.001** | 0.001 | 0.001400 | 0.001980 | 0.001 / 0.002 | **pop ✓** |
| BM σm@10 0.0068±**0.001** | 0.001 | 0.001350 | 0.001909 | 0.001 / 0.002 | **pop ✓** |
| BM top-1@10 99.9±**0.1** | 0.1 | 0.088193 | 0.107983 | 0.1 / 0.1 | pop ✓ (ambiguous at 1 d.p.) |
| CS τ@1 0.436±**0.171** | 0.171 | 0.170881 | 0.209314 | 0.171 / 0.209 | **pop ✓** |
| CS τ@10 0.278±**0.112** | 0.112 | 0.112275 | 0.137506 | 0.112 / 0.137 | **pop ✓** |
| CS σm@1 0.0094±**0.007** | 0.007 | 0.006966 | 0.008603 | 0.007 / 0.009 | **pop ✓** |
| CS σm@10 0.0050±**0.001** | 0.001 | 0.001067 | 0.001285 | 0.001 / 0.001 | pop ✓ (ambiguous at 3 d.p.) |
| CS top-1@10 98.5±**1.3** | 1.3 | 1.289300 | 1.579017 | 1.3 / 1.6 | **pop ✓** |

Seed values: `clip_sonar[0].tau 0.2757`, `clip_sonar_s0[0].tau 0.36`, `clip_sonar_s1[0].tau 0.6729`;
`clip_sonar[9].{tau 0.3083, sigma_m 0.0063, top1 96.769}`, `clip_sonar_s0[9].{0.1274, 0.0037, 98.923}`,
`clip_sonar_s1[9].{0.3972, 0.0051, 99.846}`; `bio_marine_s0[0]/[9].{tau 0.1867/0.1929, sigma_m 0.0078/0.0054}`,
`bio_marine_s1[0]/[9].{0.1715/0.1867, 0.0106/0.0081}`; `ocean_tautraj.json :: marine[0].tau 0.1765`, `:: marine[9].{tau 0.1719, top1 100.0}`.

**Verdict: 8 of 10 cells unambiguously reproduce ddof=0, the other 2 are consistent with ddof=0 at the
printed precision. No cell deviates from the convention the caption declares, so no cell was changed**
(verified programmatically: all ten ± strings are byte-identical in both language files).

**Where I disagree with the review.**
1. The review's prose bullet ("Both printed values equal the *sample* sd") is **contradicted by the
   review's own A3 table**, which marks every row "pop ✓", and by the numbers above: CS σm@1 prints 0.007,
   which is ddof=0 (0.006966), not ddof=1 (0.008603); CS top-1@10 prints 1.3, which is ddof=0 (1.2893),
   not ddof=1 (1.5790). Its "neither" verdict on BM σm@1 (0.001) is a rounding artefact — 0.001400 → 0.001.
2. Consequently the caption clause "**(the convention used throughout this paper)**" was **not deleted**:
   it is accurate for this table, and I re-verified it for the two comparison tables it is measured against —
   `tab:peft` (`outputs/ocean_peft_ms.json`, three seeds) reproduces under ddof=0 in every cell where ddof=0
   and ddof=1 differ at the printed precision (R1 sd 0.0542 vs 0.0664 → prints 0.054; top-1 sd 1.317 vs 1.614
   → prints 1.32; 0.711 vs 0.871 → prints 0.71), and `tab:sonar-peft` does too (τ 0.01557 vs 0.01907 → prints
   0.016; top-1 36.05 vs 44.15 → prints 36.1).
3. Round 2's instruction to change τ@10 to **0.137** is confirmed wrong and was **not** applied: 0.137 is
   the *sample* sd; the printed 0.112 is the population sd the caption declares.

### 1.4 — Abstract texture/image asymmetry: scoped to taxonomy-text adaptation

*Evidence* — `outputs/ocean_replica.json :: marine.tau_text1 0.2781` − `:: marine.rows[5].tau_meas 0.2174`
= **+0.0607 → +0.061** (matches `tab:replica`, and the review's own arithmetic).

| file:line | before → after |
|---|---|
| `main.tex:32` (abstract) | "…and **removes the protective text/image asymmetry**." → "…and **for taxonomy-text adaptation removes** the protective text/image asymmetry (**kept by a natural-text fine-tune, Δτ +0.061**)." |
| `main_zh.tex:37` | mirrored (…且对分类学文本适配而言消除了…（自然文本微调则保留之，Δτ +0.061）) |

`main.tex:585–588` (§3.7) already stated the correction correctly and was left unchanged.

### 1.5 — Introduction no longer pre-commits its conclusion

*Evidence* — the only non-optical evidence is one acoustic backbone family (frozen CLIP ViT-B/32 → SonarCLIP
+ seeds) on NKSID and three replication instruments, one of which (UATD) failed; `main.tex:756` already
declares the side-scan set exhausted.

| file:line | before → after |
|---|---|
| `main.tex:48` | "…the alignment-health laws **are modality-general and should be assumed to structure any future non-optical contrastive model** (side-scan, LiDAR, polarimetric)." → "…the alignment-health laws **transfer to at least one non-optical channel with the same precision; whether they generalise further—to other non-optical contrastive models (side-scan, LiDAR, polarimetric)—remains a hypothesis this study cannot test, because our evidence comes from a single acoustic backbone family.**" |
| `main.tex:766` (conclusions) | "…and **should be assumed to structure future non-optical contrastive models**." → "…and **is expected to transfer to further non-optical contrastive models—though our evidence covers one acoustic backbone family, and side-scan, LiDAR and polarimetric data were not tested.**" |
| `main_zh.tex:49, 654` | mirrored |

---

## 2. SHOULD-FIX (B-list)

| # | status | change |
|---|---|---|
| **B1** | done | `main.tex:32`: "full fine-tuning destroys it (**−15% to −62% in the marine domain**)"; `highlights.tex:12` "destroys it **there**"; `highlights.docx` bullet 3 likewise; `main_zh.tex:37` mirrored. Numbers unchanged (`tab:peft`), scoping only. |
| **B2** | done | `main.tex:32`: "in a domain-specific, **saturating** way (3.6× marine, 1.8×–3.8× sonar vs 1.1× terrestrial)" → "domain-specifically, **saturating with dose but modulated by data scale (3.6× marine; sonar 3.8× at 650 images vs 1.8× at 2,617; 1.1× terrestrial)**". `cover_letter.tex:26` and `main_zh.tex:37` mirrored. JSON: `sonar_protocol.json :: {clip_frozen,sonar_ft}.sigma_m` 0.0239/0.0063 (3.79×), `sonar_protocol_full.json :: {clip_frozen,sonar_ft_full}.sigma_m` 0.0247/0.0136 (1.82×), terrestrial 0.0222 (1.11×). |
| **B3** | done (caption only — not in the task list) | `main.tex:274` caption rewritten to describe panel (a) as CLIP frozen vs SonarCLIP under the balanced-650 and full-2,617 protocols with the actual values (0.0239→0.0063, 0.0247→0.0136) and panel (b) as the matched-scale ratios (3.8×/1.8×/1.1×). `main_zh.tex:273` mirrored. **Residual not fixed**: the figure PNG still carries a stray "+ Flickr" legend entry with no bar in panel (a); removing it requires regenerating `figures/fig7_sonar_sigma.png` via `tools/clip_a2_fig7.py`, and I did not regenerate archived figures. |
| **B4** | done, with the review's prescription corrected | `main.tex:417` caption → "Bold marks the violations … **that fall inside this selected-λ subset** (OceanCLIP, λ=2; SigLIP, λ=1); **seven of the 32 grid cells violate it in total** (BioCLIP λ=−1,−0.5,−0.25; OceanCLIP λ=2; OpenCLIP λ=2; SigLIP λ=1,2), all listed in the text." `main_zh.tex:415` mirrored. **The review's proposed wording was wrong**: only 8 data rows are printed (BioCLIP 0.5/1/2, OceanCLIP 0.5/1/2, OpenCLIP 1, SigLIP 1) and exactly 2 of them are violations (verified from `outputs/ocean_rank1_bound.json :: {model}.rows[λ].{exact,corr_gauss}`: 7 violations over 32 cells — SigLIP λ=2 (+0.1320), SigLIP λ=1 (+0.0898), BioCLIP λ=−1 (+0.0606), OceanCLIP λ=2 (+0.0382), BioCLIP λ=−0.5 (+0.0340), OpenCLIP λ=2 (+0.0173), BioCLIP λ=−0.25 (+0.0080)). The other five cells **are not in the table and cannot be bolded**. |
| **B5** | done | `ext_partIV_degradation.tex:45`: "the two **optical** rows per domain are the two haze levels" → "the two **haze** rows per optical domain are the two haze levels (…), the remaining three optical rows per domain being shadow and speckle at 20% and 40%". `zh_ext_partIV_degradation.tex:39` mirrored. |
| **B6** | done | `ext_partIV_degradation.tex:32` caption: "|λ_eff| ≤ **0.11**" → "|λ_eff| ≤ **0.111** (unrounded maximum **0.1108**, marine-67 speckle 40%)". JSON: `degradation_matrix.json :: marine_bioclip.rows[4].lam_eff 0.1108`, and max over all rows = 0.1108. `zh_ext_partIV_degradation.tex:30` mirrored. The printed cell 0.111 was already correct and is unchanged. |
| **B7** | done — **claim kept, provenance recorded** | `main.tex:744` caption: "2,000-fold bootstrap over points" → "2,000-fold bootstrap over points**—the replicate count defined by `boot}(n=2000)` in `tools/clip_threshold_calibration.py`, the archived CI intervals being those the result JSON stores**". Verified myself: `tools/clip_threshold_calibration.py:69` is `def boot(cut, thr, n=2000)`. Also added the missing bracket the caption promises: `τ≥0.8 / retention≥83%` specificity "1.000" → "**1.000 [1.0, 1.0]**" (JSON `threshold_calibration.json :: cutoffs.ret_ge_0.83["0.8"].{spec_lo,spec_hi}` = 1.0, 1.0). `main_zh.tex:629, 634` mirrored. |
| **B8** | done | Reconciled at four places: `main.tex:631` "the τ>0.8 band" → "the τ>0.8 band, **read at the deployment-matched λ**"; `main.tex:719` (`tab:eng`) "τ@λ=1 (predicted vs measured); σ_m | τ≥0.8 safe" → "**τ at the deployment-matched λ**; σ_m | **τ≥0.8 at λ∈{0.25,0.5}; τ@λ=1 is a stress column, not a pass/fail gate**"; the reference-implementation snippet (`main.tex:647–650`) now checks `tau_pred[lam_deploy]` with `lam_deploy = 0.5` instead of `tau_pred[1.0]`; `ext_partV_mechanisms.tex:110` protocol step likewise; conclusions "band ≥0.8" → "band ≥0.8, **read at the deployment-matched λ**". JSON for the failing model: `ocean_nsweep.json :: oceanclip["67"].tau_meas_1 0.4539` (retention 96.7%), vs the band's own λ∈{0.25,0.5} operating points (τ 0.81–0.89). `main_zh.tex` and `zh_ext_partV_mechanisms.tex:71` mirrored. |
| **B9** | done | `main.tex:754`: (i) "**un used**" → "**unused**"; (ii) "FathomNet's API **is retired**" → "**FathomNet's signed-URL frames require credentials (the API itself is functional at database.fathomnet.org, Appendix B)**" — matching `main.tex:810`; (iii) the co-training clause split: "the remaining open validation is MarineGPT-scale (7B+) instruction tuning and co-trained bilingual branches" → "…is MarineGPT-scale (7B+) instruction tuning; **the co-trained (branch-sharing) objective is likewise still open, the measured negative of §3.7 showing that a shared objective does not transfer taxonomic organization to held-out classes**" (curriculum question stays settled in limitation 1). `main_zh.tex:647` mirrored. Co-training numbers untouched and re-verified. |
| **B10** | done | `ext_partIV_degradation.tex:83`: "at subspace dimension **k=1,2,3** … the next **two** are orthogonalized principal components" → "**k=1,…,5** … the next **four**". `zh_ext_partIV_degradation.tex:52` mirrored. JSON: `direction_subspace.json :: {domain}[i]` carries `err_k1…err_k5`. |
| **B11** | done | `ext_partIII_dynamics.tex:69`: "exact to 7×10⁻⁴ at λ=1 on the frozen baseline" → "…**at λ=1** on the frozen baseline, **3×10⁻³ worst-case over the six-λ grid**". JSON: `vlm_instruction_dynamics.json :: frozen.rows[*]` — λ=1 Δ0.0007, worst λ=−1 Δ0.0030. `zh_ext_partIII_dynamics.tex:40` mirrored. |
| **B12** | done | `main.tex:464` caption: "(**3,440 queries**, 427 videos; …)" → "(**3,440 queries over 3,416 frames**, 427 videos; …)". JSON: `ocean_ml16k_retrieval.json :: meta.{n_queries 3440, n_frames 3416}`. `main_zh.tex:462` mirrored. |

### Compliance items

- **Abstract abbreviations**: `main.tex:32` now expands both — "**top-1 (correct-class) loss bounds**" and
  "**parameter-efficient fine-tuning (PEFT)**" (previously PEFT was expanded only at `main.tex:75`, in §1.2).
  `main_zh.tex:37` mirrored.
- **`qwen2vl2024` uncited**: cited at its first substantive mention, `ext_partIII_dynamics.tex:65`
  ("(Qwen2-VL-2B \citep{qwen2vl2024}, text-only; …)"), mirrored at `zh_ext_partIII_dynamics.tex:40`.
  *Note*: I cited it there rather than at `main.tex:754` — that line contains no Qwen mention (the review's
  pointer was to the Limitations paragraph), and `ext_partIII_dynamics.tex` is `\input` at `main.tex:620`,
  i.e. it is where the model is actually used and first appears. Result: **28/28 bibitems cited in both
  builds** (aux-verified), no uncited and no missing entries.
- **`radford2021` in the mirror**: added at `main_zh.tex:92` ("该家族源自对比视觉--语言预训练（CLIP 式）\cite{radford2021}"),
  matching `main.tex:93`.
- **Repository-side metadata deviations — noted, JSONs NOT edited** (as instructed):
  1. `outputs/dynamics_fathomnet.json :: meta.dataset` says "8 concepts × 30" while `:: meta.classes` has
     6 entries and `:: meta.n` = 144 = 6×24. Noted in `ext_partIII_dynamics.tex:123` and
     `main_zh.tex:105` / `zh_ext_partIII_dynamics.tex:38`: the label is stale, the operative fields are
     `meta.classes` and `meta.n`, and those are what the paper reports.
  2. The `tab:sonar-sigma` balanced row is archived in `sonar_protocol.json` / `sonar_spectrum.json`, not in
     `mechanism_summary.sources.sonar` (which holds only the full-protocol triple —
     `clip_frozen 0.0247 / sonar_ft_full 0.0136 / clip_flickrft 0.0222`). Noted in the `tab:sonar-sigma`
     caption, `main.tex:249`, and `main_zh.tex:248`.

---

## 3. Additional cheap, clearly-correct items I fixed (C-list, beyond the task's B-list)

| item | change |
|---|---|
| **C3** | `ext_partV_mechanisms.tex:48` "each **check point** keeps" → "each **checkpoint** keeps". (The ZH already used 检查点.) |
| **C4** | "un used" → "unused" (folded into B9). |
| **C8** (carried over from Round 1) | `ext_partIII_dynamics.tex:54` and `zh_ext_partIII_dynamics.tex:32`: "τ drops from 1 to **0.13–0.67**" → "**0.17–0.67**". The six archived direction–seed pairs span 0.17–0.67 (`bio_marine_s0[0].tau 0.1867`, `bio_marine_s1[0] 0.1715`, `ocean_tautraj.marine[0] 0.1765`, `clip_sonar[0] 0.2757`, `clip_sonar_s0[0] 0.36`, `clip_sonar_s1[0] 0.6729`); 0.13 is the deliberately excluded collapsed seed, which the next clause already reports separately. |
| **C9** | `ext_partIII_dynamics.tex:71–73` and `zh_ext_partIII_dynamics.tex:40`: Qwen τ range "0.93–0.97" → "**0.926–0.968**" (`vlm_instruction_dynamics.json :: traj[*].tau_l1` spans 0.926…0.9682), and "settles near 0.075" → "settles near **0.0755 at epoch 10**" (`:: traj[9].sigma_m 0.0755`). |
| **B3 caption** | see B3 row above. |

### Items I skipped, and why

- **C1** (residual-fraction ranking silently changes domain: `main.tex:424`: "speckle 0.70 < blur 0.81 < shadow 0.90 < marine haze/colour cast 0.94–0.95") — hygiene only, not on the task list, and the fix is a wording choice ("sonar speckle … sonar shadow … marine …") best made by the author in one pass with C2.
- **C2** (prose prints τ to 3 dp as 0.18/0.07 vs the table's 0.177/0.069; `main.tex:632`) — cosmetic digit alignment; `outputs/ocean_tautraj.json :: marine[0].{tau 0.1765, top1 58.396}` confirms the table, so the prose is not *wrong*, merely less precise. Left for author copy-editing.
- **C5** (`ext_partI_theory.tex:187`, `tab:theory-stack` claims validation "9/9 ≤0.002" while `a1_theory_verify.json :: predicted_tau_orthogonal` vs `:: measured_tau_orthogonal` gives a worst case of 0.0624) — **deliberately not touched**: changing a table cell is a substantive claim decision (the cell may name a different quantity, in which case it must be *named*), not copy-editing, and it is outside the task's list. **Flagged for the author.**
- **C6** (`main.tex:86`/`main_zh.tex:84` "only NKSID was retrievable" vs four datasets acquired later) — the review's own fix is an editorial framing choice ("as of the first acquisition attempt (2026-08)") that touches the §2.5 narrative; not applied.
- **C7** (name `a1_theory_verify.json` explicitly in §A.2) — the review itself grades this "hygiene only: no contradiction found".
- **B3's figure-side defect** (stray "+ Flickr" legend entry with no bar) — needs `figures/fig7_sonar_sigma.png` regenerated; I did not regenerate archived figures.

---

## 4. Chinese mirror sync (`main_zh.tex` + `zh_ext_part*.tex`)

Every English change above was mirrored. In addition, the four mirror divergences named in the review were fixed:

| divergence | fix |
|---|---|
| (a) extra Introduction paragraph with no English counterpart | `main_zh.tex:47` — replaced with a translation of EN `main.tex:50`; the unmatched extra claim ("本文将诊断带入海洋领域，并在此过程中发现海洋模型并非"类目更小的 ImageNet"——它们具有可测的不同、且可以说更有利的对齐几何") was removed |
| (b) divergent conclusions clause | after the A1/A2/A5 sync, the ZH conclusions carry the same "narrowing the remaining modality risk to class-set scale and composition" clause as the EN; verified equivalent |
| (c) date | `main_zh.tex:22` 2026 年 9 月 2 日 → **2026 年 9 月 14 日** (matches `main.tex` + `cover_letter.tex`) |
| (d) `radford2021` uncited | cited at `main_zh.tex:92` |

ZH edits by file: `main_zh.tex` 22, 37, 47, 49, 53, 92, 105, 169, 176, 248, 249(EN-side), 415, 462, 530, 545,
611, 613, 629, 634, 645, 647, 654, 273; `zh_ext_partII_domains.tex:45`;
`zh_ext_partIII_dynamics.tex:32, 38, 40`; `zh_ext_partIV_degradation.tex:30, 39, 52`;
`zh_ext_partV_mechanisms.tex:71`.

**Numeric fidelity re-check** (token-level diff of every numeric token in the six EN files vs the six ZH
files, after stripping LaTeX): the five extension-file pairs have **zero** asymmetric numeric tokens
(EN-only = none, ZH-only = none in every pair); `main.tex` has one asymmetric token, `17`, which is the
documented `4.17` / `17.33` `{,}`-separator tokenisation artefact the review also found, plus
reference-list DOI/host fragments caused by `\href{...}{doi:...}` vs `https://doi.org/...` formatting.
Totals: 2,656 EN / 2,705 ZH numeric tokens.

---

## 5. Compile results (final, after all edits)

| build | command | exit codes | pages | errors (`!`) | undefined refs/cites | `LaTeX Warning` | Overfull hbox | bibcite |
|---|---|---|---|---|---|---|---|---|
| English | `pdflatex -interaction=nonstopmode main.tex` ×2 | **0, 0** | **65** (`Output written on main.pdf (65 pages, 1503254 bytes)`) | **0** | **0** | **0** | 5 (≤18.8 pt, unchanged) | **28/28** |
| Chinese | `xelatex -interaction=nonstopmode main_zh.tex` ×2 | **0, 0** | **45** (`Output written on main_zh.pdf (45 pages)`) | **0** | **0** | **0** | 0 | **28/28** |
| Cover letter | `pdflatex cover_letter.tex` | **0** | 2 | 0 | — | 0 | — | — |
| Highlights | `pdflatex highlights.tex` | **0** | 1 | 0 | — | 0 | — | — |

Citation coverage is aux-verified (28 unique `\citation` keys = 28 `\bibitem`s in each language; no uncited,
no missing). The single remaining `undefined` string in the ZH log is the cosmetic
`Font shape TU/SimSun(0)/b/it undefined` warning the review also recorded.

**Page growth**: English 62 → **65**, Chinese 43 → **45**. This is the cost of the added 38-vs-42 count
explanation (three sentences), the expanded captions, and the new qualifications. The journal sets **no word
limit for research papers** (review §3 item 18), and `elsarticle[review]` double-spacing is retained.

---

## 6. Files changed

Manuscript (12): `paper_a2/main.tex`, `main_zh.tex`, `ext_partII_domains.tex`, `ext_partIII_dynamics.tex`,
`ext_partIV_degradation.tex`, `ext_partV_mechanisms.tex`, `zh_ext_partII_domains.tex`,
`zh_ext_partIII_dynamics.tex`, `zh_ext_partIV_degradation.tex`, `zh_ext_partV_mechanisms.tex`,
`cover_letter.tex`, `highlights.tex`, plus the binary `highlights.docx` (bullets 1 and 3 replaced in
`word/document.xml` via zipfile; zip integrity verified, 5 paragraphs, max 78 characters).

Regenerated build artefacts: `main.pdf`, `main.aux`, `main.log`, `main_zh.pdf`, `main_zh.aux`, `main_zh.log`,
`cover_letter.pdf`, `highlights.pdf`.

**Not changed**: `ext_partI_theory.tex`, `zh_ext_partI_theory.tex` (no required edit), `figures/*.png`
(no figure regenerated), and **everything under `outputs/`**.
