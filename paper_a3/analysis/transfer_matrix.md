# Cross-corpus transfer matrix

Frozen adapters trained on the source corpus, evaluated on the target corpus test split (no target training).

| source | arm | target | n | R@1 i2t | R@1 t2i |
|---|---|---|---|---|---|
| rsicd | human | rsicd | 600 | 0.2033 | 0.2050 |
| rsicd | human | rsitmd | 600 | 0.1600 | 0.1800 |
| rsicd | human | nwpu_captions | 600 | 0.1333 | 0.1600 |
| rsicd | templated | rsicd | 600 | 0.2083 | 0.2000 |
| rsicd | templated | rsitmd | 600 | 0.1600 | 0.1483 |
| rsicd | templated | nwpu_captions | 600 | 0.1383 | 0.1433 |
| rsicd | metadata | rsicd | 600 | 0.1550 | 0.1633 |
| rsicd | metadata | rsitmd | 600 | 0.1117 | 0.1367 |
| rsicd | metadata | nwpu_captions | 600 | 0.1467 | 0.1450 |
| nwpu_captions | human | rsicd | 600 | 0.2033 | 0.1967 |
| nwpu_captions | human | rsitmd | 600 | 0.1633 | 0.1550 |
| nwpu_captions | human | nwpu_captions | 600 | 0.2300 | 0.2217 |
| nwpu_captions | templated | rsicd | 600 | 0.1650 | 0.1583 |
| nwpu_captions | templated | rsitmd | 600 | 0.1500 | 0.1400 |
| nwpu_captions | templated | nwpu_captions | 600 | 0.1517 | 0.1483 |
| nwpu_captions | metadata | rsicd | 600 | 0.1433 | 0.1067 |
| nwpu_captions | metadata | rsitmd | 600 | 0.1250 | 0.0867 |
| nwpu_captions | metadata | nwpu_captions | 600 | 0.1167 | 0.0917 |
