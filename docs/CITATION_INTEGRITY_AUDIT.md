# Citation-Integrity Audit — `paper_a1` and `paper_a2`

**Date:** 2026-09-15 · **Auditor role:** independent (no prior involvement in compiling these bibliographies)
**Question asked:** does every cited work actually exist as described, and is every citation used for what the source says?
**Files inspected (read-only):**

| Manuscript | Files | Bibitems |
|---|---|---|
| `paper_a1` | `main.tex`, `related_work.tex`, `related_work_bibitems.tex` | **56** (13 in `main.tex` + 43 in `related_work_bibitems.tex`, spliced via `\input` at `main.tex:583`) |
| `paper_a2` | `main.tex` + `ext_partI…V*.tex` | **28** (all in the `thebibliography` of `main.tex:838-895`) |

No file was modified except this report.

---

## 0. Method and its limits

Every entry was resolved against an **external, primary or publisher-deposited record**, and the record page was opened before a verdict was given. Sources used, by class:

* **DOI resolution** — `api.crossref.org/works/<doi>` (publisher-deposited metadata; used because `doi.org` → ScienceDirect/Springer/ACM landing pages returned 403 or cross-origin refusals from this machine).
* **Conference proceedings** — `proceedings.mlr.press` (ICML), `proceedings.neurips.cc` / `datasets-benchmarks-proceedings.neurips.cc` (NeurIPS), `openaccess.thecvf.com` (CVPR/ICCV/ECCV/WACV), `iclr.cc/virtual` and `proceedings.iclr.cc`, `aclanthology.org` (ACL/EACL), `isca-archive.org` (Interspeech), `icml.cc/virtual` (ICML 2026), `cvpr.thecvf.com/virtual` (CVPR 2026).
* **Preprints** — `arxiv.org/abs/<id>` (title, full author list, and the authors' own `Comments:` field).
* **Datasets/models/repositories** — `api.github.com/repos/…` (authoritative licence + description), `huggingface.co/…` where reachable, project/CRIS records (`ros.hw.ac.uk`, `cris.technion.ac.il`).
* Two entries were confirmed through the citing literature (e.g. NKSID's collection parameters via *Scientific Reports* 15:22617 = PMC12214808).

**Verdict definitions used** — VERIFIED (exists; authors/year/title/venue as stated), MISMATCH (exists but a stated field is wrong), UNVERIFIABLE (could not confirm; queries listed in §6), SUSPECT (cannot be a real publication). "Author lists abbreviated with *et al.*" is accepted; **spelled-out author lists that name people who are not authors are not**.

**Environment limits that bound this audit (stated once, here):**

1. **`huggingface.co` is unreachable from this machine.** DNS resolves it to `108.160.167.159` (a Meta/Facebook address) and TCP 443 is refused; `web_fetch` rejects the host as non-public. Everything HF-hosted is therefore unverifiable here — see §6.
2. `dl.acm.org`, `academic.oup.com`, `link.springer.com`/`idp.springer.com`, `sciencedirect.com`, `openreview.net`, `dblp.org` (bot wall), `api.semanticscholar.org` (429), `pnas.org`/`cell.com` (403) were all unreachable. Where that happened, the publisher-*deposited* Crossref record was used and is named as the source; this is one step less direct than the publisher page.
3. Today is **2026-09-15**, so CVPR/ICLR/ICML 2026 and IEEE 2026 volumes are past, published, and checkable — they were checked, not assumed.

---

## 1. Totals per file

| File | `\bibitem` count | Distinct keys | Cited | Orphans | Undefined cites | Duplicate keys | Duplicate works |
|---|---|---|---|---|---|---|---|
| `paper_a1/main.tex` | 13 | 13 | 13 | 0 | 0 | 0 | 0 |
| `paper_a1/related_work_bibitems.tex` | 43 | 43 | 43 | 0 | 0 | 0 | 0 |
| **`paper_a1` total** | **56** | **56** | **56** | **0** | **0** | **0** | **0** |
| `paper_a2/main.tex` | 28 | 28 | 28 | 0 | 0 | 0 | 0 |
| **`paper_a2` total** | **28** | **28** | **28** | **0** | **0** | **0** | **0** |

Note on the header claim in `related_work_bibitems.tex`: it says the block adds "40 entries to the 13 already present" and enumerates 40 new keys — the file actually defines **43** `\bibitem`s. The three CZSL entries (`liu2025concept`, `liu2026semineg`, `liu2025mlcp`, lines 101–103) are missing from that inventory (they are cited, so nothing breaks; the header is simply wrong).

---

## 2. `paper_a1` — all 56 entries

Verdicts: **49 VERIFIED · 6 MISMATCH · 1 UNVERIFIABLE · 0 SUSPECT**

### 2.1 From `main.tex` (13)

| key | authors as printed | year | venue as printed | verdict | source checked | correction / note |
|---|---|---|---|---|---|---|
| `liang2022` | V. W. Liang et al. | 2022 | NeurIPS 2022 | VERIFIED | proceedings.neurips.cc (hash `702f4db7…`) + Crossref | pp. 17612–17625 |
| `radford2021` | A. Radford et al. | 2021 | ICML 2021 | VERIFIED | proceedings.mlr.press/v139/radford21a | PMLR 139:8748–8763 |
| `yi2025` | L. Yi, R. Douady, C. Chen | 2025 | arXiv:2510.03268, 2025 | VERIFIED | arxiv.org/abs/2510.03268 | title/authors exact; ICML 2026 version exists (see §4) |
| `cai2026` | Y. Cai et al. | 2026 | ICML 2026 | VERIFIED | arxiv.org/abs/2601.19597 (`Comments: Accepted at ICML 2026`) + icml.cc/virtual/2026/poster/63447 | Yichao Cai, Zhen Zhang, Yuhang Liu, Javen Qinfeng Shi |
| `levi2025` | **D.** Levi, G. Gilboa | 2025 | ICML 2025 | **MISMATCH** | cris.technion.ac.il record + PMLR vol. 267 | first author is **Meir Yossef Levi → "M. Y. Levi"**; pp. 33999–34019 |
| `imod` | M. Zhang et al. | 2026 | CVPR 2026 | VERIFIED | openaccess.thecvf.com CVPR2026 `Zhang_Parameter-Efficient_Adaptation…` + cvpr.thecvf.com/virtual/2026/poster/38314 | Mingfang Zhang, Yunhong Wang, Lu Wang, Jiaxin Chen; pp. 37745–37755. Key name `imod` breaks this file's author–year key convention |
| `mistretta2025` | M. Mistretta et al. | 2025 | ICLR 2025 | VERIFIED | proceedings.iclr.cc 2025 hash `c15da559…` | Marco Mistretta, Alberto Baldrati, Lorenzo Agnolucci, Marco Bertini, Andrew Bagdanov |
| `yamaguchi2025` | S. Yamaguchi et al. | 2025 | CVPR 2025 | VERIFIED | openaccess.thecvf.com CVPR2025 `Yamaguchi_Post-pre-training…` | title exactly as stated; pp. 4256–4266 |
| `sofer2025` | A. Sofer, Y. Goldman, S. E. Chazan | 2025 | Interspeech 2025 | VERIFIED | isca-archive.org/interspeech_2025/sofer25_interspeech | pp. 196–200; DOI 10.21437/interspeech.2025-1664 |
| `chowers2026` | **I.** Chowers, O. Naparstek | 2026 | CVPR 2026 | **MISMATCH** | openaccess.thecvf.com CVPR2026 `Chowers_Is_the_Modality_Gap…` + arxiv.org/abs/2603.29080 | first author is **Rhea Chowers → "R."**; the paper has **4** authors (Chowers, Naparstek, Barzelay, Weiss); pp. 30288–30298 |
| `grassucci2026` | E. Grassucci, **L.** Cicchetti, et al. | 2026 | ICLR 2026 | **MISMATCH** | arxiv.org/abs/2601.18525 (`Comments: ICLR 2026`) + github.com/ispamm/ModGap | second author is **Giordano Cicchetti → "G. Cicchetti"** |
| `wortsman2022` | M. Wortsman et al. | 2022 | CVPR 2022 | VERIFIED | openaccess.thecvf.com CVPR2022 | pp. 7959–7971 |
| `wan2026protect` | H. Wan | 2026 | under review, Pattern Recognition | UNVERIFIABLE (expected) | no public record (see §6) | the author's own under-review manuscript; **title matches A2's `wanP1` exactly** ✔ |

### 2.2 From `related_work_bibitems.tex` (43)

| key | authors as printed | year | venue as printed | verdict | source checked | correction / note |
|---|---|---|---|---|---|---|
| `hendrycks2021imagenetr` | D. Hendrycks et al. | 2021 | ICCV 2021 | VERIFIED | openaccess.thecvf.com ICCV2021 | 13 authors; CVF pagination 8340–8349. The file's *comment* claims "pp. 8320–8329" — see §7 |
| `miller2021accuracy` | J. P. Miller et al. | 2021 | ICML 2021 | VERIFIED | proceedings.mlr.press/v139/miller21b | PMLR 139:7721–7735 |
| `fang2022data` | A. Fang et al. | 2022 | ICML 2022 | VERIFIED | proceedings.mlr.press/v162/fang22a | PMLR 162:6216–6234 |
| `cherti2023openclip` | M. Cherti et al. | 2023 | CVPR 2023 | VERIFIED | openaccess.thecvf.com CVPR2023 | pp. 2818–2829 |
| `kumar2022finetuning` | A. Kumar et al. | 2022 | ICLR 2022 | VERIFIED | iclr.cc/virtual/2022/poster/5945 | |
| `jia2022vpt` | M. Jia et al. | 2022 | ECCV 2022 | VERIFIED | Crossref DOI 10.1007/978-3-031-19827-4_41 | LNCS pp. 709–727 |
| `mosbach2021stability` | M. Mosbach, M. Andriushchenko, D. Klakow | 2021 | ICLR 2021 | VERIFIED | iclr.cc/virtual/2021/poster/2558 | exact |
| `french1999catastrophic` | R. M. French | 1999 | Trends in Cognitive Sciences | VERIFIED | Crossref DOI 10.1016/S1364-6613(99)01294-2 | 3(4):128–135 |
| `ramasesh2021anatomy` | V. V. Ramasesh, E. Dyer, M. Raghu | 2021 | ICLR 2021 | VERIFIED | iclr.cc/virtual/2021/poster/2907 | exact |
| `kirkpatrick2017ewc` | J. Kirkpatrick et al. | 2017 | PNAS | VERIFIED | Crossref DOI 10.1073/pnas.1611835114 | PNAS 114(13):3521–3526 |
| `houlsby2019adapter` | N. Houlsby et al. | 2019 | ICML 2019 | VERIFIED | proceedings.mlr.press/v97/houlsby19a | PMLR 97:2790–2799 |
| `hu2022lora` | E. J. Hu et al. | 2022 | ICLR 2022 | VERIFIED | iclr.cc/virtual/2022/poster/6319 | |
| `luo2023empirical` | Y. Luo et al. | 2023 | **arXiv:2308.08747, 2023** (labelled arXiv-only) | **MISMATCH** | arxiv.org/abs/2308.08747 + Crossref DOI 10.1109/TASLPRO.2025.3606231 | **not arXiv-only**: *IEEE Transactions on Audio, Speech and Language Processing* **vol. 33, pp. 3776–3786, 2025**. Authors Yun Luo, Zhen Yang, Fandong Meng, Yafu Li, Jie Zhou, Yue Zhang ✔ |
| `zhai2023forgetting` | Y. Zhai et al. | 2023 | **arXiv:2309.10313, 2023** (labelled arXiv-only) | **MISMATCH** | arxiv.org/abs/2309.10313 + proceedings.mlr.press/v234/zhai24a | **not arXiv-only**: *Conference on Parsimony and Learning (CPAL) 2024*, **PMLR 234:202–227**; published title uses singular "…Multimodal Large Language **Model** Fine-Tuning". Authors ✔ |
| `nicolas2024mopclip` | J. Nicolas et al. | 2024 | WACV 2024 | VERIFIED | openaccess.thecvf.com WACV2024 | pp. 1762–1772; Julien Nicolas first |
| `kendall1938` | M. G. Kendall | 1938 | Biometrika | VERIFIED | Crossref DOI 10.1093/biomet/30.1-2.81 | 30(1–2):81–93 |
| `spearman1904` | C. Spearman | 1904 | American Journal of Psychology | VERIFIED | Crossref DOI 10.2307/1412159 + OpenAlex | 15(1):72 ff. Journal's full name is *The* American Journal of Psychology (cosmetic) |
| `buckley2000stability` | C. Buckley, E. M. Voorhees | 2000 | SIGIR 2000 | VERIFIED | Crossref SIGIR'00 DOI 10.1145/345508.345543 | pp. 33–40; author order matches |
| `voorhees2002topic` | E. M. Voorhees, C. Buckley | 2002 | SIGIR 2002 | VERIFIED | OpenAlex/Crossref DOI 10.1145/564376.564432 | pp. 316–323; author order matches |
| `carterette2012multiple` | B. Carterette | 2012 | ACM Transactions on Information Systems | VERIFIED | Crossref/OpenAlex DOI 10.1145/2094072.2094076 | TOIS 30(1), art. 4, 2012 |
| `kornblith2019cka` | S. Kornblith et al. | 2019 | ICML 2019 | VERIFIED | proceedings.mlr.press/v97/kornblith19a | PMLR 97:3519–3529 |
| `raghu2017svcca` | M. Raghu et al. | 2017 | NeurIPS 2017 | VERIFIED | proceedings.neurips.cc 2017 hash `dc6a7e65…` | |
| `williams2021shape` | A. H. Williams et al. | 2021 | NeurIPS 2021 | VERIFIED | proceedings.neurips.cc 2021 hash `252a3dba…` | |
| `ding2021grounding` | F. Ding, **J.-Y.** Denain, J. Steinhardt | 2021 | NeurIPS 2021 | **MISMATCH** | proceedings.neurips.cc 2021 hash `0c0bf917…` (+ independent reference list in DOI 10.1145/3728458) | middle author is **Jean-Stanislas Denain → "J.-S. Denain"** |
| `thrush2022winoground` | T. Thrush et al. | 2022 | CVPR 2022 | VERIFIED | openaccess.thecvf.com CVPR2022 | pp. 5238–5248 |
| `yuksekgonul2023when` | M. Yuksekgonul et al. | 2023 | ICLR 2023 | VERIFIED | iclr.cc/virtual/2023/poster/10875 | title casing only ("Bags-of-Words") |
| `klabunde2025similarity` | M. Klabunde et al. | 2025 | ACM Computing Surveys | VERIFIED | Crossref DOI 10.1145/3728458 + OpenAlex | CSUR 57(9), 2025 ✔. The file's *comment* adds "art. 242" — not confirmable (§7) |
| `guo2017calibration` | C. Guo et al. | 2017 | ICML 2017 | VERIFIED | proceedings.mlr.press/v70/guo17a | PMLR 70:1321–1330 |
| `minderer2021revisiting` | M. Minderer et al. | 2021 | NeurIPS 2021 | VERIFIED | proceedings.neurips.cc 2021 hash `8420d359…` | |
| `ovadia2019trust` | Y. Ovadia et al. | 2019 | NeurIPS 2019 | VERIFIED | proceedings.neurips.cc 2019 hash `8558cb40…` | title wording exact |
| `hu2025inferencecal` | M. Hu, H. Chang, S. Shan, X. Chen | 2025 | Pattern Recognition Letters, 2025 | VERIFIED | Crossref DOI 10.1016/j.patrec.2025.03.010 + OpenAlex + VIPL/ICT-CAS list | **this is the "Pattern Recognition Letters paper" flagged in the brief**: real, and correctly labelled — PRL vol. 192, pp. 15–21, 2025; authors Minyang Hu, Hong Chang, Shiguang Shan, Xilin Chen |
| `zhou2022coop` | K. Zhou et al. | 2022 | International Journal of Computer Vision | VERIFIED | Crossref DOI 10.1007/s11263-022-01653-1 | IJCV 130(9):2337–2348 |
| `zhou2022cocoop` | K. Zhou et al. | 2022 | CVPR 2022 | VERIFIED | openaccess.thecvf.com CVPR2022 | pp. 16816–16825; distinct paper from `zhou2022coop` ✔ |
| `khattak2023maple` | M. U. Khattak et al. | 2023 | CVPR 2023 | VERIFIED | openaccess.thecvf.com CVPR2023 | pp. 19113–19122 |
| `shu2022tpt` | M. Shu et al. | 2022 | NeurIPS 2022 | VERIFIED | proceedings.neurips.cc 2022 hash `5bf2b802…` | |
| `wang2020alignment` | T. Wang, P. Isola | 2020 | ICML 2020 | VERIFIED | proceedings.mlr.press/v119/wang20k | PMLR 119:9929–9939 |
| `steck2024cosine` | H. Steck, C. Ekanadham, N. Kallus | 2024 | ACM Web Conference 2024 (Companion) | VERIFIED | Crossref DOI 10.1145/3589335.3651526 | WWW '24 Companion, pp. 887–890 ✔ (the file's comment DOI is correct) |
| `thakur2021beir` | N. Thakur et al. | 2021 | NeurIPS 2021 Datasets & Benchmarks Track | VERIFIED | datasets-benchmarks-proceedings.neurips.cc 2021 hash `65b9eea6…` | |
| `muennighoff2023mteb` | N. Muennighoff et al. | 2023 | EACL 2023 | VERIFIED | aclanthology.org/2023.eacl-main.148 | pp. 2014–2037 |
| `huh2024platonic` | M. Huh et al. | 2024 | ICML 2024 | VERIFIED | proceedings.mlr.press/v235/huh24a | "Position:" prefix present in the proceedings title ✔ |
| `liu2025concept` | Y. Liu, X. Wang, X. Gao, J. Han, L. Shao | 2025 | IEEE TNNLS **36(6):10394–10406** | VERIFIED | Crossref DOI 10.1109/TNNLS.2025.3528885 + OpenAlex | every field exact (Yang Liu, Xinshuo Wang, Xinbo Gao, Jungong Han, Ling Shao) |
| `liu2026semineg` | Y. Liu, X. Wang, X. Gao, J. Han, L. Shao | 2026 | IEEE TIP **35:2640–2652** | VERIFIED | Crossref DOI 10.1109/TIP.2026.3671655 + OpenAlex | every field exact |
| `liu2025mlcp` | Y. Liu et al. | 2025 | IEEE TIP **34:4856–4868** | VERIFIED | Crossref/OpenAlex DOI 10.1109/TIP.2025.3592560 | volume/pages exact |

---

## 3. `paper_a2` — all 28 entries

Verdicts: **13 VERIFIED · 11 MISMATCH · 4 UNVERIFIABLE · 0 SUSPECT**

`paper_a2` uses `elsarticle` author–year style, so author lists are **spelled out** rather than abbreviated. That is precisely where most of its defects are: several entries name people who are not authors of the cited work.

| key | authors as printed | year | venue as printed | verdict | source checked | correction / note |
|---|---|---|---|---|---|---|
| `aquaticclip2026` | Alawode, B., Ganapathi, I. I., Javed, S., **Werghi, N.**, Bennamoun, M., Mahmood, A. | 2026 | IEEE TNNLS, DOI 10.1109/TNNLS.2026.3657138 (arXiv:2502.01785) | **MISMATCH** | Crossref DOI record + arxiv.org/abs/2502.01785 | DOI resolves ✔: TNNLS **37(8):3956–3969, Aug 2026**. But the **published** paper has **5** authors — Alawode, Iyappan Ganapathi, Javed, Bennamoun, Mahmood — and **not Naoufel Werghi**; the 6-author list (with Werghi) is the **arXiv preprint** version. The entry mixes the two |
| `oceangpt2023` | Bi, Z., Zhang, N., Xue, Y., Ou, Y., et al. | 2023 | **In: Advances in Neural Information Processing Systems (NeurIPS)** | **MISMATCH** | aclanthology.org/2024.acl-long.184 (+ arXiv:2310.02031 `Comments: ACL2024`) | published at **ACL 2024** (62nd Annual Meeting, Long Papers), pp. 3357–3372, DOI 10.18653/v1/2024.acl-long.184 — **not NeurIPS**; publication year 2024. Author list ✔ |
| `biderman2024` | Biderman, D., Portes, J., Ortiz, J. J. G., Paul, M., et al. | 2024 | **In: Advances in Neural Information Processing Systems (NeurIPS)** | **MISMATCH** | mlanthology.org TMLR 2024 record + OpenReview `aloEru2qCG` | published in **Transactions on Machine Learning Research (TMLR), 2024** — **not NeurIPS**. Author list ✔ (12 authors) |
| `chen2025` | Chen, L., Huang, Y., Dong, J. | 2025 | ACM Computing Surveys, DOI 10.1145/3759243 | VERIFIED (notes) | Crossref DOI record | DOI resolves ✔. Actual title ends "…Current, **Challenge**, and Future"; **CSUR 58(3)**, online 2025-09-09 / print Feb 2026; paper has **8** authors (only 3 listed, no "et al.") |
| `chowers2026` | **Chowers, I.**, Naparstek, O. | 2026 | CVPR 2026 | **MISMATCH** | openaccess.thecvf.com CVPR2026 + arxiv.org/abs/2603.29080 | **R. Chowers**; **4** authors (add Barzelay, Weiss); pp. 30288–30298 |
| `christensen2026` | Christensen, K. A., Tufte, A. G., Gusev, A., Sinha, R., et al. | 2026 | Ocean Engineering, DOI 10.1016/j.oceaneng.2026.124646 | VERIFIED | Crossref DOI record | DOI resolves ✔: **vol. 359, art. 124646, June 2026**; 8 authors, first four exact |
| `grassucci2026` | Grassucci, E., **Cicchetti, L.**, **Maiorca, M.**, et al. | 2026 | ICLR 2026 | **MISMATCH** | arxiv.org/abs/2601.18525 (`Comments: ICLR 2026`) + github.com/ispamm/ModGap | correct list: Grassucci, **Giordano Cicchetti**, Emanuele Frasca, Aurelio Uncini, Danilo Comminiello. **"Maiorca, M." is not an author of this paper at all** |
| `jian2024` | Jian, M., Yang, N., Chen, T. | 2024 | Intelligent Marine Technology and Systems, DOI 10.1007/s44295-024-00023-6 | VERIFIED (notes) | Crossref DOI record | DOI resolves ✔: vol. 2, art. 9, 2024, title exact; **5** authors (3 listed, no "et al."); 3rd author is indexed given "Chen"/family "Tao" — name order ambiguous in the index |
| `s3simulator2024` | **Kamal, B.**, et al. | 2024 | Pattern Recognition (ICPR volume), Springer, DOI 10.1007/978-3-031-78444-6_15 | **MISMATCH** | Crossref chapter record + Crossref book DOI 10.1007/978-3-031-78444-6 | chapter real: title ✔, **LNCS "Pattern Recognition", ICPR 2024 Part XVI, pp. 219–235**, online 2024-12-04. But the record's authors are **"S. Kamal Basha"** (family *Kamal Basha*, given *S.*) **and Athira Nambiar — two authors only**, so "Kamal, B., et al." mis-states the lead author and implies a longer list |
| `levi2025` | **Levi, D.**, Gilboa, G. | 2025 | ICML 2025 | **MISMATCH** | cris.technion.ac.il + PMLR vol. 267 | **Meir Yossef Levi → "M. Y. Levi"**; pp. 33999–34019 |
| `liang2022` | Liang, V. W., Zhang, Y., Kwon, Y., Yeung, S., Zou, J. | 2022 | NeurIPS 2022 | VERIFIED | proceedings.neurips.cc 2022 hash `702f4db7…` | exact |
| `maione2026` | Maione, F., Arici, S. S., Hasan, A., Sukarevicius, M. | 2026 | Ocean Engineering, DOI 10.1016/j.oceaneng.2026.127078 | VERIFIED | Crossref DOI record | DOI resolves ✔: **vol. 364, art. 127078, Aug 2026**; first four authors exact |
| `mistretta2025` | Mistretta, M., **Deng, C.**, **Ma, A.**, et al. | 2025 | ICLR 2025 | **MISMATCH** | proceedings.iclr.cc 2025 hash `c15da559…` | correct list: Mistretta, Alberto Baldrati, Lorenzo Agnolucci, Marco Bertini, Andrew Bagdanov. **Neither "Deng, C." nor "Ma, A." is an author** |
| `nksid2024` | (dataset entry, no authors) | 2024 | github.com/Jorwnpay/NK-Sonar-Image-Dataset (MIT licence) | VERIFIED | api.github.com repo record (licence `{"key":"mit"}`) + repo README + PMC12214808 | repo, licence **MIT** ✔, "2 617 images / 8 classes / natural long tail" ✔. The text's "Bohai Bay … Oculus M750d multibeam sonar" ✔ (Sci Rep 15:22617). NKSID does appear in the `sonarsurvey2025` timeline figure ✔ |
| `qin2022` | Qin, J., Li, M., Li, D. | 2022 | Remote Sensing, DOI 10.3390/rs14153794 | VERIFIED (notes) | Crossref DOI record | DOI resolves ✔: RS 14(15):3794, 2022, title exact; **5** authors (Jiangying Qin, Ming Li, Deren Li, Jiageng Zhong, Ke Yang) — 2 omitted without "et al." |
| `qwen2vl2024` | Qwen Team | 2024 | HuggingFace model card, "(CC-BY-4.0)" | UNVERIFIABLE | HF unreachable (DNS → 108.160.167.159, TCP 443 refused); search index confirms the page exists; a ModelScope mirror of the *same* model id is tagged `apache-2.0` | **possible MISMATCH on the licence** (CC-BY-4.0 vs Apache-2.0) — needs an off-box check. A citable report exists and can replace the bare model card: **arXiv:2409.12191**, "Qwen2-VL: Enhancing Vision-Language Model's Perception of the World at Any Resolution" |
| `radford2021` | Radford, A., Kim, J. W., Hallacy, C., et al. | 2021 | ICML 2021 | VERIFIED | proceedings.mlr.press/v139/radford21a | PMLR 139:8748–8763 |
| `sofer2025` | Sofer, A., Goldman, Y., Chazan, S. E. | 2025 | Interspeech | VERIFIED | isca-archive.org/interspeech_2025/sofer25_interspeech | pp. 196–200 |
| `sonarsurvey2025` | **(no authors given at all)** | 2025 | "A review of sonar image datasets: resources, challenges and applications", arXiv:2510.03353 | **MISMATCH** | arxiv.org/abs/2510.03353 + arxiv.org/html/2510.03353v1 | the id is real but belongs to a **differently titled** work: *"Sonar Image Datasets: A Comprehensive Survey of Resources, Challenges, and Applications"*, by **9 authors** (Larissa S. Gomes, Gustavo P. Almeida, Bryan U. Moreira, Marco Quiroz, Breno Xavier, Lucas Soares, Stephanie L. Brião, Felipe G. Oliveira, Paulo L. J. Drews-Jr). The record's own comment field says it is **published in SIBGRAPI 2025** — so it is not an arXiv-only preprint either. The `Awesome-Sonar-Image-Resources` catalogue URL in the same entry is separately correct ✔ (and it does list NKSID first under "Classification") |
| `mvaldenegro2024` | Valdenegro-Toro, M. | **2024** | PhD thesis, Heriot-Watt University | **MISMATCH** | ros.hw.ac.uk item `8250bc8d-…` (hdl 10399/4035) + api.github.com repo record | thesis real, correct title and institution, but **issued 2019**, not 2024; author renders "Valdenegro Toro, Matias Alejandro" (unhyphenated). Dataset repo ✔, abstract confirms ARIS Explorer 3000 |
| `wanA1` | Wan, H. | 2026 | Manuscript PRLETTERS-D-26-01941 (Pattern Recognition Letters, 2026) | UNVERIFIABLE (expected) + **title inconsistency** | no public record (§6); cross-checked against `paper_a1/main.tex:14` and `HANDOFF.md` | the cited title **"A decoupled view of class-ordering and classification robustness under gap surgery" has zero public trace and is not the title of the companion manuscript in this workspace** — see §5.1 |
| `wanP1` | Wan, H. | 2026 | Under review, Pattern Recognition (PR-D-26-10149) | UNVERIFIABLE (expected) | no public record (§6); consistent with `paper_a1`'s `wan2026protect` ✔ | the author's own under-review manuscript. The workspace's own records disagree on whether it is still under review — see §5.2 |
| `wortsman2022` | Wortsman, M., Ilharco, G., Kim, J. W., et al. | 2022 | CVPR 2022 | VERIFIED | openaccess.thecvf.com CVPR2022 | pp. 7959–7971 |
| `uatd2022` | Xie, K., Yang, J., Qiu, K. | 2022 | Scientific Data 9:739, DOI 10.1038/s41597-022-01854-w | VERIFIED | Crossref DOI record | DOI resolves ✔; **article number 739 ✔**; authors exact (Kaibing Xie, Jian Yang, Kang Qiu) |
| `yamaguchi2025` | Yamaguchi, S., **Sotani, R.**, **Shim, V.**, et al. | 2025 | CVPR 2025 | **MISMATCH** | openaccess.thecvf.com CVPR2025 `Yamaguchi_Post-pre-training…` | correct list: Shin'ya Yamaguchi, **Dewei Feng, Sekitoshi Kanai, Kazuki Adachi, Daiki Chijiwa**. **Neither "Sotani, R." nor "Shim, V." is an author**; pp. 4256–4266 |
| `yi2025` | Yi, L., Douady, R., Chen, C. | 2025 | arXiv:2510.03268 (+ "ICML 2026 version: The convergent representation of V-L contrastive learning") | VERIFIED (note) | arxiv.org/abs/2510.03268 + icml.cc/virtual/2026/poster/66630 | arXiv record exact ✔. The ICML 2026 title as printed is an **inexact abbreviation**: the real title is *"The Convergent Representation of Contrastive Vision-Language Models: Geometry, Modality Gap and Shared Space Alignment"* (same three authors, poster, OpenReview `206P2ygDYN`) |
| `marinegpt2023` | Zheng, Z., Zhang, J., Vu, T.-A., Diao, S., et al. | 2023 | arXiv:2310.13596 | VERIFIED | arxiv.org/abs/2310.13596 | exact (Ziqiang Zheng, Jipeng Zhang, Tuan-Anh Vu, Shizhe Diao, Yue Him Wong Tim, Sai-Kit Yeung) |
| `oceanclip2025` | zjunlp | 2025 | HuggingFace model card (OceanGPT-X collection) | UNVERIFIABLE | HF unreachable; search index confirms the page and its title "OceanCLIP-0.15B: Marine Vision-Language Model" + commit history; no 404 evidence | the model card is the paper's central object, so this is the most consequential unverified item in A2 — needs an off-box check. The parent-collection claim is also unconfirmed |

---

## 4. Self-consistency inside each manuscript

| Check | `paper_a1` | `paper_a2` |
|---|---|---|
| Every `\cite` key resolves to a `\bibitem` | ✅ 0 undefined (97 cite calls, 56 distinct keys) | ✅ 0 undefined (40 cite calls, 28 distinct keys) |
| Every `\bibitem` is cited (orphans) | ✅ 0 orphans | ✅ 0 orphans |
| Duplicate keys | ✅ none | ✅ none |
| Two keys for the same work | ✅ none (all 56 normalised titles distinct) | ✅ none (all 28 distinct) |
| Entry description contradicts its use in the text | ⚠️ 2 items — see §5.3 | ⚠️ 3 items — see §5.3 |

Two extra self-consistency notes:

* `paper_a1/main.tex` defines its 13 entries and then `\input{related_work_bibitems}` at line 583; the 43 keys in the included file do not overlap with those 13 (verified key-by-key), so the split is safe. `related_work.tex` is `\input` at line 47 and there is no duplicated `\section{Related Work}`.
* **Out of scope but worth flagging:** `paper_a1/main_zh.tex` (the Chinese version) contains its **own** `thebibliography` with **16** entries — the same 13 plus `liu2025concept`, `liu2026semineg`, `liu2025mlcp` — and does **not** `\input` anything. Those three keys are therefore defined in two places in the repository. As long as `main_zh.tex` never inputs `related_work_bibitems.tex` this is harmless, but if the two are ever merged there will be three duplicate `\bibitem` keys and a LaTeX "multiply defined" error.

---

## 5. Cross-manuscript consistency

### 5.1 The companion papers — one of them is cited under a title that does not exist

| Work | `paper_a1` | `paper_a2` | Consistent? |
|---|---|---|---|
| The other manuscript (A1, PRLETTERS-D-26-01941) | — (a paper does not cite itself) | `wanA1`: *"A decoupled view of class-ordering and classification robustness under gap surgery"*, Ms PRLETTERS-D-26-01941, Pattern Recognition Letters, 2026 | ❌ |
| The P1 companion ("Protect, Don't Perturb") | `wan2026protect`: title ✔, "under review, Pattern Recognition, 2026" | `wanP1`: **same title** ✔, "Under review, Pattern Recognition (PR-D-26-10149)" | ✅ |

**Finding (highest-impact item in this audit).** `paper_a2`'s bibliography describes its own companion manuscript with a title that appears nowhere: the workspace's `paper_a1/main.tex:14` titles that manuscript **"The Modality Gap Is Not a Universal Health Metric: Order Preservation Governs Zero-Shot Robustness"**, and `HANDOFF.md:60` records that this is the title actually submitted to Pattern Recognition Letters under PRLETTERS-D-26-01941. A search for the phrase returns nothing. The provenance of the error is visible in the repository: `docs/A2_literature.md:32` carries the "A Decoupled View…" title with the annotation *"（A1 题名以投稿版为准）"* ("A1's title is to follow the submitted version") — a placeholder that was never updated before it was copied into `paper_a2/main.tex:880` and `paper_a2/main_zh.tex:748`. A reader (or an editor checking the disclosure in `paper_a2/cover_letter.tex:32`) cannot resolve the reference.

Related status drift in the same entry: it says the manuscript is "(Pattern Recognition Letters, 2026); revised version in preparation for resubmission", but the workspace records that PRLETTERS-D-26-01941 was **rejected on 2026-09-14** (`docs/A1_RESUBMISSION_MASTER_PLAN.md:3`, `HANDOFF.md:8`). The cover letter handles this correctly ("previously submitted … decision received; a revised version is in preparation for resubmission elsewhere"); the bibliography entry does not.

**Second, smaller inconsistency in the same place.** `paper_a2/main.tex:46` states the companion "was confined to one domain (ImageNet, 1,000 classes) and to general-purpose models". `paper_a1`'s own abstract claims five zero-shot benchmarks (ImageNet-1K, DTD, Food-101, iNaturalist-wild, a rare-species benchmark), three model families and sixteen fine-tuned checkpoints, with a dedicated section "Further zero-shot and fine-grained benchmarks". One of the two descriptions is out of date; A2 should not understate the companion it is reusing.

### 5.2 The P1 companion's stated status

Both manuscripts describe PR-D-26-10149 as **under review**. That matches `HANDOFF.md:8` ("P1（PR）Under Review（08-23，等）"), but the same file's 2026-09-09 entry says *"用户确认 P1 曾投稿并被拒"* ("the operator confirmed P1 was submitted and rejected"), and `docs/PA_P3_MERGE_PLAN.md` is titled *"PA + P3 merge plan (triggered by P1 rejection)"* with the trigger marked as met. The workspace's own records therefore contradict each other. This does not make the citation false, but since both manuscripts state a submission status in print, **the operator should confirm which is current before submission**.

### 5.3 Shared prior work — described consistently across the two papers

All eleven shared works (`liang2022`, `radford2021`, `yi2025`, `levi2025`, `mistretta2025`, `yamaguchi2025`, `sofer2025`, `chowers2026`, `grassucci2026`, `wortsman2022`, and the P1 companion) are used for **the same claims** in both manuscripts, and where both papers make a claim about a specific source the claims agree:

* `grassucci2026` — A1: "training-based gap closing leaves instance-wise tasks (retrieval) unaffected while helping group-wise tasks (clustering)"; A2: "training-based gap closing preserves instance-wise task structure". Both match the source abstract ✔.
* `chowers2026` — A1: "moving the text side … finds weak and inconsistent effects on accuracy"; A2: "text-side shifts leave accuracy largely unchanged". Both consistent with the source's "decreasing the gap does not change the clean accuracy" ✔.
* `wortsman2022` — both attribute weight-space interpolation preserving both behaviours ✔.
* `levi2025`, `mistretta2025`, `yamaguchi2025`, `sofer2025` — same roles in both ✔.

The *differences* between the two descriptions of shared work are bibliographic, not interpretive: A1 abbreviates author lists with "et al." (which is safe) where A2 spells them out and introduces non-authors (§3).

---

## 6. Citations used to support claims the source does not make — and uncited claims about sources

### 6.1 Usage that over-reaches the source

1. **`imod` cited for "gap reduction is an explicit design objective"** — `paper_a1/main.tex:32` groups `imod` with `mistretta2025, yamaguchi2025, sofer2025` under "methods explicitly optimize gap reduction", and `related_work.tex:47` does the same. The CVPR 2026 paper (verified, pp. 37745–37755) is about **modality-imbalanced parameter updates in PEFT for MLLMs** (splitting LoRA parameters into text-specific / non-text-specific / modality-sharing components); its "Modality-Agnostic Alignment Constraint" is a *parameter-space* objective. It does not optimise the centroid modality gap. The citation is real; the claim it is attached to is not what the paper does.
2. **`mistretta2025` cited for "gap reduction is an explicit design objective"** — same sentence in both manuscripts (`paper_a1/related_work.tex:47`; `paper_a2/main.tex:70`). Mistretta et al. use modality *inversion* to expose intra-modal misalignment; it is not primarily a gap-reduction method, unlike `sofer2025` ("Pull it together: reducing the modality gap") and `yamaguchi2025` (modality alignment).
3. **`radford2021` cited as evidence for the modality gap** — `paper_a1/main.tex:32` lists it among sources for "the image and text clusters are systematically separated". The phenomenon was identified by `liang2022`; the CLIP paper does not document a modality gap. Loose, not false.
4. **`chowers2026` "moving the text side"** — `paper_a1/main.tex:154` characterises the source as "prior work that translated the text side". The published abstract does not state which side was moved (it says post-processing "moves one modality towards the mean of the other"). The claim rests on the project's own full-text note (`docs/A1_literature_check.md:6`, quoting the paper's Figure 2 caption "moving the text embeddings by α·g⃗"); it could not be confirmed from the published record alone. Low risk, but the sentence is a claim about a specific source that the source's own abstract does not support on its face.

