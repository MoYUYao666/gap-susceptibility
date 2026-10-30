# Flickr first (paper-critical ODE validation), then the LLaVA adaptation-site comparison at the
# smallest setting this hardware finishes: 48 samples, 1 epoch, batch 6, 30 evaluation pairs.
# Measured cost: ~2 min per training step at batch 4, so the set is sized to finish, not to be large.
$ErrorActionPreference = 'Continue'
Set-Location 'D:\Realdesktop\Wan\Important\New'
$log = 'outputs\analysis\_p834_chain.log'
function Write-Log($m) { "$(Get-Date -Format 'HH:mm:ss') $m" | Out-File -FilePath $log -Encoding utf8 -Append }
$py = 'D:\Anaconda\envs\pytorch\python.exe'
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
$env:HF_HUB_OFFLINE = '1'; $env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_PROGRESS_BARS = '1'; $env:PYTORCH_ALLOC_CONF = 'expandable_segments:True'
Write-Log "chain started; waiting for the Flickr sweep (PID 30144)"
while (Get-Process -Id 30144 -EA SilentlyContinue) { Start-Sleep -Seconds 60 }
Write-Log "Flickr finished"
Start-Sleep -Seconds 25

Write-Log "starting LLaVA adaptation sites (48 samples, 1 epoch, batch 6, 30 eval pairs)"
& $py -u -X utf8 tools\_p820_llava_sites.py --samples 48 --eval-pairs 30 --epochs 1 `
    --batch 6 --max-len 2048 --seeds 2 --lr 1e-4 --rank 8 `
    --arms text_only,vision_only,both --apply *>> outputs\analysis\_p820_run5.out
Write-Log "LLaVA exit $LASTEXITCODE"

Write-Log "starting the full-COCO scale-up"
& $py -u -X utf8 tools\_p818_full_coco.py --train-images 10000 --epochs 3 --batch 64 `
    --eval-batch 64 --rank 8 --seeds 3 --lr 1e-5 --apply *>> outputs\analysis\_p818.log
Write-Log "full COCO exit $LASTEXITCODE; chain done"
