# -*- coding: utf-8 -*-
r"""**统一串行执行器**：解决三个驱动争抢 GPU 的架构缺陷（2026-10-08 02:45）。

## 昨夜暴露的三个缺陷（全部实测）

| # | 缺陷 | 后果 |
|---|---|---|
| 1 | **三个驱动各自"等信号"**（各看不同的文件/超时） | **必然撞车**：队列 2 在 ③b 未完成时启动 α 重跑 → **8 GB 显存被两实验争抢** |
| 2 | **硬超时不杀子进程** | ③b 超时后其子进程**继续训练**，孤儿占 GPU |
| 3 | **`subprocess.run(timeout=)` 捕获 stdout 不落盘** | α 重跑跑到哪一步**无从得知** |

## 本执行器怎么修

| 设计 | 做法 |
|---|---|
| **单写者** | **一个**执行器按序跑全部任务；任务间**不并行**（GPU 只有 8 GB） |
| **超时即杀** | `Popen` + `start_new_session`（新进程组）→ 超时 `killpg` **杀整组**（含 spawn 的子进程） |
| **实时日志** | stdout/stderr **逐行追加写文件**（不捕获到内存），可随时 `tail` |
| **GPU 互斥** | 启动每个任务前**检查显存**（`nvidia-smi`）→ 若已被占则等待（除非是同一任务的重启） |
| **可续跑** | 已有 `results.json`/结果 JSON 的任务**跳过** |

## 任务队列（按优先级）

1. **α 重跑**（`--maxsamples 5000`）—— 已在跑，本执行器接手后续
2. **③b 剩余两臂**（CLIP B/16 `both`、`vision_only`）
3. **COCO 补跑 12 配置 × 3 seed**（严格冻结）
4. **④ Qwen2-VL**（脚本就绪后）

    python tools\_p20_serial_executor.py --list
    python tools\_p20_serial_executor.py --apply
"""
from __future__ import annotations

import io
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
LOG = REPO / "outputs" / "_serial_executor.log"
GPU_WAIT_MAX = 8 * 3600   # 等 GPU 空闲的上限（等 GPU 是正常等待，不是失败）
LOCK = REPO / "outputs" / "_gpu.lock"


def log(msg: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def gpu_used_mb() -> int:
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=20)
        return int((r.stdout or "0").strip().splitlines()[0])
    except Exception:
        return 0




def running_pids(pattern: str) -> list[int]:
    """按**命令行内容**找正在跑的 python 进程（不按 CPU/启动时间筛）。"""
    ps = ("[Console]::OutputEncoding = [Text.Encoding]::UTF8; "
          "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
          "ForEach-Object { \"$($_.ProcessId)|$($_.CommandLine)\" }")
    try:
        # **必须显式 encoding**：Windows 默认 GBK，遇中文路径会 UnicodeDecodeError
        # （实测：该异常会让本函数返回空列表，使"已有同任务在跑"检测静默失效）
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
    except Exception:
        return []
    out = []
    for ln in (r.stdout or "").splitlines():
        if "|" not in ln:
            continue
        pid, cl = ln.split("|", 1)
        if pattern in cl:
            try:
                out.append(int(pid.strip()))
            except ValueError:
                pass
    return out