### 6.2 Claims about sources with no citation

The two manuscripts are, on the whole, unusually disciplined here — the sweeps for "a recent survey / studies have shown / it is known / the literature shows" found no unsupported attribution of a finding to an unnamed source. The residual cases:

* `paper_a1/main.tex:26` (abstract) — "narrowing it is an explicit objective in method design, and gap-based quantities predict retrieval degradation" carries no citation (normal in an abstract; the same claim is cited at line 32).
* `paper_a2/main.tex:85` — S3Simulator described as "**the reference for** synthetic sonar validation": an evaluative claim about a source, no citation, and not verifiable as stated.
* `paper_a2/main.tex:80` and `:93` — "OceanCLIP-0.15B fine-tunes a BioCLIP backbone on marine imagery and biological terminology" and "(BioCLIP ViT-B/16 backbone, 512-d embedding; marine fine-tune, 50 epochs)". These are precise factual claims about a model card that **could not be opened from this environment** (§7). They are the load-bearing description of the paper's central model and should be confirmed off-box.

### 6.3 Provenance claims inside the bibliography files

`related_work_bibitems.tex:37-43` asserts: *"PROVENANCE: every entry was checked against the publisher/venue record … before being written. Two entries are preprints with no confirmed peer-reviewed venue and are cited as arXiv only (luo2023empirical, zhai2023forgetting)."* Both halves of that statement are contradicted by this audit: six entries in the file are wrong in a stated field, and the two entries named as preprints have both been peer-reviewed and published (§2.2). The comment will be read by reviewers/editors who open the source; it should be corrected or removed.

