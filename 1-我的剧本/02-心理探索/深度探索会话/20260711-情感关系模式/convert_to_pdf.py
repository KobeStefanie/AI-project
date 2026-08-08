#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将 Markdown 文件转换为 PDF
使用 reportlab 库生成中文 PDF
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re

# 注册中文字体（使用 Windows 自带的微软雅黑）
try:
    pdfmetrics.registerFont(TTFont('msyh', 'C:/Windows/Fonts/msyh.ttc'))
    pdfmetrics.registerFont(TTFont('msyhbd', 'C:/Windows/Fonts/msyhbd.ttc'))
    FONT_NAME = 'msyh'
    FONT_NAME_BOLD = 'msyhbd'
except:
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'
    print("警告：无法加载中文字体，将使用默认字体")

def clean_text(text):
    """清理文本，移除特殊标记"""
    # 移除加粗标记
    text = text.replace('**', '')
    # 转义 XML 特殊字符
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def parse_markdown_to_pdf(md_file, pdf_file):
    """将 Markdown 文件转换为 PDF"""
    
    # 读取 Markdown 文件
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建 PDF 文档
    doc = SimpleDocTemplate(pdf_file, pagesize=A4,
                           rightMargin=50, leftMargin=50,
                           topMargin=50, bottomMargin=30)
    
    # 定义样式
    styles = getSampleStyleSheet()
    
    # 标题样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME_BOLD,
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=20,
        alignment=1
    )
    
    # 一级标题
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontName=FONT_NAME_BOLD,
        fontSize=15,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    # 二级标题
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontName=FONT_NAME_BOLD,
        fontSize=13,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=12
    )
    
    # 三级标题
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading2'],
        fontName=FONT_NAME_BOLD,
        fontSize=12,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=6,
        spaceBefore=10
    )
    
    # 正文样式
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName=FONT_NAME,
        fontSize=10.5,
        leading=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8
    )
    
    # 加粗样式
    bold_style = ParagraphStyle(
        'CustomBold',
        parent=body_style,
        fontName=FONT_NAME_BOLD
    )
    
    # 引用样式
    quote_style = ParagraphStyle(
        'CustomQuote',
        parent=body_style,
        leftIndent=25,
        rightIndent=25,
        textColor=colors.HexColor('#7f8c8d'),
        fontSize=10,
        leading=15
    )
    
    # 构建 PDF 内容
    story = []
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # 空行
        if not line:
            story.append(Spacer(1, 0.05*inch))
            continue
        
        # 一级标题（# 开头）
        if line.startswith('# '):
            text = clean_text(line[2:].strip())
            story.append(Paragraph(text, title_style))
            continue
        
        # 二级标题（## 开头）
        if line.startswith('## '):
            text = clean_text(line[3:].strip())
            story.append(Paragraph(text, h1_style))
            continue
        
        # 三级标题（### 开头）
        if line.startswith('### '):
            text = clean_text(line[4:].strip())
            story.append(Paragraph(text, h2_style))
            continue
        
        # 分隔线
        if line.startswith('---'):
            story.append(Spacer(1, 0.15*inch))
            continue
        
        # 引用块（> 开头）
        if line.startswith('>'):
            text = clean_text(line[1:].strip())
            story.append(Paragraph(text, quote_style))
            continue
        
        # 跳过表格分隔线
        if re.match(r'\|[\s\-:]+\|', line):
            continue
        
        # 表格行（| 开头）
        if line.startswith('|'):
            cells = [clean_text(cell.strip()) for cell in line.split('|')[1:-1]]
            text = '  |  '.join(cells)
            story.append(Paragraph(text, body_style))
            continue
        
        # 加粗文本（**text**）
        if line.startswith('**') and line.endswith('**'):
            text = clean_text(line)
            story.append(Paragraph(text, bold_style))
            continue
        
        # 普通段落
        text = clean_text(line)
        story.append(Paragraph(text, body_style))
    
    # 生成 PDF
    doc.build(story)
    print(f"PDF 已生成：{pdf_file}")

if __name__ == '__main__':
    # 转换两个文件
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
                print(f"转换失败：{e}")
        else:
            print(f"文件不存在：{md_file}")
