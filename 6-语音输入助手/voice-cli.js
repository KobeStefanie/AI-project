// VoiceType - 全局语音输入 CLI
// 录音 → 转文字 → 自动键入当前光标
// 用法: node voice-cli.js

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// ====== 配置 ======
const RECORD_SECONDS = 10;        // 最长录音秒数
const SILENCE_THRESHOLD = 0.02;   // 静默检测阈值
const SILENCE_SECONDS = 1.8;      // 连续静默多少秒自动停止

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

// ====== 录音（sox） ======
function recordAudio(outputPath, maxSeconds = RECORD_SECONDS) {
  return new Promise((resolve, reject) => {
    // sox 录音命令：单声道 16kHz 16-bit
    const sox = spawn('sox', [
      '-t', 'waveaudio', 'default',   // Windows 默认麦克风
      '-r', '16000',                   // 16kHz 采样率
      '-c', '1',                       // 单声道
      '-b', '16',                      // 16-bit
      outputPath,
      'silence', '1', '0.1', `${SILENCE_THRESHOLD}%`,  // 静默检测
      '1', `${SILENCE_SECONDS}`, `${SILENCE_THRESHOLD}%`  // 静默N秒停止
    ], { timeout: (maxSeconds + 5) * 1000 });

    let stderr = '';
    sox.stderr.on('data', d => stderr += d.toString());

    sox.on('close', code => {
      if (code === 0 || stderr.includes('done')) {
        resolve(outputPath);
      } else {
        reject(new Error(`sox exited ${code}: ${stderr}`));
      }
    });

    sox.on('error', reject);
  });
}

// ====== 语音转文字（Chrome Web Speech API） ======
async function transcribe(audioPath) {
  // 用 PowerShell 调用 System.Speech 做识别
  // 这是唯一能在本地离线工作的方案
  const psScript = `
Add-Type -AssemblyName System.Speech
\$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
\$recognizer.SetInputToWaveFile('${audioPath.replace(/\\/g, '\\\\')}')
\$recognizer.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
try {
  \$result = \$recognizer.Recognize()
  if (\$result) { Write-Output \$result.Text }
} catch { }
\$recognizer.Dispose()
`;
  try {
    const result = execSync(`powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "${psScript.replace(/"/g, '\\"')}"`, {
      encoding: 'utf-8',
      timeout: 30000
    });
    return result.trim();
  } catch (e) {
    console.error('Transcription error:', e.message);
    return '';
  }
}

// ====== 粘贴到当前窗口 ======
function pasteText(text) {
  const psScript = `
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Clipboard]::SetText([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("${Buffer.from(text, 'utf-8').toString('base64')}")))

Add-Type @'
using System;
using System.Runtime.InteropServices;
public class KB {
    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
}
'@

Start-Sleep -Milliseconds 300
[KB]::keybd_event(0x11, 0, 0, [UIntPtr]::Zero)
[KB]::keybd_event(0x56, 0, 0, [UIntPtr]::Zero)
Start-Sleep -Milliseconds 60
[KB]::keybd_event(0x56, 0, 2, [UIntPtr]::Zero)
[KB]::keybd_event(0x11, 0, 2, [UIntPtr]::Zero)
`;
  try {
    execSync(`powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "${psScript.replace(/"/g, '\\"')}"`, {
      timeout: 5000, windowsHide: true
    });
    return true;
  } catch (e) {
    console.error('Paste error:', e.message);
    return false;
  }
}

// ====== 主流程 ======
async function main() {
  console.log('🎤 开始录音…（说完停顿 ' + SILENCE_SECONDS + ' 秒自动结束）');

  const tmpFile = path.join(os.tmpdir(), 'voicetype-' + Date.now() + '.wav');

  try {
    // 1. 录音
    await recordAudio(tmpFile, RECORD_SECONDS);
    console.log('✓ 录音完成，正在识别…');

    // 2. 检查文件大小
    const stats = fs.statSync(tmpFile);
    if (stats.size < 1000) {
      console.log('⚠ 录音太短或无声音');
      return;
    }

    // 3. 转文字
    const text = await transcribe(tmpFile);
    if (!text) {
      console.log('⚠ 未能识别到文字');
      return;
    }
    console.log('📝 识别: ' + text);

    // 4. 清洗
    const cleaned = cleanText(text);
    console.log('✨ 清洗后: ' + cleaned);

    // 5. 粘贴
    if (cleaned) {
      const ok = pasteText(cleaned);
      if (ok) console.log('✓ 已粘贴到光标位置');
      else console.log('✗ 粘贴失败');
    }

  } catch (e) {
    console.error('Error:', e.message);
  } finally {
    // 清理临时文件
    try { fs.unlinkSync(tmpFile); } catch(e) {}
  }
}

main();
