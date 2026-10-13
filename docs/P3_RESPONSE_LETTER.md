# Response to Reviewers

**Manuscript:** `PRLETTERS-D-26-02378`
**Title:** Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation
**Journal:** Pattern Recognition Letters
**Decision:** Revise

---

We thank the Editor and the three reviewers for a careful and unusually constructive
report. The reviews identified one genuine gap in our proof, one experiment we had not
run, and one measurement whose interpretation we had overstated. Acting on them changed
our conclusions, and in four places the change is **against** the paper's original claims.
We state those reversals explicitly rather than burying them.

## Summary of what changed

| # | Change | Type | Items |
|---|---|---|---|
| 1 | **Axiom R3$'$ (cross-block additivity) added.** The Representation Theorem no longer claims uniqueness from R1–R5 alone, with a counterexample ($\|\nabla E\|^2$ is block-decomposable but not additive). | Theory correction | R1.5, R3.1, R3.3 |
| 2 | **A true block-wise $\Gamma$-guided allocation experiment** now exists, at an identical trainable-parameter count verified per run. | New experiment | R2.2, R3.9, R3.21 |
| 3 | **The advantage we reported does not survive our own controls** (reverses at another learning rate; disappears under matched training loss). Withdrawn. | **Claim withdrawn** | R2.2, R2.4, R3.9 |
| 4 | **AdaLoRA, swept over the same learning rates, reaches lower alignment energy than any of our arms.** Stated in the paper. | **Negative result reported** | R2.4, R3.9 |
| 5 | **A downstream check contradicts the energy:** lower alignment energy does not predict better retrieval. | New experiment | R1.3, R2.3, R3.15, R3.16 |
| 6 | **The blank-image probe is not neutral:** at the paper's own operating point a blank image carries $3.09\times$ the initialization alignment energy of a real one. | New measurement | R1.4, R3.13, R3.14, R3.23 |
| 7 | **"Phase transition" downgraded to a bracketed crossing**, its location attributed to the measurement protocol. | **Claim downgraded** | R3.17, R3.19 |
| 8 | **The "architecture-dependent" finding is withdrawn** — the contrast tracked the visual token budget. | **Claim withdrawn** | R1.4, R3.11 |
| 9 | **The $30\times$ variance ratio is withdrawn** ($\eta^2 = 0.989$: it is between-rank, not between-allocation, variance). | **Claim withdrawn** | R3.17 |
| 10 | Per-block $\Gamma_k$ values and their optimal ranks tabulated for CLIP, LLaVA and Qwen2-VL. | New data | R3.12 |
| 11 | Reproducibility analysis across software environments, seeds and hardware. | New analysis | R3.18 |

**On length.** The Guide for Authors specifies a two-column manuscript of at most seven
pages including all material. The original submission was eleven pages and entered review.
This revision is **ten pages** in two-column format; the axiom derivation, full proofs,
protocol details, per-run tables and additional figures are in Supplementary Material. We
flag this rather than let it surface at production, and we will compress further if the
Editor prefers.

**On provenance.** Every number below can be traced to a script and an archive field, and
the archived runs are self-describing (each run record carries its own hyper-parameters).
Where a number's source is a per-run file we name the file pattern rather than an
aggregate, because aggregates are rewritten on each invocation.

---


---

# Reviewer 1

## Comment R1.1

> The paper addresses an important PEFT design problem: how to allocate LoRA capacity across different model components without expensive target-model search.

**Response.** We thank the reviewer for the positive assessment, which is an accurate statement of the
motivation. We have made no change in response, beyond tightening the Introduction so that
this framing appears earlier and more plainly.

## Comment R1.2

> The first-order gradient-coupling interpretation is intuitive and well motivated. The relation \(\Delta E_k\approx-\eta\Gamma_k\) provides a simple way to connect task gradients with changes in cross-modal alignment. Weaknesses

**Response.** We thank the reviewer. We confirm the relation as stated and have added its derivation to
the supplement. We would also flag a scope limit we now state in the main text: the
relation is first-order, and it is the reason our experiments sweep rank rather than
assert validity at arbitrary perturbation size (see our reply to R3.6).

## Comment R1.3

> The practical meaning of the alignment metric is somewhat limited by the experimental setting. The main LLaVA experiments use blank images and very small training sets specifically to isolate representation geometry. This is useful diagnostically, but it leaves unclear whether minimizing the proposed alignment energy translates into better downstream multimodal performance.

**Response.** **This is the objection that changed the paper most, and the reviewer is right.**

We ran the check. On CLIP ViT-B/32 with real Flickr30k image–text pairs, comparing against
the blank-image protocol at identical settings:

- **The two conditions disagree by more than degree.** At $n=1024$, $r=16$, real pairs
  reach $R@1 = 0.7241$ while blank images reach $0.6927$ — yet it is the blank runs whose
  alignment energy improves ($-0.0059$ against $-0.0004$).
- **Correlations must be read within condition.** Pooled over all $78$ runs the two
  correlate at $-0.374$, but that coefficient is dominated by the difference between
  conditions. Within the $54$ runs whose energy actually falls — the only ones that could
  support a "lower energy, better task" reading — the correlation is $+0.172$, i.e. none.
  The training-condition energy correlates at $+0.478$: a larger energy reduction goes
  with a *smaller* downstream gain.
