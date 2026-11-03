# PR R1.3 / R2.4 / R3.3 -- parameter-matched perturbation tables

Source: `outputs/analysis/pr_relative_perturbation.json` (producing script `tools/_p255_relative_perturbation.py`, status `complete`, 426 conditions, 0 errors, 10 seeds, model `openai/clip-vit-base-patch32`, 1000 evaluation images).

Baseline on the evaluation set: R@1(i2t) = 0.6950, R@1(t2i) = 0.6710, CG = 0.7742, DG = 0.8308 (`baseline`).


## T1 -- weight geometry of the two towers (`weight_geometry.<tower>`)

| quantity | vision | text | ratio V/T |
|---|---|---|---|
| injected tensors (`n_injected_tensors`) | 192 | 192 | 1.000 |
| injected parameters (`n_injected_params`) | 85054464 | 37828608 | 2.248 |
| tower parameters (`n_total_params`) | 87456000 | 63165952 | 1.385 |
| injected share of tower parameters | 0.973 | 0.599 | -- |
| ||W_inj||_F (`frob_injected`) | 333.043 | 274.830 | 1.212 |
| ||W_inj||_F / ||W_enc+proj||_F (`injected_share_of_all_frob`) | 0.9915 | 0.9709 | -- |
| RMS of injected weights (`rms_injected`) | 0.03611 | 0.04468 | 0.808 |
| expected tower-level rel. perturbation per unit sigma (`expected_rel_at_unit_sigma_injected`) | 0.48303 | 0.42366 | 1.1401 |

## T2 -- the same sigma is not the same relative perturbation (`weight_geometry.<tower>.by_kind[*].expected_rel_at_unit_sigma`)

Expected per-tensor relative perturbation ||dW_i||_F/||W_i||_F produced by the archived injector at sigma = 1 (its noise sd is 1*std(W_i)); multiply by any sigma. LayerNorm weights receive ~10x less relative perturbation than the attention/MLP weight matrices at the same sigma.

| tensor kind | vision | text | vision/text | params (V) | params (T) |
|---|---|---|---|---|---|
| `layer_norm2.weight` | 0.0983 | 0.0757 | 1.298 | 9216 | 6144 |
| `layer_norm1.weight` | 0.1049 | 0.0766 | 1.369 | 9216 | 6144 |
| `fc1.bias` | 0.4910 | 0.4066 | 1.207 | 36864 | 24576 |
| `fc1.weight` | 0.9999 | 0.9999 | 1.000 | 28311552 | 12582912 |
| `fc2.weight` | 1.0000 | 1.0000 | 1.000 | 28311552 | 12582912 |
| `layer_norm2.bias` | 0.9900 | 0.9992 | 0.991 | 9216 | 6144 |
| `q_proj.bias` | 1.0003 | 1.0002 | 1.000 | 9216 | 6144 |
| `q_proj.weight` | 1.0000 | 1.0000 | 1.000 | 7077888 | 3145728 |
| `k_proj.weight` | 1.0000 | 1.0000 | 1.000 | 7077888 | 3145728 |
| `v_proj.weight` | 1.0000 | 1.0000 | 1.000 | 7077888 | 3145728 |
| `out_proj.weight` | 1.0000 | 1.0000 | 1.000 | 7077888 | 3145728 |
| `layer_norm1.bias` | 0.9911 | 0.9869 | 1.004 | 9216 | 6144 |
| `fc2.bias` | 1.0004 | 1.0008 | 1.000 | 9216 | 6144 |
| `out_proj.bias` | 1.0005 | 1.0007 | 1.000 | 9216 | 6144 |
| `v_proj.bias` | 0.9990 | 0.9997 | 0.999 | 9216 | 6144 |
| `k_proj.bias` | 0.9999 | 0.9975 | 1.002 | 9216 | 6144 |

Realized per-block relative perturbation at the archived sigma = 0.3 (`rows[*].rel_realized_by_block`), spread over the 12 blocks:

| tower | min | mean | max | max/min |
|---|---|---|---|---|
| vision | 0.0945 | 0.1683 | 0.2161 | 2.29 |
| text | 0.1076 | 0.1280 | 0.1442 | 1.34 |

LayerNorm share of the injected Frobenius norm (`weight_geometry.<tower>.by_kind[*].frob`):

