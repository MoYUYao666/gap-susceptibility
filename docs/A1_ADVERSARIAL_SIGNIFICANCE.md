# A1 — Adversarial desk-reject case (significance)

**Role:** senior associate editor, Elsevier journal (IF ≈ 8), deciding whether to send out for review.
**Brief:** build the strongest *possible* case for desk-rejection on **insufficient significance**, before a real editor does.
**Artifact reviewed:** `paper_a1/main.tex` (653 lines, read in full) plus `paper_a1/related_work.tex` (398 lines, `\input` at `main.tex:60`). PDF build date 2026-10-10, 13 pp-class elsarticle.
**Precedent:** desk-rejected by Neurocomputing — *within aim and scope, below the required significance level*, no reviewer comments.
**Evidence discipline:** every claim below is tied to a line number in the files as written. Where I could not find something, I say so explicitly. Nothing is inferred from other papers in this repository.

---

## 0. The manuscript in one paragraph, as an editor sees it

The paper takes a familiar diagnostic — the modality gap — and shows, by controlled interventions, that gap magnitude does not predict zero-shot classification health, while a Kendall order-preservation coefficient τ does. It then spends roughly half its length (`main.tex:231–565`, §4.6–§4.10 plus five "hardening experiments") delimiting what τ may *not* be used for. The result is a manuscript whose own text disclaims the significance of its own headline in ten or more places. That asymmetry — a modest positive claim, then a much longer list of constraints — is the single largest desk-reject liability, and it is not a matter of tone: the disclaimers are load-bearing for the method.

---

## 1. What is the single-sentence contribution?

### 1a. As the paper actually supports it

> **Under controlled embedding perturbations of contrastive dual-encoder VLMs, the Kendall order-preservation coefficient τ of class-relative ranks tracks zero-shot top-1 accuracy where the modality gap does not; the gap's failure to predict classification health has a closed-form explanation (a class-dependent bias field), and the same bias field explains why image-side translations destroy classification and text-side translations do not.**

Every clause of that sentence is evidenced in the manuscript: the τ–top-1 coupling (`main.tex:117`, Table 4 `tab:topk` `main.tex:258–271`, §4.9 `main.tex:528`), the gap's failure (`main.tex:185`), the closed form (`main.tex:190–207`), and the asymmetry (Table 3 `tab:asym` `main.tex:174–182`; text-side detail at `main.tex:167`).

Note what that sentence does **not** contain: "monitor". The monitoring claim is the title's promise (`main.tex:21`), the fifth highlight (`highlights.tex:16`), and the abstract's framing sentence (`main.tex:33`), but it is *not* what the experiments establish — see §4 and §5 below.

### 1b. The strongest importance sentence the authors actually wrote

> **"Finally, τ is not merely descriptive --- it is the *best* available proxy for zero-shot health among common metrics."** (`main.tex:185`)

Runners-up, both of which claim practical rather than descriptive value:

> "…it is computable from the top-$k$ class sets already available during validation---making it a **zero-overhead training-time monitor** for classification-oriented fine-tuning." (`main.tex:308`)

> "**Tau is a zero-overhead training-time health signal**" (`highlights.tex:16`)

> "Mixed-purpose practitioners should monitor both, or **derive τ cheaply** from top-$k$ class sets already computed during validation." (`main.tex:570`)

And the most quotable *framing* claim (a rhetorical rather than empirical sentence) is the thesis statement, repeated verbatim in the abstract and the conclusion:

> "The thesis we defend is **the negative one**: the gap is not a *universal* arbiter of representation health." (`main.tex:82`)

An editor reading only `main.tex:185`, `main.tex:308` and `highlights.tex:16` would expect a monitoring tool. The body delivers a correlation and a caution — as documented next.

---

## 2. Is it a negative result dressed up as a positive one?

**Verdict: it is mostly a cautionary observation, wrapped around a modest positive correlation, and labelled as a tool. The "monitor" is asserted, never exercised.** The paper is unusually explicit that the positive part is narrow; the problem is that the title, the highlights and the abstract sentence at `main.tex:33` present the narrow part as a deliverable.

### 2a. The evidence that it is a cautionary observation