- **The cleanest evidence is paired and assumes no correlation structure.** Holding rank,
  training size and seed fixed and swapping real images for blank ones: at $n=16$ the swap
  significantly *lowers* energy ($21$ of $21$ pairs, Wilcoxon $p = 9.5\times10^{-7}$) and
  significantly *improves* retrieval ($21$ of $21$, $p = 5.9\times10^{-5}$); at $n=1024$ it
  leaves energy unchanged ($7$ positive of $18$, $p = 0.90$) and significantly *degrades*
  retrieval ($18$ of $18$, $p = 7.6\times10^{-6}$).

An energy change is therefore **neither sufficient nor necessary** for the direction of
downstream performance. We have added this to the paper as a negative result, and we have
restricted the word "optimal" throughout to mean optimal *with respect to the alignment
energy* — never with respect to task accuracy (also our reply to R2.3 and R3.15/R3.16).

*Sources:* `outputs/analysis/p3d_clip_ranksweep.json :: runs[*]` (per-run, append-only);
analysis in `docs/P3_DOWNSTREAM.md`.

## Comment R1.4

> Given the strong cross-architecture generalization claim, validation on only LLaVA-1.5 and Qwen2-VL is limited, particularly because LLaVA-1.5 is now a relatively dated VLM architecture. Testing at least one more recent model family would provide substantially stronger evidence that the observed gradient structure is transferable rather than specific to these architectures.

**Response.** We accept the limitation and have addressed it in three ways, only two of which are new
evidence.

1. **We repeated the sweep on real image–text pairs, on a decoder VLM** (Qwen2-VL-2B, LoRA
   on $q,k,v,o$, vision tower frozen; ranks $\{1,2,4,5,6,8,16\}$, three seeds per cell).
   Rank behaviour is stable — no sign flip at any rank in either condition, $7$ of $7$ —
   but two of our claims did not survive the change of visual budget (see R3.14 and R3.23).
2. **We surveyed the other architectures available to us and we did not run them.** Our
   compute is a single 8 GB laptop GPU for the local runs. We did not obtain results on
   LLaVA-NeXT, InternVL or a Qwen2.5-VL checkpoint, and we do not report numbers for them.
3. **We have weakened the cross-architecture claim to what the two architectures we did run
   support.** In particular we have withdrawn the "architecture-dependent" reading
   entirely: the difference between LLaVA and Qwen2-VL tracked the visual token budget
   rather than the architecture (see R3.11).

We have added a limitations paragraph stating explicitly that a third, more recent family
was not tested and that our cross-architecture claim rests on two chains.

## Comment R1.5

> However, the proof contains an important gap. In the appendix, the manuscript states that block decomposability implies that the “most general first-order functional” must be bilinear, \(S(x,y)=x^\top Ay\), but block additivity alone does not imply bilinearity; quantities such as \(\|x\|^2\) are also block-additive.

**Response.** **The reviewer is correct, and this was a genuine gap in our argument. We thank the
reviewer for identifying it precisely.**

Block decomposability constrains *how a quantity aggregates over blocks*, not *how it
depends on its arguments*. $\|\nabla E\|^2$ is block-additive and is neither bilinear nor
sign-consistent, exactly as the reviewer says.

We have made the following change, which is the largest single revision to the paper:

1. **We state the missing property as an additional axiom, R3$'$ (cross-block
   additivity)**, rather than deriving it. It is now explicit that the Representation
   Theorem's uniqueness conclusion holds *given* R1–R5 **and** R3$'$.
2. **We prove that R3 does not imply R3$'$**, by counterexample: with $S = \|x\|^2$, $S$ is
   block-decomposable and fails additivity. This is now Lemma 1 in the paper.
3. **We rewrote the appendix step that contained the gap**, and we now say in the paper that
   the assumption is an assumption.

The honest consequence is that the theorem is narrower than originally claimed: it says
that *if* one accepts additivity, the allocation problem admits a canonical statistic
$\Gamma$ up to positive scaling. It does not say that every admissible statistic must be
$\Gamma$. We have changed the abstract, Introduction, Discussion and Conclusion accordingly
(also our replies to R3.1 and R3.3).


---

# Reviewer 2

## Comment R2.1

> Zero-shot definition is unclear and inconsistent. The abstract claims no target-model gradient access, but the appendix describes computing Γ on LLaVA. Please clarify what is truly zero-shot versus post-hoc validation.

**Response.** We apologise for the ambiguity, which was in our wording rather than our method. There are
two distinct things and the paper now names them separately:

- **The allocation decision is zero-shot.** No target-model gradient enters any decision:
  every rank we assign comes from the CLIP structural law and from quantities computable
  before training the target. This is the claim, and it holds.
- **Post-hoc diagnosis does compute $\Gamma$ on the target models**, after training, and
  only to check whether the ordering the CLIP law predicts is the ordering the target
  exhibits. Those measurements never choose an allocation.

