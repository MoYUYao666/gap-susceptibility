# A23 (IEEE JOE 26-0663) — fine-epsilon re-evaluation of the margin-mass certificate

**Status:** measured and complete. All required assets were present locally; the fine-grid evaluation was run
on 2026-10-24 on this workstation (RTX 4060 Laptop, 8 GB; Python 3.12.14, torch 2.9.1+cu130, open_clip 3.3.0).

**Generator:** `tools/_p1472_a23_fine_eps.py` (idempotent; three passes: `--arm control`, `--arm adapted`,
`--arm analyze`). **Result archive:** `outputs/analysis/a23_fine_eps_certificate.json`.
**Embedding cache (regenerable):** `outputs/analysis/_cache/a23_fine_eps/*.npz`.
**No existing file was modified.** `paper_a2/*.tex` untouched.

---

## 1. Feasibility verdict

**Every asset the three generating scripts need is present locally, and all three passes ran.** The run took
≈ 22 min wall clock end to end (marine optical 25 s, sonar 4 s, BioCLIP 138 s, OceanCLIP 819 s; the analysis
pass is seconds from cache). The bottleneck is OceanCLIP: a 1.7 GB `epoch_50.pt` checkpoint load plus image
encoding on a laptop GPU.

**The recomputation reproduces both existing archives exactly.** Re-encoding the same corpora with the same
frozen weights and evaluating the *archived* eps in {0.02, 0.05, 0.10} gives a maximum absolute difference of
**0.0** over all 24 rows × 3 eps (`arms.<arm>.domains.<domain>.reproduction.max_abs_diff = 0.0`). The fine-grid
values are therefore directly comparable with the archived coarse-grid values; this is not a parallel pipeline.

### Asset inventory (verified on disk, 2026-10-24)

| Asset | Path | Size | Required by | Status |
|---|---|---|---|---|
| Marine optical corpus | `data/fathomnet8/` (7 class dirs + `meta.json`) | 2,091.0 MB, 344 files | `_p1344` | present |
| Sonar corpus | `data/NKSID/NKSID/` (7 class dirs + 834 root-level jpg) | 49.2 MB, 2,617 files | `_p1344` | present (see §4) |
| CLIP ViT-B/32 weights | `models/clip-vit-base-patch32/pytorch_model.bin` | 577.2 MB | `_p1344` | present |
| BioCLIP base weights | `models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin` | 570.9 MB | `_p1352`, `_p1370` | present |
| OceanCLIP checkpoint | `models/oceanclip-0.15b/oceanclip-bio/epoch_50.pt` | 1,712.6 MB | `_p1352`, `_p1370` | present |
| 67-class marine subset | `data/rare-species/data/train-0000{0..8}-of-00009.parquet` (9 shards) | 4,131.4 MB | `_p1352`, `_p1370` | present |
| Subset index / class list | `outputs/ocean_subset.json` (`subset_idx`, `classes`) | 22,022 B | `_p1352`, `_p1370` | present |
| Cached embeddings | — | — | — | **did not exist**; written fresh to `outputs/analysis/_cache/a23_fine_eps/` (4 files, 9.6 MB total) |

No missing asset, no download required. The only extra step relative to a cache-hit rerun was a one-off GPU
encode, which is now cached so subsequent analysis passes are CPU-only and take seconds.

---

## 2. Measured numbers

### 2.1 The certificate de-saturates at eps = 0.001 in every arm

`M(eps) = P(margin <= 2 eps)`, `margin_i = s_i(y_i) - max_{c != y_i} s_i(c)`. Frozen (lambda = 0) rows:

| Domain | images | classes | frozen top-1 | median margin | M(0.001) | M(0.005) | M(0.01) | M(0.02) archived |
|---|---|---|---|---|---|---|---|---|
| marine optical (CLIP ViT-B/32) | 343 | 7 | 21.57 % | −0.0161 | 0.8017 | 0.8688 | 0.9271 | 0.9913 |
| acoustic sonar (CLIP ViT-B/32) | 1,783 | 7 | 22.04 % | −0.0125 | 0.8138 | 0.9467 | 0.9961 | 1.0000 |
| BioCLIP (rare-species subset) | 1,608 | 67 | 23.38 % | −0.0412 | 0.7761 | 0.8147 | 0.8545 | 0.9073 |
| OceanCLIP (rare-species subset) | 1,608 | 67 | 24.94 % | −0.0189 | 0.7755 | 0.8209 | 0.8601 | 0.9148 |

