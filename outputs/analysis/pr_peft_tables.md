# PR R1.6 -- LoRA / Adapter learning-rate grid (last open fairness item)

Source: `outputs/analysis/pr_peft_lr_sweep.json` (producing script `tools/_p291_peft_lr_sweep.py`, status `complete`, 24 runs, 0 failed). Frozen baseline: zero-shot 59.91 %, CG 0.8157, DG 0.8636, R@1 0.1555 (`frozen`; identical protocol to the full-FT sweep, source `pr_fullft_lr_sweep_full.json :: frozen (identical evaluation protocol)`).

Protocol (`meta.protocol`): flickr30k captions (0, 2000), shuffle=True, num_workers=0, batch 64, fp16, 10 epochs, AdamW (wd 0.01), cosine per step, grad clip 1.0; evaluation reused from `tools/_p263_fullft_lr_sweep.py` (zero-shot on the same 14288 ImageNet-1K images, CG/DG via `src/gap_metrics`, R@1 on the same 1000 Flickr30k val pairs).


## T1 -- code-level PEFT proof (`runs[*].peft_proof`)

| config | trainable | expected (architecture) | fraction of model | non-PEFT params frozen | n modules | wrapped originals frozen |
|---|---|---|---|---|---|---|
| `lora_both` | 491520 | 491520 | 0.003249 | True | 48 | True |
| `lora_text` | 196608 | 196608 | 0.001300 | True | 24 | True |
| `adapter_both` | 3965952 | 3965952 | 0.026216 | True | 48 | True |

## T2 -- grid: every run (`runs[*].final`)

| config | lr | seed | zero-shot top-1 %% | vs frozen (pp) | CG | dCG | dDG | R@1 | final train loss |
|---|---|---|---|---|---|---|---|---|---|
| adapter_both | 1e-05 | 42 | 0.18 | -59.73 | 1.2395 | +0.4238 | +0.3789 | 0.0025 | 4.0756 |
| adapter_both | 1e-05 | 123 | 0.08 | -59.83 | 1.2147 | +0.3990 | +0.3553 | 0.0015 | 4.1259 |
| adapter_both | 3e-05 | 42 | 1.26 | -58.65 | 1.1378 | +0.3222 | +0.2844 | 0.0210 | 2.9263 |
| adapter_both | 3e-05 | 123 | 1.05 | -58.86 | 1.1276 | +0.3120 | +0.2781 | 0.0135 | 3.2678 |
| adapter_both | 0.0001 | 42 | 16.83 | -43.08 | 0.9284 | +0.1127 | +0.0919 | 0.1310 | 0.4420 |
| adapter_both | 0.0001 | 123 | 17.39 | -42.52 | 0.9326 | +0.1170 | +0.0938 | 0.1175 | 0.5060 |
| adapter_both | 0.0003 | 42 | 22.98 | -36.93 | 0.8903 | +0.0746 | +0.0614 | 0.1495 | 0.1842 |
| adapter_both | 0.0003 | 123 | 23.78 | -36.13 | 0.8839 | +0.0682 | +0.0533 | 0.1355 | 0.2057 |
| lora_both | 1e-05 | 42 | 60.72 | +0.81 | 0.8102 | -0.0054 | -0.0029 | 0.1775 | 0.2856 |
| lora_both | 1e-05 | 123 | 60.65 | +0.74 | 0.8103 | -0.0054 | -0.0050 | 0.1755 | 0.2736 |
| lora_both | 3e-05 | 42 | 60.42 | +0.51 | 0.8201 | +0.0044 | +0.0050 | 0.1800 | 0.1901 |
| lora_both | 3e-05 | 123 | 60.62 | +0.71 | 0.8162 | +0.0005 | -0.0018 | 0.1810 | 0.1739 |
| lora_both | 0.0001 | 42 | 57.41 | -2.50 | 0.8522 | +0.0366 | +0.0337 | 0.1780 | 0.1409 |
| lora_both | 0.0001 | 123 | 57.99 | -1.92 | 0.8542 | +0.0386 | +0.0262 | 0.1735 | 0.1295 |
| lora_both | 0.0003 | 42 | 47.95 | -11.96 | 0.9374 | +0.1217 | +0.0956 | 0.1615 | 0.1375 |
| lora_both | 0.0003 | 123 | 48.08 | -11.83 | 0.9328 | +0.1171 | +0.0905 | 0.1855 | 0.1195 |
| lora_text | 1e-05 | 42 | 59.95 | +0.04 | 0.8107 | -0.0050 | -0.0032 | 0.1685 | 0.3881 |
| lora_text | 1e-05 | 123 | 60.18 | +0.27 | 0.8060 | -0.0097 | -0.0073 | 0.1640 | 0.3860 |
| lora_text | 3e-05 | 42 | 59.66 | -0.25 | 0.8182 | +0.0025 | +0.0026 | 0.1700 | 0.2869 |
| lora_text | 3e-05 | 123 | 59.88 | -0.03 | 0.8128 | -0.0029 | -0.0025 | 0.1655 | 0.2873 |
| lora_text | 0.0001 | 42 | 57.10 | -2.81 | 0.7909 | -0.0248 | -0.0137 | 0.1680 | 0.1676 |
| lora_text | 0.0001 | 123 | 57.54 | -2.37 | 0.7902 | -0.0255 | -0.0160 | 0.1715 | 0.1737 |
| lora_text | 0.0003 | 42 | 50.72 | -9.19 | 0.7687 | -0.0469 | -0.0285 | 0.1670 | 0.1160 |
| lora_text | 0.0003 | 123 | 52.25 | -7.66 | 0.7687 | -0.0470 | -0.0298 | 0.1695 | 0.1294 |