The paper's own text, in its own words:

| Where | What it says |
|---|---|
| `main.tex:185` | "The gap carries **essentially no information** about classification health under perturbation." — a negative claim; the positive replacement in the same sentence is "best available proxy", i.e. best *of the things tested*, not good in absolute terms. |
| `main.tex:82` | "The thesis we defend is **the negative one**." |
| `main.tex:128`, `main.tex:574(a)` | τ is "**necessary but not sufficient**"; the paper's own table contains τ=0.615 → 78.6% versus τ=0.761 → 58.8%, i.e. the ordering of τ and the ordering of accuracy disagree in its own headline table (Table 2, `main.tex:141–147`). |
| `main.tex:524` | "**A fixed τ level is a change detector, not a health verdict.** … the alarm is tripped at the first non-zero magnitude *in both directions*, so a single level separates neither severity nor direction." |
| `main.tex:528` | "τ does **not** reliably rank the seeds *within* a dataset. The per-dataset seed correlations are −0.5 (COCO), −0.5 (Food-101) and +1.0 (DTD), and COCO seed 42 has the lowest τ₅ of its three seeds and the *highest* accuracy." |
| `main.tex:574(c)` | "τ orders datasets, not individual runs … it does not license reading τ as a per-run ranker inside a high-τ band." |
| `main.tex:246` | τ "is blind to damage caused from outside that set … it proxies accuracy only for perturbations whose action on the score vector is a per-class shift … and **not a universal property of embedding drift**." |
| `main.tex:548`, `main.tex:572`, `main.tex:574(d)` | Real checkpoints sit "+3.62 ± 1.41 accuracy points **above** the synthetic curve and we cannot explain why" — the paper's own calibration is unresolved for exactly the objects a monitor would be pointed at. |
| `main.tex:350` | "(1) **No monitoring signal is inert, and τ is not the only one that moves.**" The "τ is the sensitive signal" story is downgraded to "τ is the *more* sensitive of the three". |
| `main.tex:82` | Scope paragraph disclaims: sufficiency across mechanisms, absoluteness across k or templates, run ranking within a dataset, plus calibration, prompt engineering, forgetting, CZSL. |

A practitioner's decision problem is: *given two checkpoints, which do I keep?* The paper explicitly answers that τ cannot be used that way within a dataset (`main.tex:528`), that its absolute level is not portable across k (`main.tex:502`) or template (`main.tex:484`), that a fixed level cannot distinguish damage from a gap-*widening* perturbation (`main.tex:524`), and that the mapping is family-calibrated (`main.tex:239`, `main.tex:579`). What is left is "a τ that erodes is evidence of damage" (`main.tex:579`) — an interpretive reading of an existing validation curve, not a tool.

### 2b. The strongest counter-argument, stated fairly

The paper does have a piece of genuinely practical evidence: in the strict LoRA-only sweep, over epochs 1→10, τ loses 6.3% of its value (0.7563 → 0.7088) while top-1 loses 2.9% (59.79 → 58.08%) and validation loss is non-monotone (minimum at epoch 3, worse at epoch 10), so "a practitioner stopping on validation loss alone would **stop two epochs late**" (`main.tex:338`). That is the closest thing to a use case in the manuscript.

But it is immediately undercut by the same section and by §4.7.5:
- one seed only (stated at `main.tex:338`);
- per-image τ spread is sd = 0.26–0.28, so "**no single-image τ should be used as a tripwire**" (`main.tex:338`);
- under the alternative protocol (re-evaluated archived checkpoints) top-1 *is* flat while τ falls 0.7638 → 0.7497 — i.e. the "τ sees what top-1 cannot" story is protocol-dependent (`main.tex:343`, `main.tex:352`);
- and critically: **no early-stopping experiment is reported.** The paper never runs τ-triggered stopping, never selects a checkpoint with τ, and never compares the resulting model against loss-based or accuracy-based selection. The words "checkpoint selection" and "model selection" do not occur anywhere in the manuscript. (I checked the whole `paper_a1/*.tex` set; the only matches for "recommend" are the recommendation sentences themselves, `main.tex:442`, `main.tex:473`, `main.tex:570`, `main.tex:579`.)

