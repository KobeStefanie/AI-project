# -*- coding: utf-8 -*-
"""将 小圆筒生产单术语科普.md 转为带表格、页码的 PDF"""
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册中文字体（微软雅黑）
pdfmetrics.registerFont(TTFont('msyh', r'C:\Windows\Fonts\msyh.ttc'))
pdfmetrics.registerFont(TTFont('msyhbd', r'C:\Windows\Fonts\msyhbd.ttc'))
FONT = 'msyh'
FONT_BD = 'msyhbd'

SRC = r'd:\AI-项目\12-成本控制\织造部成本核算\小圆筒生产单术语科普.md'
OUT = r'd:\AI-项目\12-成本控制\织造部成本核算\小圆筒生产单术语科普.pdf'


def clean_text(text):
    """清理markdown格式符号，保留列表和换行结构"""
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)   # 粗体
    text = re.sub(r'\*([^*]+)\*', r'\1', text)         # 斜体
    text = text.replace('`', '')                        # 代码标记
    text = re.sub(r'^#+\s+', '', text)                 # 标题标记
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text


# 样式
styles = getSampleStyleSheet()
title_style = ParagraphStyle('T', fontName=FONT_BD, fontSize=20, leading=28,
                             textColor=colors.HexColor('#2c3e50'), spaceAfter=10)
h2_style = ParagraphStyle('H2', fontName=FONT_BD, fontSize=15, leading=22,
                          textColor=colors.HexColor('#2c3e50'), spaceBefore=12, spaceAfter=6)
h3_style = ParagraphStyle('H3', fontName=FONT_BD, fontSize=12.5, leading=19,
                          textColor=colors.HexColor('#34495e'), spaceBefore=8, spaceAfter=4)
body_style = ParagraphStyle('B', fontName=FONT, fontSize=10.5, leading=17,
                            textColor=colors.HexColor('#2c3e50'))
cell_style = ParagraphStyle('C', fontName=FONT, fontSize=9.5, leading=13,
                            textColor=colors.HexColor('#2c3e50'))
cell_hd_style = ParagraphStyle('CH', fontName=FONT_BD, fontSize=9.5, leading=13,
                               textColor=colors.HexColor('#2c3e50'))


def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    canvas.setFont(FONT, 9)
    canvas.setFillColor(colors.HexColor('#7f8c8d'))
    canvas.drawCentredString(A4[0] / 2, 20, f"第 {page_num} 页")


def build_table(rows):
    """rows: 二维字符串列表，第一行为表头"""
    data = []
    for i, row in enumerate(rows):
        style = cell_hd_style if i == 0 else cell_style
        data.append([Paragraph(clean_text(c), style) for c in row])
    ncol = len(rows[0])
    t = Table(data, colWidths=[16 * cm / ncol] * ncol, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


# 读取并逐行解析
with open(SRC, encoding='utf-8') as f:
    lines = f.read().split('\n')

story = []
i = 0
n = len(lines)
while i < n:
    line = lines[i]
    stripped = line.strip()

    # 表格：连续以 | 开头的行
    if stripped.startswith('|'):
        table_lines = []
        while i < n and lines[i].strip().startswith('|'):
            table_lines.append(lines[i].strip())
            i += 1
        rows = []
        for tl in table_lines:
            cells = [c.strip() for c in tl.strip('|').split('|')]
            # 跳过分隔行 |---|---|
            if all(re.fullmatch(r':?-+:?', c) for c in cells):
                continue
            rows.append(cells)
        if rows:
            story.append(Spacer(1, 0.15 * cm))
            story.append(build_table(rows))
            story.append(Spacer(1, 0.25 * cm))
        continue

    if stripped.startswith('# '):
        story.append(Paragraph(clean_text(stripped[2:]), title_style))
    elif stripped.startswith('### '):
        story.append(Paragraph(clean_text(stripped[4:]), h3_style))
    elif stripped.startswith('## '):
        story.append(Paragraph(clean_text(stripped[3:]), h2_style))
    elif not stripped:
        story.append(Spacer(1, 0.15 * cm))
    else:
        story.append(Paragraph(clean_text(stripped), body_style))
    i += 1

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=2 * cm, bottomMargin=3.5 * cm)
doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
print('OK ->', OUT)
