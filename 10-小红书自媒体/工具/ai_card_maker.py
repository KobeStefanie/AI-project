#!/usr/bin/env python3
"""
AI图文卡片生成工具（gpt-image-2版）
用法: python ai_card_maker.py <脚本文件.md>
输出: 输出/<日期-标题>-ai/ card_01.png ... + post.txt
"""

import re, sys, os, json, base64, time
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "requests", "-q"])
    import requests

# ── API配置 ──
API_BASE  = "https://www.catkingai.com"
API_KEY   = "sk-fd569d7e4f99c83b13c626a56b9b6b5d6630805e195967ba4405c45669c7b7f1"
MODEL     = "gpt-image-2"
IMG_SIZE  = "1024x1536"   # 2:3 接近小红书标准

BASE_DIR   = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "输出"

# ── 卡片风格基底（所有卡片共享）──
STYLE_BASE = (
    "小红书图文卡片，竖版，极简治愈风格，无边框，"
    "温暖奶油米白色系背景，深色中文文字，"
    "字体清晰可读，四周留白充足，"
    "右下角有一个极简线条风格的坐姿小人剪影，像是一个人独自坐在墙角，"
    "小人下方有小字'角落先生'作为品牌签名，"
    "类似日式轻杂志质感"
)

# ── 每种卡片类型的视觉风格 ──
CARD_STYLES = {
    "cover": (
        "封面卡，背景略有渐变（米白到浅杏色），"
        "中央超大字体，字体占画面50%，"
        "顶部小字账号名「角落先生」，"
        "底部极小字「向右滑动」，"
        "有设计感的轻盈构图"
    ),
    "content": (
        "内容卡，纯净白底，"
        "文字左对齐，字号适中，行间距宽松，"
        "顶部一条细线分隔，"
        "呼吸感强，留白大"
    ),
    "cta": (
        "结尾互动卡，米色暖底，"
        "中央装饰性大引号，"
        "文字居中，温柔有力，"
        "底部账号引导「关注·角落先生」，"
        "温暖邀请感"
    ),
}


def log(msg: str):
    print(msg.encode("gbk", errors="replace").decode("gbk"))


def parse_script(md_path: Path):
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"## 脚本正文.*?\n\n(.*?)(?=\n---|\n##|$)", text, re.DOTALL)
    if not m:
        raise ValueError("未找到'## 脚本正文'段落")
    return [l.strip() for l in m.group(1).split("\n") if l.strip()]


def parse_post(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"### 小红书\n```(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def build_prompt(card_type: str, text_lines: list) -> str:
    """构建每张卡片的生成提示词"""
    text_content = "，".join(text_lines)
    card_style = CARD_STYLES.get(card_type, CARD_STYLES["content"])
    return (
        f"{STYLE_BASE}，{card_style}。"
        f"卡片上显示以下中文文字：「{text_content}」。"
        f"文字必须清晰完整地显示在卡片上，不能截断。"
    )


def generate_image(prompt: str, output_path: Path) -> bool:
    """调用gpt-image-2生成图片"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": IMG_SIZE,
        "n": 1,
        "response_format": "b64_json",
    }
    try:
        resp = requests.post(
            f"{API_BASE}/v1/images/generations",
            headers=headers,
            json=payload,
            timeout=300,
        )
        data = resp.json()
        if "data" in data and data["data"]:
            b64 = data["data"][0].get("b64_json", "")
            if b64:
                output_path.write_bytes(base64.b64decode(b64))
                return True
        log(f"  API错误: {str(data)[:200]}")
        return False
    except Exception as e:
        log(f"  请求失败: {e}")
        return False


def main(md_path_str: str):
    md_path = Path(md_path_str)
    if not md_path.exists():
        log(f"文件不存在: {md_path}"); sys.exit(1)

    stem = re.sub(r'^\d{8}-', '', md_path.stem)
    out_dir = OUTPUT_DIR / f"{datetime.now().strftime('%Y%m%d')}-{stem}-ai"
    out_dir.mkdir(parents=True, exist_ok=True)

    log(f"\n[读取脚本] {md_path.name}")
    lines = parse_script(md_path)
    post  = parse_post(md_path)

    # 分配卡片：封面1张 + 内容每2句1张 + CTA最后1句
    content_lines = lines[:-1]
    cta_line = lines[-1]
    chunks = [content_lines[i:i+2] for i in range(0, len(content_lines), 2)]

    cards = []
    cards.append(("cover",   [lines[0]]))
    for chunk in chunks:
        cards.append(("content", chunk))
    cards.append(("cta", [cta_line]))

    log(f"[规划卡片] 共 {len(cards)} 张：封面1 + 内容{len(chunks)} + CTA1")
    log(f"[开始生成] 每张约30-60秒...\n")

    success = 0
    for i, (card_type, text_lines) in enumerate(cards, 1):
        out_path = out_dir / f"card_{i:02d}.png"
        prompt = build_prompt(card_type, text_lines)
        log(f"  [{i}/{len(cards)}] {card_type}: {' / '.join(text_lines)[:30]}...")
        if generate_image(prompt, out_path):
            log(f"       -> {out_path.name}")
            success += 1
        else:
            log(f"       -> 失败，跳过")
        time.sleep(1)   # 避免限速

    # 保存发布文案
    if post:
        (out_dir / "post.txt").write_text(post, encoding="utf-8")

    log(f"\n完成！{success}/{len(cards)} 张生成成功")
    log(f"输出目录: {out_dir}")
    os.startfile(out_dir)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python ai_card_maker.py <脚本.md>")
        sys.exit(1)
    main(sys.argv[1])
