# A1 — Adversarial Methodology Review (hostile referee report)

**Manuscript:** `paper_a1/main.tex` (653 lines) + `paper_a1/related_work.tex` (398 lines)
**Review date:** 2026-10-11
**Stance:** hostile but competent — every attack below is anchored to a line number in the manuscript and, where the manuscript cites an archive, checked against that archive in `outputs/`.
**Method note:** all quantitative re-checks were recomputed from `outputs/a1_*.json` with scipy (`spearmanr`, `pearsonr`, `t` intervals) in this session. Where I could not find a source for a claim, I say so explicitly.

---

## Executive summary — the eight attacks that can sink this paper

| # | Attack | Severity |
|---|---|---|
| **A1** | **The load-bearing predictive claim is contradicted by the paper's own checkpoint data.** Across the 7 real checkpoints used in §4.10 the cross-checkpoint Spearman is +0.786, but **within** each dataset group it is **−0.5** (COCO), **−0.5** (Food-101) — i.e. τ and accuracy are *anti*-correlated inside the only real adaptation setting the paper has. The pooled +0.786 is a between-group (dataset-difficulty) artefact. | **Fatal** |
| **A2** | **"τ predicts" is never tested out-of-sample except once, and there it explains ~37%.** The only held-out test is leave-one-family-out on 28 conditions; CLIP R²=0.371 (n=20), SigLIP R²=0.378 (n=4), **OpenCLIP R² negative (fails an R²>0 success criterion)**. Everything else (ρ=0.9125, k-ablation, 5-seed sweep, 34-condition plane) is in-sample correlation. | **Fatal** |
| **A3** | **The "theory" has no free parameter and no failure mode.** τ(λ) is proved to be an *identity* from the frozen model (§3.5.2, line 216), and the four-benchmark confirmation (line 438) stores `tau` and `tau_pred_exact` as *literally identical numbers*. The paper concedes this for r=1.000 and then uses the same non-test as "three things replicate" elsewhere. | **Severe** |
| **A4** | **Retrieval does not track the gap in this paper's own retrieval data.** Body claim (line 57) and Fig. 4 caption (line 361): "retrieval tracks the gap". Over the paper's own 20-condition 50k grid, Spearman(CG, R@1) = **−0.389**, and over the forward branch (λ≥0, n=14) it is **−0.002**. R@1 falls most steeply while the gap is *shrinking*. | **Severe** |
| **A5** | **Four incompatible λ grids, and Eq. (1) — the only definition — matches none of them.** Eq. (1) (line 70) defines λ ∈ {−2,−1,−0.5,0,0.25,0.5,1,2,4}; Table 3 (lines 199–202) uses λ ∈ {−2,−1,−0.5,−0.25,0.25,0.5,1,2,4} (no λ=0, adds −0.25); the 26-condition grid uses λ ∈ {−1,−0.5,0.25,0.5,1,2,4}. | **Severe** |
| **A6** | **Three independent runs of the same condition disagree by more than the paper's stated closure residual.** At λ=+0.5 the certified grid gives τ = 0.4625, the dose–response run 0.46563, the closure archive's "measured" column 0.4617 — spread 0.004 = 2.1× the claimed residual (0.0019); and §4.3's Table 1 prints **0.465** for the condition §3.5.2's Table 3 prints as **0.462**. Separately, the Abstract's "matches measurement to four decimals" is wrong by an order of magnitude (max residual 0.0019 = third decimal). | **Moderate–severe** |
| **A7** | **τ cannot separate the two branches of the one perturbation family it is supposed to govern.** At τ ≈ 0.48 the gap-widening branch gives top-1 = 29.48% and the gap-shrinking branch 47.48% — an 18-point gap at equal τ, and the within-family Spearman is 0.750, not 1.000. §4.9 reports the sign-blindness as a *feature* of the monitor while §3.3.1 claims monotonicity within class-agnostic families. | **Severe** |
| **A8** | **"Centroid contraction" names two different operations with opposite effects** (global-mean, which the archive shows *increasing* the gap and costing 14.5 points at a=0.5; and per-class-centroid, which gains 19 points), and the paper never distinguishes or names them, nor reconciles the Setup formula with the reported direction of the CG change. | **Severe** |

---

## 1. The two prior reviewer objections (a) and (b), and whether the response is adequate

### 1(a) "The τ–accuracy relationship is partly definitional"

**Where the paper answers.** §3.6.2 "τ and accuracy are not the same object" (lines 241–246) and Related Work §rw-scope (lines 369–373). Verbatim, line 244:

> "It is natural to ask whether the τ–accuracy relation holds partly by definition, since zero-shot prediction is an argmax over similarity ranks. The two quantities are computed on different objects, and our own tables show it. τ is the mean Kendall coefficient between frozen and perturbed ranks *within each image's frozen top-5 set* (5 of the 1,000 ImageNet classes), while accuracy is a full 1,000-way argmax. A statistic over a frozen 5-class neighbourhood and a 1,000-way decision cannot be the same quantity, and the counterexample of Section 3.7.1 (τ=0.615 with 78.6%, τ=0.761 with 58.8%) is a direct demonstration that neither one implies the other across mechanisms."

and line 244 again, the two "further facts":

> "Two further facts make the relation informative rather than tautological: the closed form of Section 3.5.1 *computes* τ(λ) from frozen margins with no free parameters (maximum error 0.0019), and a τ-based predictor fitted on the other model families still has positive held-out R² on a family it has never seen (0.371 for CLIP, 0.378 for SigLIP; pooled Spearman 0.927), which a restatement of accuracy could not achieve."

**Verdict: adequate as a rebuttal of *strict* definitional identity; inadequate as a defence of the paper's actual claim.**

Three reasons, in increasing order of severity:

1. The "different objects" argument is a *category* argument, not an empirical one. It establishes only that τ and top-1 are not literally the same functional. Nobody claimed they were. The real objection is that **accuracy under a class-agnostic perturbation is a monotone function of perturbation magnitude, and τ is also a monotone function of perturbation magnitude, so any monotone statistic of the perturbation will "predict" accuracy identically on these grids.** The paper never runs the obvious control: does *any* smooth monotone quantity (‖δ‖, λ itself, mean embedding cosine) achieve the same ρ? It does report mean cosine (0.862) and CKA (0.755) — but not ‖λ‖ itself, which is the strongest rival and is trivially available.
2. The second "further fact" — the closed form — is **not independent of the objection**: the paper proves in §3.5.2 (line 216) that the pair-inversion criterion is an *exact equivalence*, and in §3.5.4 (line 225) that the prediction and the measurement are functions of the same frozen array. A quantity that is an exact identity cannot arbitrate between "τ governs accuracy" and "τ is a restatement of perturbation magnitude."
3. The held-out R² of 0.371/0.378 is the one genuinely independent number, and it is weak (§2 below).

### 1(b) "The paper contradicts itself: Gaussian τ=0.761→58.8% but class contraction τ=0.615→78.6%"

**Where the paper answers.** §3.3.1 "τ is necessary, not sufficient, across intervention families" (lines 152–157); §4.4 (line 128); Table 1 caption (line 135); Abstract (line 33); Discussion Limitation (a) (line 574); Related Work "What we do not claim" (i) (lines 362–368). Verbatim, line 155:

> "Table 1 contains cases in which the lower τ carries the higher accuracy, and we treat them as decisive for the interpretation of τ rather than as an anomaly. On the same 5,000-image sample, an isotropic Gaussian field at σ=0.25 leaves top-1 at 58.8% with τ=0.761, whereas a class-conditional contraction at a=0.5 reaches 78.6% with τ=0.615; the near-equal-τ pair is sharper still (τ=0.761 at 58.8% against τ=0.760 at 70.3%). τ is therefore not a sufficient statistic for zero-shot accuracy across mechanisms, and we do not present it as one."

and line 157:

> "Contraction therefore changes the argmax *without* preserving the frozen ordering: it is a second, structurally different route to accuracy, and τ—defined against frozen ranks—is not the appropriate reference for it."

**Verdict: this is a genuine concession, not a restatement — the contradiction is resolved by restricting the claim to "class-agnostic" families. But the restriction destroys most of the paper's evidential base, and the paper does not say so.**

The concession is real: the paper explicitly narrows to "along the destruction direction... for perturbations that carry no class information" (line 155) and repeats the narrowing in the Abstract and Conclusion. But:

**(i) The retained claim is nearly vacuous as a scientific claim.** The retained content is: *among perturbations that carry no class information, accuracy cannot survive order destruction, and the response is monotone within each family.* On the paper's own certified 26-condition grid, the within-family Spearman(τ, top-1) is **1.000 for the Gaussian family, 1.000 for the global low-rank family, 1.000 for the orthogonal family, and 1.000 for the C/centroid family** (recomputed from `outputs/a1_h_baseline_metrics.json::conditions[*]`). Perfect within-family monotonicity in *five* one-parameter families is what you get from any smooth degradation curve; it is not evidence that τ is the governing quantity. The claim "accuracy cannot survive order destruction" is likewise near-analytic: with τ ≤ 0 the frozen top-1 is not the argmax any more by construction.

