# Experiment progress monitor: manual start / stop / status.
#
# The monitor is a tiny local web page (http://127.0.0.1:8787/) that only reads files: it never touches experiments,
# the training processes or the DSH application. It scans only when a page asks, and by default it exits after 30
# minutes with no visitors, so "closed" really means nothing is running.
#
#   powershell -File tools\progress_monitor.ps1 -Action start
#   powershell -File tools\progress_monitor.ps1 -Action stop
#   powershell -File tools\progress_monitor.ps1 -Action status
#
# -IdleMinutes controls the self-stop timer (0 = keep running until stopped explicitly).
param(
    [ValidateSet("start", "stop", "status")]
    [string]$Action = "status",
    [int]$IdleMinutes = 30,
    [int]$Port = 8787
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $repo "tools\_p1777_progress_server.py"))) {
    $repo = (Get-Location).Path
}
$serverScript = Join-Path $repo "tools\_p1777_progress_server.py"
$python = "D:\Anaconda\envs\pytorch\python.exe"

function Get-MonitorPid {
    param([int]$LocalPort)
    $conns = Get-NetTCPConnection -State Listen -LocalPort $LocalPort -ErrorAction SilentlyContinue
    if (-not $conns) { return $null }
    return ($conns | Select-Object -First 1).OwningProcess
}

function Show-Status {
    param([int]$LocalPort)
    $owner = Get-MonitorPid -LocalPort $LocalPort
    if ($owner) {
        $proc = Get-Process -Id $owner -ErrorAction SilentlyContinue
        Write-Output "MONITOR: running on http://127.0.0.1:$LocalPort/ (pid $owner, $($proc.ProcessName))"
        try {
            $j = Invoke-RestMethod -Uri "http://127.0.0.1:$LocalPort/progress.json" -TimeoutSec 5
            $jobs = ($j.jobs | ForEach-Object { "$($_.name) $($_.done)/$($_.target)" }) -join " | "
            Write-Output "DATA:    $jobs"
            if ($j.gpu) { Write-Output "GPU:     $($j.gpu.mem_used_mb)/$($j.gpu.mem_total_mb) MB, $($j.gpu.util_pct)%" }
        } catch {
            Write-Output "DATA:    page did not answer (starting up?)"
        }
    } else {
        Write-Output "MONITOR: stopped (nothing listening on port $LocalPort)"
    }
}

switch ($Action) {
    "status" { Show-Status -LocalPort $Port }
    "stop" {
        $owner = Get-MonitorPid -LocalPort $Port
        if ($owner) {
            Stop-Process -Id $owner -Force
            Start-Sleep -Milliseconds 400
            Write-Output "MONITOR: stopped (pid $owner)"
        } else {
            Write-Output "MONITOR: already stopped"
        }
    }
    "start" {
        $owner = Get-MonitorPid -LocalPort $Port
        if ($owner) {
            Write-Output "MONITOR: already running (pid $owner) -> http://127.0.0.1:$Port/"
            break
        }
        if (-not (Test-Path $serverScript)) { throw "server script not found: $serverScript" }
        $args = @($serverScript, "--port", "$Port")
        if ($IdleMinutes -gt 0) { $args += @("--idle-exit", "$($IdleMinutes * 60)") }
        $p = Start-Process -FilePath $python -ArgumentList $args -WindowStyle Hidden -PassThru
        Start-Sleep -Seconds 2
        if (Get-MonitorPid -LocalPort $Port) {
            $idle = if ($IdleMinutes -gt 0) { "auto-stops after $IdleMinutes min idle" } else { "runs until stopped" }
            Write-Output "MONITOR: started (pid $($p.Id)) -> http://127.0.0.1:$Port/  ($idle)"
        } else {
            Write-Output "MONITOR: failed to start; check $python and $serverScript"
        }
    }
}