def task_done(done: Path) -> tuple[bool, str]:
    """**唯一的"已完成"判据**（供 run_task 与 --list 共用）。

    为什么不能只看"文件存在"：α 的首跑结果文件在**重跑开始前**就已存在，
    只看存在性会把"未跑"误判为"已完成"，**静默丢数据**。
    （本项目同类教训：下载脚本的"目录非空即跳过"连败两次。）

    返回 (是否完成, 理由)。
    """
    if not (done.exists() and done.stat().st_size > 0):
        return False, "文件不存在"
    # 实验 A 的判据：**必须 aligned 且真跑完**——该脚本未对齐时也会写文件
    # （内容 `"aligned": false`），只看存在会把 100 样本的诊断运行当成完成（实测踩过）。
    if done.name == "alpha_trainer_based.json":
        try:
            d = json.loads(io.open(done, encoding="utf-8").read())
        except Exception as e:
            return False, f"读结果失败（{e}）"
        if not d.get("aligned"):
            return False, "未对齐（诊断运行残留）"
        if "passed" not in d:
            return False, "缺 passed 字段（未真正跑完）"
        return True, f"aligned={d.get('aligned')} passed={d.get('passed')}"
    if done.name == "alpha_from_gradients.json":
        bak = done.with_name("alpha_from_gradients_maxsamp2000.json")
        if bak.exists():
            try:
                d = json.loads(io.open(done, encoding="utf-8").read())
                newer = done.stat().st_mtime > bak.stat().st_mtime
                if not (newer and d.get("max_samples") == 5000 and len(d.get("records", [])) >= 2):
                    return False, (f"仍是首跑（max_samples={d.get('max_samples')}, "
                                   f"晚于备份={newer}）")
            except Exception as e:
                return False, f"读结果失败（{e}）"
    return True, "合格"

def task_alpha() -> tuple[list[str], Path]:
    out = REPO / "outputs/theory/alpha_from_gradients/alpha_from_gradients.json"
    return ([PY, "tools/_p2_alpha_from_gradients.py", "--apply",
             "--arms", "both", "--seeds", "42,123", "--epochs", "10", "--maxsamples", "5000"],
            out)


def task_b16_both() -> tuple[list[str], Path]:
    out = REPO / "outputs/strict_freeze_b16/r4/both/seed42/results.json"
    return ([PY, "experiments/strict_freeze_control.py",
             "--model", "models/clip-vit-base-patch16",
             "--out-dir", "outputs/strict_freeze_b16/r4", "--name", "b16_r4_",
             "--rank", "4", "--alpha-mult", "2", "--tags", "both",
             "--seeds", "42", "--epochs", "10", "--max-samples", "5000",
             "--batch-size", "128", "--skip-frozen"], out)


def task_b16_vision() -> tuple[list[str], Path]:
    out = REPO / "outputs/strict_freeze_b16/r4/vision_only/seed42/results.json"
    return ([PY, "experiments/strict_freeze_control.py",
             "--model", "models/clip-vit-base-patch16",
             "--out-dir", "outputs/strict_freeze_b16/r4", "--name", "b16_r4_",
             "--rank", "4", "--alpha-mult", "2", "--tags", "vision_only",
             "--seeds", "42", "--epochs", "10", "--max-samples", "5000",
             "--batch-size", "128", "--skip-frozen"], out)


def task_coco(site: str, rk: int) -> tuple[list[str], Path]:
    out = REPO / f"outputs/coco_sweep/r{rk}/{site}/seed42/results.json"
    return ([PY, "experiments/strict_freeze_control.py",
             "--dataset", "coco", "--data-dir", ".",
             "--out-dir", f"outputs/coco_sweep/r{rk}", "--name", f"coco_{site}_r{rk}_",
             "--rank", str(rk), "--alpha-mult", "2", "--tags", site,
             "--seeds", *"42 123 456".split(), "--epochs", "10", "--max-samples", "5000",
             "--batch-size", "128", "--skip-frozen"], out)