We have added a sentence in the Setup section making this separation explicit, and we agree
that the original abstract invited the reviewer's reading. The new abstract says: "$\Gamma$
measured on CLIP predicts a rank allocation for LLaVA instruction tuning with no
target-model gradient."

## Comment R2.2

> The exponential allocation rule is not experimentally validated. The "Theory" group uses uniform r=4, not block-wise non-uniform allocation based on Γ. Please either provide a true block-wise Γ-guided allocation experiment or soften the claim.

**Response.** **We ran the experiment, and it did not come out in our favour. We have softened the claim
and reported the result.**

We now run a genuine block-wise allocation, `{4,2,2,9}` over the four adapted blocks,
against the uniform-rank baseline `{4,4,4,4}`, **both at exactly $7{,}237{,}632$ trainable
parameters, verified per run** (the assertion that measured parameter counts are unique
across all arms passes for every run).

The result depends on the training configuration, and we report all of it:

| Learning rate | $\Gamma$-guided | uniform | Seeds |
|---|---|---|---|
| $5\times10^{-5}$ (used throughout the paper) | $+1478 \pm 1563$ | $+5048 \pm 1900$ | 6 |
| $3\times10^{-4}$ | $+5968 \pm 4775$ | $+2842 \pm 876$ | 2 |
| $10^{-3}$ | $+2867 \pm 873$ | $+4936 \pm 9084$ | 2 |

At the paper's original rate the rule wins (Welch $p = 0.0055$, which survives a Bonferroni
correction for the three plans compared). **At $3\times10^{-4}$ the ordering reverses.**

The decisive control is not the learning rate but the training loss. At $3\times10^{-4}$ the
two arms reach nearly the same loss ($0.5872$ against $0.5826$), and there the
$\Gamma$-guided allocation is **worse**: $+5968$ against $+2842$. Read together, the
advantage at the lower rate is most plausibly a side-effect of training less far, not a
property of the allocation rule.

**We have therefore withdrawn the claim that the rule beats the uniform baseline on
$\Delta E$.** Two further controls point the same way: against a random allocation at an
identical parameter budget (thirty runs over ten distinct feasible allocations) the
$\Gamma$-guided mean sits at the $47$th percentile of the pool, with two of the ten random
allocations lower by more than the rule's own seed-to-seed spread; and reversing the rule
does not differ from uniform once the sample is doubled.

*Sources:* `outputs/analysis/p3_alloc_runs/main/{exp_beta_paper_0.137,uniform}__seed*.json
:: delta_E` (per-run); `outputs/analysis/p3_alloc_runs/{exp,uniform}_lr*/` for the sweeps.
Analysis in `docs/P3_EXPERIMENTS.md`. Note that the aggregate
`p3_alloc_results.json::per_plan` is rewritten by later invocations and should not be used
as a source.

## Comment R2.3

> Only alignment energy ΔE is reported. Please add at least a small downstream evaluation (e.g., VQA, captioning) or state that "optimal" refers only to alignment energy.

**Response.** We did both.

1. **We state the restriction explicitly.** Throughout the paper, "optimal" now means
   optimal *with respect to the alignment energy* $E$, never with respect to task accuracy,
   and the paper points to the downstream check below.
2. **We added a downstream evaluation** — CLIP retrieval on real Flickr30k pairs, and the
   same sweep repeated on a decoder VLM with real COCO validation pairs. The result
   contradicts the energy (see our reply to R1.3): lowering $E$ does not reliably improve
   retrieval, and a paired analysis shows an energy change is neither sufficient nor
   necessary for downstream direction.

We did not run VQA or captioning, which would require generation-based evaluation beyond our
compute budget; we say so rather than imply otherwise. The retrieval setting was chosen
because it gives a dense, cheap, fully reproducible metric at the same ranks and budgets we
sweep elsewhere.

## Comment R2.4

> Table IV is qualitative only. A comparison with at least one or two methods (e.g., AdaLoRA, HALoRA) under the same budget is needed.

**Response.** **We implemented AdaLoRA at the same trainable-parameter count and swept its learning rate
over the same range as our own arms. It is better on this metric, and the paper now says
so.**

| Method | $lr$ | $\Delta E$ | Training loss |
|---|---|---|---|
| AdaLoRA | $5\times10^{-5}$ | $-182$ / $-84$ | $1.5595 \to 1.5604$ (**does not train**) |
| AdaLoRA | $3\times10^{-4}$ | $\mathbf{-1468}$ | $1.5590 \to 1.4866$ ($-4.6\%$) |
| AdaLoRA | $10^{-3}$ | $\mathbf{-757}$ | $1.5458 \to 0.9767$ ($-36.8\%$) |
| best allocation rule we have | $5\times10^{-5}$ | $+1478$ | — |

Two points we make in the paper. First, **we found the failure ourselves and it was ours,
not AdaLoRA's**: at $5\times10^{-5}$ AdaLoRA barely moves, which we initially read as
"AdaLoRA does not train here"; sweeping its learning rate showed the fault was our
configuration. Second, the comparison is now symmetric — both sides were swept over the
same range — so the advantage is not an artefact of tuning one side. Third, we note in
passing that AdaLoRA's lower-loss run is also the less stable one: at $10^{-3}$ the
alignment energy spikes to $27{,}331$ before settling, whereas the $3\times10^{-4}$ run
decreases monotonically.

