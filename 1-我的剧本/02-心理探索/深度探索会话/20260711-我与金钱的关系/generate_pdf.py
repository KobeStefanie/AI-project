#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF生成脚本 - 我与金钱的关系
生成两个PDF：对话记录 + 自我探索总结
角色区分：来访者（黑色加粗）/ 治疗师（灰色常规）
"""

import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors

# 注册中文字体
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
FONT_PATH_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_NAME = "MicrosoftYaHei"
FONT_NAME_BOLD = "MicrosoftYaHei-Bold"

try:
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
    pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, FONT_PATH_BOLD))
    print(f"字体注册成功: {FONT_NAME}")
except Exception as e:
    print(f"字体注册失败: {e}")
    exit(1)

def clean_text(text):
    """清理markdown格式符号，但保留列表标记和结构"""
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    text = text.replace('`', '')
    symbol_map = {
        '✓': '√', '✔': '√',
        '✗': '×', '✘': '×',
        '✅': '[完成]', '❌': '[×]',
        '⚠️': '[注意]', '⚠': '[注意]',
        '→': '->', '←': '<-',
        '…': '...',
        '👤': '', '🤖': '',   # emoji微软雅黑不支持，去掉
        '​': '', '﻿': '',
    }
    for orig, repl in symbol_map.items():
        text = text.replace(orig, repl)
    return text

def detect_role_header(line):
    """检测角色标题行，返回 (角色, 显示名称) 或 None"""
    if line.startswith('#') and '👤' in line:
        return 'client'
    if line.startswith('#') and '🤖' in line:
        return 'therapist'
    return None

def format_role_header(line, role):
    """把 '## 👤 用户 (08:01:58)' 变成 '来访者 (08:01:58)'"""
    text = clean_text(line).strip()
    # 去掉原角色名（用户/Claude），保留时间括号
    time_match = re.search(r'[\(（].*?[\)）]', text)
    time_str = time_match.group(0) if time_match else ''
    label = '来访者' if role == 'client' else '治疗师'
    return f"{label} {time_str}".strip()

def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"第 {page_num} 页"
    canvas.setFont(FONT_NAME, 9)
    canvas.setFillColor(colors.HexColor('#7f8c8d'))
    canvas.drawCentredString(A4[0] / 2, 20, text)

def parse_markdown_table(lines, start_idx):
    table_lines = []
    i = start_idx
    while i < len(lines) and '|' in lines[i]:
        table_lines.append(lines[i])
        i += 1
    if len(table_lines) < 2:
        return None, start_idx
    table_lines = [line for line in table_lines if not re.match(r'^\s*\|[\s\-:|\-]+\|\s*$', line)]
    if not table_lines:
        return None, start_idx
    table_data = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        if cells:
            table_data.append(cells)
    return table_data, i

def generate_pdf(md_file, pdf_file, title):
    print(f"\n正在生成: {pdf_file}")
    print(f"源文件: {md_file}")

    doc = SimpleDocTemplate(
        pdf_file, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=35
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontName=FONT_NAME_BOLD, fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=20, alignment=TA_CENTER
    )

    # 治疗师内容：灰色常规
    body_style = ParagraphStyle(
        'CustomBody', parent=styles['BodyText'],
        fontName=FONT_NAME, fontSize=11, leading=16,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8, alignment=TA_LEFT
    )

    # 来访者内容：黑色加粗
    client_style = ParagraphStyle(
        'ClientBody', parent=styles['BodyText'],
        fontName=FONT_NAME_BOLD, fontSize=11, leading=16,
        textColor=colors.HexColor('#000000'),
        spaceAfter=8, alignment=TA_LEFT
    )

    # 角色标题：黑色加粗，略大
    role_header_style = ParagraphStyle(
        'RoleHeader', parent=styles['BodyText'],
        fontName=FONT_NAME_BOLD, fontSize=13, leading=18,
        textColor=colors.HexColor('#000000'),
        spaceBefore=12, spaceAfter=6, alignment=TA_LEFT
    )

    table_cell_style = ParagraphStyle(
        'TableCell', parent=styles['BodyText'],
        fontName=FONT_NAME, fontSize=10, leading=14,
        textColor=colors.HexColor('#34495e')
    )

    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.5*cm))

    current_role = None  # 当前说话角色，决定正文样式

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # 角色标题
        role = detect_role_header(line)
        if role:
            current_role = role
            story.append(Paragraph(format_role_header(line, role), role_header_style))
            i += 1
            continue

        # 表格
        if '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
            table_data, next_i = parse_markdown_table(lines, i)
            if table_data:
                cell_data = []
                for row in table_data:
                    cell_row = [Paragraph(clean_text(cell), table_cell_style) for cell in row]
                    cell_data.append(cell_row)
                num_cols = len(cell_data[0])
                col_width = 15*cm / num_cols
                t = Table(cell_data, colWidths=[col_width] * num_cols)
                t.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(t)
                story.append(Spacer(1, 0.3*cm))
                i = next_i
                continue

        # 普通文本：按当前角色选样式（来访者黑色加粗，治疗师灰色常规）
        if line.strip():
            cleaned_line = clean_text(line)
            if cleaned_line.strip():
                style = client_style if current_role == 'client' else body_style
                story.append(Paragraph(cleaned_line, style))
        else:
            story.append(Spacer(1, 0.2*cm))

        i += 1

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

    if os.path.exists(pdf_file):
        size_kb = os.path.getsize(pdf_file) / 1024
        print(f"生成成功: {size_kb:.1f} KB")
    else:
        print(f"生成失败")

def main():
    base_dir = r"d:\AI-项目\1-我的剧本\02-心理探索\深度探索会话\20260711-我与金钱的关系"
    files = [
        {
            'md': os.path.join(base_dir, '对话记录-20260711-我与金钱的关系.md'),
            'pdf': os.path.join(base_dir, '对话记录-20260711-我与金钱的关系.pdf'),
            'title': '心理探索深度访谈 - 我与金钱的关系'
        },
        {
            'md': os.path.join(base_dir, '自我探索总结-20260711-我与金钱的关系.md'),
            'pdf': os.path.join(base_dir, '自我探索总结-20260711-我与金钱的关系.pdf'),
            'title': '自我探索总结 - 我与金钱的关系'
        }
    ]
    for file_config in files:
        if os.path.exists(file_config['md']):
            generate_pdf(file_config['md'], file_config['pdf'], file_config['title'])
        else:
            print(f"源文件不存在: {file_config['md']}")
    print("\n全部完成！")

if __name__ == '__main__':
    main()
