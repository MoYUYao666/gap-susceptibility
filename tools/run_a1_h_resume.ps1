$py='D:\Anaconda\envs\pytorch\python.exe'
$log='logs_a1_h_resume.txt'
$fail=@()
function Step($name, $a) {
  "=== STEP $name  $(Get-Date -Format o) ===" | Out-File -FilePath $log -Append -Encoding utf8
  & $py @a *>> $log
  $rc = $LASTEXITCODE
  "exit=$rc  $(Get-Date -Format o)" | Out-File -FilePath $log -Append -Encoding utf8
  if ($rc -ne 0) { $script:fail += "$name (exit $rc)" }
  Start-Sleep -Seconds 5
}
"=== A1 hardening resume batch, started $(Get-Date -Format o) ===" | Out-File -FilePath $log -Encoding utf8
Step 'cert-baseline-metrics' @('tools/a1_h_baseline_metrics.py','--tau-k','5','10')
Step 'dtd-seed44-eval-recovery' @('tools/a1_h_e4_seed.py','--dataset','dtd','--seed','44','--seed-json','outputs/a1_h_recover_spec_dtd_seed44.json','--out','outputs/a1_h_seeds_dtd_seed44.json')
Step 'templates' @('tools/a1_h_templates.py')
Step 'bootstrap' @('tools/a1_h_bootstrap.py')
Step 'offset' @('tools/a1_h_offset.py')
Step 'seed-summary' @('tools/a1_h_seed_summary.py')
if ($fail.Count -gt 0) { "=== FAILED STEPS: $($fail -join '; ') ===" | Out-File -FilePath $log -Append -Encoding utf8 } else { "=== ALL STEPS OK ===" | Out-File -FilePath $log -Append -Encoding utf8 }
"=== BATCH DONE $(Get-Date -Format o) ===" | Out-File -FilePath $log -Append -Encoding utf8