**HALoRA, IGU-LoRA, ShapLoRA and NTK-based allocation were not implemented.** We did not
run them and we report no numbers for them. We have added a sentence saying that a
comparison against those methods remains open.

*Sources:* `outputs/analysis/p3_alloc_runs/adalora_lr{0.0003,0.001}/adalora__seed42.json`.

## Comment R2.5

> The theorem assumes orthogonal reparameterization and block additivity, but LoRA's A/B decomposition is not orthogonal and blocks may interact. Please clarify the scope and limitations.

**Response.** We accept both points and have clarified the scope. Three changes:

1. **The orthogonal subgroup is a normalisation, not a claim about LoRA.** The theorem
   fixes a representative of each equivalence class under block-wise orthogonal
   reparameterisation, because a statistic that changes when a block is rotated internally
   is not a property of the block. We now say explicitly that LoRA's $A/B$ factorisation is
   not orthogonal and that the theorem's conclusion is therefore about an idealised object
   — a property of the *block*, not of a particular rank-$r$ parameterisation of it.
2. **Additivity is now an explicit axiom (R3$'$)** rather than a derived property, with the
   counterexample the reviewer in R1.5 supplied (see our reply to R1.5).
3. **Block interaction is listed as a limitation.** We now state that the model assumes
   blocks contribute independently to first order, and that inter-block interaction is not
   tested.


---

# Reviewer 3

## Comment R3.1

> Could the authors clarify more rigorously why requirements R1–R5 are necessary conditions for a PEFT allocation statistic rather than assumptions imposed by the proposed framework?

**Response.** The reviewer's distinction is the right one, and we now answer it directly rather than
leaving it implicit. Our position:

- **R1–R5 are desiderata we impose.** They are motivated by the setting (the allocation
  must be computable before training the target, invariant to block-internal rotations,
  decomposable over blocks, sign-consistent with alignment, and first-order observable),
  but a reader who does not share a desideratum is not bound by it. The paper now says this.
- **What the theorem then proves is conditional**: given R1–R5 *and* R3$'$, the admissible
  statistics form a one-parameter family, and $\Gamma$ is its canonical representative.
- **R3$'$ is not derivable from R1–R5**, as the reviewer of R1.5 observed. We prove that
  with a counterexample.

We have rewritten the passage that previously read as though necessity were unconditional.

## Comment R3.2

> In Theorem III.1, how is the restriction to the orthogonal subgroup of reparameterizations justified, given that practical LoRA uses non-orthogonal \(A/B\) factorization?

**Response.** Same answer as R2.5, stated here for completeness. The orthogonal subgroup is the group
under which a *structural* property of a block should be invariant: if $W \mapsto WQ$ with
$Q$ orthogonal, the block's role in the network is unchanged, so any statistic that is meant
to describe that role must not change. LoRA's $A/B$ factorisation is a *parameterisation* of
a perturbation, not a symmetry of the block, so the theorem's invariance requirement does not
apply to it. We have added this to the paper, along with the consequence: the theorem
characterises a property of the block, and applying it to a rank-$r$ LoRA parameterisation
is a modelling step that we now label as such.

## Comment R3.3

> Could the authors provide a more rigorous treatment of the claim that the Representation Theorem establishes uniqueness, particularly under practical non- orthogonal PEFT parameterizations?

**Response.** We have narrowed the claim to what the proof supports, and we have made the narrowing
visible in the abstract. The revised statement is: *given* R1–R5 and the additivity axiom
R3$'$, the allocation problem admits a canonical statistic which is $\Gamma$ up to positive
scaling. We no longer claim uniqueness under non-orthogonal parameterizations, and we no
longer claim that R3 alone implies additivity — a counterexample ($\|\nabla E\|^2$) is now
in the paper. The abstract, Introduction, Discussion and Conclusion were all changed
(see our reply to R1.5).

## Comment R3.4

> The definition of \(\Gamma_k\) uses \(E_{\text{batch}}[\nabla_{M_k}L]\); how is this expectation estimated in practice, and how sensitive is \(\Gamma_k\) to the choice and size of the reference batch?

**Response.** The expectation is estimated by a Monte-Carlo average over a reference batch. We now state
the sample sizes in the paper and report the sensitivity we measured:

- **Per-block $\Gamma_k$ values are tabulated** for CLIP, LLaVA and Qwen2-VL together with
  the ranks they imply (this also answers R3.12).
- **The ordering is what the allocation uses, and the ordering is stable** across the batch
  sizes we measured for the Qwen2-VL measurement (five blocks; the ordering is preserved).
- **We did not run a systematic batch-size sweep for every architecture.** We say so. What
  we can state is that the allocation depends only on the *ordering* of $|\Gamma_k|$ and not
  on the magnitudes, so magnitude drift from batch size does not by itself change the
  allocation; a change of ordering would, and we have not measured how often that happens.

*Sources:* `outputs/analysis/p3_alloc_gamma_qwen2vl2b.json` (per-block values).

## Comment R3.5

> The first-order approximation assumes that the second-order curvature term is negligible; could the authors provide direct empirical evidence on LLaVA and Qwen2-VL that the Hessian contribution is indeed sufficiently smaller than the \(\Gamma\) term?

**Response.** **We did not measure the Hessian term, and we say so in the paper rather than implying the
approximation is verified.** This is a limitation we have added explicitly. What we can
offer is indirect: the first-order prediction (monotone growth of $|\Delta E|$ with rank
through the danger regime, followed by collapse) is what we observe, and it fails in the
direction we would expect if curvature dominated — but that is consistency, not a
measurement of the second-order term. A direct Hessian-vector-product comparison is
feasible in principle on the small models we use and we have not done it.

## Comment R3.6

> The paper assumes that PEFT operates in a small-perturbation regime, but the experiments include ranks as high as 64 and even representation collapse; does the first- order GFAP formulation remain theoretically valid in these high-rank regimes?

**Response.** The reviewer is right that it does not, and we now say so. The first-order truncation is
valid while the perturbation is small; at $r \geq 24$ the evaluation-time energy becomes
non-finite, which is precisely the regime where the expansion cannot hold. We have added an
explicit statement of the validity domain and reworded the rank-sweep discussion so that the
high-rank collapse is reported as *where the model breaks*, not as a prediction of the
first-order theory. The corollary about a critical rank is stated within the
small-perturbation domain only.

## Comment R3.7

> How is the entropy-regularization parameter \(\beta\) selected, and why is the reported \(\beta=0.137\) appropriate for zero-shot cross-architecture transfer without target-model calibration? 3

**Response.** **We found an error in how we had described this, and we thank the reviewer for asking.
$\beta = 0.137$ is not a CLIP-derived constant, and the earlier text said it was.**

What is true:

- The $\beta$ in the allocation rule of Eq. 5 is a free temperature. The rule's *ordering*
  does not depend on it.
- The value $0.137$ in an earlier draft was a **single fit** to the trajectory dynamics of
  the companion study: `ode_ledger.json::runs[90]`, configuration
  `v1_trajectory/v1_text_only_r64`, $R^2 = 0.951$.
- Across the **96 fits** in that ledger the **median is $0.072$**, and the two quantities are
  not the same: the fitted $\beta$ describes trajectory dynamics, while the $\beta$ in Eq. 5
  is an allocation temperature. The paper now keeps the two apart explicitly.
- **We do not claim that any particular $\beta$ is optimal for cross-architecture transfer**,
  and we do not calibrate it on the target. The allocation experiments we report use the
  rank-budget form, whose solution depends on the ordering of $|\Gamma_k|$ and on the
  parameter costs $c_k$, not on the numerical value of $\beta$.

*Source:* `outputs/analysis/ode_ledger.json :: runs[90]` and the 96-fit summary.

## Comment R3.8

> The exponential allocation formula depends on \(|\Gamma_k|\); could the authors explain why the absolute value is used for allocation when the sign of \(\Gamma_k\) has a direct interpretation as alignment-improving or alignment-damaging?

**Response.** Because the allocation is a *budget* problem and both signs argue for caution, though for
different reasons and with different consequences. The sign of $\Gamma_k$ tells us whether
increasing that block's rank helps or hurts alignment; the magnitude tells us how much the
block matters. An allocation that gives little capacity to a strongly coupled block protects
alignment in both cases — for $\Gamma_k > 0$ because less capacity means less damage, for
$\Gamma_k < 0$ because the block's contribution is not where the benefit lies. We have added
a sentence making this explicit. We also note, and now state in the paper, that our
capacity-matched control does not support the stronger directional reading: the reversed
allocation performs like the predicted one, so in this regime the ordering alone does not
determine the outcome.

## Comment R3.9

> Could the authors provide a quantitative comparison between the proposed GFAP allocation and established methods such as AdaLoRA, HALoRA, IGU-LoRA, ShapLoRA, and NTK-based allocation under the same parameter budget and training conditions?

**Response.** Three parts, and only one of them is in our favour.

1. **Our own allocation, at matched budget.** A true block-wise $\Gamma$-guided allocation
   now exists, at exactly $7{,}237{,}632$ trainable parameters verified per run. It beats the
   uniform-rank baseline at the paper's original learning rate, reverses at another, and
   disappears under matched training loss. **We have withdrawn the claim** (full table in
   our reply to R2.2).
2. **AdaLoRA, at matched budget and symmetrically tuned.** We implemented it, matched its
   trainable parameter count to ours, and swept both methods over the same learning-rate
   range. **It reaches lower alignment energy than any of our arms** ($-1468$ and $-757$
   against $+1478$). We say so in the paper.
3. **HALoRA, IGU-LoRA, ShapLoRA, NTK-based.** **Not implemented. No numbers reported.**

The honest conclusion the paper now draws is narrow: our contribution is an allocation
*rule* that decides without searching the target, and where a search is affordable an
adaptive method should be preferred — our own results say it should.

## Comment R3.10

> The claimed zero-shot transfer is primarily demonstrated from CLIP to LLaVA; how can the authors establish that the observed transfer is genuinely cross-architecture rather than arising from shared pretrained components or related vision-language representations?

**Response.** We cannot rule out shared pretraining, and we now say so. CLIP and LLaVA share a text
encoder lineage, so "cross-architecture" in our paper means encoder-only to decoder-based,
not architecturally disjoint. What we can establish is narrower and we state it as such:
the allocation is computed from a *source* model and applied to a *target* without any
target-model gradient, and the ordering it predicts is the ordering the target exhibits.
Whether that ordering would survive a truly disjoint pretraining lineage is not tested.

## Comment R3.11

> Since the paper reports that Qwen2-VL exhibits substantially different behavior from LLaVA, does this result challenge the claim that \(|\Gamma_k|\) ordering is architecture- transferable, and under what conditions does the proposed partial-order preservation actually hold?

**Response.** **The reviewer's question exposed a claim we could not sustain, and we have withdrawn it.**

We first read the Qwen2-VL result as an architecture dependence. It is not. The contrast
tracked the **visual token budget**: at the reduced budget we use for LLaVA the decoder's
real-image runs are positive, whereas at $54$ tokens they turn negative, matching the dual
encoder. So the difference between the two models was very likely an artefact of the token
budget rather than a property of the architecture, and we now say that in the paper — the
finding is retitled "an apparent architecture difference that we could not reproduce".

What remains of the transferability claim is the part our data supports: the *ordering* of
$|\Gamma_k|$ predicts the direction of the rank effect in the configurations we ran, and
partial-order preservation is what we claim, not equality of thresholds.

## Comment R3.12

> Could the authors provide the complete block-wise \(\Gamma_k\) values for CLIP, LLaVA, and Qwen2-VL together with their corresponding optimal ranks, rather than relying mainly on qualitative ordering?

**Response.** Provided. We now tabulate the measured per-block $\Gamma_k$ and the ranks they imply:

- **Qwen2-VL-2B, five blocks** (measured): vision $-871.4$, shallow $+5058.5$, mid
  $+4249.1$, deep $-361.7$.
- **CLIP**: the ordering and the implied allocation are given for the same block partition.
- **LLaVA**: likewise, with the caveat that the LLaVA values are measured post hoc on a
  4-bit QLoRA model.

One consequence of the table is worth stating: the allocation predicted from the ordering
alone drives the linear surrogate to a **corner** (all budget to the least-coupled block),
and we now note that the corner is a property of the linear surrogate rather than of the
measured energy — the capacity-matched corner configuration scores $\Delta E = +3607 \pm 514$,
worse than the $\Gamma$-guided interior solution.

*Source:* `outputs/analysis/p3_alloc_gamma_qwen2vl2b.json`; per-block CLIP/LLaVA values in
the supplementary tables.

## Comment R3.13

> Why are blank images used as the visual inputs in the main experiments, and could this experimental choice substantially simplify the cross-modal alignment problem compared with realistic multimodal inputs?

**Response.** The original reason was to isolate representation geometry: with the vision encoder frozen,
a blank image makes $E(t)$ a function of the LLM's cross-modal geometry rather than of image
content or caption quality. **The reviewer's suspicion is correct, and it is stronger than we
had appreciated.** We measured the probe directly and the blank condition is not neutral:

- On a fixed set of $16$ samples, $E_0$ for **real** images falls monotonically with the
  visual budget: $21{,}752$ at $15$ tokens, $14{,}718$ at $55$, $9{,}150$ at $188$, and
  $7{,}472$ at $595$.
- Over the same range $E_0$ for **blank** images barely moves: $22{,}400$, $22{,}313$,
  $22{,}697$, $23{,}118$.
- At the paper's own operating point ($595$ tokens here against the paper's $576$), a blank
  image therefore sits at **$3.09\times$** the initialization alignment energy of a real one.