## T3 -- per (config, lr) means (`analysis.grid`)

| config@lr | n seeds | zero-shot top-1 % (mean +/- sd) | dCG (mean +/- sd) | dDG (mean +/- sd) | R@1 (mean +/- sd) |
|---|---|---|---|---|---|
| `adapter_both@0.0001` | 2 | 17.11 +/- 0.40 | +0.1148 +/- 0.0030 | +0.0929 +/- 0.0013 | 0.1242 +/- 0.0095 |
| `adapter_both@0.0003` | 2 | 23.38 +/- 0.57 | +0.0714 +/- 0.0045 | +0.0574 +/- 0.0057 | 0.1425 +/- 0.0099 |
| `adapter_both@1e-05` | 2 | 0.13 +/- 0.07 | +0.4114 +/- 0.0175 | +0.3671 +/- 0.0167 | 0.0020 +/- 0.0007 |
| `adapter_both@3e-05` | 2 | 1.16 +/- 0.15 | +0.3171 +/- 0.0072 | +0.2812 +/- 0.0045 | 0.0173 +/- 0.0053 |
| `lora_both@0.0001` | 2 | 57.70 +/- 0.41 | +0.0376 +/- 0.0014 | +0.0300 +/- 0.0053 | 0.1757 +/- 0.0032 |
| `lora_both@0.0003` | 2 | 48.02 +/- 0.09 | +0.1194 +/- 0.0033 | +0.0931 +/- 0.0037 | 0.1735 +/- 0.0170 |
| `lora_both@1e-05` | 2 | 60.69 +/- 0.05 | -0.0054 +/- 0.0001 | -0.0039 +/- 0.0014 | 0.1765 +/- 0.0014 |
| `lora_both@3e-05` | 2 | 60.52 +/- 0.14 | +0.0025 +/- 0.0028 | +0.0016 +/- 0.0048 | 0.1805 +/- 0.0007 |
| `lora_text@0.0001` | 2 | 57.32 +/- 0.31 | -0.0251 +/- 0.0005 | -0.0148 +/- 0.0016 | 0.1698 +/- 0.0025 |
| `lora_text@0.0003` | 2 | 51.48 +/- 1.08 | -0.0469 +/- 0.0000 | -0.0292 +/- 0.0009 | 0.1683 +/- 0.0018 |
| `lora_text@1e-05` | 2 | 60.06 +/- 0.16 | -0.0073 +/- 0.0034 | -0.0053 +/- 0.0029 | 0.1663 +/- 0.0032 |
| `lora_text@3e-05` | 2 | 59.77 +/- 0.16 | -0.0002 +/- 0.0038 | +0.0001 +/- 0.0036 | 0.1678 +/- 0.0032 |

