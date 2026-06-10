// VoiceType Server v2 - 全局热键语音输入服务
// Ctrl+Shift+M 开始录音 → 说话 → 自动粘贴到当前光标

const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PORT = 19876;
const HTML_FILE = 'D:\\AI-项目\\6-语音输入助手\\voice-popup.html';

// ====== 录音状态（由全局热键控制）======
let state = {
  recording: false,
  requestStop: false,    // 请求停止
  lastStartTime: null,
};

// ====== 填充词过滤 ======
const FILLERS = [
  '嗯','啊','呃','哦','额','诶','唔','嘛','呀','哈','呵','唉',
  '这个','那个','就是说','然后就是','那个什么','那个啥','怎么说呢',
  '这样子','对吧','对不对','你知道吗','你懂吗','明白吗',
  '所以说','说白了','基本上','一般来说','可以说','所以呢','那么',
  '总而言之','总的来说','简单来说','我想说的是',
  '我觉得就是说','实际上','其实','就是那个','反正就是说'
];

function cleanText(text) {
  if (!text) return '';
  let cleaned = text;
  const sorted = [...FILLERS].sort((a, b) => b.length - a.length);
  for (const f of sorted) {
    cleaned = cleaned.replace(new RegExp(f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), '');
  }
  cleaned = cleaned.replace(/\s{2,}/g, ' ').trim();
  cleaned = cleaned.replace(/^[,，。！？、…\s]+/, '').replace(/[,，。！？、…\s]+$/, '');
  return cleaned || text.trim();
}

// ====== 粘贴（PowerShell Ctrl+V）======
function pasteText(text) {
  const b64 = Buffer.from(text, 'utf-8').toString('base64');
  const psScript = `
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Clipboard]::SetText([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("${b64}")))
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class KB {
    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
}
'@
Start-Sleep -Milliseconds 200
[KB]::keybd_event(0x11, 0, 0, [UIntPtr]::Zero)
[KB]::keybd_event(0x56, 0, 0, [UIntPtr]::Zero)
Start-Sleep -Milliseconds 50
[KB]::keybd_event(0x56, 0, 2, [UIntPtr]::Zero)
[KB]::keybd_event(0x11, 0, 2, [UIntPtr]::Zero)
`;
  try {
    execSync(`powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "${psScript.replace(/"/g, '\\"')}"`, { timeout: 5000, windowsHide: true });
    return true;
  } catch (e) {
    console.error('Paste error:', e.message);
    return false;
  }
}

// ====== HTTP Server ======
const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  const url = new URL(req.url, `http://localhost:${PORT}`);

  // Health + state
  if (url.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', recording: state.recording, requestStop: state.requestStop }));
    return;
  }

  // Start recording (from hotkey)
  if (url.pathname === '/start' && req.method === 'POST') {
    state.recording = true;
    state.requestStop = false;
    state.lastStartTime = Date.now();
    console.log('🎤 START recording');
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, action: 'start' }));
    return;
  }

  // Stop recording (from hotkey)
  if (url.pathname === '/stop' && req.method === 'POST') {
    state.requestStop = true;
    console.log('⏹ STOP requested');
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, action: 'stop' }));
    return;
  }

  // Paste endpoint
  if (url.pathname === '/paste' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { text } = JSON.parse(body);
        const cleaned = cleanText(text);
        console.log(`Pasting: "${cleaned.substring(0, 50)}..."`);
        const ok = pasteText(cleaned);
        state.recording = false;
        state.requestStop = false;
        res.writeHead(ok ? 200 : 500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok, text: cleaned }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: e.message }));
      }
    });
    return;
  }

  // Report text (send text to server to be pasted)
  if (url.pathname === '/report' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { text } = JSON.parse(body);
        const cleaned = cleanText(text);
        console.log(`Auto-pasting: "${cleaned.substring(0, 50)}..."`);
        const ok = pasteText(cleaned);
        state.recording = false;
        state.requestStop = false;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok, text: cleaned }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: e.message }));
      }
    });
    return;
  }

  // Serve HTML
  if (url.pathname === '/' || url.pathname === '/popup') {
    try {
      const html = fs.readFileSync(HTML_FILE, 'utf-8');
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(html);
    } catch (e) {
      res.writeHead(500);
      res.end('Error');
    }
    return;
  }

  res.writeHead(404);
  res.end('Not found');
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`VoiceType Server: http://127.0.0.1:${PORT}`);
  console.log('Use Ctrl+Shift+M to start/stop recording');
  console.log('Popup auto-records when server says so');
});