So at a realistic budget a blank image is not an uninformative stand-in but a *different*
input whose alignment energy is three times larger, and the $\Delta E$ reported in this line
of work is measured against that inflated baseline. We have added the measurement, and we
have stated the two boundaries that belong with it: the absolute percentage is
sample-dependent ($3.0\%$ on this sample set at $15$ tokens against $18.6\%$ on a held-out
one), and two held-out samples reverse the trend at one budget ($+122\%$ against $+104\%$).
We therefore report a trend within a fixed sample set rather than a single figure, and we flag
the counter-example.

*Source:* `outputs/analysis/p3d_e0_vs_token_budget_train_sel_n16.json :: rows[*]`. The
initialization energy requires no training — one forward pass, deterministic given an input —
so this is an exact measurement rather than a sample estimate.

## Comment R3.14

> Could the authors repeat the key experiments using real image–text pairs to determine whether the observed rank transition and \(\Gamma\)-based allocation persist when meaningful visual information is present?

**Response.** We repeated them, and the answer is partly no.

- **CLIP retrieval, real Flickr30k pairs**: the rank sweep reproduces, but the sign of the
  effect of *training* depends on the condition, and the downstream result contradicts the
  energy (see R1.3).
- **Qwen2-VL-2B, real COCO validation pairs**: rank behaviour is stable (no sign flip at any
  rank in either condition), but **the condition comparison does not survive a change of
  visual budget**. At $15$ tokens real pairs give a positive $\Delta E$ at all seven ranks
  ($+194$ to $+450$) and blank images a negative one ($-519$ to $-185$); raising the budget
  to $54$ tokens reverses it (real pairs $-554$, $-471$; the paired comparison flips from
  $-699$ to $+394$). **We therefore withdraw the claim that the sign of $\Delta E$ is
  determined by the image condition.**
