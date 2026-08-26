# -*- coding: utf-8 -*-
"""
将 Markdown 文档转换为 PDF（v2版本）
遵循项目PDF规范：清理markdown符号、逐行处理、表格渲染、页码
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import re

# 注册中文字体
pdfmetrics.registerFont(TTFont('msyh', r'C:\Windows\Fonts\msyh.ttc'))
pdfmetrics.registerFont(TTFont('msyhbd', r'C:\Windows\Fonts\msyhbd.ttc'))

FONT_NAME = 'msyh'
FONT_NAME_BOLD = 'msyhbd'

def clean_text(text):
    """清理markdown格式符号，保留列表和换行结构"""
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

def add_page_number(canvas, doc):
    """添加页码到页面底部中央"""
    page_num = canvas.getPageNumber()
    text = f"第 {page_num} 页"
    canvas.setFont(FONT_NAME, 9)
    canvas.setFillColor(colors.HexColor('#7f8c8d'))
    canvas.drawCentredString(A4[0] / 2, 20, text)

def build_table(table_data):
    """构建表格，包含样式"""
    # 将表格数据转换为Paragraph对象
    table_style = ParagraphStyle(
        'TableCell',
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        leftIndent=3,
        rightIndent=3,
    )

    formatted_data = []
    for i, row in enumerate(table_data):
        formatted_row = []
        for cell in row:
            formatted_row.append(Paragraph(clean_text(str(cell)), table_style))
        formatted_data.append(formatted_row)

    # 计算列宽
    col_count = len(table_data[0]) if table_data else 1
    col_width = 15 * cm / col_count

    # 创建表格
    t = Table(formatted_data, colWidths=[col_width] * col_count)

    # 设置表格样式
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    return t

def md_to_pdf(input_md, output_pdf):
    """将Markdown转换为PDF"""

    # 读取markdown文件
    with open(input_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # 创建PDF文档
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=3.5*cm  # 底部边距要足够容纳页码
    )

    # 定义样式
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME_BOLD,
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        alignment=TA_CENTER,
    )

    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontName=FONT_NAME_BOLD,
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=6,
        spaceBefore=12,
    )

    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontName=FONT_NAME_BOLD,
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=4,
        spaceBefore=8,
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName=FONT_NAME,
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        leading=16,
        leftIndent=0,
        spaceAfter=6,
    )

    # 构建PDF内容
    story = []
    content_lines = content.split('\n')

    in_table = False
    table_data = []

    for line in content_lines:
        stripped = line.strip()

        # 跳过分隔线
        if stripped.startswith('---'):
            story.append(Spacer(1, 0.3*cm))
            continue

        # 表格处理
        if '|' in stripped and stripped.startswith('|'):
            # 跳过表格分隔行
            if re.match(r'^\|[\s\-:]+\|', stripped):
                continue

            # 解析表格行
            cells = [cell.strip() for cell in stripped.split('|')[1:-1]]

            if not in_table:
                in_table = True
                table_data = [cells]
            else:
                table_data.append(cells)
            continue
        else:
            # 表格结束
            if in_table and table_data:
                story.append(build_table(table_data))
                story.append(Spacer(1, 0.3*cm))
                in_table = False
                table_data = []

        # 一级标题
        if stripped.startswith('# ') and not stripped.startswith('## '):
            text = clean_text(stripped[2:])
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 0.3*cm))
            continue

        # 二级标题
        if stripped.startswith('## ') and not stripped.startswith('### '):
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

    # 处理末尾未闭合的表格
    if in_table and table_data:
        story.append(build_table(table_data))

    # 生成PDF
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"OK -> {output_pdf}")

if __name__ == '__main__':
    input_md = '../01-学习资料/小圆筒生产单术语科普_v2.md'
    output_pdf = '../01-学习资料/小圆筒生产单术语科普_v2.pdf'

    try:
        md_to_pdf(input_md, output_pdf)
    except Exception as e:
        print(f"生成失败: {e}")
        import traceback
        traceback.print_exc()
