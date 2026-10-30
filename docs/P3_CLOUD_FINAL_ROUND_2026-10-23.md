# P3 云端最终轮（2026-10-23）— 待实例开机

## 目标
一次跑完 revision 之外的剩余云端项，取回结果后按规则关机：

| 块 | 内容 | 预计 |
|---|---|---|
| C1 | r=3 / r=8 各 10 seeds（夹紧 crossing） | ~11 min |
| D3 | 真实图像 caption protocol 补 seed 123/789 × r5/r6 | ~8 min |
| D4 | Dolly-15k 指令数据族（r=4–7 × seed 42/123） | ~5 min + 下载 |
| A2 | VQA-RAD **1793** 训练对 per-step，r5/r6 + base eval 300 | ~1.5–2 h |
| D1 | LLaVA-OneVision-0.5B 第三族（best effort，1 h 超时） | ≤1 h |

## 操作步骤（实例开机、端口确认后）

1. 验证环境：`nvidia-smi`、`/root/miniconda3/bin/python -c "import torch"`；
2. 检查数据盘恢复：`/root/autodl-tmp/p3work`、`models/llava-hf` 软链、`data/marine_captions`、`data/vqa_rad/data/*.parquet`、`paper3/train-*.parquet`；
3. 上传最新文件（覆盖）：
   - `paper3/scripts/run_training.py`
   - `tools/_p1516_p3_vqa_downstream.py` → `tools/vqa_downstream.py`
   - `tools/_p1499_p3_hessian_probe.py` → `tools/hessian_probe.py`
   - `cloud_p3/prep_dolly.py` → `tools/prep_dolly.py`
   - `cloud_p3/loo_run.py` → `tools/loo_run.py`
   - `cloud_p3/run_final_all.sh` → 根目录
4. 启动：`nohup bash run_final_all.sh > final_all.log 2>&1 &`；
5. 轮询 `final_all.log`，确认 `ALL DONE`；
6. 打包取回 `paper3/scripts/outputs/experiments/verify_r3*_s*.json`、`verify_r8*_s*.json`、`*imgs_cap*`、`*dolly*`、`outputs/analysis/p3_vqa_downstream_*.json`、`p3_loo_family.json` 与日志；
7. 本地校验后 **`sync && shutdown -h now`**，端口探测确认不可达，再记录 HANDOFF。

## 结果整合
- C1：S33 十 seed 表扩展 r=3/r=8，重算 crossing 置换检验；
- D3：S35 真实图像 sweep 加多 seed 区间；
- D4：新增数据族小节（instruction 族扩展，r 扫描）；
- A2：S28 用 1793 满量与 eval 300 覆盖；
- D1：若成功，新增第三 VLM 族小节；若失败，HANDOFF 记原因（架构/显存）。