**(ii) One within-family correlation in the paper's own grid is *not* 1.000, and it is the family the paper cares most about.** The translation family (n=7 in the certified grid) has Spearman(τ, top-1) = **0.750**, not 1.000 (computed from the same archive). The reason is visible in the paper's own grid: at τ ≈ 0.48–0.49 the *gap-widening* branch gives top-1 **29.48%** while the *gap-shrinking* branch gives **47.48%** — an 18-point difference at essentially equal τ. §4.9 (line 524) even reports the sign-dependent failure as a *feature* of the monitor ("a single level separates neither severity nor direction", line 524). A referee will read these two sections together and ask the obvious question: **if τ cannot distinguish a 29.5% condition from a 47.5% condition that differ only in the sign of a perturbation, in what sense does τ "govern" top-1?** The manuscript never confronts its own sign-dependence with its own governance claim. This is the single strongest internal attack in the paper and it is not currently rebutted anywhere.

**(iii) The "necessary, not sufficient" framing silently deletes the failure mode most damaging to the paper.** Under the narrowed claim, τ is only claimed to be informative for *synthetic class-agnostic perturbation families*. But the paper's actual recommendation ("τ is a zero-overhead training-time monitor for classification-oriented fine-tuning", Abstract and Highlights) concerns *fine-tuned checkpoints*. In that setting the paper itself reports the within-dataset correlations **−0.5, −0.5, +1.0** (Table 12 caption/columns; line 528, line 574(c)). So the concession in (b) is granted on synthetic perturbations, while the recommendation is made for real adaptation — where the paper's own numbers say τ does not order runs. **The paper concedes the counterexample but not its scope.**

---

## 2. Is τ predictive, or a restatement? (Evidence audit)

**Short answer: it is a restatement within families; outside families the only test is one leave-one-family-out fit that explains 37% of variance and fails outright for one of the three families.**

### 2.1 What the paper reports as its predictive evidence

| Evidence | Location | What it actually tests |
|---|---|---|
| ρ(τ, top-1) = 0.9125, p=8.5e-11, n=26 | line 185, Table 4 | **In-sample** correlation over the 26-condition grid the τ definition was tuned on |
| k-ablation, ρ stays in 0.9125–0.9357 for k∈{3..100} | lines 264–268, Table 4 | **In-sample**, same 26 conditions |
| 5-seed stability, τ = 0.9167±0.0064 | line 295, Table 5 | **In-sample**; measures re-draw stability, not out-of-sample prediction |
| 34-condition plane | Fig. 2 (line 122) | **Explicitly non-quantitative**: "we use it only for the qualitative τ–accuracy relation" (line 76) |
| Cross-family hold-out | lines 227, 239, 244 | **First genuine held-out test**: LOO over 3 families, 28 conditions |
| Checkpoint contrasts | lines 473, 528 | Cross-checkpoint, mostly **in-sample**; and see §3.1 below |

### 2.2 The cross-family hold-out, quoted exactly (line 239)

> "We therefore held out an entire *model family* and fitted the predictor on the remaining families: across the 28 archived conditions (CLIP 20, OpenCLIP 4, SigLIP 4), a τ-based predictor retains positive held-out R² for CLIP (0.371) and SigLIP (0.378) and ranks all conditions correctly overall (Spearman ρ=0.927, p=1.4×10⁻¹²), whereas a Centroid-Gap-based predictor is worse than the mean in every fold (R²=−1.13 to −1.52; overall ρ=−0.251, p=0.20)."

and the paper's own caveat (line 239):

> "Two caveats belong with these numbers: the folds are very unequal (n_test=20 for CLIP against 4 for OpenCLIP and SigLIP), so the negative OpenCLIP R² is a small-sample artefact rather than a failure of the predictor, and the pooled Spearman (0.927, n=28) is the primary summary."

**Why this does not survive review:**

1. **One of three folds fails an R²>0 success criterion and is excused by fiat.** "Small-sample artefact rather than a failure of the predictor" is an assertion with no supporting analysis: no confidence interval on the OpenCLIP R², no permutation null, no simulation showing that n=4 produces negative R² under a correctly specified model. A hostile referee treats an unanalysed failure in 1 of 3 folds, on the family that most differs in pretraining data, as a failure.
2. **The pooled Spearman of 0.927 is not a held-out statistic.** It is the rank correlation between τ and top-1 computed *across all 28 conditions without any fitting*. Because each family internally traces a monotone τ→accuracy curve, and because the families sit at very different baselines (frozen top-1 59.28 / 62.51 / 73.15), any monotone within-family signal plus any between-family baseline offset produces a high pooled rank correlation. **The pooled ρ cannot distinguish "τ transfers across families" from "families have different accuracies and different τ scales."** The paper's own text concedes the mapping is "family-calibrated" (line 239) — if it is family-calibrated, the pooled ρ is measuring the calibration, not the mechanism.
3. **R²=0.371 means 63% of held-out variance is unexplained**, on n=20 test points, and the paper's own Conclusion concedes this: "Because the cross-family mapping is family-calibrated (R² 0.371/0.378 with pooled Spearman 0.927), we recommend τ as an *ordering* proxy rather than as a calibrated accuracy predictor" (line 579). An "ordering proxy" whose hold-out R² is 0.37 and which is anti-correlated within every real-checkpoint dataset (§3) is not a monitor.
4. **The one control that would settle it is absent.** A like-for-like baseline — hold-out R² for ‖δ‖, for λ, for mean cosine, for CKA, all on the same 28 conditions and same LOO split — is never reported. Only the Centroid Gap is used as a foil, and the Centroid Gap is known by construction to be non-monotone in λ (the paper says so itself, line 97: "the gap is non-monotonic in λ"). Beating a deliberately non-monotone baseline in a monotone-perturbation grid is not evidence.
5. **Nothing is held out at the level the recommendation is made.** The recommendation is about *fine-tuned checkpoints* ("zero-overhead training-time monitor"). No predictor is fitted on synthetic conditions and tested on held-out checkpoints, or fitted on some checkpoints and tested on others — except the cross-dataset contrast, which §3 dismantles.

**Verdict on Q2: not convincing.** The paper demonstrates correlation within settings it measured, plus one weak cross-family fit whose strongest fold fails. It does not demonstrate predictive power in the sense the Abstract and Conclusion assert ("top-1 is governed by τ", line 33; "accuracy is governed by the order-preservation coefficient τ", line 579).

---

## 3. The r = 1.000 claim: is the downgrade sufficient?

### 3.1 Every occurrence of the r = 1.000 result in the load-bearing artefacts

| # | Location | Verbatim |
|---|---|---|
| 1 | **Abstract**, line 33 | "A first-order class-dependent bias field matches measurement to four decimals ($r{=}1.000$; self-consistency, not independent validation) and predicts less text-side than image-side destruction." |
| 2 | **Analysis**, line 97 | "It is a first-order device for *interpreting* the bias field and for score *magnitudes*—including the $r=1.000$ agreement quoted in Section 3.5, which we treat as a self-consistency check of the closed form rather than as independent validation (Section 3.5.4)." |
| 3 | **Mechanism, first sentence of the section**, line 167 | "The analysis of Section 3 makes two quantitative predictions, both verified. First, the per-class score shift under a gap-direction translation should equal $\lambda\|g\|\,m_c$: the measured mean per-class shifts at $\lambda=1$ match the prediction with Pearson $r=1.000$ ($\mathrm{std}(m_c)=0.067$)." |
| 4 | **§3.5.3 first-order discussion**, line 218 | "The per-class shift agreement quoted in Section 3.5 ($r=1.000$ against $\lambda\|g\|m_c$, with $\mathrm{std}(m_c)=0.0673$) belongs to this second class, not to the ordering result: it is a first-order magnitude statement, taken as a mean over images, and we label it as such rather than presenting it as independent validation." |
| 5 | **§3.5.4 heading**, line 222 | "The $r=1.000$ agreement is a self-consistency check, not independent validation" |
| 6 | **§3.5.4 body**, line 225 | "A correlation of exactly $1.000$ between predicted and measured τ is anomalous as evidence, and we do not present it as validation. … We therefore label it a *self-consistency check of the implementation*, report it with the residual rather than the correlation alone, and state explicitly that it is not evidence of generalisation." |
| 7 | **Multi-seed stability**, line 284 | "the bias-field Pearson is $1.0000$ to four decimals in every seed, not exactly $1$ (stored mean $0.9999917$, $\mathrm{sd}=5.5\times10^{-7}$)" |
| 8 | **Related Work, "What we claim" (iii)**, `related_work.tex` line 353 | "(iii) The effect has a first-order mechanism—a class-dependent bias field—which accounts for the translation response and explains why image-side and text-side translations differ in destructiveness" |
| 9 | **Highlights**, `highlights.tex` line 14 | "First-order bias-field theory matches measurements with r = 1.000" |
| 10 | **Cover letter**, `cover_letter.tex` line 64 | "decimal places ($r=1.000$; this is a self-consistency check of the closed form, not …" |
| 11 | **Standalone abstract**, `abstract.tex` line 32 | "A first-order analysis yields a class-dependent bias field whose per-class score prediction matches measurement to four decimals ($r{=}1.000$; a self-consistency check of the closed form, not independent validation)" |