| tower | LayerNorm weights | all LayerNorm params (weights + biases) | attention/MLP weights |
|---|---|---|---|
| vision | 0.7198 | 0.7389 | 0.1583 |
| text | 0.7666 | 0.7966 | 0.1159 |

## T3 -- the relative budget each protocol actually delivers (`rows[*].rel_injected`, `rows[*].rel_realized_stats`)

`rel_layer` and `rel_uniform` are matched by construction (V/T = 1.0000); the two equal-absolute protocols are not. Per-tensor columns are means over the 192 injected tensors of one seed (the draw-to-draw spread is < 1%).

| protocol | level | tower-level rel (V) | tower-level rel (T) | V/T | per-tensor rel V (mean +/- sd) | per-tensor rel T (mean +/- sd) |
|---|---|---|---|---|---|---|
| rel_layer | 0.01 | 0.01000 | 0.01000 | 1.0000 | 0.0100 +/- 0.0000 | 0.0100 +/- 0.0000 |
| rel_layer | 0.03 | 0.03000 | 0.03000 | 1.0000 | 0.0300 +/- 0.0000 | 0.0300 +/- 0.0000 |
| rel_layer | 0.06 | 0.06000 | 0.06000 | 1.0000 | 0.0600 +/- 0.0000 | 0.0600 +/- 0.0000 |
| rel_layer | 0.1 | 0.10000 | 0.10000 | 1.0000 | 0.1000 +/- 0.0000 | 0.1000 +/- 0.0000 |
| rel_layer | 0.2 | 0.20000 | 0.20000 | 1.0000 | 0.2000 +/- 0.0000 | 0.2000 +/- 0.0000 |
| rel_layer | 0.3 | 0.30000 | 0.30000 | 1.0000 | 0.3000 +/- 0.0000 | 0.3000 +/- 0.0000 |
| rel_layer | 1 | 1.00000 | 1.00000 | 1.0000 | 1.0000 +/- 0.0000 | 1.0000 +/- 0.0000 |
| abs_std | 0.01 | 0.00483 | 0.00424 | 1.1408 | 0.0086 +/- 0.0031 | 0.0085 +/- 0.0033 |
| abs_std | 0.03 | 0.01449 | 0.01271 | 1.1408 | 0.0258 +/- 0.0093 | 0.0254 +/- 0.0098 |
| abs_std | 0.06 | 0.02899 | 0.02541 | 1.1408 | 0.0515 +/- 0.0186 | 0.0508 +/- 0.0197 |
| abs_std | 0.1 | 0.04832 | 0.04235 | 1.1408 | 0.0859 +/- 0.0309 | 0.0847 +/- 0.0328 |
| abs_std | 0.2 | 0.09663 | 0.08470 | 1.1408 | 0.1718 +/- 0.0618 | 0.1693 +/- 0.0657 |
| abs_std | 0.3 | 0.14495 | 0.12705 | 1.1408 | 0.2577 +/- 0.0928 | 0.2540 +/- 0.0985 |
| abs_raw | 0.001083 | 0.03000 | 0.02425 | 1.2374 | 0.0519 +/- 0.0764 | 0.0453 +/- 0.0579 |
| abs_raw | 0.002167 | 0.06000 | 0.04849 | 1.2374 | 0.1038 +/- 0.1528 | 0.0906 +/- 0.1158 |
| abs_raw | 0.003611 | 0.10000 | 0.08082 | 1.2374 | 0.1730 +/- 0.2546 | 0.1510 +/- 0.1930 |
| abs_raw | 0.01083 | 0.30001 | 0.24246 | 1.2374 | 0.5190 +/- 0.7639 | 0.4531 +/- 0.5791 |
| rel_uniform | 0.01 | 0.01000 | 0.01000 | 1.0000 | 0.1924 +/- 0.5963 | 0.1554 +/- 0.4457 |
| rel_uniform | 0.02 | 0.02000 | 0.02000 | 1.0000 | 0.3848 +/- 1.1925 | 0.3109 +/- 0.8913 |
| rel_uniform | 0.03 | 0.03000 | 0.03000 | 1.0000 | 0.5772 +/- 1.7888 | 0.4663 +/- 1.3370 |
| rel_uniform | 0.05 | 0.05000 | 0.05000 | 1.0000 | 0.9621 +/- 2.9813 | 0.7771 +/- 2.2283 |

