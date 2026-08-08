#!/usr/bin/env python3
"""
小红书图文卡片一键生成工具
用法: python card_maker.py <脚本文件.md>
输出: 输出/<日期-标题>/card_01.png ... card_N.png + post.txt
"""

import re, sys, os, textwrap
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ── 路径 ──
BASE_DIR   = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "输出"
FONT       = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD  = r"C:\Windows\Fonts\msyhbd.ttc"

# ── 卡片尺寸（小红书标准 3:4）──
W, H = 1080, 1440

# ── 配色方案 ──
PALETTE = {
    "cover_bg":    "#2C3E50",   # 封面：深蓝灰
    "cover_text":  "#FFFFFF",
    "cover_sub":   "#A8BCC8",
    "card_bg":     "#FAF8F5",   # 正文：暖白
    "card_text":   "#2C2C2C",
    "card_muted":  "#888888",
    "card_accent": "#5B7FA6",   # 强调色（冷静蓝）
    "cta_bg":      "#F0EDE8",   # 尾页：米色
    "cta_text":    "#2C2C2C",
    "divider":     "#D8D0C8",
    "watermark":   "#BBBBBB",
}

# ── 字号 ──
FS = {
    "cover_main": 78,
    "cover_sub":  38,
    "body":       52,
    "body_sm":    44,
    "label":      34,
    "watermark":  30,
}

MARGIN   = 88
MAX_CHARS = 13  # 每行最多字符数（正文）
ACCOUNT  = "心理咨询手记"


# ──────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────
def load_font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_BOLD if bold else FONT, size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(text, max_chars=MAX_CHARS):
    """中文换行：优先在标点处断行，超长时才截断"""
    # 先按标点切分
    import re
    parts = re.split(r'([，。！？…——])', text)
    segments = []
    buf = ""
    for p in parts:
        buf += p
        if p in "，。！？…——" or len(buf) >= max_chars:
            if buf.strip():
                segments.append(buf.strip())
            buf = ""
    if buf.strip():
        segments.append(buf.strip())
    # 合并太短的碎片（<3字）到上一段
    merged = []
    for s in segments:
        if merged and len(s) < 3:
            merged[-1] += s
        else:
            merged.append(s)
    return merged if merged else [text]


def draw_text_block(draw, lines, font, color, x, y, line_gap=None):
    """逐行渲染，返回总高度"""
    lh = font.size + (line_gap or int(font.size * 0.55))
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += lh
    return len(lines) * lh


def text_center_x(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return (W - (bb[2] - bb[0])) // 2


def add_watermark(draw, font):
    f = load_font(FS["watermark"])
    bb = draw.textbbox((0, 0), ACCOUNT, font=f)
    x = (W - (bb[2] - bb[0])) // 2
    draw.text((x, H - 60), ACCOUNT, font=f, fill=PALETTE["watermark"])


def parse_script(md_path: Path):
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"## 脚本正文.*?\n\n(.*?)(?=\n---|\n##|$)", text, re.DOTALL)
    if not m:
        raise ValueError("未找到'## 脚本正文'段落")
    lines = [l.strip() for l in m.group(1).split("\n") if l.strip()]
    return lines


def parse_post(md_path: Path):
    """提取小红书发布文案"""
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"### 小红书\n```(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else ""


