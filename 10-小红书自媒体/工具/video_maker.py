#!/usr/bin/env python3
"""
心理学短视频自动生成工具
用法: python video_maker.py <脚本文件.md>
输出: 输出/<日期-标题>/video.mp4 + cover.png
"""

import asyncio
import os
import re
import sys
import random
import subprocess
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ── 路径配置 ──
BASE_DIR   = Path(__file__).parent.parent
TOOLS_DIR  = Path(__file__).parent
ASSETS_DIR = TOOLS_DIR / "assets"
BG_DIR     = ASSETS_DIR / "backgrounds"
OUTPUT_DIR = BASE_DIR / "输出"
FFMPEG     = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

# ── 视频参数 ──
W, H = 1080, 1920
FPS  = 30
VOICE = "zh-CN-XiaoxiaoNeural"   # 换男声: zh-CN-YunxiNeural
FONT  = r"C:\Windows\Fonts\msyh.ttc"


# ──────────────────────────────────────────
# 1. 解析脚本
# ──────────────────────────────────────────
def parse_script(md_path: Path):
    """从 .md 文件提取配音文本，返回行列表"""
    text = md_path.read_text(encoding="utf-8")
    match = re.search(r"## 脚本正文.*?\n\n(.*?)(?=\n---|\n##|$)", text, re.DOTALL)
    if not match:
        raise ValueError(f"未找到'## 脚本正文'段落，请检查文件格式：{md_path}")
    lines = [l.strip() for l in match.group(1).split("\n") if l.strip()]
    return lines


# ──────────────────────────────────────────
# 2. TTS 配音（带词语时间戳）
# ──────────────────────────────────────────
async def generate_tts(lines: list, out_dir: Path):
    """生成配音 MP3，同时收集词语时间戳用于字幕对齐"""
    full_text = "\n".join(lines)
    audio_path = out_dir / "voice.mp3"
    communicate = edge_tts.Communicate(full_text, VOICE)
    word_events = []
    audio_chunks = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            word_events.append({
                "offset":   chunk["offset"]   / 1e7,
                "duration": chunk["duration"] / 1e7,
                "text":     chunk["text"],
            })

    audio_path.write_bytes(b"".join(audio_chunks))
    return audio_path, word_events


# ──────────────────────────────────────────
# 3. 字幕对齐
# ──────────────────────────────────────────
def words_to_subtitles(word_events: list, lines: list, total_duration: float):
    """将词语时间戳映射到脚本行，降级时按字数均分"""
    if not word_events:
        # 降级：按字数比例分配时间
        total_chars = sum(len(l) for l in lines) or 1
        t, subs = 0.0, []
        for line in lines:
            d = total_duration * len(line) / total_chars
            subs.append({"start": t, "end": t + d, "text": line})
            t += d
        return subs

    # 把 word_events 拼成一个大字符串，逐行贪心匹配
    subtitles, wi = [], 0
    for line in lines:
        if wi >= len(word_events):
            break
        start = word_events[wi]["offset"]
        matched, remaining = [], line
        while wi < len(word_events) and remaining:
            w = word_events[wi]["text"]
            if w in remaining:
                matched.append(word_events[wi])
                remaining = remaining.replace(w, "", 1)
                wi += 1
            else:
                wi += 1
        if matched:
            end = matched[-1]["offset"] + matched[-1]["duration"] + 0.15
            subtitles.append({"start": start, "end": end, "text": line})
    return subtitles