## T4 -- R@1(i2t) degradation under matched relative budgets (`analysis.per_level.rel_layer[*]`)

| r | vision drop %% (mean +/- sd) | text drop %% (mean +/- sd) | ratio of means | paired ratio per seed (mean +/- sd) | seeds V>T | seeds V>50%% | seeds T>50%% |
|---|---|---|---|---|---|---|---|
| 0.01 | 0.45 +/- 0.68 | 0.45 +/- 0.63 | 1.000 | 0.620 +/- 2.030 | 4/10 | 0 | 0 |
| 0.03 | 1.14 +/- 0.66 | 3.93 +/- 7.56 | 0.289 | -0.925 +/- 2.714 | 3/10 | 0 | 0 |
| 0.06 | 3.28 +/- 1.36 | 13.60 +/- 26.17 | 0.241 | 1.028 +/- 1.138 | 3/10 | 0 | 1 |
| 0.1 | 14.73 +/- 6.52 | 24.37 +/- 30.95 | 0.604 | 1.728 +/- 1.981 | 7/10 | 0 | 2 |
| 0.2 | 98.35 +/- 1.83 | 55.34 +/- 21.82 | 1.777 | 2.010 +/- 0.698 | 10/10 | 10 | 5 |
| 0.3 | 99.78 +/- 0.10 | 94.86 +/- 2.69 | 1.052 | 1.053 +/- 0.031 | 10/10 | 10 | 10 |
| 1 | 99.86 +/- 0.12 | 99.76 +/- 0.15 | 1.001 | 1.001 +/- 0.002 | 7/10 | 10 | 10 |

## T5 -- all four protocols: ratio of mean drops and CG/DG (`analysis.per_level.*`)

