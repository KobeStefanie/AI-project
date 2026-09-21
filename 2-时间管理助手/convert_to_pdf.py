# -*- coding: utf-8 -*-
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# 注册中文字体
FONT_NAME = 'msyh'
FONT_NAME_BOLD = 'msyhbd'
pdfmetrics.registerFont(TTFont(FONT_NAME, r'C:\Windows\Fonts\msyh.ttc'))
pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, r'C:\Windows\Fonts\msyhbd.ttc'))

def clean_text(text):
    """清理markdown格式符号，保留列表和换行结构"""
    # 移除粗体
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    # 移除斜体
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # 移除代码标记
    text = text.replace('`', '')
    # 移除标题标记（保留内容）
    text = re.sub(r'^#+\s+', '', text)
    # 转义XML特殊字符
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text

def add_page_number(canvas, doc):
    """添加页码到页面底部中央"""
    page_num = canvas.getPageNumber()
    text = f"第 {page_num} 页"
    canvas.setFont(FONT_NAME, 9)
    canvas.setFillColor(colors.HexColor('#7f8c8d'))
    canvas.drawCentredString(A4[0] / 2, 20, text)

def convert_md_to_pdf(md_file, pdf_file):
    """将Markdown文件转换为PDF"""

    # 读取Markdown内容
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 创建PDF文档
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        leftMargin=2.5*cm,
        rightMargin=2.5*cm,
        topMargin=2.5*cm,
        bottomMargin=3.5*cm  # 底部边距容纳页码
    )

    # 定义样式
    title_style = ParagraphStyle(
        'Title',
        fontName=FONT_NAME_BOLD,
        fontSize=18,
        leading=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        alignment=TA_CENTER
    )

    h2_style = ParagraphStyle(
        'Heading2',
        fontName=FONT_NAME_BOLD,
        fontSize=14,
        leading=20,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=12
    )

    h3_style = ParagraphStyle(
        'Heading3',
        fontName=FONT_NAME_BOLD,
        fontSize=12,
        leading=18,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=6,
        spaceBefore=8
    )

    body_style = ParagraphStyle(
        'Body',
        fontName=FONT_NAME,
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=4
    )

    table_style = ParagraphStyle(
        'TableCell',
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2c3e50')
    )

    # 构建故事
    story = []
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # 跳过分隔线
        if line.startswith('---'):
            story.append(Spacer(1, 0.3*cm))
            i += 1
            continue

        # 一级标题
        if line.startswith('# '):
            text = clean_text(line[2:])
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 0.3*cm))
            i += 1
            continue

        # 二级标题
        if line.startswith('## '):
            text = clean_text(line[3:])
            story.append(Paragraph(text, h2_style))
            i += 1
            continue

        # 三级标题
        if line.startswith('### '):
            text = clean_text(line[4:])
            story.append(Paragraph(text, h3_style))
            i += 1
            continue

        # 表格检测
        if '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
            # 解析表格
            table_data = []
            j = i
            while j < len(lines) and '|' in lines[j]:
                row = lines[j].strip()
                if row.startswith('|'):
                    row = row[1:]
                if row.endswith('|'):
                    row = row[:-1]

                # 跳过分隔行
                if re.match(r'^[\s\-|:]+$', row):
                    j += 1
                    continue

                cells = [cell.strip() for cell in row.split('|')]
                # 将单元格内容转换为 Paragraph 对象
                cell_paragraphs = [Paragraph(clean_text(cell), table_style) for cell in cells]
                table_data.append(cell_paragraphs)
                j += 1

            if table_data:
                # 创建表格
                col_width = 15*cm / len(table_data[0])
                t = Table(table_data, colWidths=[col_width] * len(table_data[0]))
                t.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(t)
                story.append(Spacer(1, 0.3*cm))

            i = j
            continue

        # 空行 = 段落分隔
        if not line:
            story.append(Spacer(1, 0.2*cm))
            i += 1
            continue

        # 列表项
        if line.startswith('- ') or re.match(r'^\d+\.\s', line):
            cleaned = clean_text(line)
            story.append(Paragraph(cleaned, body_style))
            i += 1
            continue

        # 普通文本
        cleaned = clean_text(line)
        if cleaned:
            story.append(Paragraph(cleaned, body_style))
        i += 1

    # 构建PDF
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"PDF已生成: {pdf_file}")

if __name__ == '__main__':
    convert_md_to_pdf(
        r'd:\AI-项目\2-时间管理助手\解读差异分析.md',
        r'd:\AI-项目\2-时间管理助手\解读差异分析.pdf'
    )
