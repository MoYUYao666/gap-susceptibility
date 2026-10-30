# DeepInfer notes (2026-10-20)

Source: repository cloned locally from `https://github.com/deepseek-ai/DeepInfer` (shallow clone, inspected `README.md`).
The probe used the VPN that the operator enabled; direct web fetch was blocked by the harness DNS guard, so the facts below
come from the cloned repository, not from a rendered page.

## What it is (verbatim facts from the README)

- "DeepInfer is the high-performance inference framework that powers DeepSeek's large-scale production services. This
  open-source release provides **offline inference** with the core features needed for serving at scale."
- Supported model in this release: **DeepSeek-V4.1-Flash** only.
- Features: optimized kernels (FlashMLA, DeepGEMM, DeepEP, TileKernels, DeepSelect, TileLang kernels); parallelism
  Attention-DP / balanced-CP and MoE-EP + EPLB; DSpark + confidence-scheduled verification (speculative decoding);
  SWA bounded replay; asynchronous scheduling; batch-invariant inference (NVIDIA only); deterministic sampling;
  structured outputs.
- Hardware: **NVIDIA SM100 GPUs** or **Huawei Ascend 950 NPUs**; Linux, GCC >= 13, Python 3.12, CUDA 13 (NVIDIA).
- The release is **not a complete service**: a KV-cache system, PD disaggregation and cross-replica load balancing are
  listed as "required for a complete inference service (not included in this release)".
- Apache 2.0; built primarily on vLLM.

## Applicability to this project

| Question | Answer |
|---|---|
| Can it run our experiments on the local RTX 4060? | **No.** It requires NVIDIA SM100 (Blackwell-class) or Ascend 950, Linux and CUDA 13; the local machine is a Windows RTX 4060 Laptop (8 GB, SM89). |
| Can it serve the models we study (CLIP, LLaVA-1.5, Qwen2-VL)? | **No evidence of vision-language or CLIP support**: the release supports DeepSeek-V4.1-Flash, a text model. Our PEFT/alignment work is on dual encoders and VLMs, so the framework is not applicable to running our models. |
| Can it help with evaluation speed or scale? | Not for our workloads; it targets high-throughput serving of one large text model on data-centre accelerators. Our evaluations are small forward passes on 8 GB. |
| Any indirect value? | Yes, as a reference: deterministic sampling, batch-invariant inference and structured outputs are useful patterns; the prefill/decode Pareto methodology is a good template if we ever report deployment cost. The code is a vLLM derivative, so vLLM/SGLang remain the practical route for serving our models on available hardware. |
| Could it be used for LLM-as-judge or paper-processing tasks? | Only if we had SM100/Ascend hardware and used DeepSeek-V4.1-Flash; not in this project's budget. |

## Conclusion

DeepInfer is a serving framework for a single large text model on data-centre hardware. It has **no direct role** in the
current experiments (8 GB local GPU, CLIP/LLaVA/Qwen-VL workloads). It is recorded as: (i) a reference for deterministic and
batch-invariant inference; (ii) a possible future deployment path if the project ever serves a DeepSeek text model on
Blackwell/Ascend hardware; (iii) not a replacement for vLLM/SGLang in our current setup.
