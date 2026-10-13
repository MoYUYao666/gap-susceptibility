"""Archive paper合/ and paper_a4/ into 备选/06_归档稿件/. Nothing is deleted.

Findings that shaped this:
  * paper合/ is NOT tracked on master (0 files) but IS tracked on publish/main
    and on the remote (10 files), so moving the workspace copy does not disturb
    master's git status and does NOT touch GitHub.
  * paper_a4/ IS tracked on master (7 files, committed at 77352fd), so its
    removal has to be staged and committed.
  * 11 files reference paper合/, including five audit scripts under tools/audit
    that open it by literal relative path. Those are deliberately left
    unmodified: Paper A is being parked, and moving the folder back restores
    them. The consequence is recorded in the manifest so it is not silent.
  * paper_a4/ has no .tex or script source at all. Four of its seven figures are
    byte-identical to paper_a2's; three share a filename but differ.
"""
import pathlib
import shutil

ROOT = pathlib.Path(r"D:\Realdesktop\Wan\Important\New")
ARCH = ROOT / "备选" / "06_归档稿件"
ARCH.mkdir(parents=True, exist_ok=True)

moved = []
for name, why in [
    ("paper合", "Paper A (P1+P2). Author parked it 2026-09-24: the residual "
                "overlap with P1 is not being worked on, so the folder is "
                "archived rather than left in the working view."),
    ("paper_a4", "Orphan figure set with no .tex or script source. 4 of its 7 "
                 "figures are byte-identical to paper_a2's; 3 share a "
                 "filename but differ. Not reproducible from its own contents."),
]:
    src = ROOT / name
    if not src.exists():
        moved.append(f"SKIP (absent)\t{name}")
        continue
    dst = ARCH / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.move(str(src), str(dst))
    moved.append(f"moved\t{name}\t{why}")

# append to the existing manifest, preserving its BOM
manifest = ROOT / "备选" / "归档清单.txt"
with manifest.open("a", encoding="utf-8") as f:
    f.write("\n\n" + "=" * 74 + "\n")
    f.write("追加归档（2026-09-24，第二次整理）：整个稿件文件夹\n")
    f.write("=" * 74 + "\n\n")
    for m in moved:
        f.write(m + "\n")
    f.write(
        "\n移回方法（整目录）：\n"
        "  备选/06_归档稿件/paper合   ->  移回仓库根目录\n"
        "  备选/06_归档稿件/paper_a4  ->  移回仓库根目录\n"
        "\n"
        "⚠️ 注意 paper合 的引用（移回即恢复，不修脚本）\n"
        "  以下 5 个脚本用字面相对路径打开 paper合/，移动后它们会找不到文件：\n"
        "    tools/audit/audit_citations.py      ('Paper A', 'paper合', 'paper合/references.bib')\n"
        "    tools/audit/check_paperA.py         paper合/main_springer.tex, paper合/sections/*\n"
        "    tools/audit/find_bib_placeholders.py os.walk('paper合')\n"
        "    tools/audit/fix_paperA_round3.py    paper合/sections/*.tex, paper合/main_springer.tex\n"
        "    tools/audit/verify_citations.py\n"
        "  另有 6 个 docs/ 文档在正文里提到 paper合（仅叙述，不影响执行）：\n"
        "    AP3_SUBMISSION_READINESS.md, AP3_SYNC_PLAN.md, P1_ADVERSARIAL_REVIEW.md,\n"
        "    P1_REMEDIATION_LOG.md, P1_REVIEW_CITATIONS.md, P1_REVIEW_OVERLAP.md,\n"
        "    PAPERHE_OVERLAP_RESOLUTION.md\n"
        "\n"
        "ℹ️ paper合 仍在 GitHub 上：publish 分支与远端 main 各跟踪它的 10 个文件。\n"
        "   本次只动本地工作区，未改动远端。若要从远端一并移除，需另行处理。\n"
        "\n"
        "ℹ️ paper_a4 的 7 张图曾在提交 77352fd 中入库；本次移出后由 git 记录为删除，\n"
        "   历史仍可恢复。其中 3 张与 paper_a2 同名的图内容不同（fig3_taupred、\n"
        "   fig5_degradation、fig7_sonar_sigma）——A23 已用 paper_a2 的版本投稿，\n"
        "   若 paper_a4 的版本更新，可在 revision 阶段替换。\n"
    )

print(f"archived into {ARCH}")
for m in moved:
    print("  " + m)