So: **a cautionary observation with a monitor-flavoured title.** An editor sees the title promising a tool, the abstract claiming it is "free to monitor", and the body delivering (a) a correlation, (b) an admitted unexplained offset of +3.6 points on real checkpoints, (c) a negative within-dataset result, and (d) an explicit statement that a fixed level is not a verdict.

---

## 3. What a sceptical editor says is missing

All items below were checked against the manuscript as written; each is genuinely absent.

1. **A head-to-head monitor comparison, or any decision-level use of τ.** The paper cites gap-aware early stopping as prior work (`main.tex:45`) and then never compares τ-based monitoring against gap-based monitoring on a decision task: no early stopping triggered by τ, no checkpoint selection by τ, no τ-based abort, no downstream accuracy for any of them. §4.7.1 (`main.tex:317–338`) tabulates three signals per epoch; that is a *description of trajectories*, not an experiment in which the monitor is used. The actionable claim is therefore untested — this is the single most damaging absence, because it is precisely the claim in the title, the abstract and `highlights.tex:16`.

2. **Any measurement of the "zero-overhead" claim.** There is no wall-clock, no FLOPs, no memory, no added-pass count, no implementation description, no cost baseline. The only occurrence of the word "overhead" in the manuscript is in the assertion itself (`main.tex:308`); the grep over `paper_a1/*.tex` for `overhead|wall-clock|runtime|seconds|GPU-hour|cost of computing` returns only that line and the identical highlight (`highlights.tex:16`). "Zero-overhead" is a claim about engineering that the paper never measures.

3. **A perturbation that matches real fine-tuning geometry.** The paper itself identifies the mismatch: real LoRA displaces the image cluster **86.0–99.7% orthogonally** to the gap direction, while synthetic surgery is **0% orthogonal by construction** (Table 11, `main.tex:561–562`), and says "a synthetic perturbation with the same *direction mix* as a real fine-tune was not measurable within the protocol under test … **We did not construct one**" (`main.tex:550`). It then leaves the resulting +3.62 ± 1.41 point offset as "an outstanding open question" (`main.tex:548`, `main.tex:572`). So the mechanism the paper offers is validated in a regime it admits real fine-tuning does not occupy, and the correction for the real regime is missing.

4. **A direct classical baseline for the monitor.** The monitor's whole value proposition is that it is more sensitive than the validation signal a practitioner already has. The paper reports Flickr30k **validation loss** per epoch (`main.tex:333`) and zero-shot top-1 per epoch (`main.tex:332`) — and never adds the obvious cheap baselines: CLIP loss *on the target distribution*, retrieval R@1 trajectory, or a single-epoch linear probe. Given that the paper's own claim is a *relative sensitivity* claim ("τ erodes fastest", `main.tex:338`), the comparison set is incomplete by its own standard; the model-selection literature it cites (`kumar2022finetuning`, `main.tex:618`) is not operationalised into a baseline.

5. **A multi-seed early-stopping/decision experiment on the real trajectory.** The dose–response has three seeds for the λ_reg sweep (`main.tex:162`), but the epoch-wise monitoring sweep is one seed (`main.tex:338`, `main.tex:352`). A single-seed trajectory table is thin support for a monitoring recommendation.

6. **Resolution of the paper's own unresolved discrepancy, in the direction the argument needs.** The Centroid Gap of one checkpoint is +0.033 under the shared evaluator and +0.114 under the legacy logger (`main.tex:471`), and the paper states: "we have not re-measured the fine-tuned checkpoint on the legacy hold-out, so we cannot attribute the whole difference to the subset, and we do not claim to" (`main.tex:471`). The missing experiment — re-measuring the checkpoint on the legacy hold-out (or the frozen model on both) — is cheap, and its absence means the headline "real fine-tuning grows the gap without zero-shot loss" rests on a number the paper cannot reproduce across its own two protocols.