## T4 -- post-injection geometry (`runs[*].post_injection_gap_retrieval`)

LoRA is identity at initialisation (B = 0); the bottleneck Adapter is NOT (`up.bias` is non-zero), so insertion alone moves the geometry. This is the state the paper's `delta_old` convention measures from.

| config | post-injection CG | post-injection dCG vs frozen | post-injection R@1 |
|---|---|---|---|
| lora_both | 0.8156 | -0.0001 | 0.1570 |
| lora_text | 0.8157 | +0.0000 | 0.1655 |
| adapter_both | 1.2617 | +0.4460 | 0.0010 |

## T5 -- best lr per configuration and the comparison with full fine-tuning (`analysis.best`, `analysis.vs_fullft`)

| config | best lr by zero-shot | best lr by CG | n runs |
|---|---|---|---|
| adapter_both | 0.0003 | 0.0003 | 8 |
| lora_both | 1e-05 | 1e-05 | 8 |
| lora_text | 1e-05 | 0.0003 | 8 |

Best PEFT run overall by zero-shot: **lora_both @ lr 1e-05 (seed 42) = 60.72 %, dCG -0.0054, R@1 0.1775** (`analysis.best.best_run_by_zero_shot`).

| quantity | full fine-tuning (best lr) | best LoRA/Adapter | delta (PEFT - FT) |
|---|---|---|---|
| lr | 1e-06 | lora_both @ 1e-05 | -- |
| zero-shot top-1 % | 61.02 | 60.72 | -0.30 pp |
| dCG | -0.0074 | -0.0054 | +0.0019 |
| R@1 | 0.1780 | 0.1775 | -0.0005 |

Full-FT per-lr reference (`analysis.vs_fullft.fullft_per_lr`, from `outputs/analysis/pr_fullft_lr_sweep_full.json`):

| lr | zero-shot % (mean +/- sd) | dCG | R@1 |
|---|---|---|---|
| 1e-06 | 60.87 +/- 0.21 | -0.0016 | 0.1808 |
| 1e-05 | 52.18 +/- 1.03 | +0.1860 | 0.1700 |
| 3e-05 | 31.44 | +0.2498 | 0.1455 |
| 0.0001 | 0.14 | +0.7969 | 0.0030 |
| 0.0003 | 0.08 | +0.8001 | 0.0010 |

Interpretation rule (`analysis.vs_fullft.interpretation_rule`): positive zero_shot_pp / negative dCG favour the PEFT method at its own best learning rate.


## T6 -- per-epoch train loss (`runs[*].history.train_loss`)