### 3.2 Is the downgrade sufficient? **No — it is insufficient in three distinct ways.**

**(i) Three artefacts still sell it as a result, not as a check.**

- **`highlights.tex` line 14 is unhedged**: "First-order bias-field theory matches measurements with r = 1.000". This is the single most-read line of the submission (Elsevier highlights are displayed verbatim in the table of contents) and it contains **no hedge at all** — no "self-consistency", no "closed form", no residual. The manuscript body's careful nine-fold hedging is contradicted by its own submitted highlights file.
- **§3.5 opens with "two quantitative predictions, both verified" (line 167) and only then concedes the first is not a test.** The sentence order does the work: a reader who stops after the first clause has read a claim of verification. The concession follows in the same paragraph, but the *rhetorical* claim precedes it.
- **The Conclusion (line 579) cites the mechanism as established** — "the kind trained adaptation produces" / "Class-aligned perturbations … raise accuracy while lowering τ" — and `related_work.tex` line 353 lists the bias field under "What we claim" as something that "accounts for the translation response", without the self-consistency caveat. The caveat lives in the body; the claim lives in the claim-list.

**(ii) The residual is honestly reported, but the "four decimals" wording is wrong by an order of magnitude.** I checked `outputs/a1_tau_holdout.json::theory_vs_measured_tau.predicted_tau_exact_vs_measured_tau_5k` element by element: predicted 0.2020 / 0.3310 / 0.4935 / 0.6545 / 0.6362 / 0.4628 / 0.2898 / 0.1559 / 0.0702 against measured 0.2002 / 0.3295 / 0.4924 / 0.6537 / 0.6355 / 0.4617 / 0.2883 / 0.1541 / 0.0683, giving |diffs| of 0.0018 / 0.0015 / 0.0011 / 0.0008 / 0.0007 / 0.0011 / 0.0015 / 0.0018 / 0.0019. **The stored summary (`max_abs_diff = 0.0019` at λ=4, `mean_abs_diff = 0.0013`) reproduces exactly. I record that explicitly: the residual reporting is accurate, and an earlier draft of this report wrongly attacked it — that attack is withdrawn.** The surviving defect is the *wording*: the Abstract (line 33) and `abstract.tex` (line 32) claim the prediction "matches measurement to four decimals", whereas max |diff| = 0.0019 means the agreement is at the **third** decimal, and all nine per-λ differences (0.0007–0.0019) perturb that third decimal. "Four decimals" overstates the agreement by an order of magnitude, in the sentence of the paper most likely to be quoted and in the Highlights bullet that carries no hedge at all.

**(ii-b) The related defect that survives: three runs of the same condition disagree, and Table 3's τ(0.5) is the outlier.** At λ = +0.5, the certified grid gives τ = **0.4625**, the dose–response run (`a1_h_offset.json::synthetic_curve`) gives **0.46563**, and the closure archive's own "measured" column gives **0.4617** — a spread of 0.004, i.e. **2.1× the paper's entire claimed closure residual**. Table 3 prints measured τ(0.5) = 0.462 and predicted 0.463 (lines 201–202); the certified grid's 0.4625 rounds to 0.463, so the table's *measured* cell corresponds to a run the table does not cite, and the paper's own Table 1 (line 264) prints the same condition as **0.465**. Two tables in the same paper give 0.462 and 0.465 for one condition on one sample, and §3.5.2 rests on the differences between such numbers being ≤0.0019. That is the defensible form of the objection; the residual itself is not misreported.

**(iii) The "four decimals" claim is contradicted by a second occurrence of the same statistic inside the paper.** Line 284 states the bias-field Pearson is "1.0000 to four decimals **in every seed**, not exactly 1 (stored mean 0.9999917, sd=5.5e-7)". 0.9999917 rounds to **0.99999**, not 1.0000. The sd of 5.5e-7 then forces *every* seed into [0.9999906, 0.9999928] — all of which round to 0.99999 or 1.0000 only at four decimals if the round-half rule is generous, and none of which equals 1.0000. So the paper contains, in the same section that downgrades r=1.000, a sentence that re-asserts it at greater precision while stating values that falsify it. (Minor, but it is exactly the kind of arithmetic slip a hostile referee uses to justify distrusting the residual analysis.)

**Verdict: the downgrade is sufficient in the body's §3.5.4, insufficient in the Highlights, insufficient in §3.5's opening sentence, insufficient in `related_work.tex`'s claim list, and quantitatively overstated ("four decimals" vs a 0.0013–0.0019 residual).**

---

## 4. Internal contradictions

Each item below is a pair of statements that cannot both be true, or a statement contradicted by the manuscript's own cited archive.

### C1 (FATAL) — τ does not order real checkpoints within a dataset; the pooled checkpoint correlation is a between-group artefact

**Statement A**, line 473:
> "Across all seven checkpoints (the four controlled runs of Table 10 plus the three archived Flickr30k LoRA checkpoints), Spearman$(\tau_5,\text{top-1})$ is $0.786$ while Spearman$(\text{CG},\text{top-1})$ is $0.286$: order preservation tracks accuracy across that set, and the gap does not."

**Statement B**, line 528 (and repeated at line 574(c)):
> "$\tau$ does *not* reliably rank the seeds *within* a dataset. The per-dataset seed correlations are $-0.5$ (COCO), $-0.5$ (Food-101) and $+1.0$ (DTD), and COCO seed 42 has the lowest $\tau_5$ of its three seeds and the *highest* accuracy."

**Verification.** Recomputing from the paper's own `outputs/a1_h_offset.json` (the file cited as Table 14's source, line 555): over all 13 archived checkpoints, Spearman(τ₅, top-1₅ₖ) = **+0.753** and Spearman(CG, top-1₅ₖ) = **+0.286**. The precise 7-subset that reproduces the paper's (0.7857, 0.2857) pair is `{coco_r8_both, food101_r8_both, dtd_r8_both, flickr30k_ref_r8_both, flickr30k_text_only_r8, flickr30k_both_r8 | flickr30k_retrain_both_ep10, coco_r8_both_seed43|seed44}` — i.e. **the paper's "seven checkpoints" is not the set the text describes** (the text says "the four controlled runs plus the three archived Flickr30k LoRA checkpoints", but that eight-strong pool contains four distinct 7-subsets that give the same ρ, and the text never says which member is dropped).

**Why this is fatal rather than a nitpick.** A pooled ρ of +0.786 pooled over three dataset groups whose *within-group* ρ is −0.5 (COCO), −0.5 (Food-101) and +1.0 (DTD, n=3, i.e. a single ordering) is the textbook signature of a between-group confound: the families sit at different accuracy levels (COCO 57.42, Food-101 58.23, DTD 54.67) and different τ levels (0.5757, 0.5797, 0.5321), and the rank correlation is being produced by *the datasets*, not by *the checkpoints*. The paper even states the same structural fact about the *nine*-run version (line 528): "the effect is carried by DTD, and dropping that family (n=6) *reverses* the comparison—τ falls to +0.486 (p=0.33) against CG +0.657 (p=0.16)". A signal that reverses when one of three groups is dropped, and is negative inside two of the three groups, cannot support "order preservation tracks accuracy across that set." **The paper reports the pooled number and the destroying sensitivity in different subsections, and never puts them side by side.**

### C2 (SEVERE) — τ cannot separate the two branches of the perturbation it is claimed to govern

**Statement A**, line 155:
> "$\tau$ is a *necessary* proxy. Accuracy cannot survive order destruction, and the class-agnostic dose–response is monotone within every such family".

**Statement B**, line 524:
> "At this paper's operating point ($k=5$) the two smallest probes are $0.4931$ and $0.4656$ at $\lambda=-0.5$ and $\lambda=+0.5$: the alarm is tripped at the first non-zero magnitude in both directions, so a single level separates neither severity nor direction."