7. **Any intervention that uses τ (or order preservation) to improve a model.** The paper shows class-conditional contraction *improves* accuracy while lowering τ (`main.tex:147`, `main.tex:438`), and separately shows training-time class alignment *hurts* (`main.tex:162`). It never asks whether preserving order during training (e.g. a rank-preservation regulariser, or τ-based λ selection) preserves accuracy. Without it, the practical claim remains diagnostic — and the paper's own counterexample suggests the diagnostic may not point the right way.

8. **A test of the monitor on its stated target population.** Real-checkpoint evidence in the monitor section is dominated by LoRA runs that barely move accuracy (55.00–58.21% against a frozen 59.28%, `main.tex:473`) and three **reconstruction-only** full-FT rows whose seed-42 run diverges (validation loss 4.11 → 7.88, R@1 0.2%, `main.tex:80`). There is no real checkpoint that is *moderately* damaged and no demonstration that τ would have flagged it earlier than the metrics a practitioner already logs.

9. **Theory beyond the single-class-agnostic-intervention case.** The exact criterion is proved for image-side translation with frozen margins (`main.tex:212–216`) and explicitly does not apply to text-side surgery, class-conditional contraction, or any training-time update (`main.tex:218`, `main.tex:229`). Since the recommendation is about fine-tuning (a training-time update), the theory does not cover the regime the recommendation targets — and no extension (e.g. a bound under joint updates) is offered.

10. **Scale.** Three dual-encoder families at ViT-B/32-and-below scale plus one small decoder VLM (`main.tex:82`). No ViT-L/14, no data-scale axis, no cross-scale trend. For a journal at IF ≈ 8, a geometric-diagnostic claim with no scale axis is a familiar incrementality flag.

11. **A stated derivation of what τ cannot see, with a bound.** The blindness limitation is admitted (`main.tex:246`) but never quantified: no experiment measures how much accuracy damage occurs with τ ≈ 1 (out-of-set promotion). The paper's own Table 6 (`main.tex:442`, iNat-wild at λ=0.25: τ = 0.5992 with top-1 still 11.14%) gestures at the reverse case, but the "τ blind spot" case is never constructed.

---

## 4. Is the "zero-overhead monitor" real?

**Verdict: the words appear four times (`main.tex:308`, `highlights.tex:16`, and, in weaker form, `main.tex:33` and `main.tex:570`). The claim is asserted, not established, and not demonstrated. No practitioner in the manuscript is ever shown using τ to decide anything.**

### 4a. Where the paper says it

- Abstract: "it is **free to monitor**: the Kendall order-preservation coefficient τ follows from the top-$k$ class sets a validation pass **already produces**." (`main.tex:33`)
- Body: "it is computable from the top-$k$ class sets **already available** during validation---making it a **zero-overhead** training-time monitor for classification-oriented fine-tuning." (`main.tex:308`)
- Discussion: "derive τ **cheaply** from top-$k$ class sets **already computed** during validation." (`main.tex:570`)
- Highlights: "Tau is a zero-overhead training-time health signal" (`highlights.tex:16`)

### 4b. What that word "already" hides

τ is not computed from class sets a validation pass produces; it is computed from the **frozen reference model's** top-5 sets. The definition at `main.tex:74` is explicit:

> "For each image, take its **top-5 class set under the frozen model**; τ is the mean Kendall coefficient between the frozen and perturbed similarity ranks over these sets."

A standard zero-shot validation pass yields the current model's argmax over 1 000 classes — not the frozen model's top-5 index, and not the frozen scores, which must be stored per image and compared rank-by-rank (top-k *sets* alone are insufficient: Kendall needs the within-set ordering, `main.tex:190`). The "already produces" phrasing is therefore only true if the practitioner has instrumented their validation loop to dump an extra N×k frozen index — which the paper never specifies, costs an extra frozen pass per image set, and is not what a validation pass normally retains.

The operational overhead is compounded by the paper's own hardening results, which the abstract does not carry:

- the reference must be frozen per **prompt template**, and with *no intervention at all* the frozen order under the default template correlates only **0.565** with a bare class-name template on ImageNet-5k (**0.481** on DTD), sharing just **57.1%** of top-5 sets (Jaccard) (`main.tex:484`);
- the absolute level shifts by up to **0.104** across k (`main.tex:502`);
- values "are **not comparable across different reference models** without recalibration" (`related_work.tex:203–205`);
- at the paper's own operating point, a fixed τ < 0.5 alarm "is tripped at the first non-zero magnitude in both directions, so a single level separates neither severity nor direction" (`main.tex:524`).