# ──────────────────────────────────────────
# 4. 写 SRT 字幕文件
# ──────────────────────────────────────────
def write_srt(subtitles: list, srt_path: Path):
    def fmt(s):
        h, m = int(s // 3600), int((s % 3600) // 60)
        sec, ms = int(s % 60), int((s % 1) * 1000)
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

    srt = ""
    for i, sub in enumerate(subtitles, 1):
        srt += f"{i}\n{fmt(sub['start'])} --> {fmt(sub['end'])}\n{sub['text']}\n\n"
    srt_path.write_text(srt, encoding="utf-8-sig")


# ──────────────────────────────────────────
# 5. 获取音频时长
# ──────────────────────────────────────────
def run_ff(cmd: list) -> subprocess.CompletedProcess:
    """统一调用 ffmpeg，返回值用 bytes 避免 GBK 解码问题"""
    return subprocess.run(cmd, capture_output=True)


def get_duration(audio_path: Path) -> float:
    result = run_ff([FFMPEG, "-i", str(audio_path), "-f", "null", "-"])
    stderr = result.stderr.decode("utf-8", errors="replace")
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    return 60.0


# ──────────────────────────────────────────
# 6. 选背景素材
# ──────────────────────────────────────────
def pick_background():
    """从 assets/backgrounds/ 随机挑一个视频；没有则返回 None（用纯色）"""
    if BG_DIR.exists():
        clips = list(BG_DIR.glob("*.mp4")) + list(BG_DIR.glob("*.mov"))
        if clips:
            return random.choice(clips)
    return None


# ──────────────────────────────────────────
# 7. ffmpeg 合成视频
# ──────────────────────────────────────────
def compose_video(audio_path: Path, srt_path: Path, bg: Path,
                  out_path: Path, duration: float):
    """两步走：1) 生成无字幕视频  2) 用 ffmpeg 烧字幕（避免路径转义问题）"""
    tmp_dir = Path(tempfile.mkdtemp())
    tmp_video = tmp_dir / "base.mp4"
    tmp_srt = tmp_dir / "sub.srt"
    shutil.copy2(srt_path, tmp_srt)

    # 第一步：生成无字幕的基础视频
    if bg:
        video_input = ["-stream_loop", "-1", "-i", str(bg)]
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    else:
        video_input = ["-f", "lavfi", "-i", f"color=c=0x1a1a2e:size={W}x{H}:rate={FPS}"]
        vf = None

    cmd1 = [FFMPEG, "-y"] + video_input + [
        "-i", str(audio_path),
        "-t", str(duration + 0.5),
    ]
    if vf:
        cmd1 += ["-vf", vf]
    cmd1 += [
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-map", "0:v", "-map", "1:a", "-shortest",
        str(tmp_video)
    ]
    result = run_ff(cmd1)
    if result.returncode != 0:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise RuntimeError("ffmpeg 第一步失败:\n" + result.stderr.decode("utf-8", errors="replace")[-1000:])

    # 第二步：烧字幕（临时目录内操作，无中文路径问题）
    tmp_final = tmp_dir / "final.mp4"
    srt_filter = (
        f"subtitles={tmp_srt.name}:force_style='"
        f"FontName=Microsoft YaHei,FontSize=52,"
        f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        f"Outline=2,Shadow=1,Bold=1,Alignment=2,MarginV=130'"
    )
    cmd2 = [
        FFMPEG, "-y", "-i", str(tmp_video),
        "-vf", srt_filter,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        str(tmp_final)
    ]
    # 在 tmp_dir 内执行，subtitles 滤镜用相对路径
    result = subprocess.run(cmd2, cwd=str(tmp_dir), capture_output=True)
    if result.returncode != 0:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise RuntimeError("ffmpeg 烧字幕失败:\n" + result.stderr.decode("utf-8", errors="replace")[-1000:])

    shutil.move(str(tmp_final), str(out_path))
    shutil.rmtree(tmp_dir, ignore_errors=True)


# ──────────────────────────────────────────
# 8. 生成封面图
# ──────────────────────────────────────────
def create_cover(first_line: str, cover_path: Path):
    img  = Image.new("RGB", (W, H), color=(26, 26, 46))
    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype(FONT, 88)
        font_sm  = ImageFont.truetype(FONT, 44)
    except Exception:
        font_big = font_sm = ImageFont.load_default()

    # 自动换行（最多14字一行）
    words = list(first_line)
    lines, cur = [], ""
    for ch in words:
        cur += ch
        if len(cur) >= 14 or ch in "，。！？":
            lines.append(cur)
            cur = ""
    if cur:
        lines.append(cur)

    y = H // 2 - len(lines) * 70
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_big)
        x = (W - (bbox[2] - bbox[0])) // 2
        # 阴影
        draw.text((x + 4, y + 4), line, font=font_big, fill=(0, 0, 0))
        draw.text((x, y), line, font=font_big, fill="white")
        y += 130

    tag = "心理咨询手记"
    bbox = draw.textbbox((0, 0), tag, font=font_sm)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, H - 180), tag,
              font=font_sm, fill=(160, 160, 180))
    img.save(cover_path)


# ──────────────────────────────────────────
# 9. 主流程
# ──────────────────────────────────────────
def log(msg):
    """兼容 GBK 终端的输出"""
    print(msg.encode("gbk", errors="replace").decode("gbk"))


async def run(md_path_str: str):
    md_path = Path(md_path_str)
    if not md_path.exists():
        log(f"[错误] 文件不存在: {md_path}"); sys.exit(1)

    title = md_path.stem
    # 如果文件名已带日期（8位数字开头），去掉避免重复
    if re.match(r'^\d{8}-', title):
        title = re.sub(r'^\d{8}-', '', title)
    out_dir = OUTPUT_DIR / f"{datetime.now().strftime('%Y%m%d')}-{title}"
    out_dir.mkdir(parents=True, exist_ok=True)
    BG_DIR.mkdir(parents=True, exist_ok=True)

    log(f"\n[1/5] 解析脚本: {md_path.name}")
    lines = parse_script(md_path)
    log(f"      {len(lines)} 段 / {sum(len(l) for l in lines)} 字")

    log(f"[2/5] 配音生成中 ({VOICE})...")
    audio_path, word_events = await generate_tts(lines, out_dir)
    duration = get_duration(audio_path)
    log(f"      时长: {duration:.1f}s")

    log(f"[3/5] 字幕对齐...")
    subs = words_to_subtitles(word_events, lines, duration)
    srt_path = out_dir / "subtitles.srt"
    write_srt(subs, srt_path)
    log(f"      {len(subs)} 条字幕")

    bg = pick_background()
    bg_desc = f"背景: {bg.name}" if bg else "纯色背景（可在 工具/assets/backgrounds/ 放入 .mp4 素材）"
    log(f"[4/5] 合成视频 ({bg_desc})...")
    video_path = out_dir / "video.mp4"
    compose_video(audio_path, srt_path, bg, video_path, duration)
    log(f"      完成: {video_path.name}")

    log(f"[5/5] 生成封面...")
    create_cover(lines[0], out_dir / "cover.png")

    log(f"\n完成！输出目录: {out_dir}")
    os.startfile(out_dir)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python video_maker.py <脚本.md>")
        print("示例: python video_maker.py ../2-脚本/2026/07/20260717-她说没事.md")
        sys.exit(1)
    asyncio.run(run(sys.argv[1]))