`related_work_bibitems.tex:106-110` additionally carries "optional volume/page detail" comments, two of which could not be substantiated: `hendrycks2021imagenetr` "pp. 8320–8329" (CVF records 8340–8349 — the two paginations differ between CVF and IEEE, so this is unresolved rather than proven wrong) and `klabunde2025similarity` "art. 242" (Crossref/OpenAlex give pp. 1–52 and ACM DL was unreachable). Neither is in the printed bibliography; both should not be relied on.

---

## 7. Items I could not verify — exact queries tried

| # | Item | What I searched / fetched | What came back |
|---|---|---|---|
| 1 | `oceanclip2025` — HF model card `zjunlp/OceanCLIP-0.15B` (and the "OceanGPT-X collection" parent) | `https://huggingface.co/zjunlp/OceanCLIP-0.15B`; `https://huggingface.co/api/models/zjunlp/OceanCLIP-0.15B`; queries *"huggingface zjunlp OceanCLIP-0.15B marine vision-language model"*, *"zjunlp OceanCLIP 0.15B OceanGPT-X collection marine CLIP model"* | Fetch refused: hostname resolves to non-public address `108.160.167.159` (TCP 443 refused). Search index **does** show the page and the title "OceanCLIP-0.15B: Marine Vision-Language Model" plus commit pages (`08cfb73`, `bdfbcec`), and there is **no** 404 evidence → **not** SUSPECT, but unconfirmed. Needs an off-box check |
| 2 | `qwen2vl2024` — licence field "(CC-BY-4.0)" on HF | same HF block; search-index hit for the model page; a **ModelScope mirror of the identical model id** is tagged `apache-2.0` | Page exists; licence **not confirmable** here, and the mirror contradicts CC-BY-4.0. Treat as probable MISMATCH pending confirmation |
| 3 | `wanA1` — "A decoupled view of class-ordering and classification robustness under gap surgery" | queries *"A decoupled view of class-ordering and classification robustness"*, *"gap surgery class-ordering robustness CLIP decoupled view"* | Zero trace anywhere public. Expected for an unpublished manuscript — **not** a fabrication flag — but it is also **not** the title of the companion manuscript in this workspace (§5.1) |
| 4 | `wanP1` / `wan2026protect` — "Protect, don't perturb" | queries *"Protect, don't perturb cross-modal alignment PEFT vision-language"*, *"Protect, don't perturb arXiv"* | Zero public trace; normal for work under review. Status should be confirmed by the operator (§5.2) |
| 5 | `klabunde2025similarity` "art. 242" (comment only) | `dl.acm.org` (403 Cloudflare); Crossref and OpenAlex for DOI 10.1145/3728458 | Volume 57, issue 9, 2025 and the DOI confirmed; the article number could not be confirmed — Crossref/OpenAlex record pagination as pp. 1–52 |
| 6 | `hendrycks2021imagenetr` page range in the file's comment | CVF ICCV 2021 page vs the comment's "pp. 8320–8329" | CVF gives 8340–8349. CVF and IEEE paginations legitimately differ; which is right was not resolvable, and the printed entry states no pages — so this is a comment-only issue |

