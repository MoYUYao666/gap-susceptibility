# Start the experiment progress monitor on demand, in a hidden window.
# The sidebar panel polls it only while its tab is open; the server itself scans only when asked and can exit after an
# idle period, so nothing runs in the background when nobody is looking.
$port = 8787
$probe = Test-NetConnection -ComputerName 127.0.0.1 -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue
if ($probe) { Write-Output "monitor already running on port $port"; exit 0 }
$py = "D:\Anaconda\envs\pytorch\python.exe"
$script = Join-Path (Split-Path -Parent $PSScriptRoot) "tools\_p1777_progress_server.py"
Start-Process -FilePath $py -ArgumentList @($script, "--port", "$port", "--idle-exit", "1800") -WindowStyle Hidden
Start-Sleep -Seconds 2
Write-Output "monitor started: http://127.0.0.1:$port/  (auto-exits after 30 min idle)"
