; VoiceType Hotkey - 全局语音输入热键
; Ctrl+Shift+M: 开始/停止录音
; 需要 voice-server.js 在 localhost:19876 运行

#Requires AutoHotkey v2.0

isRecording := false

^+m:: {
    global isRecording
    isRecording := !isRecording

    if (isRecording) {
        try {
            whr := ComObject("WinHttp.WinHttpRequest.5.1")
            whr.Open("POST", "http://127.0.0.1:19876/start", false)
            whr.Send()
            ToolTip("🎤 录音中… 说完停顿自动粘贴", , , 2)
            SetTimer () => ToolTip(, , , 2), -3000
        }
    } else {
        try {
            whr := ComObject("WinHttp.WinHttpRequest.5.1")
            whr.Open("POST", "http://127.0.0.1:19876/stop", false)
            whr.Send()
            ToolTip("⏹ 已停止", , , 3)
            SetTimer () => ToolTip(, , , 3), -1500
        }
    }
}

; 托盘提示
TrayTip("VoiceType Ready", "Ctrl+Shift+M 开始/停止语音输入", "")
