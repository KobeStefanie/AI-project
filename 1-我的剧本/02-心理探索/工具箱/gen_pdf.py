#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors

FONT_NAME = "MicrosoftYaHei"
FONT_NAME_BOLD = "MicrosoftYaHei-Bold"
pdfmetrics.registerFont(TTFont(FONT_NAME, r"C:\Windows\Fonts\msyh.ttc"))
pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, r"C:\Windows\Fonts\msyhbd.ttc"))

def clean_text(text):
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    text = text.replace('`', '')
    for orig, repl in {'✓':'√','✔':'√','✗':'×','✘':'×','✅':'[完成]','❌':'[×]','⚠️':'[注意]','⚠':'[注意]','→':'->','←':'<-'}.items():
        text = text.replace(orig, repl)
    return text

def add_page_number(canvas, doc):
    canvas.setFont(FONT_NAME, 9)
    canvas.setFillColor(colors.HexColor('#7f8c8d'))
    canvas.drawCentredString(A4[0]/2, 20, f"第 {canvas.getPageNumber()} 页")

def parse_table(lines, idx):
    rows = []
    i = idx
    while i < len(lines) and '|' in lines[i]:
        rows.append(lines[i]); i += 1
    rows = [r for r in rows if not re.match(r'^\s*\|[\s\-:|\-]+\|\s*$', r)]
    if not rows: return None, idx
    return [[c.strip() for c in r.split('|')[1:-1]] for r in rows], i

def generate_pdf(md_file, pdf_file, title):
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle('T', parent=styles['Title'], fontName=FONT_NAME_BOLD, fontSize=18,
                             textColor=colors.HexColor('#2c3e50'), spaceAfter=20, alignment=TA_CENTER)
    body_s  = ParagraphStyle('B', parent=styles['BodyText'], fontName=FONT_NAME, fontSize=11,
                             leading=16, textColor=colors.HexColor('#34495e'), spaceAfter=8)
    cell_s  = ParagraphStyle('C', parent=styles['BodyText'], fontName=FONT_NAME, fontSize=10, leading=14)

    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')

    doc = SimpleDocTemplate(pdf_file, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=35)
    story = [Paragraph(title, title_s), Spacer(1, 0.5*cm)]

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if '|' in line and i+1 < len(lines) and '|' in lines[i+1]:
            data, next_i = parse_table(lines, i)
            if data:
                n = len(data[0])
                t = Table([[Paragraph(clean_text(c), cell_s) for c in row] for row in data],
                          colWidths=[15*cm/n]*n)
                t.setStyle(TableStyle([
                    ('FONTNAME',(0,0),(-1,0),FONT_NAME_BOLD),
                    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#ecf0f1')),
                    ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#bdc3c7')),
                    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),
                    ('ALIGN',(0,0),(-1,-1),'LEFT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                    ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
                    ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
                ]))
                story += [t, Spacer(1, 0.3*cm)]
                i = next_i; continue
        if line.strip():
            story.append(Paragraph(clean_text(line), body_s))
        else:
            story.append(Spacer(1, 0.2*cm))
        i += 1

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"生成成功: {os.path.getsize(pdf_file)/1024:.1f} KB -> {os.path.basename(pdf_file)}")

BASE = r"d:\AI-项目\1-我的剧本\02-心理探索\工具箱"
generate_pdf(
    os.path.join(BASE, "救火员手册.md"),
    os.path.join(BASE, "救火员手册.pdf"),
    "救火员手册"
)
