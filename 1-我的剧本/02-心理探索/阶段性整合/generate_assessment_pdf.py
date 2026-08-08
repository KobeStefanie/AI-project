# -*- coding: utf-8 -*-
"""生成阶段性治疗师评估 PDF"""

import re
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 字体注册 ---
FONT_NAME = 'MicrosoftYaHei'
FONT_NAME_BOLD = 'MicrosoftYaHeiBold'
pdfmetrics.registerFont(TTFont(FONT_NAME, 'C:/Windows/Fonts/msyh.ttc'))
pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, 'C:/Windows/Fonts/msyhbd.ttc'))

# --- 文件路径 ---
BASE_DIR = r"d:\AI-项目\1-我的剧本\02-心理探索"
MD_FILE  = os.path.join(BASE_DIR, "阶段性治疗师评估-20260714.md")
PDF_FILE = os.path.join(BASE_DIR, "阶段性治疗师评估-20260714.pdf")

# --- 符号替换 ---
SYMBOL_MAP = {
    '✓': 'v', '✔': 'v', '✅': '[完成]',
    '✗': 'x', '✘': 'x', '❌': '[x]',
    '⚠️': '[注意]', '⚠': '[注意]',
    '→': '->', '←': '<-', '↓': '|',
    '…': '...', '​': '', '﻿': '',
    '△': '[进行中]',
}

def clean_text(text):
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    text = text.replace('`', '')
    for orig, repl in SYMBOL_MAP.items():
        text = text.replace(orig, repl)
    return text

def parse_markdown_table(lines, start_idx):
    table_lines = []
    i = start_idx
    while i < len(lines) and '|' in lines[i]:
        table_lines.append(lines[i])
        i += 1
    rows = [l for l in table_lines if not re.match(r'^\|[\s\-|:]+\|$', l.strip())]
    data = []
    for row in rows:
        cells = [c.strip() for c in row.strip().strip('|').split('|')]
        data.append(cells)
    return data, i

def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = "第 %d 页" % page_num
    canvas.setFont(FONT_NAME, 9)
    canvas.setFillColor(colors.HexColor('#7f8c8d'))
    canvas.drawCentredString(A4[0] / 2, 20, text)

def build_pdf():
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    doc = SimpleDocTemplate(
        PDF_FILE,
        pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=3.5*cm
    )

    title_style = ParagraphStyle('Title', fontName=FONT_NAME_BOLD, fontSize=18,
                                  leading=26, spaceAfter=6,
                                  textColor=colors.HexColor('#2c3e50'))
    h1_style    = ParagraphStyle('H1', fontName=FONT_NAME_BOLD, fontSize=14,
                                  leading=22, spaceBefore=14, spaceAfter=6,
                                  textColor=colors.HexColor('#2c3e50'))
    h2_style    = ParagraphStyle('H2', fontName=FONT_NAME_BOLD, fontSize=12,
                                  leading=20, spaceBefore=10, spaceAfter=4,
                                  textColor=colors.HexColor('#34495e'))
    h3_style    = ParagraphStyle('H3', fontName=FONT_NAME_BOLD, fontSize=11,
                                  leading=18, spaceBefore=8, spaceAfter=3,
                                  textColor=colors.HexColor('#555'))
    body_style  = ParagraphStyle('Body', fontName=FONT_NAME, fontSize=10,
                                  leading=18, spaceAfter=3)
    meta_style  = ParagraphStyle('Meta', fontName=FONT_NAME, fontSize=9,
                                  leading=16, textColor=colors.HexColor('#7f8c8d'))
    quote_style = ParagraphStyle('Quote', fontName=FONT_NAME, fontSize=10,
                                  leading=18, leftIndent=20, spaceAfter=4,
                                  textColor=colors.HexColor('#555'))
    table_cell  = ParagraphStyle('TableCell', fontName=FONT_NAME, fontSize=9, leading=15)
    table_head  = ParagraphStyle('TableHead', fontName=FONT_NAME_BOLD, fontSize=9, leading=15)

    story = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            story.append(Spacer(1, 0.25*cm))
            i += 1
            continue

        if re.match(r'^---+$', stripped):
            story.append(Spacer(1, 0.2*cm))
            story.append(HRFlowable(width="100%", thickness=0.5,
                                     color=colors.HexColor('#bdc3c7'), spaceAfter=6))
            i += 1
            continue

        if stripped.startswith('# ') and not stripped.startswith('## '):
            text = clean_text(stripped[2:].strip())
            story.append(Paragraph(text, title_style))
            i += 1
            continue

        if stripped.startswith('## '):
            text = clean_text(stripped[3:].strip())
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(text, h1_style))
            story.append(HRFlowable(width="100%", thickness=1,
                                     color=colors.HexColor('#2c3e50'), spaceAfter=4))
            i += 1
            continue

        if stripped.startswith('### '):
            text = clean_text(stripped[4:].strip())
            story.append(Paragraph(text, h2_style))
            i += 1
            continue

        if stripped.startswith('#### '):
            text = clean_text(stripped[5:].strip())
            story.append(Paragraph(text, h3_style))
            i += 1
            continue

        # 表格
        if stripped.startswith('|') and i + 1 < len(lines) and '|' in lines[i + 1]:
            table_data_raw, end_idx = parse_markdown_table(lines, i)
            if table_data_raw:
                table_data = []
                for row_idx, row in enumerate(table_data_raw):
                    style = table_head if row_idx == 0 else table_cell
                    table_data.append([Paragraph(clean_text(cell), style) for cell in row])
                col_count = max(len(r) for r in table_data)
                col_width = (A4[0] - 5*cm) / col_count
                t = Table(table_data, colWidths=[col_width] * col_count)
                t.setStyle(TableStyle([
                    ('FONTNAME',   (0, 0), (-1, 0), FONT_NAME_BOLD),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
                    ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [colors.white, colors.HexColor('#f8f9fa')]),
                    ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(t)
                story.append(Spacer(1, 0.3*cm))
            i = end_idx
            continue

        # 引用
        if stripped.startswith('> '):
            text = clean_text(stripped[2:].strip())
            story.append(Paragraph(text, quote_style))
            i += 1
            continue

        # 列表
        if re.match(r'^[-*]\s', stripped):
            text = clean_text(stripped[2:].strip())
            story.append(Paragraph('- ' + text, body_style))
            i += 1
            continue

        if re.match(r'^\d+\.\s', stripped):
            num = re.match(r'^(\d+)\.', stripped).group(1)
            text = clean_text(re.sub(r'^\d+\.\s', '', stripped))
            story.append(Paragraph("%s. %s" % (num, text), body_style))
            i += 1
            continue

        # 普通正文
        text = clean_text(stripped)
        if text:
            story.append(Paragraph(text, body_style))
        i += 1

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    size_kb = os.path.getsize(PDF_FILE) / 1024
    print("PDF生成成功: %s" % PDF_FILE)
    print("文件大小: %.1f KB" % size_kb)

if __name__ == '__main__':
    build_pdf()