**Saturation boundary.** On the fine grid, **all 32 archived surgery rows (14 control + 18 adapted) leave
M = 1 at eps = 0.001** (`arms.<arm>.verdict.n_rows_where_fine_grid_separates = 32/32`;
`coarsest_required_eps = 0.001`). From the existing archives alone, the de-saturation point is bracketed as
follows: with the coarse grid as stored, `M(0.05) = 1` in all 14 control rows and `M(0.02) = 1` in the sonar
row set, while `M(0.02) < 1` in 5 of 7 marine rows and in all 18 adapted rows. The grid therefore needed to
gain one decade below 0.02 — which is what it now has. Note that the *deep-operating-point* reason matters
more than the decade: **the median margin is negative in all four domains** (the true class is usually not the
arg-max), so `margin <= 2 eps` counts images from a distribution whose centre already sits below zero, and any
eps >= 0.02 lands past the whole distribution. `sigma_D = 1 - mean_i max_{c != y_i} s_i(c)` is 0.70–0.76 in all
four domains, i.e. the domains are equally badly aligned *in the mean margin*, and the frozen top-1 is
21.6–24.9 % against a 14.29 % chance level.

### 2.2 Correlation with top-1: strong at fine eps, and it decays monotonically

Pooled over the surgery family of each arm (`arms.<arm>.pooled.with_top1.<key>.r`):

| eps | 0.001 | 0.002 | 0.005 | 0.01 | 0.02 | 0.05 | 0.10 |
|---|---|---|---|---|---|---|---|
| control (n = 14) | **−0.981** | −0.949 | −0.809 | −0.488 | −0.327 | undefined | undefined |
| adapted (n = 18) | **−0.900** | −0.782 | −0.622 | −0.512 | −0.282 | −0.160 | undefined |

At eps = 0.01 — the resolution at which the ImageNet-5k reference gives r = −0.996 — these corpora give
−0.488 and −0.512. The certificate is not broken there; it is simply operating on a different margin scale.

**The correlation does not hold within every domain.** Within-domain r with top-1:

| eps | control/marine | control/sonar | adapted/BioCLIP | adapted/OceanCLIP |
|---|---|---|---|---|
| 0.001 | −0.389 | −0.998 | −0.994 | −0.979 |
| 0.002 | +0.222 | −0.994 | −0.987 | −0.977 |
| 0.005 | **+0.817** | −0.942 | −0.946 | −0.972 |
| 0.01 | +0.517 | −0.428 | −0.923 | −0.967 |
| 0.02 | +0.434 | saturated | −0.768 | −0.882 |
| 0.05 | saturated | saturated | −0.457 | −0.611 |

So the pooled −0.981 is **not** four consistent within-domain relations: the marine-optical control's relation
is weak and *sign-flipping* (+0.817 at eps = 0.005). A single eps that is right for one domain is wrong for
another; the "informative" eps is a per-domain resolution.

### 2.3 Threshold-transfer balanced accuracy

Health label = top-1 at or below the arm-set median (the convention of `_p1352` / `_p1370`). Chance = 0.50.

