"""Move unused top-level scratch into 备选/ (archive). Nothing is deleted.

Safety rules applied:
  * Only top-level entries were considered. data/ models/ coco/ flickr30k/
    outputs/ tools/ docs/ src/ exp/ experiments/ SUBMISSION/ envs/ and every
    paper*/ folder are untouched. .git/ and .worktrees/ are never touched.
  * Anything referenced by a script or document was EXCLUDED, verified by
    grepping tools/ docs/ exp/ src/ experiments/ and every paper folder.
    Deliberately kept in place for that reason:
      qwen_cf_*.json   (Paper 3 Finding-4 data archives, referenced by
                        tools/ap3_c1_qwen_asymmetry.py and _vintages.py)
      _bibbackup_20260918/ (referenced by tools/_p1_bib_fix.py and
                        docs/P1_REMEDIATION_LOG.md)
      _fnpy/           (referenced by tools/_sync_publish_round10.py)
      cloud_upload/ + cloud_upload.zip (referenced by docs/CLOUD_RUNBOOK.md)
      _guide*.txt, _oe_guide.txt, _guide_ocean_engineering.pdf
                       (cited as evidence by the venue-decision docs)
  * Two JSON files that look like results data but are referenced nowhere are
    NOT lumped in with junk: they go to 04_待你确认的疑似数据/ for a human call.
Writes 备选/归档清单.txt so every move can be reversed.
"""
import pathlib
import shutil

ROOT = pathlib.Path(r"D:\Realdesktop\Wan\Important\New")
ARCH = ROOT / "备选"

GROUPS = {
    "01_临时脚本": [
        "_abs.py", "_abs2.py", "_counts.ps1", "_counts2.py", "_counts3.py",
        "_ckpt_probe.py", "_pass2_check_counts.py", "_a1fix_verify.py",
        "_compile_all.ps1", "_extract_guides.ps1", "_hl.ps1", "_hl2.ps1",
        "_img_info.ps1", "_prl.ps1",
        "_a1pm_dup.py", "_a1pm_find_lambda.py", "_a1pm_floats.py",
        "_a1pm_gen.py", "_a1pm_heads.py", "_a1pm_lambda.py", "_a1pm_logs.py",
        "_a1pm_p2.py", "_a1pm_p3.py", "_a1pm_recheck.py", "_a1pm_repin.py",
        "_a1pm_verify.py", "_a1pm_zh_num.py",
    ],
    "02_日志与转储": [
        "_a1_class_offset.log", "_a1_refs_mismatch.log", "_a1_rowmatch.log",
        "_a1_tau_diag.log", "_a23_number_trace.log", "_final_touchups.log",
        "_run_tmp.log", "_smoke.log",
        "a1_class_aligned_rerun.log", "a1_refs_rebuild.log",
        "a1_supplement.log", "a1_tau_recompute.log", "a1_tau_recompute2.log",
        "a1_traj_recompute.log",
        "env_rebuild.log", "texput.log",
        "logs_a1_h_baseline.txt", "logs_a1_h_final.txt",
        "logs_a1_h_offset2.txt", "logs_a1_h_resume.txt",
        "logs_a1_h_seeds.txt", "logs_a1_h_templates.txt",
        "logs_a1_rr_e2.txt", "logs_a1_rr_e2_provenance.txt",
        "logs_a1_rr_e3.txt", "logs_a1_rr_e4_coco.txt",
        "logs_a1_rr_e4_dtd.txt", "logs_a1_rr_e4_eval_archived.txt",
        "logs_a1_rr_e4_flickr30k_ref.txt", "logs_a1_rr_e4_food101.txt",
        "logs_a1_rr_summary.txt",
        "_dl_1.txt", "_dl_2.txt", "_dump_en.txt", "_dump_zh.txt",
        "_en.txt", "_zh.txt", "_tmp_ei.txt", "_tmp_guide.txt",
        ".tmp_ei.txt", ".tmp_guide.txt",
        "_hl_paper_a1_Cover_letter.pdf.txt", "_hl_paper_a1_declaration.pdf.txt",
        "_hl_paper_a1_highlights.pdf.txt", "_hl_paper_a2_highlights.pdf.txt",
        "_pc_a1_main.txt", "_pc_a1_main_zh.txt", "_pc_a2_main.txt",
        "_pc_a2_main_zh.txt", "_pc_prl_submitted.txt",
        "_publish_commit_msg.txt", "_publish_commit_msg_2.txt",
    ],
    "03_检查与备份产物": [
        "_a1h_check", ".texcheck_a1", "_chk_fig1_lambda.png",
        "_chk_fig2_tau_top1.png", "_chk_fig3_trajectory.png",
        "_chk_fig4_spectrum.png", "_figbak_a1", "_scratch_20260916",
        "_sonar_index", "_inspect_opensonar", "_inspect_sctd2",
        "_inspect_sctd2_voc",
    ],
    "04_待你确认的疑似数据": [
        "_a1pm_results.json", "_a1_decl.json",
    ],
    "05_其他": [
        "0.46.1", "1.md",
    ],
}

moved, missing = [], []
for group, names in GROUPS.items():
    dest = ARCH / group
    dest.mkdir(parents=True, exist_ok=True)
    for n in names:
        src = ROOT / n
        if not src.exists():
            missing.append(n)
            continue
        target = dest / n
        if target.exists():
            shutil.rmtree(target) if target.is_dir() else target.unlink()
        shutil.move(str(src), str(target))
        kind = "dir " if target.is_dir() else "file"
        moved.append(f"{group}\t{kind}\t{n}")

manifest = ARCH / "归档清单.txt"
with manifest.open("w", encoding="utf-8") as f:
    f.write("备选/ 归档清单 —— 生成于 workspace 整理\n")
    f.write("=" * 74 + "\n")
    f.write("没有任何文件被删除。全部是 move 到本目录下，可按本清单原样移回根目录。\n")
    f.write("移回方法：把 备选/<子目录>/<名字> 移回仓库根目录即可。\n\n")
    f.write(f"共移动 {len(moved)} 项。\n\n")
    for m in sorted(moved):
        f.write(m + "\n")
    if missing:
        f.write("\n（清单中但当前不存在，跳过）：\n")
        for m in missing:
            f.write("  " + m + "\n")

print(f"moved {len(moved)} items, {len(missing)} already absent")
for m in sorted(moved):
    print("  " + m)