| config | lr | seed | ep1 | ep2 | ep3 | ep4 | ep5 | ep6 | ep7 | ep8 | ep9 | ep10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| adapter_both | 1e-05 | 42 | 4.220 | 4.167 | 4.151 | 4.139 | 4.126 | 4.112 | 4.096 | 4.085 | 4.079 | 4.076 |
| adapter_both | 1e-05 | 123 | 4.275 | 4.196 | 4.168 | 4.156 | 4.146 | 4.138 | 4.133 | 4.130 | 4.127 | 4.126 |
| adapter_both | 3e-05 | 42 | 4.184 | 4.130 | 4.026 | 3.736 | 3.455 | 3.250 | 3.085 | 3.008 | 2.954 | 2.926 |
| adapter_both | 3e-05 | 123 | 4.220 | 4.149 | 4.110 | 3.986 | 3.759 | 3.579 | 3.443 | 3.341 | 3.290 | 3.268 |
| adapter_both | 0.0001 | 42 | 4.141 | 3.640 | 2.684 | 1.531 | 0.910 | 0.629 | 0.539 | 0.498 | 0.467 | 0.442 |
| adapter_both | 0.0001 | 123 | 4.173 | 3.936 | 3.226 | 2.001 | 1.123 | 0.759 | 0.619 | 0.511 | 0.507 | 0.506 |
| adapter_both | 0.0003 | 42 | 3.992 | 2.619 | 0.975 | 0.493 | 0.352 | 0.256 | 0.240 | 0.212 | 0.213 | 0.184 |
| adapter_both | 0.0003 | 123 | 4.135 | 3.343 | 1.399 | 0.585 | 0.381 | 0.277 | 0.243 | 0.200 | 0.214 | 0.206 |
| lora_both | 1e-05 | 42 | 0.477 | 0.396 | 0.370 | 0.315 | 0.334 | 0.294 | 0.305 | 0.294 | 0.276 | 0.286 |
| lora_both | 1e-05 | 123 | 0.480 | 0.403 | 0.387 | 0.345 | 0.317 | 0.297 | 0.309 | 0.305 | 0.263 | 0.274 |
| lora_both | 3e-05 | 42 | 0.445 | 0.308 | 0.265 | 0.213 | 0.229 | 0.200 | 0.204 | 0.190 | 0.178 | 0.190 |
| lora_both | 3e-05 | 123 | 0.443 | 0.309 | 0.281 | 0.242 | 0.211 | 0.194 | 0.208 | 0.200 | 0.167 | 0.174 |
| lora_both | 0.0001 | 42 | 0.405 | 0.223 | 0.184 | 0.155 | 0.175 | 0.148 | 0.153 | 0.137 | 0.130 | 0.141 |
| lora_both | 0.0001 | 123 | 0.393 | 0.223 | 0.206 | 0.178 | 0.156 | 0.136 | 0.160 | 0.150 | 0.119 | 0.130 |
| lora_both | 0.0003 | 42 | 0.408 | 0.211 | 0.193 | 0.157 | 0.186 | 0.142 | 0.149 | 0.132 | 0.126 | 0.137 |
| lora_both | 0.0003 | 123 | 0.392 | 0.217 | 0.208 | 0.195 | 0.155 | 0.139 | 0.155 | 0.148 | 0.113 | 0.120 |
| lora_text | 1e-05 | 42 | 0.496 | 0.469 | 0.432 | 0.417 | 0.400 | 0.398 | 0.368 | 0.366 | 0.371 | 0.388 |
| lora_text | 1e-05 | 123 | 0.482 | 0.450 | 0.436 | 0.412 | 0.400 | 0.416 | 0.394 | 0.409 | 0.396 | 0.386 |
| lora_text | 3e-05 | 42 | 0.478 | 0.411 | 0.357 | 0.341 | 0.313 | 0.308 | 0.274 | 0.274 | 0.276 | 0.287 |
| lora_text | 3e-05 | 123 | 0.466 | 0.399 | 0.365 | 0.337 | 0.314 | 0.325 | 0.302 | 0.309 | 0.298 | 0.287 |
| lora_text | 0.0001 | 42 | 0.443 | 0.323 | 0.258 | 0.238 | 0.210 | 0.195 | 0.164 | 0.165 | 0.168 | 0.168 |
| lora_text | 0.0001 | 123 | 0.436 | 0.319 | 0.262 | 0.234 | 0.207 | 0.214 | 0.189 | 0.185 | 0.184 | 0.174 |
| lora_text | 0.0003 | 42 | 0.414 | 0.267 | 0.198 | 0.181 | 0.162 | 0.146 | 0.122 | 0.125 | 0.131 | 0.116 |
| lora_text | 0.0003 | 123 | 0.418 | 0.257 | 0.203 | 0.170 | 0.157 | 0.163 | 0.145 | 0.143 | 0.136 | 0.129 |

---
Rendered by `tools/_p292_peft_tables.py` from `outputs/analysis/pr_peft_lr_sweep.json`.