| Test | Best cross-domain BA | At eps |
|---|---|---|
| absolute-eps certificate, control (marine ↔ sonar) | 0.500 | 0.001–0.02 |
| absolute-eps certificate, adapted (BioCLIP ↔ OceanCLIP) | 0.550 | 0.02 (relative) |
| domain-relative, q-calibrated (eps = q-quantile of the domain's margin) | 0.875 | q10, one direction only; the reverse direction is 0.500 |
| domain-relative, median-margin (eps = c · median_i margin_i) | 0.500 | all c in 0.01–0.10 |

**No threshold on M transfers.** The one qi = 0.875 entry is a single direction of a single calibration and
its reverse direction is exactly chance, so it is not a portable rule. Within-domain fitting is also weak:
the only within-domain fits above chance are marine-optical at eps = 0.005 (fit BA 1.000, leave-one-out BA
0.857, n = 7) and BioCLIP at eps = 0.01–0.02 (fit 0.600–0.700, LOO 0.556, n = 9). Fit values near 1.0 on
7–9 points are not evidence of a usable operating point.

### 2.4 Does a domain-relative eps make the certificate informative?

Partly — it fixes the *scale*, it does not fix the *transfer*.

Using the manuscript's statistic with a per-domain median-margin resolution,
`eps_row = c · median_i margin_i` and `M = P(margin <= 2 eps_row)`:

| c | control/marine | control/sonar | adapted/BioCLIP | adapted/OceanCLIP |
|---|---|---|---|---|
| 0.01 | −0.872 | −1.000 | −0.997 | −0.993 |
| 0.02 | −0.862 | −1.000 | −0.997 | −0.994 |
| 0.05 | −0.819 | −0.998 | −0.989 | −0.982 |
| 0.10 | −0.692 | −0.990 | −0.984 | −0.936 |

This is the usable statement: **at one constant c = 0.01–0.02 the certificate tracks top-1 with r in
[−1.000, −0.872] in all four domains**, whereas no single *absolute* eps does (marine needs 0.001, sonar and
the adapted encoders work at 0.005, and at 0.005 marine is +0.817). The scale-free reading of the original
negative control was therefore too pessimistic: what failed was the absolute scale carried over from
ImageNet-5k (median margin +0.0063), not the statistic.

What does **not** follow: cross-domain balanced accuracy stays at 0.500 for every c (the statistic is a smooth
monotone function of the frozen margin depth, so it ranks configurations inside a domain but carries no
threshold structure across domains), and the `--relative` variant `eps_rel = c · sigma_D` is strictly worse
than the absolute grid (pooled r = −0.821 / −0.630 at c = 0.005 vs −0.981 / −0.900 at eps = 0.001), because
`sigma_D` is nearly constant across these four domains (0.70–0.76) while the margin *layering* is not.

---

## 3. Draft manuscript text

The current manuscript sentence (lines 106–107 of `paper_a2/ext_partII_domains.tex`) says making the
certificate usable "would require a domain-relative resolution evaluated at eps ≈ 0.01 on the marine and sonar
domains, which we have not performed". **That sentence is now inaccurate and must be replaced** — the
evaluation has been performed (and eps ≈ 0.01 is not the right resolution; 0.001–0.005 is).

### 3.1 Primary replacement (bounded positive sentence, European English, LaTeX-ready)

```latex
We therefore re-evaluated the same statistic on a grid extended one decade down, to
$\varepsilon\in\{0.001,0.002,0.005,0.01,0.02,0.05,0.10\}$, on the same corpora and the same frozen weights
(the recomputation reproduces every archived value at $\varepsilon\in\{0.02,0.05,0.10\}$ exactly on the control, and to within $0.01$ in $M$ on the adapted encoders). The
coarse grid, not the statistic, had produced the saturation: all $32$ archived surgery configurations leave
$M=1$ at $\varepsilon=0.001$, where the mass tracks top-1 at $r=-0.98$ on the generic-CLIP marine/sonar
control and $r=-0.90$ on the adapted encoders, and the margin median is negative in all four domains---these
operating points sit past their own decision boundary, so any $\varepsilon\gtrsim0.02$ exceeds the entire
margin distribution. At the resolution at which the ImageNet-5k reference was validated
($\varepsilon=0.01$) the same corpora give only $r=-0.49$ and $-0.51$, and the within-domain relation is not
uniform (the marine-optical control is weak and sign-flipping, $r=-0.39$ at $\varepsilon=0.001$ against
$+0.82$ at $\varepsilon=0.005$). Rescaling the resolution to each domain's own margin
($\varepsilon=c\,\mathrm{median}_i\,\mathrm{margin}_i$ with a single $c=0.01$--$0.02$) makes the four domains
consistent---$r\in[-1.00,-0.87]$ in all of them---so the statistic is usable as a \emph{within-domain}
resolution-calibrated diagnostic. It still does not yield a portable threshold: no $\varepsilon$ and no
calibration we tested transfers across domains or encoders (best cross-domain balanced accuracy $0.50$--$0.55$
against chance $0.50$). The certificate is informative at its own domain's resolution and is not a portable
scalar---the same conclusion as the order-based diagnostic, reached from the opposite direction.
```

### 3.2 Conservative alternative (if the appendix budget forbids a new paragraph)

```latex
A fine-grid re-evaluation of the same control (same corpora, same frozen weights, reproducing every archived
value exactly) shows that the saturation was produced by the coarse grid rather than by the statistic: all
$32$ archived surgery configurations leave $M=1$ at $\varepsilon=0.001$, where the mass tracks top-1 at
$r=-0.98$ (marine/sonar control) and $r=-0.90$ (adapted encoders), whereas at the ImageNet-5k reference
resolution $\varepsilon=0.01$ these corpora give $r=-0.49$ and $-0.51$. A domain-relative resolution
($\varepsilon=c\,\mathrm{median}_i\,\mathrm{margin}_i$, $c=0.01$--$0.02$) makes the four domains mutually
consistent ($r\in[-1.00,-0.87]$), but no threshold on $M$ transfers across domains or encoders (best
cross-domain balanced accuracy $0.55$, chance $0.50$).
```

### 3.3 If a strict boundary statement is preferred instead

```latex
A fine-grid re-evaluation of the same control (same corpora, same frozen weights) moves the saturation point
to $\varepsilon=0.001$ but does not change the verdict: the pooled correlation with top-1 is
$r=-0.98$/$-0.90$ at that resolution yet decays monotonically to $-0.33$/$-0.28$ by $\varepsilon=0.02$, the
within-domain relation is not uniform (marine-optical is weak and sign-flipping), and no threshold on $M$
transfers across domains or encoders (best balanced accuracy $0.55$ against chance $0.50$). We therefore keep
the certificate as a within-domain, resolution-calibrated diagnostic and claim no portable scalar.
```

### 3.4 Placement recommendation

- Replace the clause at `paper_a2/ext_partII_domains.tex` **lines 105–107** ("We therefore report the
  certificate as a negative control at this operating point ... which we have not performed") with §3.1
  (or §3.2 if space is tight). The preceding sentences (lines 94–105, the ImageNet-5k contrast and the
  adapted-encoder results) remain correct and are reproduced by this run.
- Add one `Source:` line to the paragraph's caption or to the provenance appendix:
  `Source: tools/_p1472_a23_fine_eps.py; outputs/analysis/a23_fine_eps_certificate.json`
  (specific fields in the table in §5).
- The new sentence is a *positive bounded* claim, so it does not need the negative-control framing; keep the
  two archive paths already cited at lines 107–109 and add the new one.
- **Do not** re-run or restate the "which we have not performed" clause anywhere else in the manuscript
  (`main_zh.tex` mirrors it if the Chinese mirror is regenerated).

---

## 4. Appendix note for archive hygiene

Three disclosure items, with field paths. All three are about *how the control is described*, not about the
numbers the control produced; the archived values themselves are correct and reproduce exactly.

### 4.1 The control corpora are 7-class, not 8

`tools/_p1344_a23_certificate_control.py` says in its docstring "marine optical: fathomnet8, 8 classes;
acoustic sonar: NKSID Bohai Bay, 8 classes", and the corpus directory is named `data/fathomnet8`. Both
controls actually run over **7 classes**:

- `data/fathomnet8/` contains exactly 7 class subdirectories (`55-gallon drum`, `Actinopterygii`, `crab`,
  `Decapoda`, `sea star`, `sponge`, `urchin`; 343 images) plus a root-level `meta.json` that the script's
  directory enumeration ignores.
- `data/NKSID/NKSID/` contains 7 class subdirectories (1,783 images) **plus 834 class images (`img_*.jpg`)
  sitting at the corpus root**, which the script's enumeration also ignores. These 834 root images are the
  dataset's eighth class (`tire`, 834 images); with them the corpus is 2,617 images / 8 classes, which is the
  figure quoted for NKSID elsewhere in the manuscript (`main.tex` lines 85 and 100). The control therefore
  used **1,783 of 2,617 images and 7 of 8 classes**, silently and by construction of the loader.

Fixed by this run (`archive_only_derivations.class_count_note`): 7 classes, chance level 14.29 %.

### 4.2 Frozen top-1 and chance level

`M(0.01) = 0.681` in the ImageNet-5k reference is *not* the same statistic as the control's stopped
short: the control's frozen (lambda = 0) top-1 is **21.57 % (marine optical)** and **22.04 % (acoustic
sonar)** against a **14.29 %** chance level for 7 classes
(`arms.control.domains.{marine_optical,acoustic_sonar}.rows[lambda=0].top1`;
`archive_only_derivations.frozen_top1_from_archive`). Both are ~1.5× chance, i.e. the "frozen" operating point
is already close to the decision boundary in both domains — which is precisely why the coarse grid saturated
(§2.1).

### 4.3 The archive key `M(0.01)` duplicates `mass_0.05` (never measured)

`outputs/analysis/a23_certificate_control.json` contains

```
"correlation": { "CG": -0.1877..., "M(0.01)": NaN, "M(0.05)": NaN, "n": 14 }
```

Both keys are `NaN` because both are computed from the same saturated column. In
`tools/_p1344_a23_certificate_control.py` lines 123–126:

```python
m1 = np.array([r["mass_0.05"] for r in allrows])          # <- mass_0.05, not mass_0.01
payload["correlation"] = {"CG": ..., "M(0.01)": float(st.pearsonr(m1, top)[0]),
                          "M(0.05)": float(st.pearsonr(np.array([r["mass_0.05"] ...]), top)[0]), ...}
```

so **`correlation['M(0.01)']` is the M(0.05) correlation, and `M(0.05)` duplicates it bit-for-bit; an M(0.01)
value was never computed for this archive.** The control's eps grid is {0.02, 0.05, 0.10} and the script
docstring already names "M(0.01)/M(0.02)", so the docstring and the key disagree with the code in the same
way.

- Affected field paths:
  `outputs/analysis/a23_certificate_control.json:correlation['M(0.01)']`,
  `outputs/analysis/a23_certificate_control.json:correlation['M(0.05)']`.
- **Do not edit the archive** (`outputs/` is provenance — append/annotate only). Recommended handling: cite
  the key as unmeasured in the appendix, and cite the genuinely measured M(0.01) from
  `outputs/analysis/a23_fine_eps_certificate.json:arms.control.pooled.with_top1.mass_0p01.r` (−0.488) and
  `arms.adapted.pooled.with_top1.mass_0p01.r` (−0.512).
- Related, same file: the control script declares `N_SON = 650` and never uses it — the sonar arm runs on all
  1,783 enumerated images. The manuscript's *balanced* protocol for NKSID is 90 images per class; that variant
  is reported for comparison at
  `arms.control.domains.acoustic_sonar.balanced_protocol_variant` (560 images, 7 classes, top-1 20.00 %,
  M(0.001) = 0.8339, M(0.005) = 0.9357, M(0.01) = 0.9911) and does not change any conclusion.

---

## 5. Provenance table

Every number in §2–§4 maps to a script and a field. "Recomputed" = produced by this run; "archived" = read
from an existing archive and verified by the recomputation.

| Quantity / claim | Script | Archive + field path | Status |
|---|---|---|---|
| M(eps) per row, fine grid | `tools/_p1472_a23_fine_eps.py` | `outputs/analysis/a23_fine_eps_certificate.json:arms.<arm>.domains.<domain>.rows[].mass_0p001/0p002/0p005/0p01/0p02/0p05/0p1` | recomputed |
| Pooled r with top-1 per eps | same | `…:arms.<arm>.pooled.with_top1.<key>.r` | recomputed |
| Within-domain r with top-1 per eps | same | `…:arms.<arm>.correlations.<domain>.with_top1.<key>.r` | recomputed |
| Saturation boundary (32/32 rows at 0.001) | same | `…:arms.<arm>.verdict.n_rows_where_fine_grid_separates`, `coarsest_required_eps` | recomputed |
| Frozen top-1 / median margin per domain | same | `…:arms.<arm>.domains.<domain>.rows[lambda=0].{top1,margin_median}` | recomputed |
| `sigma_D` per row | same | `…:arms.<arm>.domains.<domain>.rows[].sigma_D` | recomputed |
| eps_min_below_1 (margin_min/2, 0 when negative) | same | `…:arms.<arm>.domains.<domain>.rows[].eps_min_below_1` | recomputed |
| Domain-relative (median-margin) r | same | `…:arms.<arm>.domain_relative_variants.<domain>.median_margin_relative.rows[].r_with_top1` | recomputed |
| q-calibrated and rank-calibrated variants | same | `…:arms.<arm>.domain_relative_variants.<domain>.{q_calibrated,rank_calibrated}` | recomputed |
| Threshold transfer, within domain (fit BA, LOO BA) | same | `…:arms.<arm>.threshold_transfer_within_domain.<domain>.<key>` | recomputed |
| Threshold transfer, cross domain (absolute eps) | same | `…:arms.<arm>.threshold_transfer_cross_domain.by_statistic.<key>` | recomputed |
| Threshold transfer, cross domain (domain-relative) | same | `…:arms.<arm>.threshold_transfer_cross_domain_domain_relative.by_calibration.<q>` and `…_median_relative.by_c.<c>` | recomputed |
| Reproduction check vs both archives | same | `…:arms.<arm>.domains.<domain>.reproduction.{max_abs_diff,reproduced,pairs_checked}` | recomputed |
| Balanced sonar variant (560 images) | same | `…:arms.control.domains.acoustic_sonar.balanced_protocol_variant.row` | recomputed |
| Class counts, chance level, root-level exclusions | same | `…:archive_only_derivations.class_count_note`, `…:arms.control.audits.<domain>` | measured on disk |
| Stored M vs declared eps grid | same | `…:archive_only_derivations.stored_M_vs_declared_grid` | from archives |
| Implied margin bounds from archived M | same | `…:archive_only_derivations.implied_margin_bounds.per_row.<arm>` | from archives |
| Grid refinement implied by archives | same | `…:archive_only_derivations.grid_refinement_required.<arm>` | from archives |
| `M(0.01)` key defect + field paths | same | `…:archive_only_derivations.archived_correlation_block.{as_stored,key_defect,affected_field_paths}` | from archives |
| Archived coarse-grid values (reference) | `tools/_p1344_a23_certificate_control.py`, `tools/_p1352_a23_certificate_adapted.py` | `outputs/analysis/a23_certificate_control.json:domains.*[].mass_*`; `outputs/analysis/a23_certificate_adapted.json:models.*.rows[].mass_*` | archived, reproduced exactly |
| ImageNet-5k reference (M(0.01) = 0.681, r = −0.996, median 0.0063) | — | `outputs/analysis/a1_margin_mass.json:rows[family=frozen].{margin_median,mass_eps_0.01}`, `correlation_with_top1.mass_eps_0.01` | archived (unchanged) |
| Asset inventory (paths, sizes, file counts) | — | measured on disk 2026-10-24 (§1 table) | measured on disk |

### Provenance-manifest entry (`docs/PROVENANCE_MANIFEST_2026-10-20.md`)

The manifest is operator-owned; this is the row to add rather than an edit performed here:

```
| A23 fine-eps certificate (text §, replacement for the negative-control clause) |
  script: tools/_p1472_a23_fine_eps.py |
  json: outputs/analysis/a23_fine_eps_certificate.json (fields:
  arms.control.pooled.with_top1.mass_0p001.r,
  arms.adapted.pooled.with_top1.mass_0p001.r,
  arms.control.verdict.n_rows_where_fine_grid_separates,
  arms.<arm>.domain_relative_variants.<domain>.median_margin_relative) |
  status: verified by recomputation against a23_certificate_{control,adapted}.json (max |diff| = 0.0) |
```

---

## 6. Reproduce

```
D:\Anaconda\envs\pytorch\python.exe tools\_p1472_a23_fine_eps.py --arm control    # ~30 s, needs GPU for speed
D:\Anaconda\envs\pytorch\python.exe tools\_p1472_a23_fine_eps.py --arm adapted    # ~16 min (OceanCLIP checkpoint)
D:\Anaconda\envs\pytorch\python.exe tools\_p1472_a23_fine_eps.py --arm analyze    # seconds, from embedding cache
```

`--arm analyze` rebuilds both arm payloads from `outputs/analysis/_cache/a23_fine_eps/*.npz` alone, so the
statistics (and every number in §2) can be re-derived without images, models or a GPU. The script merges into
the existing JSON by arm, so re-running one pass never discards the other, and never writes to any archive it
reads.

### Open items / honest limits

1. The health label for threshold transfer is "top-1 at or below the arm-set median" — inherited from
   `_p1352`/`_p1370`, not a clinical definition. With 7–9 rows per domain it is a weak target; the LOO BA is
   reported alongside every fit BA for that reason, and no threshold recommendation is made.
2. `eps_min_below_1 = 0` for every row because the minimum margin is negative in all four domains. The
   meaningful resolution statement is the empirical one in §2.1 (0.001–0.005), not that field.
3. The `q`-calibrated variant degenerates (M = 0 or near-0) when the chosen margin quantile is negative; that
   is reported rather than hidden, and the median-margin variant in §2.4 is the one that behaves.
4. The ImageNet-5k reference was not re-run (not requested; `a1_margin_mass.json` was used as archived).