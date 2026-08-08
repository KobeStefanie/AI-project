#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将 Markdown 文件转换为 PDF（支持表格渲染）
使用 reportlab 库生成中文 PDF
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re

# 注册中文字体
try:
    pdfmetrics.registerFont(TTFont('msyh', 'C:/Windows/Fonts/msyh.ttc'))
    pdfmetrics.registerFont(TTFont('msyhbd', 'C:/Windows/Fonts/msyhbd.ttc'))
    FONT_NAME = 'msyh'
    FONT_NAME_BOLD = 'msyhbd'
except:
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'

def clean_text(text):
    """清理文本"""
    text = text.replace('**', '')
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def parse_markdown_to_pdf(md_file, pdf_file):
    """将 Markdown 文件转换为 PDF"""

    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    doc = SimpleDocTemplate(pdf_file, pagesize=A4,
                           rightMargin=40, leftMargin=40,
                           topMargin=40, bottomMargin=30)

    styles = getSampleStyleSheet()

    # 定义样式
    title_style = ParagraphStyle(
        'CustomTitle',
        fontName=FONT_NAME_BOLD,
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=20,
        alignment=1
    )

    h1_style = ParagraphStyle(
        'CustomH1',
        fontName=FONT_NAME_BOLD,
        fontSize=15,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=15
    )

    h2_style = ParagraphStyle(
        'CustomH2',
        fontName=FONT_NAME_BOLD,
        fontSize=13,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=12
    )

    h3_style = ParagraphStyle(
        'CustomH3',
        fontName=FONT_NAME_BOLD,
        fontSize=12,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=6,
        spaceBefore=10
    )

    body_style = ParagraphStyle(
        'CustomBody',
        fontName=FONT_NAME,
        fontSize=10.5,
        leading=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8
    )

    bold_style = ParagraphStyle(
        'CustomBold',
        fontName=FONT_NAME_BOLD,
        fontSize=10.5,
        leading=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8
    )

    quote_style = ParagraphStyle(
        'CustomQuote',
        fontName=FONT_NAME,
        fontSize=10,
        leading=15,
        leftIndent=25,
        rightIndent=25,
        textColor=colors.HexColor('#7f8c8d')
    )

    # 表格内文字样式
    table_style = ParagraphStyle(
        'TableText',
        fontName=FONT_NAME,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#2c3e50')
    )

    story = []
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # 空行
        if not line:
            story.append(Spacer(1, 0.05*inch))
            i += 1
            continue

        # 标题处理
        if line.startswith('# '):
            text = clean_text(line[2:].strip())
            story.append(Paragraph(text, title_style))
            i += 1
            continue

        if line.startswith('## '):
            text = clean_text(line[3:].strip())
            story.append(Paragraph(text, h1_style))
            i += 1
            continue

        if line.startswith('### '):
            text = clean_text(line[4:].strip())
            story.append(Paragraph(text, h2_style))
            i += 1
            continue

        # 分隔线
        if line.startswith('---'):
            story.append(Spacer(1, 0.15*inch))
            i += 1
            continue

        # 引用
        if line.startswith('>'):
            text = clean_text(line[1:].strip())
            story.append(Paragraph(text, quote_style))
            i += 1
            continue

        # 表格处理
        if line.startswith('|'):
            table_lines = []
            start_i = i

            # 收集所有表格行
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1

            # 解析表格数据
            table_data = []
            for tline in table_lines:
                # 跳过分隔线
                if re.match(r'\|[\s\-:]+\|', tline):
                    continue

                cells = [cell.strip() for cell in tline.split('|')[1:-1]]
                # 将每个单元格内容包装为 Paragraph
                cell_paragraphs = [Paragraph(clean_text(cell), table_style) for cell in cells]
                table_data.append(cell_paragraphs)

            if len(table_data) > 0:
                # 创建表格
                t = Table(table_data, colWidths=[15*cm / len(table_data[0])] * len(table_data[0]))

                # 设置表格样式
                t.setStyle(TableStyle([
                    # 表头样式
                    ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),

                    # 表格内容样式
                    ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),

                    # 对齐
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                    # 边框和网格
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#95a5a6')),

                    # 内边距
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

                    # 行背景色交替
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
                ]))

                story.append(t)
                story.append(Spacer(1, 0.2*inch))
            continue

        # 加粗文本
        if line.startswith('**') and line.endswith('**'):
            text = clean_text(line)
            story.append(Paragraph(text, bold_style))
            i += 1
            continue

        # 普通段落
        text = clean_text(line)
        story.append(Paragraph(text, body_style))
        i += 1

    # 生成 PDF
    doc.build(story)
    print(f"成功 PDF 已生成：{os.path.basename(pdf_file)}")

if __name__ == '__main__':
    files = [
        ('心理探索访谈-纯对话版-20260711.md', '心理探索访谈-纯对话版-20260711.pdf'),
        ('自我探索总结-20260711.md', '自我探索总结-20260711.pdf')
    ]

    base_dir = os.path.dirname(os.path.abspath(__file__))

    for md_file, pdf_file in files:
        md_path = os.path.join(base_dir, md_file)
        pdf_path = os.path.join(base_dir, pdf_file)

        if os.path.exists(md_path):
            print(f"正在转换：{md_file}")
            try:
                parse_markdown_to_pdf(md_path, pdf_path)
            except Exception as e:
                print(f"失败 转换失败：{e}")
        else:
            print(f"失败 文件不存在：{md_file}")

    print("\n全部转换完成！")
