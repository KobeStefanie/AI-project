# VoiceType Hotkey - 全局热键监听器
# 运行后注册 Ctrl+Shift+M，按键时通知本地服务开始/停止录音

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Windows.Forms;

public class GlobalHotkey : IDisposable {
    [DllImport("user32.dll")] private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);
    [DllImport("user32.dll")] private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

    private const uint MOD_CONTROL = 0x0002;
    private const uint MOD_SHIFT = 0x0004;
    private const uint MOD_ALT = 0x0001;
    private const int WM_HOTKEY = 0x0312;
    private const int HOTKEY_ID = 9999;

    private Form _form;
    public event Action HotkeyPressed;

    public GlobalHotkey(Keys key, bool ctrl = true, bool shift = true, bool alt = false) {
        _form = new Form();
        _form.Text = "VoiceType Hotkey";
        _form.ShowInTaskbar = false;
        _form.WindowState = FormWindowState.Minimized;
        _form.Opacity = 0;
        _form.Show();

        uint mods = 0;
        if (ctrl) mods |= MOD_CONTROL;
        if (shift) mods |= MOD_SHIFT;
        if (alt) mods |= MOD_ALT;

        if (!RegisterHotKey(_form.Handle, HOTKEY_ID, mods, (uint)key)) {
            throw new Exception("Failed to register hotkey. May already be in use.");
        }

        _form.KeyPreview = true;
        // Intercept WM_HOTKEY
        var originalWndProc = _form.GetType().GetMethod("WndProc",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        var newWndProc = new System.Windows.Forms.FormWindowStateHandler((ref Message m) => {
            if (m.Msg == WM_HOTKEY && m.WParam.ToInt32() == HOTKEY_ID) {
                HotkeyPressed?.Invoke();
            }
        });
        // We'll use Application.AddMessageFilter instead
        var filter = new HotkeyMessageFilter(HOTKEY_ID);
        filter.HotkeyPressed += () => HotkeyPressed?.Invoke();
        Application.AddMessageFilter(filter);
    }

    public void Dispose() {
        UnregisterHotKey(_form.Handle, HOTKEY_ID);
        _form.Close();
        _form.Dispose();
    }
}

public class HotkeyMessageFilter : IMessageFilter {
    private const int WM_HOTKEY = 0x0312;
    private int _id;
    public event Action HotkeyPressed;
    public HotkeyMessageFilter(int id) { _id = id; }
    public bool PreFilterMessage(ref Message m) {
        if (m.Msg == WM_HOTKEY && m.WParam.ToInt32() == _id) {
            HotkeyPressed?.Invoke();
            return true;
        }
        return false;
    }
}
"@ -ReferencedAssemblies "System.Windows.Forms"

# ====== 配置 ======
$SERVER = "http://127.0.0.1:19876"

# ====== 创建热键 ======
try {
    $hotkey = New-Object GlobalHotkey -ArgumentList @([System.Windows.Forms.Keys]::M, $true, $true, $false)
    Write-Host "✅ Hotkey registered: Ctrl+Shift+M"
    Write-Host "   Press Ctrl+Shift+M to start/stop voice recording"
    Write-Host "   Keep this window open (minimized is fine)"
    Write-Host ""
} catch {
    Write-Host "❌ Failed to register hotkey: $_"
    Write-Host "   Try running as Administrator or use a different shortcut"
    Start-Sleep -Seconds 5
    exit 1
}

# ====== 热键回调 ======
$isRecording = $false

$hotkeyAction = {
    $script:isRecording = -not $script:isRecording

    if ($script:isRecording) {
        # 开始录音 - 通知服务器
        try {
            $null = Invoke-RestMethod -Uri "$SERVER/start" -Method POST -TimeoutSec 2
            Write-Host "🎤 Recording started..."
        } catch {
            Write-Host "⚠ Server not reachable"
            $script:isRecording = $false
        }
    } else {
        # 停止录音
        try {
            $null = Invoke-RestMethod -Uri "$SERVER/stop" -Method POST -TimeoutSec 2
            Write-Host "⏹ Recording stopped"
        } catch {
            Write-Host "⚠ Server not reachable"
        }
    }
}

# 订阅事件
$hotkey.Add_HotkeyPressed($hotkeyAction)

# ====== 消息循环 ======
Write-Host "VoiceType Hotkey is running. Press Ctrl+C to exit."
try {
    [System.Windows.Forms.Application]::Run()
} finally {
    $hotkey.Dispose()
}
