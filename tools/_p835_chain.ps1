# After the full LLaVA run: the full-COCO scale-up, which was interrupted to give LLaVA the GPU.
$ErrorActionPreference = 'Continue'
Set-Location 'D:\Realdesktop\Wan\Important\New'
$log = 'outputs\analysis\_p835_chain.log'
function Write-Log($m) { "$(Get-Date -Format 'HH:mm:ss') $m" | Out-File -FilePath $log -Encoding utf8 -Append }
$py = 'D:\Anaconda\envs\pytorch\python.exe'
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
$env:HF_HUB_OFFLINE = '1'; $env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_PROGRESS_BARS = '1'; $env:PYTORCH_ALLOC_CONF = 'expandable_segments:True'
Write-Log "chain started; waiting for the full LLaVA run"
while (Get-Process -Id 30144 -EA SilentlyContinue) { Start-Sleep -Seconds 60 }
while (Get-Process python -EA SilentlyContinue | Where-Object { $_.WorkingSet64 -gt 4GB }) { Start-Sleep -Seconds 60 }
Write-Log "LLaVA finished; starting the full-COCO scale-up"
& $py -u -X utf8 tools\_p818_full_coco.py --train-images 10000 --epochs 3 --batch 64 `
    --eval-batch 64 --rank 8 --seeds 3 --lr 1e-5 --apply *>> outputs\analysis\_p818.log
Write-Log "full COCO exit $LASTEXITCODE; chain done"
