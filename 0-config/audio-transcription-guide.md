---
name: audio-transcription-guide
description: Windows 本地中文语音转录方案，FunASR SenseVoiceSmall + ct-punc 为第一方案，faster-whisper 为备选
metadata: 
  node_type: memory
  type: reference
  originSessionId: 67f2dda4-e991-4bc0-bb1a-1567b24f8f2e
---

## 转录方案（优先级）

### 第一方案：FunASR SenseVoiceSmall + ct-punc（稳定）

**纯本地，零 token，已验证稳定。**

- SenseVoiceSmall：语音→裸文本（无标点），893MB，缓存于 `C:\Users\Administrator\.cache\modelscope\hub\models\iic\SenseVoiceSmall`
- ct-punc：裸文本→加标点，1.05GB，缓存于 `C:\Users\Administrator\.cache\modelscope\hub\models\iic\punc_ct-transformer_cn-en-common-vocab471067-large`

### 备选方案：faster-whisper

自带标点，但 HuggingFace 被墙，模型下载未解决。
模型：`Systran/faster-distil-whisper-large-v3.5`（~756MB）
目标路径：`~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-large-v3.5/`

## 环境

- Python 3.12：`C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`
- 核心依赖（系统级安装）：`funasr torch torchaudio librosa soundfile modelscope`
- Bash 中调用用完整路径：`"C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe"`

## 标准转录流程

### 步骤 1：语音识别（SenseVoiceSmall，60s 分块）

```python
import librosa, soundfile as sf, os, tempfile
from funasr import AutoModel

mp3_path = "音频文件.mp3"
audio, sr = librosa.load(mp3_path, sr=16000)  # 必须用 librosa 重采样到 16kHz

model = AutoModel(
    model='C:/Users/Administrator/.cache/modelscope/hub/models/iic/SenseVoiceSmall',
    disable_update=True
)

target_sr = 16000
chunk_seconds = 60  # 60 秒分块，防 OOM
chunk_samples = chunk_seconds * target_sr

tmp_dir = tempfile.mkdtemp()
all_text = []

for i in range(0, len(audio), chunk_samples):
    chunk = audio[i:i + chunk_samples]
    tmp_path = os.path.join(tmp_dir, f"chunk_{i}.wav")
    sf.write(tmp_path, chunk, target_sr)
    r = model.generate(input=tmp_path)
    text = r[0]['text'] if r else ''
    # 清洗 SenseVoice 标签
    text = text.replace('<|nospeech|>','').replace('<|EMO_UNKNOWN|>','')
    for tag in ['<|zh|>', '<|NEUTRAL|>', '<|HAPPY|>', '<|ANGRY|>', '<|Speech|>']:
        text = text.replace(tag, '')
    if text.strip():
        all_text.append(text.strip())

raw_text = ''.join(all_text)

# 保存裸文本
with open('transcript_no_punc.txt', 'w', encoding='utf-8') as f:
    f.write(raw_text)
```

### 步骤 2：标点恢复（ct-punc）

```python
from funasr import AutoModel

punc_model = AutoModel(model='ct-punc')

with open('transcript_no_punc.txt', 'r', encoding='utf-8') as f:
    raw_text = f.read()

result = punc_model.generate(input=raw_text)
punctuated = result[0]['text'] if result else raw_text

with open('transcript.txt', 'w', encoding='utf-8') as f:
    f.write(punctuated)
```

### 步骤 3：导出 Word（docx-js）

```javascript
const { Document, Packer, Paragraph, TextRun } = require('docx');
const fs = require('fs');

const text = fs.readFileSync('transcript.txt', 'utf-8');
const segments = text.split(/(?<=[。！？])/);

const paragraphs = segments
    .map(s => s.trim())
    .filter(s => s)
    .map(s => new Paragraph({
        spacing: { after: 120 },
        children: [new TextRun({ text: s, font: "Microsoft YaHei", size: 24 })]
    }));

const doc = new Document({
    styles: { default: { document: { run: { font: "Microsoft YaHei", size: 24 } } } },
    sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } }, children: paragraphs }]
});

Packer.toBuffer(doc).then(b => fs.writeFileSync('transcript.docx', b));
```

注意：docx 模块全局安装（`npm install -g docx`），bash 中调用需设置 `NODE_PATH`：
```bash
NODE_PATH="C:/Users/Administrator/AppData/Roaming/npm/node_modules" node script.js
```

## 踩坑记录

| ❌ 问题 | 原因 | ✅ 修复 |
|----------|------|----------|
| SenseVoice 整段转录 OOM | 长音频自注意力 O(n²)，59min 尝试分配 55GB | 60s 分块处理 |
| 采样率错误（全是噪声标签） | sf.read 读 44100 当 16000 写 | 用 librosa.load(sr=16000) 重采样 |
| 输出无标点 | SenseVoiceSmall 不输出标点，`use_itn=True` 也无用 | 单独用 ct-punc 模型后处理 |
| faster-whisper 模型下载失败 | HuggingFace + hf-mirror 均被墙 | 降级为备选方案 |
| Paraformer large 模型 404 | ModelScope 上模型 ID 失效 | 放弃，用 SenseVoiceSmall |
| venv bin/ vs Scripts/ | Windows venv 目录结构不同 | 改为系统级 pip 安装 |
| Bash 中 python3 指向 Windows Store 桩 | Windows Store 版是重定向 | 创建 wrapper：`~/bin/python3` → 真实 Python 3.12 |

## 性能参考

| 指标 | 数值 |
|------|------|
| SenseVoiceSmall | 893MB，~0.12 RTF（CPU） |
| ct-punc | 1.05GB，~7s 处理 5000 字 |
| 59min 音频完整流程 | ~10-15 分钟（含标点恢复） |
| Token 消耗 | **零**（纯本地 CPU） |
| 支持格式 | mp3 / wav / m4a / flac / mp4 / mkv（librosa 读取） |
