# TimePlanner Watchdog v3 - monitors ports, auto-restarts on failure

$ErrorActionPreference = "Continue"
$ROOT = "D:\AI-项目\2-时间管理助手"
$LOGFILE = "$ROOT\watchdog.log"
$MAX_LOG_LINES = 500

$portServices = @{
    6371 = @{ dir = "$ROOT\src"; script = "server.js";      label = "Static-HTTP" }
    6372 = @{ dir = "$ROOT";     script = "sync-server.js"; label = "Sync-HTTP" }
    6443 = @{ dir = "$ROOT\src"; script = "server.js";      label = "Static-HTTPS" }
    6444 = @{ dir = "$ROOT";     script = "sync-server.js"; label = "Sync-HTTPS" }
}

$restartHistory = @()
$MAX_RESTARTS_PER_10MIN = 5
$COOLDOWN_SECONDS = 300

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    try { Add-Content -Path $LOGFILE -Value $line -ErrorAction SilentlyContinue } catch {}
}

function Rotate-Log {
    if (-not (Test-Path $LOGFILE)) { return }
    try {
        $lines = Get-Content $LOGFILE -ErrorAction SilentlyContinue
        if ($lines.Count -gt $MAX_LOG_LINES) {
            [System.IO.File]::WriteAllLines($LOGFILE, $lines[-($MAX_LOG_LINES)..-1])
        }
    } catch {}
}

function Test-PortListening {
    param([int]$Port)
    try {
        $result = netstat -ano 2>$null | Select-String "LISTENING.*:$Port\b"
        return ($result -ne $null)
    } catch { return $false }
}

function Get-MissingPorts {
    $missing = @()
    foreach ($port in $portServices.Keys) {
        if (-not (Test-PortListening $port)) { $missing += $port }
    }
    return $missing
}

function Test-CrashLoop {
    $now = Get-Date
    $cutoff = $now.AddMinutes(-10)
    $recent = @($restartHistory | Where-Object { $_ -gt $cutoff })
    $restartHistory = $recent
    return ($recent.Count -gt $MAX_RESTARTS_PER_10MIN)
}

function Start-Services {
    $missing = Get-MissingPorts
    if ($missing.Count -eq 0) { return }

    $toStart = @{}
    foreach ($port in $missing) {
        $svc = $portServices[$port]
        $key = "$($svc.dir)|$($svc.script)"
        if (-not $toStart.ContainsKey($key)) {
            $toStart[$key] = @{ dir = $svc.dir; script = $svc.script; label = $svc.label }
        }
    }

    Write-Log "Watchdog: Missing ports $($missing -join ', '), restarting..."

    if (Test-CrashLoop) {
        Write-Log "Watchdog: CRASH LOOP DETECTED, cooling down ${COOLDOWN_SECONDS}s..."
        Start-Sleep -Seconds $COOLDOWN_SECONDS
        Write-Log "Watchdog: Cooldown ended"
    }

    $restartHistory += (Get-Date)
    if ($restartHistory.Count -gt 50) { $restartHistory = $restartHistory[-20..-1] }

    foreach ($item in $toStart.Values) {
        Write-Log "Watchdog: Starting $($item.label)..."
        Start-Process node -WorkingDirectory $item.dir -ArgumentList $item.script -WindowStyle Minimized
    }

    Start-Sleep -Seconds 5
    $stillMissing = Get-MissingPorts
    if ($stillMissing.Count -eq 0) {
        Write-Log "Watchdog: All ports restored"
    } else {
        Write-Log "Watchdog: Still missing $($stillMissing -join ', ')"
    }
}

# MAIN
Write-Log "========== Watchdog v3 started (PID $PID) =========="
Write-Log "Watchdog: Monitoring ports: $($portServices.Keys -join ', ')"

$initMissing = Get-MissingPorts
if ($initMissing.Count -eq 0) {
    Write-Log "Watchdog: Initial check OK"
} else {
    Write-Log "Watchdog: Initial check found missing $($initMissing -join ', ')"
    Start-Services
}

Rotate-Log

$loopCount = 0
while ($true) {
    Start-Sleep -Seconds 30
    $loopCount++
    if ($loopCount % 20 -eq 0) {
        Rotate-Log
        Write-Log "Watchdog: Heartbeat #$loopCount"
    }
    $missing = Get-MissingPorts
    if ($missing.Count -gt 0) {
        Write-Log "Watchdog: Round $loopCount, missing $($missing -join ', ')"
        Start-Services
    }
}