# ──────────────────────────────────────────
# 卡片绘制
# ──────────────────────────────────────────
def make_cover(hook_line: str, index_label: str = "") -> Image.Image:
    """封面卡：温暖治愈的浅色背景"""
    # 温暖渐变背景（米白到浅杏色）
    img  = Image.new("RGB", (W, H), "#F5EFE6")
    draw = ImageDraw.Draw(img)

    # 画渐变（简化版：顶部浅，底部稍深）
    for i in range(H):
        ratio = i / H
        r = int(245 - ratio * 10)
        g = int(239 - ratio * 15)
        b = int(230 - ratio * 20)
        draw.rectangle([(0, i), (W, i+1)], fill=(r, g, b))

    # 顶部圆角矩形装饰
    draw.rounded_rectangle([(MARGIN, 90), (W - MARGIN, 170)],
                          radius=12, fill="#E8DCC8", outline=None)

    # 账号名（在装饰框内）
    f_sm = load_font(FS["label"], bold=True)
    bb = draw.textbbox((0, 0), ACCOUNT, font=f_sm)
    x = (W - (bb[2] - bb[0])) // 2
    draw.text((x, 118), ACCOUNT, font=f_sm, fill="#6B5B4F")

    # 主标题（居中，深色文字）
    f_big = load_font(FS["cover_main"], bold=True)
    lines = wrap_text(hook_line, 10)
    lh = FS["cover_main"] + 28
    total_h = len(lines) * lh
    y = (H - total_h) // 2 + 20
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=f_big)
        x = (W - (bb[2] - bb[0])) // 2
        draw.text((x, y), line, font=f_big, fill="#2C2C2C")
        y += lh

    # 底部波浪装饰 + 提示
    wave_y = H - 200
    draw.arc([(MARGIN-20, wave_y), (W//2, wave_y+40)], 0, 180, fill="#D8CFC1", width=3)
    draw.arc([(W//2, wave_y), (W-MARGIN+20, wave_y+40)], 0, 180, fill="#D8CFC1", width=3)

    f_hint = load_font(FS["label"])
    hint = "向右滑动 →"
    bb = draw.textbbox((0, 0), hint, font=f_hint)
    draw.text(((W - (bb[2] - bb[0])) // 2, H - 130), hint,
              font=f_hint, fill="#999999")
    return img


def make_content(lines_in_card: list, card_no: int, total: int) -> Image.Image:
    """正文卡：暖白背景，正文文字"""
    img  = Image.new("RGB", (W, H), PALETTE["card_bg"])
    draw = ImageDraw.Draw(img)

    # 顶部进度点
    dot_r, dot_gap, dot_y = 6, 20, 72
    total_dot_w = total * (dot_r * 2 + dot_gap) - dot_gap
    sx = (W - total_dot_w) // 2
    for i in range(total):
        cx = sx + i * (dot_r * 2 + dot_gap) + dot_r
        color = PALETTE["card_accent"] if i == card_no - 1 else PALETTE["divider"]
        draw.ellipse([cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r], fill=color)

    # 分割线
    draw.rectangle([(MARGIN, 108), (W - MARGIN, 111)], fill=PALETTE["divider"])

    # 正文
    f_body = load_font(FS["body"])
    y = 190
    lh = FS["body"] + int(FS["body"] * 0.6)
    for sentence in lines_in_card:
        wrapped = wrap_text(sentence, MAX_CHARS)
        for wl in wrapped:
            draw.text((MARGIN, y), wl, font=f_body, fill=PALETTE["card_text"])
            y += lh
        y += int(FS["body"] * 0.4)   # 句间额外间距

    add_watermark(draw, f_body)
    return img


def make_cta(cta_line: str) -> Image.Image:
    """尾页：米色背景 + CTA + 账号引导"""
    img  = Image.new("RGB", (W, H), PALETTE["cta_bg"])
    draw = ImageDraw.Draw(img)

    f_body = load_font(FS["body"])
    f_big  = load_font(FS["cover_main"], bold=True)
    f_sm   = load_font(FS["label"])

    # 大引号装饰
    draw.text((MARGIN - 10, H // 2 - 220), "“", font=f_big,
              fill=PALETTE["divider"])

    # CTA 文字
    lines = wrap_text(cta_line, MAX_CHARS)
    lh = FS["body"] + int(FS["body"] * 0.6)
    y  = H // 2 - 100
    for line in lines:
        draw.text((MARGIN + 40, y), line, font=f_body, fill=PALETTE["card_text"])
        y += lh

    # 分割线
    draw.rectangle([(MARGIN, y + 30), (W - MARGIN, y + 33)], fill=PALETTE["divider"])

    # 账号 + 引导
    draw.text((MARGIN, y + 60), ACCOUNT, font=f_sm, fill=PALETTE["card_accent"])
    draw.text((MARGIN, y + 110), "关注 · 获取更多心理洞察", font=f_sm,
              fill=PALETTE["card_muted"])
    return img


# ──────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────
def generate_cards(md_path: Path):
    lines = parse_script(md_path)
    post  = parse_post(md_path)

    content_lines = lines[:-1]
    cta_line      = lines[-1]
    chunks = [content_lines[i:i+2] for i in range(0, len(content_lines), 2)]
    total_cards = 1 + len(chunks) + 1

    cards = []
    cards.append(make_cover(lines[0]))
    for i, chunk in enumerate(chunks):
        cards.append(make_content(chunk, i + 2, total_cards))
    cards.append(make_cta(cta_line))
    return cards, post


def log(msg):
    print(msg.encode("gbk", errors="replace").decode("gbk"))


def main(md_path_str: str):
    md_path = Path(md_path_str)
    if not md_path.exists():
        log(f"[错误] 文件不存在: {md_path}"); sys.exit(1)

    stem = md_path.stem
    if re.match(r'^\d{8}-', stem):
        stem = re.sub(r'^\d{8}-', '', stem)
    out_dir = OUTPUT_DIR / f"{datetime.now().strftime('%Y%m%d')}-{stem}-cards"
    out_dir.mkdir(parents=True, exist_ok=True)

    log(f"[1/2] 生成卡片: {md_path.name}")
    cards, post = generate_cards(md_path)

    for i, card in enumerate(cards, 1):
        p = out_dir / f"card_{i:02d}.png"
        card.save(p, "PNG")
        log(f"      card_{i:02d}.png")

    post_path = out_dir / "post.txt"
    if post:
        post_path.write_text(post, encoding="utf-8")
        log(f"[2/2] 发布文案已保存: post.txt")
    else:
        log(f"[2/2] 未找到小红书文案（可从脚本文件手动复制）")

    log(f"\n完成！共 {len(cards)} 张卡片 -> {out_dir}")
    os.startfile(out_dir)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python card_maker.py <脚本.md>")
        print("示例: python card_maker.py ../2-脚本/2026/07/20260717-她说没事.md")
        sys.exit(1)
    main(sys.argv[1])