| protocol | level | vision drop % | text drop % | ratio | vision CG | text CG | vision DG | text DG |
|---|---|---|---|---|---|---|---|---|
| rel_layer | 0.01 | 0.45 +/- 0.68 | 0.45 +/- 0.63 | 1.000 | 0.7746 +/- 0.0031 | 0.7755 +/- 0.0022 | 0.8311 +/- 0.0031 | 0.8317 +/- 0.0016 |
| rel_layer | 0.03 | 1.14 +/- 0.66 | 3.93 +/- 7.56 | 0.289 | 0.7762 +/- 0.0094 | 0.7933 +/- 0.0366 | 0.8323 +/- 0.0094 | 0.8469 +/- 0.0345 |
| rel_layer | 0.06 | 3.28 +/- 1.36 | 13.60 +/- 26.17 | 0.241 | 0.7804 +/- 0.0183 | 0.8280 +/- 0.0756 | 0.8353 +/- 0.0184 | 0.8883 +/- 0.1096 |
| rel_layer | 0.1 | 14.73 +/- 6.52 | 24.37 +/- 30.95 | 0.604 | 0.7976 +/- 0.0297 | 0.8781 +/- 0.0819 | 0.8499 +/- 0.0319 | 0.9428 +/- 0.1304 |
| rel_layer | 0.2 | 98.35 +/- 1.83 | 55.34 +/- 21.82 | 1.777 | 0.9507 +/- 0.0318 | 0.9750 +/- 0.0432 | 1.0374 +/- 0.0685 | 1.0541 +/- 0.1046 |
| rel_layer | 0.3 | 99.78 +/- 0.10 | 94.86 +/- 2.69 | 1.052 | 0.9961 +/- 0.0166 | 1.0212 +/- 0.0271 | 1.0956 +/- 0.0459 | 1.1183 +/- 0.0769 |
| rel_layer | 1 | 99.86 +/- 0.12 | 99.76 +/- 0.15 | 1.001 | 1.0553 +/- 0.0161 | 1.1170 +/- 0.0231 | 1.2066 +/- 0.0210 | 1.2126 +/- 0.0330 |
| rel_uniform | 0.01 | 1.06 +/- 1.42 | 4.63 +/- 2.50 | 0.230 | 0.7742 +/- 0.0056 | 0.8048 +/- 0.0144 | 0.8301 +/- 0.0054 | 0.8544 +/- 0.0106 |
| rel_uniform | 0.02 | 5.63 +/- 2.36 | 13.96 +/- 3.19 | 0.403 | 0.7812 +/- 0.0097 | 0.8899 +/- 0.0173 | 0.8355 +/- 0.0094 | 0.9296 +/- 0.0167 |
| rel_uniform | 0.03 | 20.00 +/- 2.70 | 36.78 +/- 5.50 | 0.544 | 0.8144 +/- 0.0126 | 0.9640 +/- 0.0161 | 0.8668 +/- 0.0132 | 1.0171 +/- 0.0209 |
| rel_uniform | 0.05 | 94.76 +/- 2.46 | 90.04 +/- 5.29 | 1.052 | 0.9602 +/- 0.0239 | 1.0512 +/- 0.0186 | 1.0375 +/- 0.0329 | 1.1578 +/- 0.0245 |
| abs_std | 0.01 | 0.09 +/- 0.56 | 0.09 +/- 0.55 | 1.000 | 0.7744 +/- 0.0013 | 0.7745 +/- 0.0013 | 0.8309 +/- 0.0012 | 0.8311 +/- 0.0010 |
| abs_std | 0.03 | 0.85 +/- 0.83 | 0.86 +/- 1.42 | 0.983 | 0.7749 +/- 0.0037 | 0.7766 +/- 0.0038 | 0.8312 +/- 0.0036 | 0.8327 +/- 0.0030 |
| abs_std | 0.06 | 1.47 +/- 1.50 | 2.33 +/- 1.84 | 0.630 | 0.7763 +/- 0.0070 | 0.7838 +/- 0.0077 | 0.8322 +/- 0.0067 | 0.8382 +/- 0.0061 |
| abs_std | 0.1 | 4.96 +/- 2.25 | 5.93 +/- 2.46 | 0.837 | 0.7822 +/- 0.0106 | 0.8018 +/- 0.0140 | 0.8369 +/- 0.0101 | 0.8523 +/- 0.0113 |
| abs_std | 0.2 | 54.99 +/- 4.80 | 22.98 +/- 4.04 | 2.393 | 0.8758 +/- 0.0143 | 0.8924 +/- 0.0203 | 0.9313 +/- 0.0178 | 0.9322 +/- 0.0207 |
| abs_std | 0.3 | 99.44 +/- 0.44 | 61.96 +/- 5.23 | 1.605 | 0.9883 +/- 0.0163 | 0.9773 +/- 0.0136 | 1.0649 +/- 0.0264 | 1.0346 +/- 0.0197 |
| abs_raw | 0.001083 | 1.97 +/- 1.52 | 3.09 +/- 1.56 | 0.637 | 0.7743 +/- 0.0044 | 0.7817 +/- 0.0080 | 0.8302 +/- 0.0046 | 0.8369 +/- 0.0062 |
| abs_raw | 0.002167 | 11.64 +/- 2.21 | 10.53 +/- 2.19 | 1.105 | 0.7922 +/- 0.0071 | 0.8141 +/- 0.0184 | 0.8454 +/- 0.0072 | 0.8622 +/- 0.0152 |
| abs_raw | 0.003611 | 84.01 +/- 2.73 | 34.03 +/- 5.80 | 2.469 | 0.9182 +/- 0.0155 | 0.9019 +/- 0.0200 | 0.9839 +/- 0.0206 | 0.9420 +/- 0.0217 |
| abs_raw | 0.01083 | 99.84 +/- 0.14 | 99.73 +/- 0.14 | 1.001 | 1.0240 +/- 0.0175 | 1.0523 +/- 0.0184 | 1.1346 +/- 0.0164 | 1.1132 +/- 0.0226 |

## T6 -- headline: pooled fragility ratio and matched-drop budget ratio (`analysis.headline.*`)

Pooled per-(seed, level) ratio = vision drop / text drop. `levels_nonsaturated` = levels where both tower means lie in [1%, 90%]. Budget ratio = relative budget (r, or sigma for abs_*) needed for the same drop, text / vision; **> 1 means vision is the more fragile tower**.

