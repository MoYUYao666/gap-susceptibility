# A2 数据集审核(2026-08-31 更新)
所有条目经本地统计/API 核实;许可按仓库 LICENSE 或发布页声明。

## 一、论文已用数据集(审计结论)

| 数据集 | 实际内容(本地核实) | 许可 | 谱系/备注 | 状态 |
|---|---|---|---|---|
| rare-species (fish-67) | 11,983 行;鱼类 2,009 行;子集 67 类×24 图=1,608 | CC0(EOL) | BioCLIP 基准;每类恰 24(封顶) | ✅(已披露修正) |
| rare-species (fauna-117) | 117 类 2,808 图 | CC0 | 同源扩展 | ✅ |
| iNat-48 | 48 类×12 图=576(池 720/49 目录;1 种 0 图、1 种 2 图被过滤) | CC(观察) | iNaturalist research-grade | ✅(已披露过滤注) |
| MarineLife-16K | 427 视频组/3,416 帧/3,440 QA(卡声称 2,000/16,080) | CC-BY-4.0 | 发布子集;QA 按卡片为人工 | ✅(差异已披露) |
| NKSID | 2,617 图 8 类(逐类一致:203/288/20/951/112/94/115/834) | MIT | Oculus M750d,渤海湾,天然长尾 | ✅ |
| imagenet-1k (5k) | 5,000 张(14 parquet) | — | 标准验证集子集(seed 42) | ✅ |
| DTD | 47 类×120=5,640 | MIT | 标准 | ✅ |
| food101 | 101 类×1,000=101,000 | MIT | 标准 | ✅ |
| Flickr30k | 31,783 条(取 1,000 对) | — | 标准 | ✅ |
| BLIP 字幕 | 536 对(仅§任务谱系辅助) | 生成 | 已披露 | ✅ |
| **watertank (mvaldenegro)** | 11 类(10 类+background);训 1,646/测 352(96×96 单通道) | 发布页学术用途(release) | ARIS 3000 水槽 | ✅(已披露 background+单通道) |

## 二、新获取数据集(2026-08-31,VPN 后/手动)

| 数据集 | 内容(已核实) | 许可 | 谱系 | 用途 |
|---|---|---|---|---|
| **UATD** (figshare 21331143, 手动下载 4.5GB) | **9,200 图 + 9,200 xml**(Training 7,600 / Test_1 800 / Test_2 800);**.bmp 1024 级分辨率**(1024×1026 等,3 通道);**10 类**: ball 3072 / cube 2647 / human body 1285 / tyre 1125 / square cage 982 / plane 795 / rov 700 / circle cage 661 / cylinder 564 / metal bucket 476(实例数,训+测池);**多类图 44.8%**(取实例最多类为图像级标签,需披露);xml 含声呐参数(range/azimuth/elevation/frequency=1200k) | 论文(Scientific Data 2022, 注明 CC 类惯例;发布页未附 LICENSE 文件→**引用时注明按论文条款**) | **多波束 FLS 田野数据**(不同仪器/数据集发布,与 NKSID 独立) | **第二野外场点**(最强) |
| **riku-1825** (jsDelivr 补全 335MB) | 2,035 图 + 2,035 标注;**11 类 YOLO**(mine 157/295…;test 206)、**全分辨率**(438×658 1109/500×605 759/416×416 167);train 1627/val 202/test 206 | MIT | Roboflow 导出;文件名揭示 **ARIS3k debris(与 watertank 同传感器族、全分辨率原图)+ sonar7 mine**(mine 为独立来源) | **增量**: ①全分辨率 vs 96×96 不变性;②mine 类扩展 |
| uxo-dataset2024 (-main.zip, 12.5MB) | **仅代码+6 张媒体图**;数据在 Zenodo(不可达) | 无声明 | dfki-ric | **缺数据** |
| FathomNet (API key 已获) | API v1/v2 全部 404/301(官网已 Wix 化) | — | **API 服务不可用**;key 记录备用 | 暂不可得 |

