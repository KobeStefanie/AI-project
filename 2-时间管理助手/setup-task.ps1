# 时间管理助手 - 创建计划任务（以管理员身份运行此脚本）
# 右键 → 以管理员身份运行 PowerShell，然后执行：
#   powershell -ExecutionPolicy Bypass -File "D:\AI-项目\2-时间管理助手\setup-task.ps1"

$ErrorActionPreference = "Stop"

$taskName = "TimePlanner-AutoStart"
$scriptPath = "D:\AI-项目\2-时间管理助手\autostart-silent.bat"
$workDir = "D:\AI-项目\2-时间管理助手"

# 删除旧任务
try { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue } catch {}

# 任务动作
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory $workDir

# 触发器：启动 + 登录
$t1 = New-ScheduledTaskTrigger -AtStartup
$t2 = New-ScheduledTaskTrigger -AtLogOn

# 触发器：工作站解锁（休眠唤醒 → 解锁屏幕）
# 这个可以用 SessionStateChange trigger 注册
try {
    $t3 = Get-CimClass -Namespace Root/Microsoft/Windows/TaskScheduler -ClassName MSFT_TaskSessionStateChangeTrigger | New-CimInstance -ClientOnly -Property @{
        StateChange = 8   # TASK_SESSION_UNLOCK
        Enabled = $true
    }
} catch {
    Write-Host "WARN: Cannot create SessionUnlock trigger, skipping."
    $t3 = $null
}

# 设置
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -Compatibility Win8

# 主体（以当前用户身份运行）
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

$triggers = @($t1, $t2)
if ($t3) { $triggers += $t3 }

try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $triggers `
        -Settings $settings `
        -Principal $principal `
        -Description "Time Planner auto-start on boot/login/unlock" `
        -Force
    Write-Host "SUCCESS: Task '$taskName' created."
    Write-Host "Triggers: $($triggers.Count) (Startup, LogOn, SessionUnlock)"
} catch {
    Write-Host "ERROR creating task: $_" -ForegroundColor Red
}

# 验证
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($task) {
    Write-Host "State: $($task.State)"
    foreach ($t in $task.Triggers) {
        Write-Host "  Trigger: $($t.CimClass.CimClassName)"
    }
}
