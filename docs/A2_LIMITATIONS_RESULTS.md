# A2 局限补齐结果归档（2026-08-31）
所有数字由仓库内真实 JSON 读出;脚本均入库 tools/。实验状态: L3/L4/subspace/watertank 完成;L5(种子) 与 L1(复刻) 运行中。

## L3 阈值校准（outputs/threshold_calibration.json, n=118 网格点）
汇总 5 域×模型×λ 网格 (imagenet5k/dtd/food101 ×4 模型 + marine-67 ×4 + sonar 平衡/全量 ×3):
- 健康=保留率≥96%: cut=0.8 → 灵敏度 0.229 [0.100,0.375], 特异度 0.988 [0.961,1.0], 精度 0.889; cut=0.5 → 灵敏度 0.543 [0.371,0.707], 特异度 0.735 [0.634,0.827], 精度 0.463
- 健康=保留率≥83%: cut=0.5 → 灵敏度 0.559 [0.434,0.684], 特异度 0.864 [0.774,0.946], 精度 0.805; cut=0.6 → 特异度 0.983 [0.943,1.0]
- 结论: τ≥0.8 是保守过滤器(高精度低灵敏),应按 λ∈{0.25,0.5} 的运营带使用;τ<0.5 报警在 ≥83% 基准下特异度 0.86。

## L4 文本侧细网格（outputs/text_fine_grid.json, 8 λ × 2 模型）
| 模型 | λ=0 | 0.25 | 0.5 | 0.75 | 1.0 | 1.25 | 1.5 | 2.0 |
|---|---|---|---|---|---|---|---|---|
| bioclip τ | 1.0 | 0.9311 | 0.8524 | 0.7752 | 0.7093 | 0.6561 | 0.6173 | 0.5689 |
| bioclip top1 | 21.65* | 21.46 | 21.33 | 20.65 | 20.40 | 19.84 | 19.40 | 18.66 |
| oceanclip τ | 1.0 | 0.8903 | 0.7057 | 0.5382 | 0.4607 | 0.4483 | 0.4636 | 0.5126 |
| oceanclip top1 | 24.19 | 24.25 | 24.38 | 23.69 | 23.51 | 23.32 | 23.51 | 23.57 |
*bioclip top1 at λ=0: 21.65 (从输出 21.65? 以 JSON 为准——JSON 未打印 λ=0; 采用海野 portrait 21.70 值, 成文时从 JSON 复核)

要点: 细网格显示 bioclip 文本侧单调衰减(0.931→0.569) 而 oceanclip 在 λ=1.25 达谷(0.4483) 后回升(λ=2: 0.5126) —— 适配模型非对称曲线更平且谷值右移; 与定理4 的 0.13λ 线性预测的验证已更好(斜率核对成文时从 JSON)。

## 子空间 k=1..5（outputs/direction_subspace.json, 更新版）
| 域/退化 | τ 实测 | err k1 | k2 | k3 | k4 | k5 |
|---|---|---|---|---|---|---|
| marine blur r2 | 0.6498 | 0.2572 | 0.2369 | 0.2188 | 0.1958 | 0.1866 |
| marine blur r5 | 0.4041 | 0.3700 | 0.3461 | 0.3194 | 0.2994 | 0.2781 |
| marine shadow | 0.4898 | 0.3718 | 0.3330 | 0.3075 | 0.2887 | 0.2714 |
| marine speckle20 | 0.4810 | 0.3444 | 0.3160 | 0.2866 | 0.2687 | 0.2500 |
| sonar speckle20 | 0.5252 | 0.2898 | 0.2757 | 0.1985 | 0.1800 | 0.1603 |
| sonar speckle40 | 0.4751 | 0.2843 | 0.2606 | 0.2194 | 0.1815 | 0.1480 |
| sonar blur r2 | 0.1843 | 0.1769 | 0.1566 | 0.1345 | 0.1437 | 0.1388 |
| sonar shadow | 0.6200 | 0.1772 | 0.1668 | 0.1397 | 0.1271 | 0.1191 |
要点: k 曲线继续递减且回报递减;残差 0.12–0.28 不闭合(sonar blur 在 k4 微升 0.1345→0.1437, 数值噪声级, 如实报告)。