| protocol | pooled ratio (nonsaturated) | pooled ratio (all levels) | budget @5% drop | budget @10% drop | budget @20% drop |
|---|---|---|---|---|---|
| rel_layer | 0.610 +/- 2.283 (n=30) | 0.931 +/- 1.738 (n=70) | 0.912 +/- 0.452 (10/10) | 0.989 +/- 0.449 (10/10) | 1.061 +/- 0.435 (10/10) |
| rel_uniform | 0.410 +/- 0.285 (n=30) | 0.571 +/- 0.376 (n=40) | 0.686 +/- 0.184 (6/10) | 0.679 +/- 0.137 (10/10) | 0.761 +/- 0.060 (10/10) |
| abs_std | 1.293 +/- 1.424 (n=29) | 1.198 +/- 1.206 (n=57) | 0.955 +/- 0.281 (10/10) | 1.104 +/- 0.110 (10/10) | 1.455 +/- 0.165 (10/10) |
| abs_raw | 1.507 +/- 0.958 (n=30) | 1.381 +/- 0.856 (n=40) | 1.013 +/- 0.203 (8/10) | 1.058 +/- 0.192 (10/10) | 1.176 +/- 0.098 (10/10) |

## T7 -- per-seed R@1 drops at the informative levels (`rows[*].drop_pct_i2t`, seeds [42, 123, 456, 789, 1024, 2048, 4096, 8192, 16384, 32768])

| protocol | level | tower | seed 42 | seed 123 | seed 456 | seed 789 | seed 1024 | seed 2048 | seed 4096 | seed 8192 | seed 16384 | seed 32768 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rel_layer | 0.03 | vision | +0.86 | +0.29 | +0.72 | +0.72 | +2.30 | +0.86 | +0.72 | +2.01 | +1.73 | +1.15 |
| rel_layer | 0.03 | text | +25.04 | -0.43 | +2.88 | +0.86 | +2.45 | -0.14 | +3.31 | +2.73 | -0.29 | +2.88 |
| rel_layer | 0.06 | vision | +4.17 | +2.30 | +4.89 | +3.02 | +4.32 | +2.73 | +0.14 | +3.45 | +4.32 | +3.45 |
| rel_layer | 0.06 | text | +86.91 | +1.87 | +5.47 | +4.60 | +17.27 | +1.29 | +6.47 | +6.62 | +1.15 | +4.32 |
| rel_layer | 0.1 | vision | +12.37 | +11.37 | +18.99 | +10.94 | +10.36 | +12.23 | +8.35 | +14.96 | +30.94 | +16.83 |
| rel_layer | 0.1 | text | +93.53 | +6.62 | +17.41 | +10.07 | +69.50 | +4.89 | +16.40 | +12.09 | +4.46 | +8.78 |
| rel_layer | 0.2 | vision | +98.56 | +98.71 | +99.42 | +99.57 | +98.99 | +97.84 | +93.38 | +98.42 | +99.57 | +98.99 |
| rel_layer | 0.2 | text | +91.08 | +39.86 | +51.22 | +64.17 | +93.53 | +37.55 | +58.27 | +42.73 | +30.65 | +44.32 |
| rel_uniform | 0.01 | vision | -0.14 | -0.72 | +2.88 | +0.72 | +4.03 | +1.01 | +1.29 | +0.86 | +0.72 | +0.00 |
| rel_uniform | 0.01 | text | +9.50 | +2.30 | +7.48 | +3.74 | +3.31 | +2.59 | +3.17 | +6.33 | +5.76 | +2.16 |
| rel_uniform | 0.02 | vision | +3.17 | +4.03 | +7.63 | +3.45 | +9.93 | +8.63 | +3.60 | +5.76 | +5.47 | +4.60 |
| rel_uniform | 0.02 | text | +18.42 | +13.53 | +16.55 | +18.71 | +14.96 | +12.52 | +10.94 | +13.38 | +11.51 | +9.06 |
| rel_uniform | 0.03 | vision | +18.71 | +19.86 | +23.02 | +15.25 | +21.58 | +24.89 | +18.27 | +18.56 | +19.42 | +20.43 |
| rel_uniform | 0.03 | text | +33.96 | +31.37 | +36.12 | +40.14 | +40.29 | +38.13 | +39.14 | +46.33 | +26.19 | +36.12 |
| rel_uniform | 0.05 | vision | +93.67 | +96.83 | +97.41 | +90.22 | +94.39 | +94.53 | +92.66 | +97.41 | +93.09 | +97.41 |
| rel_uniform | 0.05 | text | +82.01 | +86.19 | +84.75 | +88.49 | +87.77 | +94.10 | +90.65 | +98.13 | +97.41 | +90.94 |
| abs_std | 0.1 | vision | +5.18 | +3.31 | +6.04 | +3.02 | +8.63 | +8.20 | +2.16 | +5.04 | +2.59 | +5.47 |
| abs_std | 0.1 | text | +8.35 | +3.60 | +8.20 | +4.60 | +6.47 | +1.73 | +6.62 | +9.64 | +3.88 | +6.19 |
| abs_std | 0.2 | vision | +55.83 | +54.39 | +57.84 | +46.19 | +52.81 | +60.86 | +52.52 | +59.14 | +49.78 | +60.58 |
| abs_std | 0.2 | text | +25.18 | +19.14 | +20.29 | +23.74 | +30.94 | +22.16 | +27.48 | +21.87 | +17.27 | +21.73 |
| abs_std | 0.3 | vision | +99.14 | +99.28 | +100.00 | +98.99 | +99.57 | +99.71 | +99.86 | +99.71 | +98.56 | +99.57 |
| abs_std | 0.3 | text | +58.56 | +54.39 | +62.45 | +68.92 | +68.78 | +62.16 | +61.44 | +65.47 | +53.81 | +63.60 |
| abs_raw | 0.001083 | vision | +1.58 | +2.16 | +2.59 | -0.29 | +4.17 | +4.03 | +0.29 | +3.17 | +1.15 | +0.86 |
| abs_raw | 0.001083 | text | +1.87 | +2.73 | +5.04 | +2.16 | +4.17 | +1.44 | +4.46 | +5.32 | +0.86 | +2.88 |
| abs_raw | 0.002167 | vision | +11.65 | +11.22 | +11.37 | +9.78 | +14.24 | +14.68 | +7.48 | +13.38 | +12.66 | +9.93 |
| abs_raw | 0.002167 | text | +11.22 | +10.94 | +12.95 | +7.63 | +11.08 | +8.06 | +14.24 | +11.51 | +8.06 | +9.64 |
| abs_raw | 0.003611 | vision | +83.60 | +86.76 | +82.16 | +82.16 | +84.60 | +89.06 | +78.99 | +84.89 | +83.45 | +84.46 |
| abs_raw | 0.003611 | text | +33.53 | +24.03 | +39.42 | +40.43 | +40.14 | +34.24 | +39.14 | +31.22 | +26.62 | +31.51 |

