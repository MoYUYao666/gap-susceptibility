# H2 - does the return from more data depend on provenance?

NWPU-Captions; common seeds 0-1; pair budgets 10k vs 50k (the derived arms cap at 31,500 pairs because that is the image count).

| arm | site | R@1 @10k | R@1 @50k | delta | gap @10k | gap @50k |
|---|---|---|---|---|---|---|
| human | vision | 0.1110 | 0.1270 | +0.0160 | 0.8953 | 0.9376 |
| human | both | 0.1257 | 0.1689 | +0.0433 | 0.8963 | 0.9872 |
| segmented | vision | 0.0919 | 0.1050 | +0.0131 | 0.9919 | 0.9081 |
| segmented | both | 0.1309 | 0.1392 | +0.0083 | 0.9692 | 0.9566 |
| templated | vision | 0.0867 | 0.1016 | +0.0149 | 0.9988 | 0.9295 |
| templated | both | 0.1008 | 0.1382 | +0.0374 | 0.9880 | 0.9741 |
| metadata | vision | 0.0469 | 0.0659 | +0.0190 | 1.0019 | 0.8772 |
| metadata | both | 0.0685 | 0.1890 | +0.1205 | 1.0002 | 0.7704 |
