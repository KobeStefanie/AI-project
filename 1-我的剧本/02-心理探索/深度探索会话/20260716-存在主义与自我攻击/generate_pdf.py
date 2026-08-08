#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF生成 - 漂泊的意义 | 角色区分：来访者（黑色加粗）/ 治疗师（灰色常规）"""

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

SYMBOL_MAP = {
    '✓': '√', '✔': '√', '✗': '×', '✘': '×',
    '✅': '[完成]', '❌': '[×]', '⚠️': '[注意]', '⚠': '[注意]',
    '→': '->', '←': '<-', '…': '...', '👤': '', '🤖': '',
    '​': '', '﻿': '',
}

def clean(text):
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    text = text.replace('`', '')
    for k, v in SYMBOL_MAP.items():
        text = text.replace(k, v)
    return text

def detect_role(line):
    s = line.strip()
    for pat in [r'^\*\*(用户|来访者)\*\*\s*[:：]\s*(.*)', r'^(用户|来访者)\s*[:：]\s*(.*)']:
        m = re.match(pat, s)
        if m: return 'client', m.group(2)
    for pat in [r'^\*\*(AI|Claude|治疗师)\*\*\s*[:：]\s*(.*)', r'^(AI|Claude|治疗师)\s*[:：]\s*(.*)']:
        m = re.match(pat, s)
        if m: return 'therapist', m.group(2)
    return None, None

def add_page_num(canvas, doc):
    canvas.setFont(FONT_NAME, 9)
    canvas.setFillColor(colors.HexColor('#7f8c8d'))
    canvas.drawCentredString(A4[0]/2, 20, "第 %d 页" % canvas.getPageNumber())

def parse_table(lines, idx):
    rows = []
    i = idx
    while i < len(lines) and '|' in lines[i]:
        rows.append(lines[i]); i += 1
    rows = [r for r in rows if not re.match(r'^\s*\|[\s\-:]+\|\s*$', r)]
    data = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows if r.strip()]
    return data, i

def gen(md_file, pdf_file, title):
    print("生成: " + pdf_file)
    doc = SimpleDocTemplate(pdf_file, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=35)
    S = getSampleStyleSheet()
    ts = ParagraphStyle('T', parent=S['Title'], fontName=FONT_NAME_BOLD, fontSize=18,
        textColor=colors.HexColor('#2c3e50'), spaceAfter=20, alignment=TA_CENTER)
    body = ParagraphStyle('B', parent=S['BodyText'], fontName=FONT_NAME, fontSize=11,
        leading=16, textColor=colors.HexColor('#34495e'), spaceAfter=8)
    client = ParagraphStyle('C', parent=S['BodyText'], fontName=FONT_NAME_BOLD, fontSize=11,
        leading=16, textColor=colors.HexColor('#000000'), spaceAfter=8)
    role_hdr = ParagraphStyle('R', parent=S['BodyText'], fontName=FONT_NAME_BOLD, fontSize=13,
        leading=18, textColor=colors.HexColor('#000000'), spaceBefore=12, spaceAfter=6)
    tc = ParagraphStyle('TC', parent=S['BodyText'], fontName=FONT_NAME, fontSize=10, leading=14,
        textColor=colors.HexColor('#34495e'))

    with open(md_file, encoding='utf-8') as f:
        lines = f.read().split('\n')

    story = [Paragraph(title, ts), Spacer(1, 0.5*cm)]
    cur = None
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        role, rest = detect_role(line)
        if role:
            cur = role
            story.append(Paragraph('来访者' if role=='client' else '治疗师', role_hdr))
            if rest and rest.strip():
                story.append(Paragraph(clean(rest), client if role=='client' else body))
            i += 1; continue
        if '|' in line and i+1 < len(lines) and '|' in lines[i+1]:
            tdata, ni = parse_table(lines, i)
            if tdata:
                cd = [[Paragraph(clean(c), tc) for c in row] for row in tdata]
                ncol = max(len(r) for r in cd)
                t = Table(cd, colWidths=[15*cm/ncol]*ncol)
                t.setStyle(TableStyle([
                    ('FONTNAME',(0,0),(-1,0),FONT_NAME_BOLD),
                    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#ecf0f1')),
                    ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#bdc3c7')),
                    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),
                    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
                    ('LEFTPADDING',(0,0),(-1,-1),6),
                ]))
                story.append(t); story.append(Spacer(1,0.3*cm))
            i = ni; continue
        if line.strip():
            t = clean(line)
            if t.strip():
                story.append(Paragraph(t, client if cur=='client' else body))
        else:
            story.append(Spacer(1, 0.2*cm))
        i += 1

    doc.build(story, onFirstPage=add_page_num, onLaterPages=add_page_num)
    print("完成: %.1f KB" % (os.path.getsize(pdf_file)/1024))

BASE = r"d:\AI-项目\1-我的剧本\02-心理探索\深度探索会话\20260716-存在主义与自我攻击"
gen(BASE+r"\对话记录-20260716-存在主义与自我攻击.md",
    BASE+r"\对话记录-20260716-存在主义与自我攻击.pdf",
    "心理探索深度访谈 - 存在主义与自我攻击")
gen(BASE+r"\自我探索总结-20260716-存在主义与自我攻击.md",
    BASE+r"\自我探索总结-20260716-存在主义与自我攻击.pdf",
    "自我探索总结 - 存在主义与自我攻击")
print("全部完成")
