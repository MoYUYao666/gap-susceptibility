# Wait for the Flickr30k rank sweep to finish, then run the full-COCO evaluation.
$ErrorActionPreference = 'Continue'
Set-Location 'D:\Realdesktop\Wan\Important\New'
$flickr = 34144
$log = 'outputs\analysis\_p818_launch.log'
"=== launcher started $(Get-Date -Format 'HH:mm:ss') : waiting for Flickr sweep (PID $flickr) ===" | Out-File -FilePath $log -Encoding utf8
$waited = 0
while (Get-Process -Id $flickr -EA SilentlyContinue) {
    Start-Sleep -Seconds 60
    $waited += 1
    if ($waited % 15 -eq 0) { "  still waiting: $waited min" | Out-File -FilePath $log -Encoding utf8 -Append }
    if ($waited -gt 600) { "  gave up after 600 min" | Out-File -FilePath $log -Encoding utf8 -Append; exit 1 }
}
"=== Flickr sweep finished after $waited min; starting full COCO ===" | Out-File -FilePath $log -Encoding utf8 -Append
Start-Sleep -Seconds 30
$py = 'D:\Anaconda\envs\pytorch\python.exe'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:PYTORCH_ALLOC_CONF = 'expandable_segments:True'
& $py tools\_p818_full_coco.py --train-images 10000 --epochs 3 --batch 64 --eval-batch 64 --rank 8 --seeds 3 --lr 1e-5 --apply *>> outputs\analysis\_p818.log
"=== full COCO finished with exit $LASTEXITCODE at $(Get-Date -Format 'HH:mm:ss') ===" | Out-File -FilePath $log -Encoding utf8 -Append