So the honest operational statement is: τ is *cheap in floating-point terms* but requires a maintained (model, template, k) reference cell and direction-checking logic before any value can be read as health. The abstract's "free to monitor / already produces" is a stronger and simpler claim than the body supports.

### 4c. Is it demonstrated or merely asserted?

**Asserted.** Concretely:

- **No cost measurement of any kind.** Confirmed by content search over the whole `paper_a1/` LaTeX set for `overhead|wall-clock|runtime|seconds|GPU-hour|cost of computing|implementation`: the only hits are the assertion itself and the highlight. There is no timing, no FLOP count, no memory figure, no "cost N% of a validation pass".
- **No "already produced" demonstration.** Nothing in the manuscript shows a validation pass emitting the top-k sets, nor labels the pipeline that would do it. The computation is described as *computable* (`main.tex:308`, `main.tex:570`) — an existence statement, not an implementation.
- **τ itself has a hidden sampling requirement**: it is reported as a mean over 5 000 images, whose per-image sd is 0.26–0.28, and "only the mean is diagnostic" (`main.tex:338`). A monitor that requires 5 000 images per evaluation point to be stable is not a byproduct of an arbitrary validation pass.

### 4d. Does anyone *use* it as a monitor, or only show correlation?

**Only correlation, plus per-epoch tabulation.** Everything in §4.7 and §4.7.1 is *observational*: Figure 3 (`main.tex:310–315`) plots τ, CG and top-1 per epoch; Table 5 (`main.tex:327–335`) tabulates τ, top-1 and val loss at epochs 1, 2, 3, 5, 10. Nowhere is a decision taken on the basis of τ:

- no early stopping triggered by τ;
- no checkpoint selected by τ;
- no comparison of "stop at τ-threshold" versus "stop at best validation loss" or "stop at best top-1";
- no ablation of monitoring cadence or cost;
- no false-alarm/false-negative accounting for the monitor across the seventeen checkpoints, even though the paper does compute rank statistics across checkpoints (`main.tex:473`, `main.tex:528`).

The nearest thing to a use is the counterfactual sentence at `main.tex:338` — "a practitioner stopping on validation loss alone would stop two epochs late" — which is a post-hoc observation about a single-seed trajectory, not a monitor experiment. There is a voided internal note (`docs/_VOID_A1_tau_earlystop_results.md`) whose own "用途" section says a "正式早停对照实验" (formal early-stopping comparison experiment) still had to be written; that experiment is not in the manuscript.

**Consequence for the editor's desk decision:** the title sells a tool (`main.tex:21`), the highlights sell it again (`highlights.tex:16`), and the evidence is a correlation plus a disclaimer that the correlation cannot rank runs within a dataset. That gap between claim and evidence is exactly the kind of "significance" failure a desk editor cites.

---

## 5. Where the paper oversells

Each quote is verbatim from the manuscript, followed by what the evidence actually supports.

**O1. Abstract, `main.tex:33`** (and highlight `highlights.tex:16`):
> "Only the second governs zero-shot accuracy, and it is **free to monitor**: the Kendall order-preservation coefficient τ follows from the top-$k$ class sets a validation pass already produces."

*Evidence:* τ needs the **frozen** model's top-5 sets (`main.tex:74`); no pass in the paper emits them automatically; no cost is measured anywhere; and the same paper states τ is necessary-not-sufficient (`main.tex:128`), does not rank runs within a dataset (`main.tex:528`), and that a fixed level is "a change detector, not a health verdict" (`main.tex:524`). *Supports at most:* τ can be computed from stored class-relative ranks at negligible marginal FLOPs, given a fixed (model, template, k) reference.

**O2. Abstract, `main.tex:33`:**
> "Across 34 perturbation conditions, three families and seventeen fine-tuned checkpoints top-1 is **governed by** τ, not gap magnitude."

