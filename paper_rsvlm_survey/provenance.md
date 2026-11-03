# Provenance of the survey's numeric claims (2026-10-27)

Rule: every number in the manuscript names the record it came from. Values were extracted from the real abstracts returned
by OpenAlex (`tools/_p1794_rsvlm_abstracts.py`, archive `literature/abstracts_2026-10-27.json`); nothing is estimated.
The gate `tools/_p1797_rsvlm_number_gate.py` re-opens each abstract (OpenAlex for journal records, the arXiv archive `literature/arxiv_abstracts_2026-10-27.json` for the foundational preprints, and `literature/fulltext/` for values read out of open-access full texts) and requires the value to appear in it, so a typo or a
drifted value fails mechanically.

| claim | value | source (DOI) |
|---|---|---|
| BigEarthNet-MM patch pairs | 590,326 | `10.1109/mgrs.2021.3089174` |
| NWPU-Captions images | 31,500 | `10.1109/tgrs.2022.3201474` |
| NWPU-Captions sentences | 157,500 | `10.1109/tgrs.2022.3201474` |
| RS5M image-text pairs | 5 million | `10.1109/tgrs.2024.3449154` |
| MultiSenGE patches | 8,157 | `10.5194/isprs-annals-v-3-2022-635-2022` |
| MMFlood acquisitions | 1,748 | `10.1109/access.2022.3205419` |
| MMFlood flood events | 95 | `10.1109/access.2022.3205419` |
| MMFlood countries | 42 | `10.1109/access.2022.3205419` |
| DDFAV imagery | 1.6 GB | `10.3390/rs17040719` |
| EarthGPT instruction pairs | 1 million | `10.1109/tgrs.2024.3409624` |
| EarthGPT source datasets | 34 | `10.1109/tgrs.2024.3409624` |
| RingMoGPT instruction pairs | 1.6 million | `10.1109/tgrs.2024.3510833` |
| AiRs trainable parameters | 4.4% | `10.1109/tgrs.2024.3351889` |
| UPetu trainable parameters | 0.73% | `10.1109/tgrs.2024.3382734` |
| Fed-RSAdapter trainable parameters | 5% | `10.3390/rs18142352` |
| SAMOIS LoveDA mIoU | 55.22% | `10.1080/22797254.2025.2609404` |
| SAMOIS LoveDA OA | 73.49% | `10.1080/22797254.2025.2609404` |
| SAMOIS Potsdam mIoU | 78.94% | `10.1080/22797254.2025.2609404` |
| SAMOIS Potsdam OA | 90.73% | `10.1080/22797254.2025.2609404` |
| RS-CLIP zero-shot UCM-21 | 95.94% | `10.1016/j.jag.2023.103497` |
| RS-CLIP zero-shot WHU-RS19 | 95.97% | `10.1016/j.jag.2023.103497` |
| RS-CLIP zero-shot NWPU-RESISC45 | 85.76% | `10.1016/j.jag.2023.103497` |
| RS-CLIP zero-shot AID-30 | 87.52% | `10.1016/j.jag.2023.103497` |
| PE-RSIC trainable parameters | 5% | `10.1109/tgrs.2025.3584887` |

| SigLIP zero-shot ImageNet accuracy | 84.5% | `10.48550/arXiv.2303.15343` |
| SigLIP batch saturation | 32k | `10.48550/arXiv.2303.15343` |
| BLIP-2 zero-shot VQAv2 gain over Flamingo-80B | 8.7% | `10.48550/arXiv.2301.12597` |
| BLIP-2 trainable-parameter factor | 54 | `10.48550/arXiv.2301.12597` |
| RemoteCLIP zero-shot gain over CLIP | 6.39% | `10.48550/arXiv.2306.11029` |
| RemoteCLIP RSITMD mean recall gain | 9.14% | `10.48550/arXiv.2306.11029` |
| RemoteCLIP RSICD mean recall gain | 8.92% | `10.48550/arXiv.2306.11029` |