def build_queue() -> list[tuple[str, list[str], Path, int]]:
    """(名称, 命令, 完成标志文件, 超时秒数)"""
    q = [("α重跑(5000样本)", *task_alpha(), 4 * 3600)]
    q.append(("③b both", *task_b16_both(), 3 * 3600))
    q.append(("③b vision_only", *task_b16_vision(), 3 * 3600))
    # **同秩对照**：论文 patch-32 组是 rank 8，而新增的 CLIP B/16 是 rank 4
    # → 必须补 CLIP B/32 @ rank 4，否则"排序由 patch size 决定"无法与"由预训练目标决定"区分。
    for site in ("both", "text_only", "vision_only"):
        out = REPO / f"outputs/strict_freeze_b32_r4/{site}/seed42/results.json"
        q.append((f"同秩对照 CLIP B/32 r4 {site}",
                  [PY, "experiments/strict_freeze_control.py",
                   "--model", "models/clip-vit-base-patch32",
                   "--out-dir", "outputs/strict_freeze_b32_r4", "--name", f"b32_r4_{site}_",
                   "--rank", "4", "--alpha-mult", "2", "--tags", site,
                   "--seeds", "42", "--epochs", "10", "--max-samples", "5000",
                   "--batch-size", "128", "--skip-frozen"], out, 3 * 3600))

    # **B：统一口径重跑**（操作者选 B）——记录的 DG* 是论文 ODE 的状态变量，
    # 而此前 COCO 补跑只记了 centroid_gap/distribution_gap。
    # 写入**新目录**：① 保留现有 36 run 作对照；② 避免跳过逻辑按旧 results.json 误判。
    for site in ("both", "text_only"):
        for rk in (4, 16, 64, 1, 2, 32):
            out = REPO / f"outputs/coco_sweep_dgstar/r{rk}/{site}/seed42/results.json"
            q.append((f"COCO-DG* {site} r={rk}",
                      [PY, "experiments/strict_freeze_control.py",
                       "--dataset", "coco", "--data-dir", ".", "--dg-star",
                       "--out-dir", f"outputs/coco_sweep_dgstar/r{rk}",
                       "--name", f"cocodg_{site}_r{rk}_", "--rank", str(rk), "--alpha-mult", "2",
                       "--tags", site, "--seeds", *"42 123 456".split(),
                       "--epochs", "10", "--max-samples", "5000",
                       "--batch-size", "128", "--skip-frozen"], out, 3 * 3600))

    # **实验 A** 排在 COCO-DG* 之后：A 需先修学习率（四次未对齐），
    # 而 COCO-DG* 是操作者选定的口径统一任务，应优先拿到确定产出。
    a_out = REPO / "outputs/theory/alpha_trainer_based/alpha_trainer_based.json"
    q.append(("A: α 由梯度预测(trainer基座)",
              [PY, "tools/_p21_alpha_trainer_based.py", "--apply",
               "--seeds", "42", "--epochs", "10", "--rank", "8", "--maxsamples", "5000"],
              a_out, 4 * 3600))

    # 旧口径 COCO 任务（写 outputs/coco_sweep/，**无 dg_star**）已由上方 COCO-DG* 取代。
    # 已完成的 31/36 产物**保留在盘上作对照**，但不再排队（对论文的表无用）。
    return q