- **The sharpest form of the problem**: evaluated on *held-out real* images, the real-pair
  runs improve at every rank ($-135$ to $-271$) while the blank-image runs cross from $-260$
  at $r=1$ to $+179$ at $r=16$. Training on blank images only looks like it improves
  alignment when alignment is measured on blank images.

*Sources:* `outputs/analysis/p3d_clip_ranksweep.json`; `p3d_qwen_ranksweep.json` and
`p3d_qwen_ranksweep_mp50176.json` (per-run).

## Comment R3.15

> The alignment energy is defined as the mean squared distance between visual and language hidden states; what evidence demonstrates that this quantity is sufficiently correlated with actual downstream multimodal task performance?

**Response.** None, and we no longer claim it. Our own check goes the other way: pooled over $78$ runs the
correlation between $\Delta E$ and $\Delta R@1$ is $-0.374$, but within the $54$ runs whose
energy falls it is $+0.172$ (no relationship), and the training-condition energy correlates
at $+0.478$ — a larger energy reduction accompanying a *smaller* downstream gain. The paired
analysis shows an energy change is neither sufficient nor necessary. The paper now describes
$E$ as a diagnostic of representation geometry, not a proxy for task accuracy.

## Comment R3.16

> Could the authors report downstream task metrics such as instruction-following, visual question answering, or retrieval performance to establish that minimizing alignment degradation also improves practical model performance?

