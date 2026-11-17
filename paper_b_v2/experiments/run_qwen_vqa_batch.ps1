$py = 'D:\Anaconda\envs\pytorch\python.exe'
$root = 'D:\Realdesktop\Wan\Important\New'
$runs = @(
    @('8','47'),
    @('32','45'),
    @('32','47')
)
foreach ($r in $runs) {
    $rank = $r[0]; $seed = $r[1]
    $out = Join-Path $root "outputs\paper_b\qwen_vqa_r${rank}_s${seed}.log"
    $err = Join-Path $root "outputs\paper_b\qwen_vqa_r${rank}_s${seed}.err.log"
    $p = Start-Process -FilePath $py -ArgumentList @('paper_b_v2/experiments/run_qwen_vqa.py','--rank',$rank,'--seed',$seed,'--train','80','--test','12','--epochs','3') -WorkingDirectory $root -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden -PassThru
    $p | Wait-Process
}
"QWEN_BATCH_DONE"