## 三、论文陈述建议(落笔时)
1. **声学数据从"3 套"升级为"4 套"**:NKSID(双口径)+ watertank(ARIS 3000 水槽)+ UATD(田野多波束,10 类)+ riku(ARIS3k 全分辨率+sonar7 mine,11 类)。§5.9 表扩展:watertank/riku/UATD 三行 + 原声呐行。
2. **UATD 披露要点**:图像级标签=实例最多类(44.8% 多类图);类名含合成摆放目标(ball/cube/cage 等——人工布设水下目标,非自然类群;这其实是**亮点**:证明方形成类群——与生物类群互补),写作措辞"人工布设的目标与残骸(球、立方体、笼、轮胎、人形、ROV、金属桶等)类集"。
3. **riku 披露要点**:Roboflow 导出(来源同名 mvaldenegro ARIS3k 相机数据 + sonar7 mine 集);作为增量使用: 全分辨率不变性与类集扩展,非独立新域。
4. FathomNet 与 uxo 的记录:附录 B 追加(正确主机 database.fathomnet.org 已证实可用;Zenodo 不可达、key 已备案)。

## 四、ARACATI2017(2026-09-01 获取,第三野外场点候选)
- 6,370 文件/202.6MB(jsDelivr 逐文件,6103 成功,267 个 validation/gt 限速失败);train input 2464 + gt 2524;validation input 289 + gt 273;test input 289 + gt 261(真实 FLS,意大利 ARACATI 2017 比赛,Translation 任务:声呐→光学转换)。
- **形态判定:gt 为实例掩码(灰度=实例 ID,0–14+,无命名类别)→ 与类集协议(需语义类文本)不匹配;未用于论文协议**;作为"第三野外场点"的野外图像池留存。
- **已穷尽的场点渠道**:Zenodo 000(不可达)、figshare API 403(需手动浏览器,UATD 已证明可行)、其余仓库数据外链或同源(riku 第二仓库=同源 2035 图)。**第三野外场点建议手动路径**:浏览器打开 figshare 搜索 side-scan sonar / sonar dataset,或 Zenodo(达时)下载 dfki-ric/uxo-dataset2024 数据。

## 五、MILCO/NOMBO 数据集(2026-09-01 手动 figshare 24574879,585MB)
- **figshare 记录 24574879 = 历年海底目标分类集(2010/2015/2017/2018/2021 + Training)**:1,170 图(345/120/93/564/48)+ YOLOv4 训练包(obj.names.txt = **MILCO / NOMBO** 两类:水雷样/非水雷样底物目标;yolov4-custom_5000.weights 为随附模型)。
- **形态判定:仅二分类(MILCO/NOMBO)→ 不满足类集协议(需 ≥5 类语义类集)**,无法用于 τ/σ_m 类集实验;已解压存档 `data/aracati_full/expanded/`(图像+YOLO 标注)作为检测/像素级资源留存。
- **Zenodo 11068046(94.7GB)**:用户已核对——量级远超磁盘(91GB 可用)与实验需求,决定不下载;若需 dfki-ric/uxo-dataset2024 的标注子集,可只取图像部分(需浏览器查看文件列表)。
- **现状**:第三野外场点在公域已核查到:①ARACATI-Translation(实例掩码,无类名)②MILCO/NOMBO(仅 2 类)③SCTD(无许可)④UXO(Zenodo 94.7GB 或需子集)— **均不能直接补足 τ 类集协议;协议数据实际上已由 NKSID+UATD 两个野外场点 + watertank/riku 两套补充覆盖**。

## 六、figshare 29290638(2026-09-01 手动下载,1.5GB——侧扫候选)
- 标题 "Efficient processing of side-scan sonar images and fast detection of sparse targets in large-scale images";zip 内容 = **12 幅 7680×4320 RGBA TIF(figuers_01–12)**+ **无任何标注文件(0 个)**;抽查第 1 幅 = 论文**处理流程图**(Raw SSS Data Flow → … → Refined SSS Image)。
- **判定:论文插图包,非数据集**——无法用于类集协议;已记录以终结"侧扫公开多类数据集"检索:侧扫领域公开集(SeabedObjects-KLSG 2 类 / KLSG-II 3 类·外链 / KD-YOLOX-ViT 二分类·外链 / Bala-jpg 外链)均 ≤3 类或外链。
- **结论:侧扫(SSS)多类集在公域不可得;论文以 NKSID(FLS)+UATD(FLS 不同仪器)+watertank/riku(补充)作协议证据,侧扫复现保留为 future work(如实)**。

