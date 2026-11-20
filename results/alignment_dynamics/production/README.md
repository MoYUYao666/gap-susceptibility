# Optional measurement code

These producers are not required for offline replay. The paired-energy tracker
takes in-memory Torch tensors. The LLaVA producer requires local model files,
the COCO val2014 images and caption annotations, CUDA, PyTorch, Transformers,
PEFT and Pillow (bitsandbytes for the 4-bit arm).

Run inside an independent working copy of this production directory:

```text
python tools/_p820_llava_sites.py --help
python tools/_p820_llava_sites.py --verify-only --model <local-model> --coco-root <local-coco>
```

The two archived cohorts use different sample counts. Do not interpret the
archived comparison as a matched precision effect.
