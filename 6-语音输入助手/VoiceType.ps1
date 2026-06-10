# VoiceType - Windows 语音输入 → 直接键入
# 零依赖，基于 Windows 内置中文语音识别
# 用法：终端输入 voice，或双击桌面 VoiceType 快捷方式

Add-Type -AssemblyName System.Speech
Add-Type -AssemblyName System.Windows.Forms

# ====== Win32 API ======
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
}
"@

$KEYEVENTF_KEYUP = 0x02
$VK_CONTROL = 0x11
$VK_V = 0x56

# ====== 填充词过滤 ======
$FILLERS = @(
    '嗯','啊','呃','哦','额','诶','唔','嘛','呀','哈','呵','唉',
    '这个','那个','就是说','然后就是','那个什么','那个啥','怎么说呢',
    '这样子','对吧','对不对','你知道吗','你懂吗','明白吗',
    '所以说','说白了','基本上','一般来说','可以说','所以呢','那么',
    '总而言之','总的来说','简单来说','我想说的是',
    '我觉得就是说','实际上','其实','就是那个','反正就是说'
)

function Clean-Text($text) {
    if (-not $text) { return "" }
    $cleaned = $text
    foreach ($f in $FILLERS | Sort-Object { $_.Length } -Descending) {
        $cleaned = $cleaned -replace [regex]::Escape($f), ''
    }
    $cleaned = $cleaned -replace '\s{2,}', ' '
    $cleaned = $cleaned -replace '^[,，。！？、…\s]+', ''
    $cleaned = $cleaned -replace '[,，。！？、…\s]+$', ''
    $cleaned = $cleaned.Trim()
    if ([string]::IsNullOrWhiteSpace($cleaned)) { return $text.Trim() }
    return $cleaned
}

# ====== 保存前台窗口 ======
$prevWindow = [Win32]::GetForegroundWindow()

# ====== 保存剪贴板 ======
try { $oldClipboard = [System.Windows.Forms.Clipboard]::GetText() } catch { $oldClipboard = "" }

# ====== 监听提示窗口 ======
$form = New-Object System.Windows.Forms.Form
$form.Size = New-Object System.Drawing.Size(300, 60)
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$form.Location = New-Object System.Drawing.Point($screen.Width - 320, $screen.Height - 100)
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.BackColor = [System.Drawing.Color]::FromArgb(40, 40, 40)
$form.Opacity = 0.85
$form.TopMost = $true
$form.ShowInTaskbar = $false

$label = New-Object System.Windows.Forms.Label
$label.Text = "🎤 正在听… 说完停顿即可"
$label.ForeColor = [System.Drawing.Color]::White
$label.Font = New-Object System.Drawing.Font("Microsoft YaHei", 10)
$label.AutoSize = $false
$label.Size = New-Object System.Drawing.Size(280, 40)
$label.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$label.Location = New-Object System.Drawing.Point(10, 10)
$form.Controls.Add($label)

$form.Show()
# 不抢焦点
[Win32]::SetForegroundWindow($prevWindow) | Out-Null

# ====== 语音识别 ======
$results = [System.Collections.ArrayList]::new()
$done = $false
$silenceTimer = $null
$lock = New-Object Object

try {
    $recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    $recognizer.SetInputToDefaultAudioDevice()
    $recognizer.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))

    $action = {
        param($s, $e)
        if ($e.Result -and $e.Result.Text.Trim()) {
            $t = $e.Result.Text.Trim()
            lock ($lock) { [void]$results.Add($t) }
            try {
                $label.Invoke([Action[string]]{ param($txt) $this.Text = "🎤 $txt" }, $t)
            } catch {}
            lock ($lock) {
                if ($silenceTimer) { $silenceTimer.Dispose() }
                $silenceTimer = New-Object System.Timers.Timer(1800)
                $silenceTimer.AutoReset = $false
                $silenceTimer.Add_Elapsed({ $script:done = $true })
                $silenceTimer.Start()
            }
        }
    }

    $null = Register-ObjectEvent -InputObject $recognizer -EventName SpeechRecognized -Action $action
    $recognizer.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Multiple)

    $deadline = [DateTime]::Now.AddSeconds(25)
    while (-not $done -and [DateTime]::Now -lt $deadline) {
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 100
    }

    $recognizer.RecognizeAsyncCancel()
    Start-Sleep -Milliseconds 300
    Get-EventSubscriber | Where-Object { $_.SourceObject -eq $recognizer } | Unregister-Event -Force
    $recognizer.Dispose()
    lock ($lock) { if ($silenceTimer) { $silenceTimer.Dispose() } }

} finally {
    $form.Close()
    $form.Dispose()
}

# ====== 处理结果 ======
$rawText = ($results -join ' ').Trim()
if (-not $rawText) {
    # 恢复剪贴板
    try { [System.Windows.Forms.Clipboard]::SetText($oldClipboard) } catch {}
    exit 0
}

$cleaned = Clean-Text $rawText
if (-not $cleaned) { $cleaned = $rawText }

# ====== 粘贴到前台窗口（剪贴板 + Ctrl+V）======
try {
    [System.Windows.Forms.Clipboard]::SetText($cleaned)
} catch {
    # 重试
    Start-Sleep -Milliseconds 200
    try { [System.Windows.Forms.Clipboard]::SetText($cleaned) } catch { exit 1 }
}

Start-Sleep -Milliseconds 150
[Win32]::SetForegroundWindow($prevWindow) | Out-Null
Start-Sleep -Milliseconds 100

# 模拟 Ctrl+V
[Win32]::keybd_event($VK_CONTROL, 0, 0, [UIntPtr]::Zero)
[Win32]::keybd_event($VK_V, 0, 0, [UIntPtr]::Zero)
Start-Sleep -Milliseconds 50
[Win32]::keybd_event($VK_V, 0, $KEYEVENTF_KEYUP, [UIntPtr]::Zero)
[Win32]::keybd_event($VK_CONTROL, 0, $KEYEVENTF_KEYUP, [UIntPtr]::Zero)

# 延迟恢复剪贴板
Start-Sleep -Milliseconds 500
try { [System.Windows.Forms.Clipboard]::SetText($oldClipboard) } catch {}