Not counted as unverifiable but worth recording: `pnas.org`, `cell.com`, `academic.oup.com`, `dl.acm.org`, `link.springer.com`, `idp.springer.com`, `sciencedirect.com`, `openreview.net`, `dblp.org` and `api.semanticscholar.org` were all unreachable from this machine. Entries resting on those publishers (e.g. `kirkpatrick2017ewc`, `french1999catastrophic`, `kendall1938`, `hu2025inferencecal`, `zhou2022coop`, `steck2024cosine`, `luo2023empirical`) were verified through the **publisher-deposited Crossref registration record** rather than the article landing page — authoritative for bibliographic fields, but one step less direct.

---

## 8. Verdict counts and the one-line defect list

### `paper_a1` — 56 entries

**49 VERIFIED · 6 MISMATCH · 1 UNVERIFIABLE · 0 SUSPECT**

* **MISMATCH** — `levi2025`: first author is **M. Y. Levi** (Meir Yossef Levi), not "D. Levi" (source: Technion CRIS + PMLR 267).
* **MISMATCH** — `chowers2026`: first author is **R. Chowers** (Rhea), not "I."; the paper has 4 authors (Chowers, Naparstek, Barzelay, Weiss), not 2 (source: CVF CVPR 2026 + arXiv:2603.29080).
* **MISMATCH** — `grassucci2026`: second author is **G. Cicchetti** (Giordano), not "L." (source: arXiv:2601.18525, `Comments: ICLR 2026`).
* **MISMATCH** — `luo2023empirical`: **not an arXiv-only preprint** — published in *IEEE Trans. Audio, Speech and Language Processing* 33:3776–3786, 2025, DOI 10.1109/TASLPRO.2025.3606231 (source: arXiv:2308.08747 + Crossref).
* **MISMATCH** — `zhai2023forgetting`: **not an arXiv-only preprint** — published at *CPAL 2024*, PMLR 234:202–227 (source: arXiv:2309.10313 + proceedings.mlr.press/v234/zhai24a).
* **MISMATCH** — `ding2021grounding`: middle author is **J.-S. Denain** (Jean-Stanislas Denain), not "J.-Y." (source: proceedings.neurips.cc 2021).
* **UNVERIFIABLE (expected)** — `wan2026protect`: the author's own under-review manuscript; no public record (queries in §7). Title matches `paper_a2`'s `wanP1` ✔.

