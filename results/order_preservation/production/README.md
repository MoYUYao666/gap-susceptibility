# Optional upstream producers

Use a separate copy of this production directory. The matched-gap and campaign
producers require PyTorch, torchvision, Pillow, NumPy, SciPy, Transformers,
datasets and (for campaign training) PEFT. Provide the ImageNet parquet shards
under data/imagenet_hf, a local CLIP ViT-B/32 checkpoint, and the benchmark
directories referenced in the scripts. No datasets or weights are bundled.

```text
python tools/_p1209_matched_gap_families.py --help
python tools/_p1319_realfinetune_campaign.py --help
```

The public replay uses NumPy only and never invokes these upstream stages.
