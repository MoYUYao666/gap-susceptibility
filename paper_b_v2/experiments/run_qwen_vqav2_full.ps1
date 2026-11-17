$py = 'D:\Anaconda\envs\pytorch\python.exe'
$root = 'D:\Realdesktop\Wan\Important\New'
$ranks = @('8','16','32','64')
$seeds = @('45','46','47','48')
foreach ($rank in $ranks) {
  foreach ($seed in $seeds) {
    $out = Join-Path $root "outputs\paper_b\qwen_vqav2_full_r${rank}_s${seed}.log"
    $err = Join-Path $root "outputs\paper_b\qwen_vqav2_full_r${rank}_s${seed}.err.log"
    $p = Start-Process -FilePath $py -ArgumentList @('paper_b_v2/experiments/run_qwen_vqa.py','--dataset','vqav2','--rank',$rank,'--seed',$seed,'--train','80','--test','12','--epochs','3') -WorkingDirectory $root -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden -PassThru
    $p | Wait-Process
  }
}
"VQAV2_FULL_DONE"