*Evidence:* the manuscript explicitly forbids pooling those 34 conditions — "Because the 34-condition plane mixes two sample sizes … **we use it only for the qualitative τ–accuracy relation**" (`main.tex:76`), with frozen baselines of 59.28% (50k) and 59.10% (5k). The quantitative excesses are computed within one sample size only (`main.tex:76`, `main.tex:122`). Within the family the paper designates as the real target — real checkpoints on one code path — "τ is *not* a tight cross-checkpoint predictor: Spearman is only 0.400" (`main.tex:475`). *Supports at most:* a monotone qualitative τ–top-1 relation over synthetic perturbations, and an ordering-level contrast over nine controlled runs (`main.tex:528`).

**O3. Abstract, `main.tex:33`:**
> "**A first-order class-dependent bias field matches measurement to four decimals** ($r{=}1.000$; self-consistency, not independent validation)."

The parenthetical is creditable honesty, but the sentence still leads with the decimal count. The paper itself says the two sides are functions of the same frozen arrays, that the two curves "**must** agree", that the difference is "rounding", and that it "**is not evidence of generalisation**" (`main.tex:167`, `main.tex:225`). *Supports:* the implementation of the closed form agrees with an independent Kendall recomputation to 0.0019 (`main.tex:225`). Nothing more. Putting $r{=}1.000$ in the abstract invites the reader to weigh a tautology as a result — and `highlights.tex:14` goes further, stating it as a finding ("First-order bias-field theory matches measurements with r = 1.000") with the caveat removed.

**O4. Results, `main.tex:185`:**
> "Finally, τ is not merely descriptive---it is the ***best*** available proxy for zero-shot health among common metrics."

*Evidence:* the comparison is a 26-condition grid at one sample size, one model, one template, one k, using Spearman rho against top-1; the "common metrics" set is only four (τ, mean cosine, linear CKA, Centroid Gap). Two of the four archived comparator values are **not reproducible** — the paper states the archived Centroid-Gap correlation was −0.082 and the recomputation gives −0.215, and mean cosine 0.872 archived versus 0.862 recomputed, while "the archived script state therefore **cannot be certified from the record**, and we do not claim that it can" (`main.tex:279`). *Supports:* τ has the highest Spearman among four candidates on one grid; the runner-up (mean cosine 0.862 archived / 0.862 certified) is close enough that "best" is not robust to the paper's own unresolved provenance.

**O5. Results, `main.tex:308`:**
> "Two practical points follow: τ is an earlier and more sensitive indicator of order erosion than top-1 itself, and it is computable from the top-$k$ class sets already available during validation---making it a **zero-overhead training-time monitor**…"

*Evidence:* one seed, 5 000 images, per-image sd 0.26–0.28, protocol-dependent direction of top-1, and no monitoring experiment at all (§4d). *Supports:* in one trajectory, τ's relative decline exceeded top-1's (6.3% vs 2.9%, `main.tex:338`).

**O6. Results, `main.tex:117`:**
> "The synthetic perturbations trace a **near-monotonic curve**: accuracy falls only as much as class order is destroyed."

*Evidence:* the same figure is the 34-condition plane whose sample sizes the paper forbids mixing (`main.tex:76`), and the paper's own Table 2 violates the sentence: contraction at a = 0.5 reaches 78.6% at τ = 0.615 while Gaussian noise sits at 58.8% at τ = 0.761 (`main.tex:141–147`, restated `main.tex:155`). *Supports:* near-monotonicity within the class-agnostic families only.

**O7. Abstract `main.tex:33` and Results `main.tex:356`:**
> "…giving a task-sensitivity ordering (centroid < zero-shot < retrieval)". / "The gap is a meaningful health metric **only for the retrieval family**".

