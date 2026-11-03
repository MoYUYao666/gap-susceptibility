# Training-length ablation (2 versus 6 epochs)

If the provenance ordering survives three times the training, it is not a training-length artefact.

| dataset | arm | R@1 2ep | R@1 6ep | change |
|---|---|---|---|---|
| nwpu_captions | human | 0.1653 | 0.1937 | +0.0284 |
| nwpu_captions | templated | 0.1164 | 0.1434 | +0.0270 |
| nwpu_captions | metadata | 0.0746 | 0.1652 | +0.0906 |
| rsicd | human | 0.1483 | 0.1463 | -0.0020 |
| rsicd | templated | 0.0812 | 0.0776 | -0.0036 |
| rsicd | metadata | 0.0476 | 0.2442 | +0.1966 |

Ordering:

- nwpu_captions: 2ep human > templated > metadata / 6ep human > metadata > templated -> CHANGED
- rsicd: 2ep human > templated > metadata / 6ep metadata > human > templated -> CHANGED