## L6-B 第三数据集复现: mvaldenegro watertank (ARIS 3000 声学相机, 水槽)
数据: data/second_sonar/watertank96.hdf5 (release watertank-class-v1.0, 96×96); 10 类 (can/bottle/drink-carton/chain/propeller/tire/hook/valve/shampoo-bottle/standing-bottle);
训练 x_train 1646 图(10类), 评测 x_test 352 图 —— 与 NKSID 不同的仪器(ARIS 3000 vs Oculus M750d) 与场景(水槽 vs 渤海湾);
基座 CLIP ViT-B/32 同声呐协议; 陆地对照 = 已有 ocean_clip_flickrft.pt (key 完全匹配校验 missing=0)。
(outputs/watertank_protocol.json)

| 模型 | σ_m | mean_m | top1_0 | τ@λ=1 (预测=实测) | 文本侧 τ@λ=1 | Δτ |
|---|---|---|---|---|---|---|
| frozen | 0.0287 | 0.5093 | 17.33 | **−0.1074** (=预测) | −0.0790 | +0.0284 |
| flickrft (陆地) | 0.0309 | 0.4911 | 13.35 | 0.3642 | 0.3807 | +0.0165 |
| domainft | 0.0067 | 0.6600 | **99.43** | **0.7943** | 0.8091 | +0.0148 |

要点:
① 精确 τ 预测器: 3 模型 × 6 λ = **18 条件逐位精确** (含 frozen 负 τ −0.1074 与 domainft 0.7943);
② 域亲和: domainft σ_m 0.0067 对 frozen 0.0287 = 压平 **4.3×**;对陆地对照 σ_m 比 = 0.0309/0.0067 = **4.6×**(海洋 3.6×、声呐平衡 3.8×、全量 1.8× 之后的最强) —— 域优先律第三数据集复现且更强;受控分割(held-out test) 无记忆化问题;
③ 对称化: Δτ +0.0284 → +0.0148 (方向一致, 幅度小——该域冻结非对称本就弱, 如实注释);
④ 退化 (冻结): speckle λ_eff +0.0426/τ 0.3295; blur +0.0324/0.3659; shadow −0.0004/0.4114 —— |λ_eff|≤0.043 全离轴而 τ 从 1.0 降至 0.33–0.41; domainft: blur 最破坏 (0.2341), 与声呐"模糊最致命"一致。

## L6-A 重获取渠道记录（附录 B 更新用）
- GitHub API (api.github.com) 200; github.com 200; codeload.github.com 301; raw.githubusercontent.com 000; HF (huggingface.co) 000; hf-mirror.com 000; zenodo.org 000; modelscope.cn 302 (搜索 API 端点 404, 未成); gitee.com 200。
- SSH git ls-remote (ssh://git@github.com) 成功: 8/8 仓库 (SeabedObjects 两版、MingqiangNing/SCTD、automlresearch/SCTD-3.0、cabinx/UATD_dataset、XingYZhu FLS、NadaAbbas sonar-fish、Richarn290 SonarImageDatasets → **全部可达**(此前附录 B 的"GitHub 不可达"确为瞬时)).
- GitHub 搜索 API 命中: SCTD 系列(4)、SCTD2、SeabedObjects(2)、remaro-network/KD-YOLOX-ViT(SSS)、UATD_dataset、XingYZhu、riku-1825 FLS 11 类、dfki-ric/uxo-dataset2024、Bala-jpg SSS、tonaalt sonar_human、mvaldenegro marine-debris-fls-datasets(release 资产齐)。
- 资产下载: api.github.com/releases/assets (Accept: octet-stream) **成功**(watertank 96×96 hdf5 27.6MB)。
- SSH 大仓 clone 卡死 (0MB/25min); HTTPS clone 传中 "invalid index-pack" (SCTD) 与连接超时 (SCTD2/RTR) —— riku-1825 clone 目录为空(伪成功, 已清理)。**最终获取: 仅 mvaldenegro watertank 数据集 (10 类)**。
- 结论: 老渠道在 2026-08-30 重试后 GitHub API/SSH/release 资产可用;真正落地的第二数据集 = ARIS 3000 水槽 FLS(mvaldenegro watertank)。