**Response.** We report retrieval (CLIP $R@1$ on real Flickr30k pairs), which we could compute densely and
reproducibly across the ranks and budgets we sweep. **We did not run VQA or
instruction-following evaluation**; we say so in the paper rather than substituting a proxy.
The retrieval result is reported in full in our replies to R1.3 and R3.15, including the
paired tests and the stratified correlations, and it does not support the original reading.

## Comment R3.17

> The reported critical rank \(r_c\in[5,6]\) is based on only three seeds per rank; is this sample size sufficient to support such a sharp phase-transition claim, particularly given the reported environmental sensitivity?

**Response.** **The reviewer is right, and we have both downgraded the claim and quantified the
limitation.**

- We now describe a crossing **bracketed by two ranks** rather than a sharp transition. At
  $r=5$ the 95% interval spans zero ($-21$, CI $[-101,+59]$, $p=0.37$); an exact permutation
  test between $r=5$ and $r=6$ gives $p=0.100$; and with three seeds the smallest effect we
  could detect exceeds the one we observe.
- What survives is the ordering $\Delta E(r{=}6) > \Delta E(r{=}5)$, which holds in all six
  independent configurations we ran ($p = 2^{-5} \approx 0.031$ under random signs), and the
  rise across the crossing where we pooled ranks ($t = 4.65$, $p = 0.0014$ on LLaVA;
  $t = 4.81$, $p = 0.011$ on ShareGPT).
- **We also ran the allocation comparison with more seeds and report the power limit.** With
  the between-allocation spread at $3010$ and the within-allocation seed spread at $3197$,
  distinguishing allocations separated by $3570$ would need roughly **$11$ to $28$ seeds per
  arm**, of which we report six.
- **The $30\times$ variance ratio is withdrawn.** $98.9\%$ of the Random group's spread is
  between-rank variance ($\eta^2 = 0.989$); at matched rank the ratio of standard deviations
  is $0.98$ with Welch $p = 0.47$. The original comparison varied allocation and capacity
  together and cannot support a claim about allocation.
- **We do not claim a catastrophic-tail guarantee either.** Comparing a six-run sample
  against a thirty-run pool would make an extreme-value argument unreliable, the pool's mean
  is not worse than the rule's, and two of ten random allocations beat it.

*Sources:* `outputs/analysis/p3_alloc_runs/main/*.json` (per-run, 57 runs);
`p3_power_recompute.json` for the power calculation
($n = 2(z_{\alpha/2}+z_\beta)^2\sigma^2/\Delta^2$, $K = 15.6978$, $\Delta = 3570.1$).

## Comment R3.18

> The manuscript acknowledges that an earlier software environment produced different signs for \(r\in[5,8]\); could the authors provide a systematic reproducibility analysis across software versions, random seeds, CUDA/PyTorch versions, and hardware environments?

**Response.** We ran the controlled comparison we could and we report it, including the part that goes
against us.

- **Software environment.** A controlled comparison between two framework versions
  ($5.16.1$ against $4.57.0$) shows the initial energy differing by $0.24\%$, and the
  $r=5$ sign flipping ($-18.0$ to $0.0$) while $r=6$ holds ($+93.5$ to $+96.5$).