## T8 -- same tower-level relative budget, different per-tensor allocation (`rows`, paired by seed)

`abs_raw` uses sigma = r * rms(vision injected weights), so the VISION tower's tower-level relative budget equals r in both protocols -- yet the two protocols spread that budget differently over the 192 tensors (abs_raw: nearly all of it on the small-norm attention/MLP matrices; rel_layer: an equal *relative* share on every tensor including the LayerNorm weights that carry most of ||W_inj||_F). Same seed = same random direction.

| r (tower-level rel, vision) | tower | drop % rel_layer | drop % abs_raw | paired difference (rel_layer - abs_raw) |
|---|---|---|---|---|
| 0.03 | vision | 1.14 +/- 0.66 | 1.97 +/- 1.52 | -0.83 +/- 1.37 |
| 0.03 | text | 3.93 +/- 7.56 | 3.09 +/- 1.56 | +0.83 +/- 7.89 |
| 0.06 | vision | 3.28 +/- 1.36 | 11.64 +/- 2.21 | -8.36 +/- 1.81 |
| 0.06 | text | 13.60 +/- 26.17 | 10.53 +/- 2.19 | +3.06 +/- 25.88 |
| 0.1 | vision | 14.73 +/- 6.52 | 84.01 +/- 2.73 | -69.28 +/- 7.07 |
| 0.1 | text | 24.37 +/- 30.95 | 34.03 +/- 5.80 | -9.65 +/- 29.80 |
| 0.3 | vision | 99.78 +/- 0.10 | 99.84 +/- 0.14 | -0.06 +/- 0.18 |
| 0.3 | text | 94.86 +/- 2.69 | 99.73 +/- 0.14 | -4.86 +/- 2.76 |

---
Rendered by `tools/_p256_pr_causal_tables.py` from `outputs/analysis/pr_relative_perturbation.json` (sha1 of the producing script: `3148c9f40d93a89325a2effb9fc88bb83dc2a6ca`).