**Statement C** (from the paper's own certified grid, `outputs/a1_h_baseline_metrics.json`): at τ = 0.4931 (λ = −0.5) top-1 is **29.48%**; at τ = 0.4656 (λ = +0.5) top-1 is **47.48%**.

These three cannot all be true in the sense the paper needs. Within the translation family — the family that defines the paper's entire thesis — the same τ corresponds to accuracies 18 points apart, and the within-family Spearman is **0.750, not 1.000** (§1(b)(ii)). The paper's own certified grid therefore contains a counterexample to "governed by τ" as strong as the class-contraction counterexample the paper spends two subsections conceding — and this one is *inside the class-agnostic family the paper retains*.

### C3 (SEVERE) — "Retrieval tracks the gap" is contradicted by the paper's own retrieval numbers

**Statement A**, line 57 (finding iii):
> "Tasks fall into a sensitivity spectrum: centroid classification is entirely insensitive, zero-shot classification tracks τ, and retrieval tracks the gap."

**Statement B**, Fig. 4 caption, line 361:
> "Centroid classification is gap-insensitive; zero-shot tracks order; retrieval tracks the gap."

**Statement C**, line 49:
> "Meanwhile, retrieval $\Rk{1}$ responds to the gap as expected."

**Contradicting evidence** (from the paper's own cited 50k grid, `outputs/a1_full_results.json`, the file named in Table 10's caption at line 454):
- Spearman(CG, R@1) over the paper's own 20 CLIP conditions = **−0.389**; Pearson = −0.299.
- Over the forward branch (λ ≥ 0, n=14) Spearman(CG, R@1) = **−0.002**, Pearson = −0.037 — i.e. **no relationship at all**.
- The mechanism claim fails in the direction that matters: at λ = +1 the gap is at its **minimum** (CG 0.0117 vs frozen 0.8153) yet R@1 has already fallen from 0.1645 to 0.1340; at λ = 2 and λ = 4 the gap **re-grows** (0.4537, 0.6826) while R@1 *falls further* (0.1020, 0.0795). So on the paper's own grid, R@1 falls while the gap shrinks and keeps falling as the gap grows — the gap is not driving retrieval. The sign of the correlation is *negative* (bigger gap → worse retrieval), while the paper's framing is "gap reduction predicts retrieval degradation" (line 45) — the opposite reading.
- The only retrieval number offered to the reader is a single retention figure at one λ (line 356: "retrieval R1 retains 81%"), which is λ = +1, the one point where the gap is ~0. A single point cannot establish "retrieval tracks the gap" against a 20-point correlation of −0.389 in the opposite direction.

The paper attributes the retrieval claim to a *different* manuscript (line 45: "gap change predicts retrieval degradation \citep{wan2026protect}", and `related_work.tex` line 47: "Our prior empirical study found that the Distribution Gap predicts retrieval R1 (r = −0.827)"). That prior result is about the *Distribution Gap*, not the Centroid Gap, and it is not reproduced here. **The paper asserts a fact about its own data that its own data contradicts.** This directly undermines the Abstract's task-sensitivity ordering and the Discussion's "for retrieval-oriented adaptation, the gap … is the right signal" (line 570).

### C4 (SEVERE) — Two undefined contraction families, same name, opposite conclusions

**Statement A**, Setup, line 72 (the manuscript's *only* definition of "centroid contraction"):
> "We add two control families: orthogonal translations (same magnitudes, random unit direction $r\perp \hat d$) and centroid contractions $\tilde x=\mathrm{norm}((1-a)x+a\mu_I)$."

**Statement B**, Results §4.1, line 104:
> "The centroid contraction family is the mirror image: it barely moves the gap ($0.82\to 0.84$ at $a=0.1$) and barely moves top-1 ($59.3\%\to 58.8\%$)."

**Statement C**, Results §4.4, line 128 / Table 1, line 147:
> "What works is *class alignment*: contracting each image toward its own class centroid *improves* accuracy to $78.6\%$ ($a=0.5$), beyond the frozen baseline".

**Contradicting evidence.** In the paper's own 50k archive (`a1_full_results.json`) the family called `C` with parameter a = 0.1/0.25/0.5 gives CG **0.8365 / 0.8713 / 0.9327** against a frozen 0.8153 — i.e. **the gap *grows* under the operation the Setup defines as a contraction toward the image mean**, and top-1 falls to **58.84 / 57.36 / 44.76**. In the 5k spectrum archive the family the paper calls "class contraction" (given as `class_contraction` in `a1_subspace_results.json`, τ 0.7598/0.6150, top-1 70.32/78.58) is a *different generator*, and the certified 26-condition grid labels it `P` with a = 0.25/0.5 (τ 0.7519/0.6086, top-1 69.18/78.08).

Consequences, all of them quotable against the paper:
1. **The reported direction of the gap change under the Setup's own formula is the opposite of what the formula implies, and the paper never notices or explains it.** I verified the implementation (`tools/clip_a1_full.py` line 131: `F.normalize((1 - a) * full + a * mu_i, dim=-1)`) — the code does exactly what Eq. (1) says. Pulling images by half the distance to the global image mean should *close* the gap (at a = 1 the image centroid is μ_I itself, so CG = ‖μ_I − μ_T‖ = 0.8153), yet the archive reports CG *rising* from 0.8153 to 0.9309 at a = 0.5. The renormalisation (which inflates the cluster mean's distance as the image vectors shorten) evidently dominates — but the paper never decomposes this, never states that the a = 0.1/0.25/0.5 values lie below the crossover, and prints the increase as if it corroborated the Setup. **A reader who takes Eq. (1) seriously will predict the opposite sign and conclude the paper has mixed up its two contraction families.**
2. **The same phrase "centroid contraction" carries opposite sign in two sections** — near-neutral at small a but *harmful at a = 0.5* in §4.1 (top-1 58.8 at a=0.1, and 44.76 at a = 0.5 on the same archive), dramatically *helpful* in §4.4 (78.6). The Setup defines only μ_I-contraction; Table 5 says "Class contraction"; §4.4 says "toward each image's own class centroid"; §4.9/Table 12 and the archived files call the helpful one `P`/`class_contraction`. **There is no place in the manuscript where the two generators are distinguished and named**, so a reader cannot tell that §4.1 and §4.4 are describing different operations — and §4.1's own sentence ("it barely moves the gap … and barely moves top-1") is false at a = 0.5 on the family the Setup defines, where top-1 falls 14.5 points.
3. The Abstract's headline ($59.3\%\to78.6\%$, line 33) inherits this ambiguity: it says "contraction toward class centroids improves it", but the reader who checks Table 5 finds a "Class contraction" row at a = 0.5 with top-1 **78.6** — which is the `P`/`class_contraction` generator — while §4.1's "centroid contraction" family is the harmful one. The manuscript never reconciles the two.
4. **The same conflation makes the necessary-not-sufficient argument depend on an unmeasured embedding-space assertion.** `tools/clip_a1_theory_verify.py` lines 156–163 computes the contraction prediction **entirely in score space**: `S2 = S + a * Delta` with `Delta = e @ tf.T`, and predicts top-1 as `(S2.argmax(1) == labels).mean()` — with *no* renormalisation. The real intervention is applied to embeddings and renormalised (`clip_a1_full.py` line 131). So the agreement quoted at line 157 ("The same closed form applied to this different generator reproduces both contraction entries") validates the score-space surrogate, not the embedding-space operation, and the discrepancy those two must have is never quantified. The paper's most important concession (τ = 0.615 → 78.6%) therefore rests on a demonstration that has never been shown to represent the operation it is said to explain.

### C5 (SEVERE) — The λ grid in the Setup is not the λ grid in the Results

**Statement A**, Eq. (1), line 70:
> "$\lambda\in\{-2,-1,-0.5,0,0.25,0.5,1,2,4\}$."

**Statement B**, Table 3 / §3.5.3, lines 199–202:
> "$\lambda$ & $-2$ & $-1$ & $-0.5$ & $-0.25$ & $0.25$ & $0.5$ & $1$ & $2$ & $4$"

The Setup's grid **contains λ = 0** (the frozen baseline, explicitly "including the frozen baseline at $\lambda=0$", line 76) and **contains no λ = −0.25**. Table 3 contains **λ = −0.25** and, as a "λ value" of the prediction, **no λ = 0** (the baseline τ = 1 is by definition, not a prediction). The 26-condition certified grid (recomputed from `a1_h_baseline_metrics.json`) uses λ ∈ {−1, −0.5, 0.25, 0.5, 1, 2, 4} for translations — **λ = −2 is absent and λ = −0.25 is absent**, i.e. neither of the two grids matches Eq. (1). Table 2 (line 178) reports λ ∈ {0.5, 1.0, 2.0}; Table 7 (line 378) reports λ ∈ {0.5, 1, 2}; §4.1 reports λ ∈ {0.5, 1}; §4.9 (line 524) reports λ ∈ {−0.5, +0.5, +1, +2}. **Four different λ grids appear, and Eq. (1) — the only formal definition — matches none of them.**

Additionally: the text's *own* headline λ = 1 (line 104: "at $\lambda=1$ … top-1 to $32.0\%$" and "CG shrinks to 0.41 and 0.01") is drawn from two different archives: 32.01%/0.0117 from `a1_full_results.json` (50k) but 0.41 is the λ = +0.5 value (0.4149 in that same file). So even the abstract's "$\text{CG}{:}0.82{\to}0.01$, top-1: $59.3\%{\to}32.0\%$" (line 33) silently mixes a gap value and an accuracy value that are consistent only at 50k, while the fallback 5k sample gives 0.2636 and 32.10.

### C6 (MODERATE) — The asymmetry table is a *third* independent run, and it exceeds the paper's own precision claims

Table 2's numbers are sourced: `outputs/a1_text_surgery.json` reproduces them exactly (image-side 47.88 / 31.94 / 13.48; text-side 55.74 / 45.10 / 38.26; τ 0.4618 / 0.2885 / 0.1539 and 0.6337 / 0.4295 / 0.3588 → 0.46/0.29/0.15 and 0.63/0.43/0.36). I record this correction explicitly because it is the one place where I initially suspected an unsourced table and the archive exonerated it. **But the exoneration creates a three-way disagreement the paper never quantifies:**

| λ = +1, image-side, 5k sample | top-1 | τ |
|---|---|---|
| Certified grid (`a1_h_baseline_metrics.json`, 26 conditions) | **32.10** | 0.2901 |
| Asymmetry run (`a1_text_surgery.json`, the source of Table 2) | **31.94** | 0.2885 |
| Exact predictor's own "measured" column (Table 3) | **32.0** | 0.288 |
| Table 3 print | **32.0** | 0.29 |

So the **same perturbation, same sample size, three runs**: top-1 spans 0.16 points (31.94 / 32.01 / 32.10) and τ spans **0.0016** (0.2885 / 0.2887 / 0.2901). The τ spread is therefore **comparable in size to the entire claimed closure residual (0.0019)** — i.e. run-to-run variability in τ is the same order as the effect the closure is said to reproduce, and the certified grid is the outlier among the three (its 0.2901 vs the other two runs' 0.2885/0.2887). The paper's response to all of this is one clause: "measured in a dedicated re-run (hence slight deviations from Table 7)" (line 172) — deviations it never quantifies, never attributes, and never propagates, and which the paper's precision language ("to within 0.002 at every one of nine λ values", line 207) implicitly assumes away.

### C7 (MODERATE) — "Twelve" and "thirteen" checkpoints used interchangeably within one paragraph

Line 548, same paragraph:
> "Measured over twelve vision-LoRA checkpoints—the four controlled seed-42 runs, the six new seeds and the two archived Flickr30k LoRA checkpoints—the excess is $+3.62\pm1.41$ accuracy points … All embeddings are unit-norm and \texttt{logit\_scale} is identically $100.0$ for the frozen model and for all **thirteen** checkpoints of the offset analysis".

The arithmetic also does not close: the parenthetical enumerates 4 + 6 + 2 = 12, but the archive (`a1_h_offset.json::offset_analysis`) has `n_checkpoints_with_measurement = 13` with `excess_top1_mean = 3.3754`, `sd = 1.604`, `min = 0.48`, `max = 6.06`. Recomputation over the 12 `vision_lora = true` rows gives mean **3.6167**, sd **1.4075** — reproducing the paper's 3.62/1.41 — so **the paper silently drops one of the 13 archived checkpoints** (the text-only row, which the Table 13 caption at line 555 does disclose: "the vision-frozen text-only checkpoint is excluded because gap surgery on a frozen vision tower is a no-op"). Fine — but then "all thirteen checkpoints of the offset analysis" (line 548) contradicts both the twelve-checkpoint claim in the preceding sentence and the caption's exclusion. And the archive's own summary (n=13, mean 3.3754, sd 1.604, max 6.06) is printed nowhere, so a reader cannot reconcile the paper's numbers with the cited JSON's summary block. Table 13 (line 562) nonetheless prints the *twelve*-checkpoint mean, while the file it cites reports the *thirteen*-checkpoint mean.

### C8 (MODERATE) — "the same both-position checkpoint measures 59.7% (50k)" vs the archive's 59.32%

Line 49:
> "Fine-tuning both encoders (``both'' LoRA, rank 8) *increases* the Centroid Gap, yet ImageNet zero-shot accuracy stays at $59.7\%$ (50k)—differing from the frozen model's $59.3\%$ by only $0.4$ percentage points, within sampling noise."

The archive row the paper cites for this checkpoint (`a1_h_offset.json`, tag `flickr30k_both_r8`, path `outputs/imagenet_zs/both_r8/best_checkpoint.pt`, CG 0.847886 — the exact file named at line 471) records `summary_top1_5k = 59.32`. On the paper's own 5k sample the frozen baseline is 59.10; on the 50k sample 59.28. So the archived both-position checkpoint is **+0.22 points vs frozen at 5k** and **+0.04 points at 50k** — the paper's "59.7 (50k)" is not in the cited record, and 59.7 would be +0.42 over 59.28. "Within sampling noise" would survive either way, so the **conclusion is unaffected but the number is unsourced**. (Per the project's own "every number must name its archive" rule, this one cannot currently be sourced.)

### C9 (MODERATE) — The retrospective on the archived ρ = 0.926 is internally inconsistent about *what* cannot be certified

Line 279:
> "two other metrics stored in the same archived file are not reproduced exactly by any variant tried (Centroid-Gap correlation with top-1 $-0.2150$ recomputed against $-0.0821$ stored; mean embedding cosine $0.8619$ against $0.8715$ stored; linear CKA does match, $0.755214$ against $0.755200$)"

but three lines earlier, line 273 (Table 4 footnote) and line 185 report **τ = 0.9125 (certified) vs 0.926 (archived)** as the *only* τ ambiguity. Meanwhile the paper's own `a1_tau_holdout.json::key_numbers.baseline_metric_correlations` stores **τ = 0.9262, CG = −0.0821, CKA = 0.7552, mean_cos = 0.8715** — i.e. the "archived" tuple — while `a1_h_baseline_metrics.json::metric_correlations` stores **τ(k=5) = 0.9125, τ(k=10) = 0.9262, CG = −0.215, CKA = 0.7552, mean_cos = 0.8619**. So **the *same* file that the paper calls "the certified values" preserves the archived τ only at k = 10**, and the τ discrepancy the paper presents as a k-labelling puzzle (0.926 ↔ k=10) is accompanied by a CG discrepancy of 0.133 and a cosine discrepancy of 0.0096 that the paper never explains except as "the archived script state cannot be certified from the record" (line 279). The paper's framing — one clean k-mislabel plus some collateral — is not what the archives show: the archived tuple is a **uniformly different run** (τ, CG, cos all differ; only CKA coincides, which is exactly what you would expect if CKA is insensitive to the same re-draw). The honest statement is "the archived metrics block does not come from the run we can reproduce, in three of four statistics", which is a provenance failure, not a labelling slip.

### C10 (MINOR but quotable) — "all 26 lie in [+0.264, +1.220]" vs the paper's inclusion of a λ = −2 condition elsewhere

Lines 279 and 76 both describe the certified grid as spanning CG ∈ [0.264, 1.220]. The 20-condition *other* grid contains CG = 1.345 (λ = −2, `a1_full_results.json`), and §4.9 discusses gap *widening* to 1.0729 (line 524). Not a contradiction, but the paper quotes CG ranges from three different grids without flagging which range belongs to which grid, so any reader checking one number against another will find apparent inconsistencies.

---

## 5. First-order approximation vs perturbation magnitude

### 5.1 The paper's own magnitudes

- **Gap magnitude:** ‖g‖ = 0.8154 (line 418, and `a1_h_offset.json::meta.gap.gap_norm = 0.814929`; the frozen CG on the same grid is 0.8147–0.8153 across archives).
- **Perturbation magnitude:** Eq. (1) gives displacement **λ‖g‖**, with λ up to **4** (line 70) — so the largest perturbation used is **4 × 0.8154 = 3.26** in a unit-sphere embedding space, i.e. **3.26× the sphere radius**, and 4× the quantity the expansion is in.
- The perturbation spectrum matches magnitude *to* ‖g‖ (line 78: "At matched magnitude $\|g\|$"), i.e. λ_eff = 1, again not small.
- Class contraction uses a up to 0.5, i.e. a displacement of up to half the distance from each image to its class centroid — the paper's own Table 14 puts real ‖Δx‖ at 0.118–0.339 (line 562); synthetic Gap surgery is λ‖g‖ = 0.20–3.26.

### 5.2 The paper's defence, quoted (line 216)

> "The analysis of Section 3.5.1 is written as a first-order expansion, which may suggest a small-perturbation assumption that our experiments violate, since the perturbations used are of size $\approx\|g\|$. That premise does not apply to the criterion we actually use. The pair-inversion statement of Section 3.5.1—pair $(i,j)$ inverts if and only if $\lambda\|g\|(m_j-m_i)>d_{ij}$—is an *exact* equivalence for every $\lambda$, positive or negative, once the margins are frozen. … Nothing in Table 6 assumes $\lambda\|g\|\ll 1$, and its inputs ($\{m_c\}$, $\{d_{ij}\}$, the frozen top-5 sets) are read off the frozen model. The agreement over nine $\lambda$ values spanning $\lambda=-2$ to $\lambda=+4$—where the translation reaches four times the gap magnitude—is what a non-perturbative criterion should produce."

and line 218:

> "In the ordering analysis, higher-order terms in $\|\delta\|$ are not neglected but *absent*: they enter only through changes in the frozen quantities themselves ($m_c$, $\{d_{ij}\}$, and the membership of the top-5 sets), i.e. exactly in the regimes where the closed form does not claim to hold".

### 5.3 Assessment — the defence is technically correct for exactly one quantity and misleading for the rest

**(a) The defence is valid for the τ(λ) closure, and the paper should be credited.** The algebra is right: with $\tilde x = (x+\delta)/\|x+\delta\|$ and $\tilde s_c = (s_c + \lambda\|g\|m_c)/\|x+\delta\|$, the denominator is a positive per-image constant, so pairwise comparisons are exact with no truncation. Nobody can attack this. **But note what it means: the object that survives the large-perturbation objection is the *identity*, i.e. the object that cannot provide evidence (attack A3). The paper's defence of its non-perturbative claim is exactly its admission that the claim is a re-derivation.**

**(b) The first-order expansion is load-bearing where it cannot be defended, and the paper says so only in passing.** The r = 1.000 result is explicitly assigned to "statements about score *magnitudes* (the per-class profile $\lambda\|g\|m_c$ and the Centroid-Gap displacement)" (line 218) — i.e. to the **truncated** use. At λ = 4 the truncation is not a correction, it is the whole answer: the second-order term in Eq. (2) is $O(\|\delta\|^2) = O(10.6)$, two orders of magnitude larger than the retained term's scale. The paper never quantifies the neglected term, never shows a second-order check, and its one "first step that does introduce an approximation" control is a *different* approximation (a Gaussian surrogate for the margins, line 220), with no ablation of the truncation order. **A first-order expansion used at $\|\delta\| = 4\|g\|$ with no error term is not an approximation the paper is entitled to call first-order.**

**(c) The specific magnitude claim in §3.5.3 does violate the small-perturbation assumption and the paper's own text concedes it.** The per-class shift claim is "measured mean per-class shifts at λ=1 match the prediction with Pearson r=1.000" (line 167) — at λ = 1 the displacement is 0.8154, i.e. comparable to the embedding scale, and the *mean* is taken over images (line 218: "taken as a mean over images"), which is precisely the operation that hides second-order per-image terms. The residual then behaves as the truncation would predict: it is ~0.0013–0.0019, i.e. **0.2% of the predicted τ range**, and it *grows* at the largest |λ| in the stored arrays (0.0011 at λ=1 vs 0.0013 at λ=−2). An honest framing is "the first-order form is accurate to 0.2% over |λ| ≤ 4 on the mean profile", not "matches to four decimals".

**(d) The claim that second-order terms are "absent rather than neglected" (line 218) over-reaches.** They are *not* absent from the system; they are absent from the **frozen-margin closure**, which is a *different object* from the measured behaviour of a real perturbation. Line 218 concedes this in the same breath ("they enter only through changes in the frozen quantities themselves"), which means: the closure is exact for frozen $m_c, d_{ij}$, top-5 membership, and **real perturbations do not preserve those quantities** — which is why the paper has to "re-measure instead of extrapolating" in exactly the regimes it cares about (text-side surgery, real fine-tunes, class contraction). The defence therefore proves too much: if the closure only applies when the frozen quantities are unchanged, then the paper's central claim about *fine-tuned checkpoints* — where $m_c$, $d_{ij}$ and top-5 membership all change — is outside the closure's validity, and the closure cannot be used to argue for it. Correctly stated, the honest version of §3.5.2 is: *the one object in this paper that survives the large-perturbation objection is the object that cannot provide evidence.*

**(e) I checked the four-benchmark claim at the source, and it is worse than a validation — it is a tautology by construction.** Line 438 says "the exact bias-field predictor matches measurement to better than $5\times10^{-7}$ at every grid point of all four benchmarks---in the primary variant the difference is exactly $0$ at all nine $\lambda$ values". Opening `outputs/a1_rr_e3_benchmarks.json` (Food-101, `variants.flickr30k.surgery`) shows why the difference is exactly zero: **every row stores `tau` and `tau_pred_exact` with identical values** (0.246495/0.246495, 0.424539/0.424539, 0.612673/0.612673, 0.769608/0.769608, 0.621061/0.621061, 0.440404/0.440404, 0.260412/0.260412, 0.13699/0.13699). The generator (`tools/a1_rr_e3_benchmarks.py` lines 245–250) writes `tau` from `kendall_topk(base_np, Sl, idx5)` — the Kendall recomputation on the same frozen scores — and `tau_pred_exact` from the 5-line closure of lines 84–95, which is a step function of the *same* `base_np`, `m` and `idx5`. The two agree to 1e-6 because of **integer division of the same float32 tie mass**, exactly as the paper says ("float32 tie mass", line 438). So the "four further benchmarks" contribute **zero independent evidence** for the bias field, and the paper presents them as the *third* of "three things replicate".

**Verdict on Q5: the small-perturbation assumption is violated (λ up to 4, i.e. ‖δ‖ up to 3.26 in a unit-norm space), the paper knows it, and its escape hatch covers only the re-derivation. The magnitude claims and the r=1.000 result remain first-order at magnitudes where first-order is meaningless, and no second-order or numerical-integrity check of the truncation is reported.**

---

## 6. Statistical hygiene

### 6.1 Headline numbers **with** an uncertainty

| Number | Location | Uncertainty given |
|---|---|---|
| τ Spearman vs top-1 (26-cond grid) | line 295, Table 5 | 5-seed mean ± sd (0.9167 ± 0.0064) |
| mean cosine / CKA / CG correlations | line 296–298, Table 5 | 5-seed mean ± sd |
| bias-field Pearson | line 284 | sd across 5 seeds (5.5e-7) |
| τ(k) levels, λ ∈ {−0.5, 0.5, 1, 2} | Table 12, lines 513–519 | bootstrap half-widths quoted in text (line 502: 0.0024–0.0269) |
| τ levels per benchmark | line 526 | 2,000-replicate image bootstrap half-widths ±0.0034–0.0311 |
| offset excess (12 ckpt) | lines 548, 562, 574(d) | +3.62 ± 1.41 (t-interval [2.72, 4.51]) |
| LoRA seed spread | Table 13, lines 539–541 | τ₅ and top-1 sd over 3 seeds |
| λ_reg dose–response endpoints | line 162 | 3-seed mean ± sd at λ_reg ∈ {0, 1} |
| Table 6 val loss endpoint | line 325 | two measurements, agreement to 0.0051 |
| asymmetric-surgery table | line 172 | **none** — "dedicated re-run (hence slight deviations)" is a qualitative caveat, no interval |
| top-1 under surgery (Tables 6, 7, 8) | lines 104, 178–180, 201–202, 332, 378–380, 399–403 | **none anywhere** |

### 6.2 Headline numbers **without** any uncertainty (each is a defensible referee complaint)

**Every top-1 and τ number in the paper's central figures and tables is a point estimate with no interval, no seed range, and in most cases a stated precision finer than the paper's own seed sd:**
- "classification can collapse while the gap shrinks (CG: 0.82→0.01, top-1: 59.3%→32.0%)" — **Abstract, line 33**; single run, 50k, no interval. The paper's own seed sd for 50k top-1 is 0.48–0.66 points (Table 12), and the frozen baselines quoted in the same abstract (59.3) and the tables (59.28) differ by 0.02 with no interval.
- "at λ=1, the gap-direction shift reduces top-1 to 32.0% while an equal-magnitude orthogonal shift leaves 42.2%" — **line 104**; single run, no interval; and the *certified* archive gives 32.10/45.64 (§C6), so the quoted pair is not internally reconcilable at the stated precision.
- "Closing the gap by global translation *hurts* classification." — **line 104**; the entire thesis, from one run.
- "3-template and 7-template ensembles reproduce parallel collapse curves (frozen 60.1%/60.3%; λ=1: 36.9%/36.5%)" — **line 104**; two numbers, no intervals, no seed variation, no per-template τ.
- "it barely moves the gap (0.82→0.84 at a=0.1) and barely moves top-1 (59.3%→58.8%)" — **line 104**; single run.
- Table 1 (spectrum) rows "58.8 / 0.761", "78.6 / 0.615" — **lines 141–147**; the paper's central necessary-not-sufficient counterexample, **single run, no interval**, and the *certified* re-run of the same two cells gives 57.96/0.7605 and 78.08/0.6086 (from `a1_h_baseline_metrics.json`), i.e. **the counterexample's own numbers differ between the paper's illustrative run and its certified run** (top-1 78.6 → 78.08, τ 0.615 → 0.6086). The paper quotes the illustrative run in the Abstract, the Introduction, Table 5, §4.4, the Discussion and the Limitations list, and never reconciles it with the certified grid.
- "the mean per-class shifts at λ=1 match the prediction with Pearson r=1.000" — **line 167**; a correlation with no CI, no seed range, no permutation null. (The natural null is degenerate because both sides are deterministic functions of one frozen array, but the paper does not say so.)
- "$\tau$ $0.9125$ ($p{=}8.5\times10^{-11}$)" and the other three correlations — **line 185**; p-values are given (and I verified all four are exactly right: 8.45e-11, 0.292, 0.198, 0.69) but for a **26-point** correlation with no CI; and the 5-seed stability is reported separately, so a reader must combine two sections.
- "$R^2$ $0.371$/$0.378$" with "$n_\text{test}=20$" and "$n_\text{test}=4$" — **lines 227, 239, 579**; **no CI on either R²**, and the failing fold's R² is quoted as a range (−1.13 to −1.52) with no interval.
- "Spearman ρ=0.927, p=1.4×10⁻¹²" — **lines 227, 239, 574**; verified numerically (1.40e-12), but as argued in §2 it is not a held-out statistic and no CI is given.
- "$\rho$ stays inside $0.9125$–$0.9357$ throughout" — **line 185**; 7 correlations, no intervals.
- "We quote $0.9125$ with the top-5 and fixed-$k$ qualifications" — **line 279**; and §4.8 states outright that a *different* stored value (0.926) cannot be certified. The one number the paper leads with is the one whose provenance section documents a failure to reproduce two companion statistics.
- "$\tau$ falls monotonically … in **15 of 15** benchmark×template combinations, $\tau(2)$ lies in $[0.071,0.297]$" — **line 484**; 15 cells, one number each, no intervals per cell (bootstrap half-widths are given for a *different* grid at line 502).
- "the spread of τ across the five templates reaches 0.111 … never falls below 0.065" — **line 484**; spread of 5 points, no uncertainty on the spread.
- "$\tau$ between the default template and `{}` is 0.565 on ImageNet-5k and 0.481 on DTD" — **line 484**; two correlations, no intervals.
- "the frozen class-relative order … the two templates share only 57.1% of their frozen top-5 sets" — **line 484**; Jaccard, one number.
- "$\tau=-\!0.083$, 0.122, 0.122 … collapse to 0.1%, 7.4%, 7.0%" — **line 117**; three points, no intervals; and the three full-FT rows are **reconstructions** whose own record "carries a legacy constant (7.38) that its own measurement (0.13%) contradicts" (line 80). Reporting τ = 0.122 for two of three rows to three decimals, from reconstructions whose provenance the paper itself describes as having a broken constant, is indefensible precision.
- "retrieval R1 retains 81%" — **line 356**; one number at one λ (§C3).
- "NCC is flat at ≈69% across *all* conditions" — **line 106**; single run; the archive shows 68.93–69.11 across 20 conditions with no interval, so "flat" is asserted at a precision the archive supports but the paper never states the range.
- "iNat-wild the same behaviour appears at λ=0.25, where τ has already fallen to 0.5992 while top-1 is still at its frozen 11.14%" — **line 442**; **n = 718 images**, no interval; and §4.9 line 526 gives its bootstrap half-width as the widest in the paper (±0.031), which the early-warning claim at 0.5992 does not need but a referee will demand.
- "class-conditional contraction improves top-1 on 4/4 benchmarks (+15.3, +16.5, +3.6, +4.8)" — **line 438**; four deltas, no intervals, three of them on benchmarks with n ≤ 1,880.
- "top-1 falls from 58.11%±0.05 to 55.60%±0.27 and τ from 0.708±0.006 to 0.635±0.008" — **line 162**; three seeds at the two endpoints, but "*the intermediate points single-seed*" — the monotonicity of the dose–response, which is the section's claim ("The response is monotone and opposite to the post-hoc effect"), **rests on single-seed points at λ_reg ∈ {0.1, 0.5}**.
- "Food-101 … raises top-1 from 82.06% to 98.59%" — **line 442**; one run, no interval, and this is a 16.5-point improvement used as a headline necessary-not-sufficient instance.
- "$\tau=0.759$ at 58.50% against the frozen 59.06%" — **line 548**; note the frozen reference here is **59.06**, whereas the same paper's frozen references are 59.10 (5k), 59.28 (50k) and 59.3 (Abstract). Four different frozen baselines are in circulation (§C11).

### 6.3 Claims resting on a **single seed** (the paper discloses some, not all)

**Disclosed by the paper** (credit where due): the Table 6 epoch sweep is "one seed (seed 42)" (line 338, and again at line 352); the intermediate λ_reg points are single-seed (line 162); "Each non-Flickr30k dataset was trained in a single run here (seed 42)" (line 477).

**Not disclosed / still single-seed:**
- **Table 1, the entire perturbation spectrum** — "58.8 / 0.761" vs "78.6 / 0.615", the paper's central counterexample, is one run. §4.8's 5-seed sweep covers *correlations*, not these two cells, and the certified re-run of the same cells differs (57.96/0.7605, 78.08/0.6086). **The paper's most-quoted counterexample has no seed support and is quoted at a precision that its own re-run does not reproduce.**
- **All of §3.5 (the mechanism section)**: Table 2 (asymmetry) — dedicated re-run, one seed, no interval; Table 3 (pointwise τ(λ)) — one run; the r=1.000 result — one run, with the multi-seed check reported only for the *correlation* (line 284).
- **§4.1's gap-surgery headline numbers** (32.0%, 42.2%, 47.6%, 0.41, 0.01, the 3-template/7-template control): one run each.
- **§4.5–4.6's cross-model and decoder results** (Table 7, Table 8): one run per model; no seed variation for OpenCLIP, SigLIP, Qwen2-VL-2B, DINOv2-base.
- **§4.7's four benchmarks, including the 4/4 contraction claim** (line 438): one run per benchmark.
- **§4.9's bootstrap CI half-widths** (line 526): described as "2,000-replicate bootstrap resampling images" — that quantifies *image* sampling, which is the correct unit for τ, but it is **not** a seed/run interval and cannot substitute for one; the paper uses it in place of run-to-run uncertainty when arguing that template spreads are "4.3 to 28.4 times" the half-widths (line 484).
- **Table 10's "the same checkpoint, two gap measurements"** (line 471): the paper says "we have not re-measured the fine-tuned checkpoint on the legacy hold-out, so we cannot attribute the whole difference to the subset, and we do not claim to" — an honest disclosure, but it means the **range 0.033–0.114 reported in the Abstract and Introduction is not resolved by any experiment in the paper**; the range is quoted as a result ("we quote the range") when it is an unresolved measurement conflict.

**Verdict on Q6: no.** Uncertainty is reported for the correlation table, the bootstrap k-sweep, the seed sweep, the offset and one dose–response endpoint. It is **absent for every top-1 accuracy in the paper's central figures/tables, for the perturbation-spectrum counterexample, for the whole mechanism section, and for all four cross-model/benchmark replications.** At least six headline claims (the 59.3→32.0 collapse, the 78.6/0.615 counterexample, the 42.2 vs 32.0 direction effect, the four-benchmark contraction gain, the DINOv2 immunity range, the Qwen τ=1.000 text-side result) rest on a single run or a single seed, and the paper's own 5-seed sweep demonstrates that the *correlations* move by up to ±0.021 (CKA) — i.e. the noise floor is not zero, and the paper has not propagated it to any accuracy.

---

## 7. Additional methodology attacks not covered by the six questions above

### 7.1 The number of "conditions" is a moving target and the counts do not match the archives
Line 76 promises an accounting, but the three counts are inconsistent with each other and with the files: 34 = 20 + 11 + 3 (verified: `a1_full_results.json` has 20, `a1_subspace_results.json` has 11, per-image low-rank 3); 26 = the certified grid (verified); 28 = 20 + 8 (verified, `a1_crossmodel_results.json` has 8 = 4 OpenCLIP + 4 SigLIP). But the **same physical condition appears in up to three grids with three different τ values**: λ=+1 translation at 5k is τ = 0.2887 (subspace archive), 0.2901 (certified grid), 0.290 (Table 10); at 50k it is 0.2887 (full-results archive) and 0.29 (Table 5). The Abstract's headline count "34 perturbation conditions, three families and seventeen fine-tuned checkpoints" (line 33) mixes grids whose frozen baselines differ (59.28 / 59.10 / 59.06) and whose λ sets differ (§C5). **The paper is entitled to one of these grids, not all of them, in a single headline claim.**

### 7.2 The number of model families in the abstract is not the number assessed
Abstract line 33: "Across the **three** families assessed—CLIP ViT-B/32, OpenCLIP laion2B, SigLIP base-patch16-224". Line 82: "three contrastive dual-encoder families", but then adds Qwen2-VL (decoder) and DINOv2 (negative control). Conclusion line 579 returns to "34 perturbation conditions **across three model families**". Meanwhile the cross-model replication table (Table 8) has 4 conditions per family, and the held-out analysis folds one family of 4 points (R² < 0 for OpenCLIP). **Three families × four conditions is not a cross-family replication of a 34-condition result; the 34 conditions are 20 CLIP + 11 CLIP-spectrum + 3 CLIP-per-image, i.e. effectively one family plus two 4-point sanity checks.**

### 7.3 17 checkpoints
Line 82: "seventeen fine-tunes: fourteen LoRA runs (five on Flickr30k: the two originally trained checkpoints, the retrain run's two epoch-10 endpoints and one same-code control; plus COCO, Food-101 and DTD with three seeds each) and three reconstructed full-fine-tuning runs". The itemisation "five + nine = fourteen" closes, but three of the five Flickr30k entries are **the same weights measured three ways** (the two "originally trained checkpoints" are the archived text-only and both-position runs, and the offset analysis's "three archived" includes the retrain endpoint which the paper elsewhere insists "differ[s] from the archived best_checkpoint.pt tensors entry by entry", line 80). The paper argues both that the retrain endpoints are distinct runs *and* that they are the archived checkpoints ("text-only and both-position are the epoch-10 checkpoints of the retrain run", line 117, vs "the two originally trained Flickr30k LoRA runs (text-only and both-position)" in the same scope paragraph, line 80). **A count that can be read as 17 or 14 depending on which sentence you read is not a count.**

### 7.4 The patch-size claim the brief mentioned
**I could not find any patch-size claim in the manuscript.** `grep` over `paper_a1/*.tex` finds "patch" only inside the model name `SigLIP base-patch16-224` (lines 33, 65, 82, 367) and inside `OpenCLIP laion2B ViT-B/32`. There is no statement of the form "patch size determines X", no patch-size ablation, and no table grouping by patch size. The related-work file is likewise silent. **I therefore report explicitly: the manuscript contains no patch-size claim, so there is no patch-size contradiction to report from the manuscript.** (Patch-size material exists in the *project's other* documents — e.g. `docs/BIOCLIP_RESULT_20261006.md` lines 49–58 assert "patch32 → text_only | patch16 → both" and `docs/PENDING_EXPERIMENTS.md` line 19 anticipates the referee objection — but none of it is in this manuscript. If the parent agent expected a patch-size claim here, it is not in `paper_a1/main.tex`.)

### 7.5 The bibliography does not compile as shipped
The file uses `\citep{...}` (natbib syntax) with `\documentclass[review,authoryear]{elsarticle}` (lines 1, 45), while the related-work integration instructions (`related_work.tex` lines 23–25) state "main.tex does NOT use natbib/\citep and has no .bib file" and instruct `\cite{}` — i.e. the two files disagree about the citation regime. There is no `.bbl`, no `.bib`, and no `\bibliography`/`\bibliographystyle`; the bibliography is a manual `thebibliography` environment (lines 593–651) whose first two entries are literally `\bibitem[Anon., 2021]{hu2022lora}` and `\bibitem[Anon., 2026]{imod}` (lines 594–595) — **anonymous placeholders in a non-anonymous submission**, with key `hu2022lora` attached to "LoRA: Low-rank adaptation of large language models" but labelled "Anon., 2021". The `\Rk` macro (line 13) is used throughout (lines 49, 117, 356) and is *not* used anywhere in `related_work.tex`, so the two files are not in the same naming regime either. **None of this is a methodology attack, but all of it is a desk-reject risk and it is trivially checkable, which means a hostile referee who finds it will discount the paper's precision claims elsewhere.**

### 7.6 The "self-consistency" language is applied to a result that is not an implementation check either
Line 225: "what the $1.000$ reports is that our implementation of the closed form and an independent Kendall re-computation of the shifted scores coincide to within rounding—the two sides are not the same array (`identical = false`; maximum absolute difference $0.0019$...)". But the archive's own `identical: false` flag with `max_abs_diff 0.0019` is exactly what you would get from **float32 tie handling and Kendall tie correction**, which the paper itself invokes for the same magnitude elsewhere (line 220: "Residuals at this level are threshold and tie handling between the pair-count and the Kendall implementations"). So the residual does not discriminate "correct implementation of an identity" from "two implementations of the same identity that differ in tie handling" — meaning the check has **no failure mode**: there is no residual value that would have falsified the claim. A check that cannot fail is not a check, and the paper's own framing ("label it a self-consistency check of the implementation") implies otherwise.

---

## 8. What would have to change (constructive closing)

For the parent agent's planning, in priority order:

1. **Test the model out-of-sample against a rival.** Fit τ→accuracy on synthetic conditions; predict held-out *checkpoints*; compare against ‖λ‖, ‖δ‖, mean cosine, CKA on the identical split. If τ does not beat ‖δ‖, the paper's central claim is unsupported.
2. **Report the within-dataset checkpoint correlations next to the pooled one in the same sentence**, and drop the pooled +0.786 as evidence of anything. §C1 is currently a silent Simpson's paradox.
3. **Either produce retrieval evidence for "retrieval tracks the gap" from this dataset, or delete the task-sensitivity ordering from the Abstract, §4.1, Fig. 4's caption and the Discussion.** The −0.389 (and −0.002 on the forward branch) is in the paper's own cited file.
4. **Name and define both contraction generators** (global-mean vs per-class-centroid), state which table uses which, and reconcile the Setup formula with the C-family's *increasing* CG (§C4).
5. **Delete the patch-size concern** — it is not in this manuscript.
6. **Move the r=1.000 hedge into `highlights.tex` and the first sentence of §3.5, and change "four decimals" to "0.0013 mean / 0.0019 max residual".** Table 3's measured column should cite `a1_tau_holdout.json` explicitly, and Table 1's 0.465 and Table 3's 0.462 for the same condition should be reconciled or one of them dropped.
7. **Report seed/run intervals for every top-1 in Tables 5–9 and 11–13.** At minimum, re-run the two spectrum cells (Gaussian σ=0.25, contraction a=0.5) over 5 seeds, because the paper's certified grid already disagrees with the quoted values (57.96/0.7605 and 78.08/0.6086).

---

## Appendix — sources checked in this review

**Manuscript.** `paper_a1/main.tex` (read in full, 653 lines; the eight lines exceeding the reader's 2,000-character display cap were re-extracted with PowerShell: 80, 117, 163, 167, 176–183, 471, 484, 528, 548, 574). `paper_a1/related_work.tex` (398 lines). Also `paper_a1/highlights.tex`, `cover_letter.tex`, `abstract.tex` (for the r = 1.000 occurrences).

**Archives opened and recomputed** (all under `outputs/`):
- `a1_full_results.json` — the 20-condition CLIP 50k grid (CG, R@1, top1, top5, τ, NCC). Used for §C3, §C4, §C5, §C8.
- `a1_crossmodel_results.json` — 8 conditions (OpenCLIP 4, SigLIP 4). Used for §7.1, §7.2.
- `a1_subspace_results.json` — 11 spectrum conditions incl. `class_contraction` and `translation λ=1`. Used for §C4, §C6, Table 1 verification.
- `a1_h_baseline_metrics.json` — the certified 26-condition grid, `metric_correlations`, `per_image_tau_k_sweep` (raw per-image arrays), `conditions[*]`. Used for §1(b), §C2, §C5, §C6, §C9, §2.1.
- `a1_tau_holdout.json` — `theory_vs_measured_tau` (predicted/measured arrays + the stored summary), `key_numbers`, `conditions_per_file`, `leave_one_model_out`. Used for §3.2, §C9, §A6.
- `a1_h_offset.json` — 13 checkpoints with `summary_tau5`/`summary_top1_5k`/`summary_CG_flickr`/`matched_tau`; `offset_analysis` (n=13 summary). Used for §C1, §C7, Table 13 verification.
- `a1_rr_e3_benchmarks.json` — the four-benchmark records with `tau` and `tau_pred_exact` side by side. Used for §5.3(e).
- `a1_text_surgery.json` — the image-side/text-side asymmetry run that is the source of Table 2 (exonerates that table, and supplies the third disagreeing estimate in §C6).
- `a1_dinov2_surgery.json` — negative control (frozen top-1 48.20, CG 0.0433, τ range). Used for §6.2.
- `a1_h_seed_summary.json`, `a1_h_seed_subsets.json`, `a1_h_templates.json`, `a1_h_bootstrap.json`, `a1_multiseed.json`, `a1_rr_e2_topk.json`, `a1_spectrum*` (absent — see below) referenced through the manuscript's citations; the numbers quoted from them in the text were checked where I report a discrepancy.

**Generating code read:** `tools/clip_a1_full.py` (the C family's formula, line 131), `tools/a1_rr_e3_benchmarks.py` (`kendall_topk`, `predicted_tau_exact`, lines 68–95, 245–250), `tools/clip_a1_theory_verify.py` (score-space contraction prediction, lines 152–187).

**Could not locate:** `outputs/a1_spectrum_results.json` does not exist (the spectrum rows live in `a1_subspace_results.json`); the manuscript cites no such file, so this is not a manuscript error, but the name is used in some project documentation.

**Statistical recomputations performed** (scipy): Spearman/Pearson for the 26-condition grid overall and per family; Spearman for the 7- and 12-checkpoint sets; exact reproduction of the 7-checkpoint (τ, CG) correlation pair over all 35 subsets; p-value reconstruction for ρ = 0.9125 (n=26 → 8.45e-11), ρ = 0.927 (n=28 → 1.40e-12), ρ = −0.215 (n=26 → 0.292), ρ = −0.251 (n=28 → 0.198), ρ = −0.082 (n=26 → 0.690); t-intervals for the +3.62±1.41 (n=12) and +4.72±0.70 (n=9) offsets; Spearman(CG, R@1) over the 20-condition grid and its λ≥0 branch; mean per-image τ per condition at k ∈ {2,3,5,10,20,50,100}.