*Evidence:* the ordering comes from one intervention point (λ = +1, Figure 4 `main.tex:358–363`, "performance retained at λ=+1"), and centroid insensitivity is described as true "by construction" (`main.tex:356`). *Supports:* a three-family comparison at a single λ; not a ranking of task families in general. (The retrieval side is also the least developed: no retrieval numbers appear in the cross-model table, and the paper's retrieval evidence about the gap is largely inherited by citation to its own prior work, `main.tex:45`, `main.tex:49`.)

**O8. Title, `main.tex:21`:**
> "Order Preservation as a **Zero-Overhead Monitor** for Classification Fine-Tuning: Why the Modality Gap Is Not a Universal Health Metric"

*Evidence:* the manuscript contains no monitoring experiment, no cost measurement, and an explicit statement that τ cannot rank runs within a dataset. *Supports:* "Order preservation as a **negatively useful indicator** under controlled perturbation" — a much less striking title.

**O9. Framing, `main.tex:45` / `main.tex:82`:**
> "…often read implicitly as a quality proxy … What we dispute is the *unconditional* form of that reading".

This is *under*-claiming to the point of deflating the contribution: the paper concedes the gap is genuinely used for alignment and retrieval and targets only the "unconditional" reading. Together with the ten "we do not claim" clauses (`main.tex:82`, `related_work.tex:362–398`), an editor reads the introduction as announcing that the finding is a correction of an inference no cited paper actually makes. That is a self-inflicted significance wound, distinct from overselling: the paper argues itself down in the same breath as it claims a monitor.

---

## 6. Top 5 desk-reject reasons, ranked by likelihood an editor writes them

1. **The headline deliverable is never exercised**: the title, abstract and highlights promise a "zero-overhead training-time monitor", yet no experiment ever uses τ to make a decision (no τ-based early stopping, no checkpoint selection, no comparison against loss-based selection), so the paper's principal claim is unsupported by its own design.
2. **The practical claim is contradicted by the authors' own results**: τ is necessary-not-sufficient (τ = 0.615 → 78.6% vs τ = 0.761 → 58.8%, `main.tex:147`), does not rank runs within a dataset (ρ = −0.5, −0.5, +1.0, `main.tex:528`), and a fixed level "is a change detector, not a health verdict" (`main.tex:524`) — leaving only the weak negative thesis.
3. **The intervention does not represent the phenomenon it is used to explain**: "gap surgery" translates the image cluster 100% along the gap direction, whereas real LoRA displaces it 86.0–99.7% orthogonally (`main.tex:561–562`), the paper did not construct a matched synthetic perturbation (`main.tex:550`), and the resulting +3.62 ± 1.41 accuracy-point offset on real checkpoints remains unexplained (`main.tex:548`).
4. **The "r = 1.000" centrepiece is by the authors' own admission a self-consistency check, not evidence** (`main.tex:167`, `main.tex:225`; still headline in `highlights.tex:14`), and the companion metric comparison rests on archived values two of which the paper cannot reproduce (`main.tex:279`) — so the theoretical contribution reduces to an identity plus a closed form already implicit in the definition.
5. **The advance is incremental relative to the authors' own prior work and the existing literature**: gap-aware monitoring was already proposed (`main.tex:45`), the paper concedes the gap remains the right signal for retrieval and that centroid pipelines need neither (`main.tex:570`), and it does not claim a theory of fine-tuning, a new metric, calibration, forgetting, or CZSL (`main.tex:82`, `related_work.tex:195–209`, `related_work.tex:362–398`) — leaving a geometric diagnostic of one intervention family in one model class, which is below the significance bar for a journal of this tier.

*Bonus sixth, if the editor reaches the appendix-level detail:* the paper's own hardening experiments report results that weaken its stated contrast — dropping the DTD family **reverses** the τ-versus-gap comparison (`main.tex:528`, ρ +0.486 vs +0.657), and DTD is also the one dataset trained on a smaller budget (300 vs 320 steps, `main.tex:546`), so the headline nine-run contrast rests on the family the paper flags as confounded.

---

## 7. What would have to change for this to clear the desk (for the authors' use)

Not requested, but it follows from §3–§5 and is the fastest route to a defensible resubmission:

1. **Run the monitor experiment.** τ-triggered early stopping / checkpoint selection against validation-loss and top-1 selection, multi-seed, with downstream ImageNet top-1 as the outcome. This converts the title from a claim into a result. (If it fails, retitle around the negative thesis.)
2. **Measure the overhead**, or drop the word. One paragraph: marginal cost of storing the frozen top-5 index and recomputing τ per epoch, against the cost of the validation pass itself.
3. **Close the real-vs-synthetic gap**: construct a perturbation whose direction mix matches measured LoRA displacement (`main.tex:550` says this was not done) and report whether the +3.62-point offset persists.
4. **Retitle to what is proved** — the negative thesis plus a task-dependence ordering — and reserve "monitor" for the section that earns it.
5. **Fix the internal contradictions**: the abstract's pooled-34 claim versus `main.tex:76`; `main.tex:117`'s "near-monotonic curve" versus Table 2; and the unresolved Centroid-Gap protocol split (`main.tex:471`) — the last is one re-measurement away.

---

## Appendix A — Evidence index (line numbers as of the reviewed copy)

| Topic | Lines |
|---|---|
| Title / keywords / journal | `main.tex:15, 21, 36–38` |
| Abstract | `main.tex:33` |
| Highest importance claim | `main.tex:185` |
| "Zero-overhead monitor" | `main.tex:308`; `highlights.tex:16`; abstract `main.tex:33`; discussion `main.tex:570` |
| τ definition (frozen top-5 reference) | `main.tex:74` |
| Condition-count discipline (34/26/28) | `main.tex:76` |
| Scope / non-claims | `main.tex:82`; `related_work.tex:362–398` |
| Gap-surgery collapse (CG 0.82→0.01, top-1 59.3→32.0) | `main.tex:104` |
| Table 2 spectrum (τ = 0.615 → 78.6%) | `main.tex:141–147` |
| Necessary-not-sufficient | `main.tex:128, 155, 574(a)` |
| Training-time class alignment hurts | `main.tex:162` |
| r = 1.000 identity check | `main.tex:167, 207, 225–229` |
| τ "best available proxy" | `main.tex:185` |
| Archived-number provenance failure (ρ 0.926 vs 0.9125; CG −0.082 vs −0.215) | `main.tex:279` |
| Per-epoch monitoring table & "τ erodes fastest" | `main.tex:317–338` |
| "No monitoring signal is inert" | `main.tex:350` |
| Protocol dependence of "top-1 inert" | `main.tex:343, 352` |
| Task-sensitivity spectrum (λ = +1 only) | `main.tex:356–363` |
| Checkpoint transfer table; τ vs CG across 7 | `main.tex:451–475` |
| CG protocol discrepancy (+0.033 vs +0.114) | `main.tex:471` |
| Template-conditional absolute level | `main.tex:484`; Table 8 `main.tex:491–500` |
| k-specific threshold; "change detector, not a health verdict" | `main.tex:502–524` |
| Seed spread; τ does not rank runs within a dataset; drop-DTD reversal | `main.tex:528`; Table 9 `main.tex:535–544` |
| DTD budget confound | `main.tex:546` |
| Offset unexplained (+3.62 ± 1.41); orthogonal displacement | `main.tex:548–565` |
| Limitations (a)–(g) | `main.tex:574` |
| Conclusion / recommendation form | `main.tex:579` |
| Related-work self-limitation | `related_work.tex:195–209, 296–307, 362–398` |

## Appendix B — Searches performed (so the "absent" claims are auditable)

- `overhead|wall-clock|runtime|seconds|GPU-hour|cost of computing|implementation` over `paper_a1/*.tex` → only `main.tex:308`, `highlights.tex:16`, and unrelated uses of "implementation" in the residual discussion (`main.tex:220, 225`).
- `early stop|early-stop|stopping|tripwire|threshold|alarm|deploy|practitioner` over `main.tex` → only `main.tex:45` (citation of *prior* early-stopping work), `main.tex:338`, `main.tex:507`, `main.tex:524`, `main.tex:570`.
- `checkpoint selection|model selection|which epoch|we recommend|recommend` over `paper_a1/*.tex` → recommendation sentences only; no selection experiment exists.
- No file in `paper_a1/` reports a monitoring *outcome* (there is no τ-triggered stopping run, no cost log, no selection ablation). `docs/_VOID_A1_tau_earlystop_results.md` (self-marked VOID) confirms a formal early-stopping comparison was still outstanding internally.

*Report written for the A1 desk-decision simulation. No manuscript file was modified.*