| RSGPT RSICap human-annotated captions | 2,585 | `10.1016/j.isprsjprs.2025.03.028` |
| Woodpecker POPE accuracy gain over MiniGPT-4 | 30.66% | `10.1007/s11432-024-4251-x` |
| Woodpecker POPE accuracy gain over mPLUG-Owl | 24.33% | `10.1007/s11432-024-4251-x` |
| MM-InstructEval evaluated models | 45 | `10.1016/j.inffus.2025.103204` |
| MM-InstructEval datasets | 16 | `10.1016/j.inffus.2025.103204` |
| MM-InstructEval tasks | 6 | `10.1016/j.inffus.2025.103204` |
| MM-InstructEval instruction variants | 10 | `10.1016/j.inffus.2025.103204` |

| LSKNet-T parameters relative to ResNet-18 | 38% | `10.1007/s11263-024-02247-9` |
| LSKNet-T FLOPs reduction | 50% | `10.1007/s11263-024-02247-9` |
| Distilled detector mAP gain | 20% | `10.1016/j.inffus.2024.102742` |
| Distilled detector inference speed-up | 2.5 | `10.1016/j.inffus.2024.102742` |

| DDFAV images | 1,755 | `10.3390/rs17040719` |
| DDFAV source datasets | 5 | `10.3390/rs17040719` |

| ChangeCLIP land-cover categories | 56 | `10.1016/j.isprsjprs.2024.01.004` |
| ChangeCLIP IoU on LEVIR-CD | 85.20% | `10.1016/j.isprsjprs.2024.01.004` |
| ChangeCLIP IoU on LEVIR-CD+ | 75.63% | `10.1016/j.isprsjprs.2024.01.004` |
| ChangeCLIP IoU on WHU-CD | 90.15% | `10.1016/j.isprsjprs.2024.01.004` |
| ChangeCLIP IoU on CDD | 95.87% | `10.1016/j.isprsjprs.2024.01.004` |
| ChangeCLIP IoU on SYSU-CD | 71.41% | `10.1016/j.isprsjprs.2024.01.004` |

| RSAdapter trainable budget | 10% | `10.1109/tgrs.2024.3413174` |
| MLAE trainable share | 0.34% | `10.1109/tip.2026.3712351` |
| MLAE reported accuracy | 90.9% | `10.1109/tip.2026.3712351` |
| MVP trainable share | 1% | `10.1109/tgrs.2024.3359599` |
| LoRA-CLIP trainable share | 2% | `10.1109/lgrs.2025.3589738` |
| LoRA detector trainable share | 12.4% | `10.1109/tgrs.2024.3524578` |
| Fed-RSAdapter trainable share | 4.93% | `10.3390/rs18142352` |

| LuoJiaHOG images | 94,856 | `10.1016/j.isprsjprs.2025.02.009` (arXiv 2403.10887 text) |
| RSVG image-query pairs | 38 320 | `10.1109/tgrs.2023.3250471` |
| RSVG source images | 17 402 | `10.1109/tgrs.2023.3250471` |
| RS-LLaVA instruction samples | 7,058 | `10.3390/rs16091477` |

| RemoteCLIP training images | 165,745 | `10.1109/tgrs.2024.3390838` |
| RemoteCLIP training pairs | 828,725 | `10.1109/tgrs.2024.3390838` |
| SkyEyeGPT instruction samples | 968k | `10.1016/j.isprsjprs.2025.01.020` |

Pipeline counters (833 de-duplicated records, 826 with DOI, 821 verified) come from
`literature/summary_2026-10-27.json` and `literature/verify_summary_2026-10-27.json` rather than from a published abstract,
and are excluded from the gate by construction.

## Tables that report our own audit

| table | generating script | archive |
|---|---|---|
| `tab:disclosure` (disclosure audit of eight papers) | `tools/_p1801_rsvlm_disclosure_audit.py` | `literature/disclosure_audit_2026-10-28.json` (per-paper pattern hits and hand verdicts) |
