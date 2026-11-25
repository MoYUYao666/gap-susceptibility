# Project state access and third-party notices

These version-bound artifacts are supplied by Hongrui Wan for research
verification. They are project-trained or project-initialized delta/resume
states, not complete foundation models. The software MIT grant does not
relicense checkpoints, source datasets or third-party assets.

The 330 unique native state files cover 372 logical epoch/native records across
42 core/spectral and 24 source-method trajectories. Exact duplicate native and
epoch-zero bytes are stored once, while their functional roles remain distinct.
Twenty-four latest restart serialization aliases are inventoried but are not
additional epochs and are not distributed as separate binary objects.

States preserve recorded trainables, optimizer, scheduler, RNG/progress and
identity. Methods also retain deterministic position-index buffers, fixed
router/rotary constants and related method buffers. Spectral states and 24 small
supplementary ReferenceBuffers.pt files contain fixed aggregate calibration
statistics; these are not trainable parameters or per-example feature banks.
References.json source-token provenance is deliberately excluded.

OpenAI CLIP ViT-B/32 is the separately obtained foundation. See FoundationLock.json
for exact asset hashes, and OPENAI_CLIP_LICENSE.txt for the applicable OpenAI MIT
notice and disclaimer. No learned foundation weights or tokenizer assets are
bundled. Upstream documentation and model-card limitations remain applicable;
research reproducibility is not an endorsement for deployment, surveillance or
facial recognition. The foundation model source is https://github.com/openai/CLIP.

Training provenance: CIFAR100 (Alex Krizhevsky, *Learning Multiple Layers of
Features from Tiny Images*, 2009; https://www.cs.toronto.edu/~kriz/cifar.html),
DTD (Cimpoi et al., *Describing Textures in the Wild*, CVPR 2014;
https://www.robots.ox.ac.uk/~vgg/data/dtd/), and Food101 (Bossard et al.,
*Food-101 -- Mining Discriminative Components with Random Forests*, ECCV 2014;
https://data.vision.ee.ethz.ch/cvl/datasets_extra/food-101/). DTD is provided in a
research context. No general image, commercial-data, institutional ownership or
third-party rights grant is inferred. Obtain original inputs under their source
terms. Raw images, captions/tokens, per-example feature arrays and private
manuscript/editorial materials are not included.

The inspected official sources contained no explicit prohibition on publication
of this bounded author-trained-state/aggregate scope. This is not an exhaustive
rights certification or a guarantee that models cannot memorize training data.
No warranty of fitness, non-infringement, cross-hardware equality or complete
historical-state recovery is made. Retain attribution and these notices.