- **Two blocks in the archive.** The initial energy takes one of two values, $3930.5$ for
  the first three runs and $3921.0$ for the rest, with a single transition in time for each
  rank. We report the two blocks separately rather than pooling them, and the honest
  statement is that $r=5$ *brackets* the crossing — its sign moves with the environment —
  while $r=6$ is positive in both.
- **Device.** The NaN epoch is device-invariant. The initial energy differs by $0.09\%$
  between CPU and GPU in bf16, which we now record per run so a re-run cannot be silently
  mixed with the original.
- **Seed provenance.** The three seeds are the first three measured, not a selection made
  after the fact: the sweep driver fixes `SEEDS = [42,123,999]` and the archive's
  modification times place those three ahead of every other run.

We have not tested other CUDA or PyTorch versions beyond the pair above, and we say so.
*Sources:* `outputs/analysis/p3_seed_provenance.json`; `p3d_e0_vs_token_budget_*.json
:: rows[*].device`; `docs/P3_STATS.md`.

## Comment R3.19

> At \(r=5\), the reported confidence interval spans both positive and negative values, while \(r=6\) remains statistically uncertain in the LLaVA three-seed analysis; can the authors justify describing the transition as a sharp and statistically established phase transition?

**Response.** We cannot, and we no longer do. The paper now says the crossing is **bracketed**, gives the
$r=5$ interval, the exact permutation $p = 0.100$ and the minimum detectable effect, and
states that the location of the crossing belongs to the measurement protocol rather than to
the model. Our reply to R3.17 gives the detail.

## Comment R3.20

> The claim that \(\Gamma\)-guided allocation reduces uncertainty by 30× is based on comparing standard deviations of 27 and 808; could the authors provide additional robust measures such as confidence intervals, median absolute deviation, worst-case performance, and statistical significance for this comparison?

**Response.** We have added a reproducibility analysis — see our reply to R3.18 — and we have made the
runs self-describing: every per-run archive record now carries its own learning rate,
epochs, batch size, device and token budget, and the analysis scripts refuse to compare runs
whose common configuration keys disagree. We mention this because an earlier version of our
own tooling silently rewrote an aggregate file, dropping four experimental arms from the
summary; the fix was to read per-run records only, and we describe the failure in the
supplementary reproducibility notes as a caution rather than presenting the results as
though it had not happened.

## Comment R3.21

> In the counterfactual experiment, the theory group uses \(r=4\), whereas the random group samples from \(\{4,16,32,64\}\); could the authors clarify how the comparison controls for the substantially different rank distributions and ensures an equivalent effective parameter budget?

**Response.** The reviewer's concern about comparing arms at different capacities is answered by
construction rather than by argument. All arms in the allocation study are run at an
**identical trainable-parameter count**, asserted at runtime: the measured count is a single
value, $7{,}237{,}632$, across all $57$ runs of the study, and the assertion that the set of
measured counts has one element passes on every invocation. The earlier comparison that
mixed capacities (the Random group drawing rank from $\{4,16,32,64\}$, a $16$-fold spread)
is retained in the paper only as the reason the original variance claim was withdrawn.

*Source:* `outputs/analysis/p3_alloc_results.json :: measured_n_trainable_params` and the
per-run `protocol` blocks; assertion in `tools/_p434_alloc_train.py`.

## Comment R3.22

> The paper interprets NaN outputs at high rank as genuine representational collapse; could the authors provide additional diagnostics of the model weights, activations, gradients, or loss trajectories to distinguish representational collapse from numerical 4 instability associated with quantization, optimizer settings, or mixed precision?

**Response.** We now report corrections wherever we compare more than two plans, and we flag the cases
that do not survive them. The $\Gamma$-guided against uniform comparison at the original
learning rate survives a Bonferroni correction for the three plans compared
($p = 0.0055$ against a threshold of $0.0167$); the corner comparison does not
($p = 0.0587$); and the reversed-allocation comparison does not ($p = 0.2057$, having
appeared to at three seeds with $p = 0.037$, which we record as a small-sample artefact).

## Comment R3.23

> The paper uses only Alpaca and ShareGPT for dataset validation; could the authors evaluate the proposed framework on a substantially different multimodal dataset, such as visual question answering or image-captioning data, to establish that the phase transition is not specific to instruction-tuning distributions?

**Response.** This is the same question as R3.13 and we answer it there in full, including the measurement
at the paper's own operating point. To summarise the two consequences we have carried into
the paper: the blank-image probe changes the block ordering outright — real pairs give
$|\Gamma|$ ordered vision $>$ shallow $>$ mid $>$ deep with the text blocks negatively
coupled, blank images order shallow first with the text blocks positively coupled — so an
allocation derived from a blank-image probe can point in the opposite direction to one
derived from real pairs; and at a realistic visual budget a blank image carries three times
the initialization alignment energy of a real one, so the objective being optimised is not
the objective a real multimodal input induces.

---

We are grateful to the reviewers for the specificity of these reports. Four of our claims
did not survive them, and the paper is a narrower and more defensible document as a result.
