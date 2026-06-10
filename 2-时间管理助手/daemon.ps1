# TimePlanner Silent Daemon v4
# Zero windows, zero taskbar items
# TCP port check for reliable detection (avoids HTTP HEAD issues)

$ErrorActionPreference = "Continue"
$ROOT = "D:\AI-项目\2-时间管理助手"
$LOGFILE = "$ROOT\daemon.log"
$MAX_LOG = 300

$Script:staticPID = 0
$Script:syncPID = 0
$Script:restartTimes = @()
$MAX_RESTART_3MIN = 4

function Write-Log($msg) {
    try { Add-Content -Path $LOGFILE -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg" -ErrorAction SilentlyContinue } catch {}
}

function Rotate-Log {
    if (-not (Test-Path $LOGFILE)) { return }
    try {
        $lines = Get-Content $LOGFILE -ErrorAction SilentlyContinue
        if ($lines -and $lines.Count -gt $MAX_LOG) {
            [System.IO.File]::WriteAllLines($LOGFILE, $lines[-($MAX_LOG)..-1])
        }
    } catch {}
}

function Test-TCPPort {
    param([int]$Port, [int]$TimeoutMS = 5000)
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $result = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $success = $result.AsyncWaitHandle.WaitOne($TimeoutMS)
        $client.Close()
        return $success
    } catch {
        return $false
    }
}

function Test-PortReliable {
    param([int]$Port)
    # Try once, if it fails retry after 3s
    if (Test-TCPPort $Port 4000) { return $true }
    Start-Sleep -Seconds 3
    return Test-TCPPort $Port 4000
}

function Test-CrashLoop {
    $cutoff = (Get-Date).AddMinutes(-3)
    $Script:restartTimes = @($Script:restartTimes | Where-Object { $_ -gt $cutoff })
    return ($Script:restartTimes.Count -gt $MAX_RESTART_3MIN)
}

function Start-OneNode {
    param([string]$Dir, [string]$Script, [string]$Label, [ref]$TrackPID)

    if ($TrackPID.Value -gt 0) {
        try {
            $old = Get-Process -Id $TrackPID.Value -ErrorAction SilentlyContinue
            if ($old) {
                Write-Log "Stopping $Label (PID $($TrackPID.Value))"
                $old.Kill()
                $old.WaitForExit(3000)
            }
        } catch {}
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "node"
    $psi.Arguments = $Script
    $psi.WorkingDirectory = $Dir
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden

    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
        $TrackPID.Value = $proc.Id
        Write-Log "$Label OK (PID $($proc.Id))"
        return $true
    } catch {
        Write-Log "FAIL $Label : $_"
        $TrackPID.Value = 0
        return $false
    }
}

# ====== MAIN ======
Write-Log "==== Daemon v4 PID=$PID ===="

# One-time cleanup
$stale = @(Get-Process -Name "node" -ErrorAction SilentlyContinue)
if ($stale.Count -gt 0) {
    Write-Log "Cleanup: $($stale.Count) old node"
    $stale | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

Write-Log "Starting servers..."
Start-OneNode -Dir "$ROOT\src" -Script "server.js" -Label "6371" -TrackPID ([ref]$Script:staticPID)
Start-OneNode -Dir "$ROOT" -Script "sync-server.js" -Label "6372" -TrackPID ([ref]$Script:syncPID)
Start-Sleep -Seconds 6

$s1 = Test-TCPPort 6371 3000
$s2 = Test-TCPPort 6372 3000
Write-Log "Init: 6371=$s1 6372=$s2 PID=$($Script:staticPID),$($Script:syncPID)"
Rotate-Log

$round = 0
while ($true) {
    Start-Sleep -Seconds 30
    $round++

    if ($round % 20 -eq 0) {
        Rotate-Log
        Write-Log "HB #$round 6371=$(Test-TCPPort 6371 3000) 6372=$(Test-TCPPort 6372 3000) PID=$($Script:staticPID),$($Script:syncPID)"
    }

    $need = @()
    if (-not (Test-PortReliable 6371)) { $need += @{L="6371"; D="$ROOT\src"; S="server.js"; P=6371; R=[ref]$Script:staticPID} }
    if (-not (Test-PortReliable 6372)) { $need += @{L="6372"; D="$ROOT"; S="sync-server.js"; P=6372; R=[ref]$Script:syncPID} }

    if ($need.Count -gt 0) {
        if (Test-CrashLoop) {
            Write-Log "CRASH LOOP - wait 5min"
            Start-Sleep -Seconds 300
        }
        foreach ($s in $need) {
            Write-Log "$($s.L) DOWN, restarting..."
            Start-OneNode -Dir $s.D -Script $s.S -Label $s.L -TrackPID $s.R
        }
        $Script:restartTimes += (Get-Date)
        if ($Script:restartTimes.Count -gt 50) { $Script:restartTimes = $Script:restartTimes[-20..-1] }
        Start-Sleep -Seconds 5
    }
}
