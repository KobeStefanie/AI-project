# -*- coding: utf-8 -*-
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# 注册中文字体
FONT_PATH = r'C:\Windows\Fonts\msyh.ttc'
FONT_NAME = 'msyh'
FONT_NAME_BOLD = 'msyh'

try:
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
    pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, FONT_PATH))
except:
    print(f"字体注册失败: {FONT_PATH}")
    exit(1)

def clean_text(text):
    """清理markdown格式符号"""
    # 移除粗体
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    # 移除斜体
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # 移除代码标记
    text = text.replace('`', '')
    # 移除标题标记
    text = re.sub(r'^#+\s+', '', text)
    # 转义XML特殊字符
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text

def add_page_number(canvas_obj, doc):
    """添加页码"""
    page_num = canvas_obj.getPageNumber()
    text = f"第 {page_num} 页"
    canvas_obj.setFont(FONT_NAME, 9)
    canvas_obj.setFillColor(colors.HexColor('#7f8c8d'))
    canvas_obj.drawCentredString(A4[0] / 2, 20, text)

# 读取markdown文件
input_file = 'd:/AI-项目/1-我的剧本/02-心理探索/阶段性整合/治疗师整体评估-50天回顾-20260830.md'
output_file = 'd:/AI-项目/1-我的剧本/02-心理探索/阶段性整合/治疗师整体评估-50天回顾-20260830.pdf'

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 创建PDF
doc = SimpleDocTemplate(
    output_file,
    pagesize=A4,
    topMargin=2.5*cm,
    bottomMargin=3.5*cm,
    leftMargin=2*cm,
    rightMargin=2*cm
)

# 定义样式
title_style = ParagraphStyle(
    'Title',
    fontName=FONT_NAME_BOLD,
    fontSize=18,
    textColor=colors.HexColor('#2c3e50'),
    spaceAfter=0.3*cm,
    alignment=TA_CENTER
)

h2_style = ParagraphStyle(
    'Heading2',
    fontName=FONT_NAME_BOLD,
    fontSize=14,
    textColor=colors.HexColor('#34495e'),
    spaceAfter=0.2*cm,
    spaceBefore=0.4*cm
)

h3_style = ParagraphStyle(
    'Heading3',
    fontName=FONT_NAME_BOLD,
    fontSize=12,
    textColor=colors.HexColor('#34495e'),
    spaceAfter=0.15*cm,
    spaceBefore=0.3*cm
)

body_style = ParagraphStyle(
    'Body',
    fontName=FONT_NAME,
    fontSize=10,
    textColor=colors.HexColor('#34495e'),
    leading=14,
    spaceAfter=0.1*cm
)

code_style = ParagraphStyle(
    'Code',
    fontName=FONT_NAME,
    fontSize=9,
    textColor=colors.HexColor('#2c3e50'),
    leading=12,
    leftIndent=1*cm,
    spaceAfter=0.2*cm,
    spaceBefore=0.2*cm
)

story = []

# 解析内容
lines = content.split('\n')
in_code_block = False
code_content = []

for line in lines:
    stripped = line.strip()

    # 代码块处理
    if stripped.startswith('```'):
        if in_code_block:
            # 结束代码块
            if code_content:
                code_text = '\n'.join(code_content)
                cleaned = clean_text(code_text)
                story.append(Paragraph(cleaned, code_style))
            code_content = []
            in_code_block = False
        else:
            # 开始代码块
            in_code_block = True
        continue

    if in_code_block:
        code_content.append(line)
        continue

    # 跳过分隔线
    if stripped.startswith('---'):
        story.append(Spacer(1, 0.3*cm))
        continue

    # 一级标题
    if stripped.startswith('# '):
        text = clean_text(stripped[2:])
        story.append(Paragraph(text, title_style))
        story.append(Spacer(1, 0.3*cm))
        continue

    # 二级标题
    if stripped.startswith('## '):
        text = clean_text(stripped[3:])
        story.append(Paragraph(text, h2_style))
        continue

    # 三级标题
    if stripped.startswith('### '):
        text = clean_text(stripped[4:])
        story.append(Paragraph(text, h3_style))
        continue

    # 空行
    if not stripped:
        story.append(Spacer(1, 0.2*cm))
        continue

    # 普通文本
    cleaned = clean_text(stripped)
    if cleaned:
        story.append(Paragraph(cleaned, body_style))

# 构建PDF
print("正在生成PDF...")
doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
print(f"PDF生成成功: {output_file}")
