$ROOT = "D:\AI-项目\2-时间管理助手"
$ws = New-Object -ComObject WScript.Shell
$startup = [Environment]::GetFolderPath('Startup')

if (-not (Test-Path $startup)) {
    New-Item -ItemType Directory -Path $startup -Force | Out-Null
}

$shortcut = $ws.CreateShortcut("$startup\TimePlanner-Watchdog.lnk")
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = '-ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $ROOT + '\watchdog.ps1"'
$shortcut.WorkingDirectory = $ROOT
$shortcut.WindowStyle = 7
$shortcut.Description = "TimePlanner Watchdog - port monitor and auto-restart"
$shortcut.Save()
Write-Output "[OK] Watchdog shortcut created"

$shortcut2 = $ws.CreateShortcut("$startup\TimePlanner-AutoStart.lnk")
$shortcut2.TargetPath = "cmd.exe"
$shortcut2.Arguments = '/c ""' + $ROOT + '\autostart-silent.bat""'
$shortcut2.WorkingDirectory = $ROOT
$shortcut2.WindowStyle = 7
$shortcut2.Description = "TimePlanner AutoStart"
$shortcut2.Save()
Write-Output "[OK] AutoStart shortcut created"

Remove-Item "$startup\TimePlanner.lnk" -ErrorAction SilentlyContinue
Write-Output "Startup items configured!"
