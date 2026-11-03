# -*- coding: utf-8 -*-
r"""校验新快照，**通过后才**删除旧快照。校验失败则拒绝删除。

## 校验四步（缺一不可）

1. **SHA256 一致**：`.sha256` 文件记录的摘要 == 重新计算的摘要
2. **条目数一致**：zip 实际条目数 == manifest 行数 == manifest 头部 `files=`
3. **zip 完整性**：`zipfile.testzip()` 返回 None（无损坏条目）
4. **关键内容抽查**：`HANDOFF.md`、`.git/`、`outputs/`、`paper_review_prl/` 均在内

## 删除安全规则

- **旧 zip 只有在第 1–4 步全部通过后才删除**；任何一步失败 → **不删，并打印原因**
- 删除前**打印待删文件的绝对路径与体积**，供人工确认目标正确
- 旧 zip 的 `.sha256` / `.manifest.txt` 已在 `tools/obsolete/_backups_legacy_20260924/` 留档

    python tools/_verify_and_cleanup_backups.py                # 只校验
    python tools/_verify_and_cleanup_backups.py --delete-old   # 校验通过后删旧快照
"""
from __future__ import annotations

import hashlib
import io
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BAK = REPO / "backups"

NEW = "snapshot_FULL_20260930.zip"
OLD = "snapshot_FULL_20260924.zip"

# 关键内容抽查：zip 内应出现这些路径前缀
PROBES = ["HANDOFF.md", ".git/", "outputs/", "paper_review_prl/", "tools/", "docs/",
          "paper3/", "文件地图.md"]


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    delete_old = "--delete-old" in sys.argv
    zp = BAK / NEW
    if not zp.exists():
        print(f"❌ 新快照不存在：{zp}")
        return 1

    problems: list[str] = []

    # 1) SHA256
    print("1) SHA256 校验")
    side = BAK / (NEW + ".sha256")
    if not side.exists():
        problems.append("缺少 .sha256 文件")
        print("   ❌ 缺少 .sha256 文件")
    else:
        recorded = side.read_text(encoding="utf-8").split()[0]
        actual = sha256_of(zp)
        ok = recorded == actual
        print(f"   记录: {recorded[:32]}…")
        print(f"   实测: {actual[:32]}…  {'✅ 一致' if ok else '❌ 不一致'}")
        if not ok:
            problems.append("SHA256 不一致")

    # 2) 条目数
    print("2) 条目数一致性")
    man = BAK / (NEW + ".manifest.txt")
    with zipfile.ZipFile(zp) as z:
        names = z.namelist()
        n_zip = len(names)
        # 3) 完整性
        print("3) zip 完整性（testzip）")
        bad = z.testzip()
        print(f"   testzip: {'✅ 无损坏' if bad is None else f'❌ 损坏条目 {bad}'}")
        if bad is not None:
            problems.append(f"zip 损坏：{bad}")
        # 4) 关键内容
        print("4) 关键内容抽查")
        joined = "\n".join(names)
        for probe in PROBES:
            hit = probe in joined
            print(f"   {probe:<22} {'✅' if hit else '❌ 缺失'}")
            if not hit:
                problems.append(f"缺少关键内容：{probe}")

    n_man = 0
    n_head = None
    if man.exists():
        for line in io.open(man, encoding="utf-8"):
            if line.startswith("#"):
                if "files=" in line:
                    n_head = int(line.split("files=")[1].split()[0])
                continue
            if line.strip():
                n_man += 1
    print(f"   zip 条目 {n_zip} ｜ manifest 行 {n_man} ｜ manifest 头 files={n_head}")
    if not (n_zip == n_man == n_head):
        problems.append(f"条目数不一致 zip={n_zip} man={n_man} head={n_head}")
        print("   ❌ 三者不一致")
    else:
        print("   ✅ 三者一致")

    print()
    if problems:
        print(f"❌ 校验未通过（{len(problems)} 项）：")
        for p in problems:
            print(f"   - {p}")
        print("\n⛔ 拒绝删除旧快照。")
        return 1
    print("✅ 新快照校验全部通过")

    old = BAK / OLD
    if not old.exists():
        print(f"（旧快照已不存在：{OLD}）")
        return 0
    print(f"\n旧快照待删：")
    print(f"   路径: {old.resolve()}")
    print(f"   体积: {old.stat().st_size / 1024**3:.2f} GB")
    if not delete_old:
        print("\n（未加 --delete-old，暂不删除）")
        return 0
    # 目标校验：确认路径确实在 backups/ 下且文件名与预期完全一致
    assert old.parent.resolve() == BAK.resolve(), "待删文件不在 backups/ 下"
    assert old.name == OLD, "文件名与预期不符"
    old.unlink()
    print(f"\n🗑 已删除旧快照 {OLD}")
    print(f"   backups/ 现有：{[p.name for p in sorted(BAK.iterdir())]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
