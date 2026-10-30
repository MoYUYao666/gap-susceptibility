# Queue: resume the Flickr30k rank sweep, then the full-COCO scale-up, after LLaVA finishes.
$ErrorActionPreference = 'Continue'
Set-Location 'D:\Realdesktop\Wan\Important\New'
$log = 'outputs\analysis\_p829_chain.log'
function Write-Log($m) { "$(Get-Date -Format 'HH:mm:ss') $m" | Out-File -FilePath $log -Encoding utf8 -Append }
$py = 'D:\Anaconda\envs\pytorch\python.exe'
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
$env:HF_HUB_OFFLINE = '1'; $env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_PROGRESS_BARS = '1'; $env:PYTORCH_ALLOC_CONF = 'expandable_segments:True'
Write-Log "chain started; waiting for LLaVA"
while (Get-Process python -EA SilentlyContinue | Where-Object { $_.WorkingSet64 -gt 2GB }) { Start-Sleep -Seconds 60 }
Write-Log "LLaVA finished; resuming the Flickr30k rank sweep (completed ranks are skipped)"
Start-Sleep -Seconds 20
& $py -u -X utf8 tools\_p812_flickr_rank.py --images 2000 --eval-images 1000 --epochs 5 --batch 128 `
    --seeds 1 --arms text_only --ranks 1,2,4,8,16,32,64 --lr 1e-5 --dropout 0.0 --apply `
    *>> outputs\analysis\_p812.log
Write-Log "Flickr sweep exit $LASTEXITCODE"
Write-Log "starting the full-COCO scale-up"
& $py -u -X utf8 tools\_p818_full_coco.py --train-images 10000 --epochs 3 --batch 64 `
    --eval-batch 64 --rank 8 --seeds 3 --lr 1e-5 --apply *>> outputs\analysis\_p818.log
Write-Log "full COCO exit $LASTEXITCODE; chain done"