### `paper_a2` — 28 entries

**13 VERIFIED · 11 MISMATCH · 4 UNVERIFIABLE · 0 SUSPECT**

* **MISMATCH** — `wanA1`: cited title **"A decoupled view of class-ordering and classification robustness under gap surgery"** is not the companion manuscript's title (it is "The Modality Gap Is Not a Universal Health Metric: Order Preservation Governs Zero-Shot Robustness", `paper_a1/main.tex:14`), and the entry's venue/status is out of date (PRLETTERS-D-26-01941 was rejected 2026-09-14).
* **MISMATCH** — `biderman2024`: venue is **TMLR 2024**, not NeurIPS (source: mlanthology TMLR record + OpenReview `aloEru2qCG`).
* **MISMATCH** — `oceangpt2023`: venue is **ACL 2024 Long Papers**, pp. 3357–3372, DOI 10.18653/v1/2024.acl-long.184 — not NeurIPS (source: ACL Anthology + arXiv `Comments: ACL2024`).
* **MISMATCH** — `sonarsurvey2025`: wrong title, **all 9 authors missing**, and it is a SIBGRAPI 2025 paper rather than an arXiv preprint (source: arxiv.org/abs/2510.03353 and its HTML record).
* **MISMATCH** — `mvaldenegro2024`: Heriot-Watt thesis year is **2019**, not 2024 (source: ros.hw.ac.uk hdl 10399/4035).
* **MISMATCH** — `grassucci2026`: **"Maiorca, M." is not an author**; second author is G. (Giordano) Cicchetti, not L. (source: arXiv:2601.18525 + github.com/ispamm/ModGap).
* **MISMATCH** — `yamaguchi2025`: **"Sotani, R." and "Shim, V." are not authors** (real list: Yamaguchi, Feng, Kanai, Adachi, Chijiwa) (source: CVF CVPR 2025).
* **MISMATCH** — `mistretta2025`: **"Deng, C." and "Ma, A." are not authors** (real list: Mistretta, Baldrati, Agnolucci, Bertini, Bagdanov) (source: ICLR 2025 proceedings).
* **MISMATCH** — `chowers2026`: first author is **R. Chowers** (not "I.") and the paper has 4 authors, not 2 (source: CVF CVPR 2026).
* **MISMATCH** — `levi2025`: first author is **M. Y. Levi**, not "D. Levi" (source: Technion CRIS + PMLR 267).
* **MISMATCH** — `s3simulator2024`: lead author is **S. Kamal Basha** (not "Kamal, B.") and the chapter has only **2** authors, so "et al." is wrong; it is an LNCS/ICPR 2024 chapter, pp. 219–235 (source: Crossref chapter record for 10.1007/978-3-031-78444-6_15).
* **MISMATCH (minor)** — `aquaticclip2026`: the 6-author list including **Werghi, N.** matches the arXiv preprint; the published TNNLS version has 5 authors and no Werghi (source: Crossref DOI 10.1109/TNNLS.2026.3657138 + arXiv:2502.01785).
* **UNVERIFIABLE** — `qwen2vl2024` (HF unreachable; licence likely Apache-2.0, not CC-BY-4.0).
* **UNVERIFIABLE** — `oceanclip2025` (HF unreachable; the paper's central model card).
* **UNVERIFIABLE (expected)** — `wanA1`, `wanP1` (author's own unpublished manuscripts).

### Overall

**62 VERIFIED · 17 MISMATCH · 5 UNVERIFIABLE · 0 SUSPECT** across 84 bibliography entries (73 distinct works).

**No entry in either manuscript is fabricated.** Every resolvable identifier resolved to a real, correctly-attributed publication. The defects are citation-accuracy errors, and they are heavily concentrated in `paper_a2`'s spelled-out author lists (four entries name people who are not authors of the cited work) and in two venue mis-statements (`biderman2024`, `oceangpt2023`) where a real paper is attributed to a conference that did not publish it — the class of error a desk editor is most likely to catch.