def run_task(name: str, cmd: list[str], done: Path, timeout: int, logdir: Path) -> str:
    """跑一个任务：实时落盘、超时杀进程组、返回状态。"""
    finished, why = task_done(done)
    if finished:
        log(f"⏭ {name} 已完成（{why}）→ 跳过")
        return "skipped"
    if done.exists():
        log(f"   {name}: 输出存在但{why} → **需重跑**")

    # **已有同任务在跑**（例如旧的驱动启动的 α 重跑）→ 不重复启动，等它结束。
    # 判据用命令行里出现的**首个 python 脚本名**，避免误匹配。
    marker = next((a for a in cmd if a.endswith(".py")), "")
    if marker:
        pids = running_pids(marker.replace("\\", "/"))
        if pids:
            log(f"⏳ {name}: 已有同任务在跑（PID {pids}）→ 等它结束，不重复启动")
            t0 = time.time()
            while running_pids(marker.replace("\\", "/")):
                if time.time() - t0 > timeout:
                    log(f"⚠ {name}: 等已有任务超时（{timeout//3600} h）")
                    return "waited_timeout"
                time.sleep(60)
            log(f"✅ {name}: 已有任务已结束 → 复查完成判据")
            fin2, why2 = task_done(done)
            if fin2:
                log(f"⏭ {name} 现已完成（{why2}）→ 跳过")
                return "skipped"
            log(f"   {name}: 已有任务结束但{why2} → 本执行器启动")
    # **等 GPU 空闲**（轮询）。注意：等 GPU 是正常等待，**不是失败**——
    # 若此处"跳过任务"，执行器会在启动时把首个任务永久丢弃（静默丢数据）。
    t_wait = time.time()
    waited = False
    while gpu_used_mb() > 2000:
        if not waited:
            log(f"⏳ {name}: GPU 已被占 {gpu_used_mb()} MB → 轮询等待（不跳过）")
            waited = True
        if time.time() - t_wait > GPU_WAIT_MAX:
            log(f"⚠ {name}: 等 GPU 超时（{GPU_WAIT_MAX//3600} h）→ 本轮放弃")
            return "gpu_timeout"
        time.sleep(60)
    if waited:
        log(f"✅ {name}: GPU 已空闲 → 开跑")
    # **文件名净化**：任务名可能含 Windows 非法字符（实测 `:` 直接抛 FileNotFoundError，
    # 且异常逃出 main() 的循环会把整个队列带走）。只保留安全字符 + CJK，限长 80。
    import re as _re
    safe = _re.sub(r"[^0-9A-Za-z._\-\u4e00-\u9fff]+", "_", name).strip("_")[:80] or "task"
    tlog = logdir / (safe + ".log")
    log(f"▶ {name}  日志 {tlog.name}")
    with io.open(tlog, "a", encoding="utf-8") as f:
        f.write(f"\n=== {name} @ {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        f.write(" ".join(cmd) + "\n")
        f.flush()
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=str(REPO),
                             start_new_session=True)
        t0 = time.time()
        while p.poll() is None:
            if time.time() - t0 > timeout:
                log(f"⚠ {name} 超时（{timeout//3600} h）→ **杀进程组**")
                try:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                    time.sleep(10)
                    os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                except Exception as e:
                    log(f"   杀进程组失败: {e}")
                return "timeout"
            time.sleep(30)
        rc = p.returncode
    log(f"{'✅' if rc == 0 else '❌'} {name} rc={rc} 用时 {int(time.time()-t0)//60} min")
    return "ok" if rc == 0 else "fail"


def main() -> int:
    argv = sys.argv
    if "--list" in argv or "--apply" not in argv:
        q = build_queue()
        print(f"=== 串行队列（{len(q)} 项）===")
        for i, (n, c, d, t) in enumerate(q, 1):
            fin, why = task_done(d)
            mark = "✅ 已完成" if fin else f"⏳ 待跑（{why}）"
            print(f"  {i:>2}. {n:<24} {mark}")
        print(f"\n  日志: {LOG} ｜ 单任务日志目录: outputs/_serial_logs/")
        return 0

    logdir = REPO / "outputs" / "_serial_logs"
    logdir.mkdir(parents=True, exist_ok=True)
    log("=" * 72)
    log("串行执行器启动")
    if gpu_used_mb() > 2000:
        log(f"⚠ 启动时 GPU 已被占 {gpu_used_mb()} MB —— 可能有别的训练在跑；本执行器会等待")
    stats = {}
    for name, cmd, done, timeout in build_queue():
        # **任何单任务异常都不得杀死队列**（实测：一个非法日志文件名曾让整个 36 h 队列停摆）
        try:
            st = run_task(name, cmd, done, timeout, logdir)
        except Exception as e:
            st = "crashed"
            log(f"❌ {name} 抛异常（已捕获，队列继续）: {type(e).__name__}: {str(e)[:160]}")
        stats[name] = st
        if st == "blocked":
            log("   因 GPU 被占而停止本轮（避免争抢）")
            break
    log("汇总: " + json.dumps(stats, ensure_ascii=False))
    log("串行执行器结束")
    log("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