## §七（2026-09-03 手动获取复核）
- 桌面压缩包 1: CTX_UXO_DS_v2_2025.zip（3.7GB, 10,587 条目）——12 类 UXO（AntiSubmarine Bomb / Aviation Bomb / Cartridge / Cartridge Magazine / Fuse / Grenade / LandMine / Mortar Bomb / Projectile / RPG / Rocket / Sea Mine），3,520 张 jpg（train 2,461 / valid 530 / test 529），标注=COCO（train 11,146 实例）+ YOLO bbox + YOLO segmentation，data.yaml nc=12。**检查结论：纯光学**（UXOs_1 地面锈蚀弹丸 640×480；UXOs_142 'Sea Mine' 为海滩光学照 720×1600；随机样本为仓库/地面相机照，最大 4640×3472）；无公开版室内声呐/侧扫子集 → 不是 SSS 多类集；许可：压缩包内无 LICENSE（源= Zenodo/figshare 'An Acoustic and Optical Dataset for the Perception of Underwater UXO'，IEEE 2024 论文记录；Zenodo 本机不可达，许可未核验）→ 按 SCTD 标准（无许可不用）不入论文正文，仅审计留痕。
- 桌面压缩包 2: 24574879.zip（585MB）——figshare article 24574879 = MILCO/NOMBO 二分类（2010/2015/2017/2018/2021/Training.zip 六个子包）→ 仍是二分类，非多类。
- 结论：(d) 侧扫多类集仍空缺；若需继续：Zenodo record 11068046 的完整记录标题即 'Acoustic AND Optical'，3.7GB 是光学子集，声呐部分应为该记录的另一文件（记录原 94.7GB → 用户可浏览器进 Zenodo 该记录 Files 列表另下载声呐/水声部分）。

## §八（2026-09-03 晚 续）——DFKI ARIS 3000 UXO 声呐集获取尝试（Zenodo 13778485, BSD-3）
- 记录“An Acoustic and Optical Dataset for the Perception of Underwater UXO”(OCEANS 2024, Dahn 等; ARIS 3000 + GoPro, ~100 轨迹, 74,000+ 帧, 3 类 UXO, 极坐标声呐帧+标注)。
- **sample.7z 已获取并验证(1.65GB)**: 5 条 100lbs_bomb 轨迹, 每帧 aris_polar/*.png + labels/*.json, 标注 = {class: 100lbs_aircraft_bomb, bbox} —— 多类声呐集设计坐实(类=目录名/标注 class 字段)。
- **data_export_recordings.7z(16,658,054,765 B) 2026-09-03 晚手动续传至 77%(12,233 MiB) 后按操作者要求停止**; 过程中遇 Zenodo 大 Range 504/限速(64MiB 分块可稳定 206)。部分文件保留于 data/ctx_uxo/recordings.7z(可续传; 续传脚本 tools/clip_uxo_download_robust.py; 7z 头在文件尾部, 未完成前不可解压)。
- 结论不变: (d) 仍为数据可得性事项(论文表述不改); 若未来续传完成, 用 tools/clip_uxo_aris_protocol.py 可直接复现(冻结精确性/σ_m/退化图/10ep 匹配微调)。

## §九（2026-09-04 停止 + 数据集清理）
- **(d) 终止**: ARIS UXO 声呐集 (Zenodo 13778485) 手动续传至 77% 后按操作者要求停止; data/ctx_uxo 全部删除(部分文件+sample, ~15.3GB)。若日后续跑: 记录页 https://zenodo.org/records/13778485 (data_export_recordings.7z, 16,658,054,765 B) + 协议脚本 tools/clip_uxo_aris_protocol.py + 稳健续传脚本 tools/clip_uxo_download_robust.py (64MiB 分块, 仅 206 写入)。
- **删除清单** (共释放约 40GB): ctx_uxo(15.3) / inat2021-val(9.7, HANDOFF 已标冗余) / imagenet_hf(6.2, A1 核验分片, 数字已归档 outputs/imagenet1k_zs_50k_*.json; 重下: HF ILSVRC/imagenet-1k validation 4 分片, 需 hf login) / sss_figs(1.5, figshare 29290638 图件包, 非数据集) / aracati_full+aracati2017(1.4, 实例掩码集, 未用于论文) / food-101.tar.gz(4.8, 解压目录保留) / cifar-100(0.33, 审计排除) / tiny-imagenet-200.zip(0.07, 审计排除; tiny_wnids*.json 保留) / marinegpt(0.02, 未用) / second_sonar/SCTD* (0.36, 未授权未用, 保留审计记录)。
- **保留清单** (论文数字依赖): second_sonar/{UATD(36.4GB), riku1825, watertank96.hdf5} / rare-species / fathomnet8 / marinelife16k / food-101(已解压) / dtd / marine_captions / inat_wild / NKSID / imagenet_1k_names.json。
- 数据目录现状: 9 个目录共 ~49.6GB; D 盘空闲 146.9GB。
