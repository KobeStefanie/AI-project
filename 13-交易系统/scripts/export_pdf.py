"""
export_pdf.py — 访谈记录导出 PDF（格式按全局 CLAUDE.md「Markdown 转 PDF 规则」）
  - 清理 ** * # ` 等符号，保留列表编号、段落空行，逐行处理
  - Markdown 表格渲染为真正的表格（灰色表头、网格线、隔行底色）
  - 微软雅黑字体，底部居中页码，bottomMargin 3.5cm
输出：output/interviews/访谈记录-{id}.pdf
"""
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import store

OUT_DIR = store.ROOT / 'output' / 'interviews'
FONT_NAME, FONT_NAME_BOLD = 'msyh', 'msyhbd'
_fonts_ready = False

# 微软雅黑没有 emoji 字形，渲染出来是方块，导出前去掉
_EMOJI = re.compile('[\U00010000-\U0010FFFF☀-➿⬀-⯿️‍]')


def _register_fonts():
    global _fonts_ready
    if not _fonts_ready:
        pdfmetrics.registerFont(TTFont(FONT_NAME, r'C:\Windows\Fonts\msyh.ttc', subfontIndex=0))
        pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, r'C:\Windows\Fonts\msyhbd.ttc', subfontIndex=0))
        _fonts_ready = True


def clean_text(text: str) -> str:
    """清理 markdown 格式符号，保留列表和换行结构"""
    text = _EMOJI.sub('', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = text.replace('`', '')
    text = re.sub(r'^#+\s+', '', text)
    # 先转义 &，否则 &lt; 会被二次转义成 &amp;lt;
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').strip()


def _styles() -> dict:
    base = dict(fontName=FONT_NAME, wordWrap='CJK')
    return {
        'title': ParagraphStyle('title', fontSize=16, leading=24, fontName=FONT_NAME_BOLD, wordWrap='CJK'),
        'meta': ParagraphStyle('meta', fontSize=9, leading=14, textColor=colors.HexColor('#7f8c8d'), **base),
        'who': ParagraphStyle('who', fontSize=11, leading=18, fontName=FONT_NAME_BOLD, wordWrap='CJK',
                              textColor=colors.HexColor('#2c3e50'), spaceBefore=6),
        'h2': ParagraphStyle('h2', fontSize=12, leading=18, fontName=FONT_NAME_BOLD, wordWrap='CJK'),
        'h3': ParagraphStyle('h3', fontSize=11, leading=17, fontName=FONT_NAME_BOLD, wordWrap='CJK'),
        'body': ParagraphStyle('body', fontSize=10, leading=17, **base),
        'list': ParagraphStyle('list', fontSize=10, leading=17, leftIndent=12, **base),
        'cell': ParagraphStyle('cell', fontSize=9, leading=13, **base),
        'cell_head': ParagraphStyle('cell_head', fontSize=9, leading=13, fontName=FONT_NAME_BOLD, wordWrap='CJK'),
    }


def _table(rows: list, st: dict):
    cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r':?-{2,}:?', c) for c in r if c)]  # 去掉 |---|---| 分隔行
    if not cells:
        return None
    n = max(len(r) for r in cells)
    data = [[Paragraph(clean_text(r[i]) if i < len(r) else '', st['cell_head' if k == 0 else 'cell'])
             for i in range(n)] for k, r in enumerate(cells)]
    t = Table(data, colWidths=[16 * cm / n] * n, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


def _content_flow(text: str, st: dict) -> list:
    """一条消息的正文：逐行处理，空行=段落间距，表格成块渲染"""
    flow, lines, i = [], text.split('\n'), 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith('|'):  # 收集连续的表格行
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i]); i += 1
            t = _table(rows, st)
            if t:
                flow += [t, Spacer(1, 0.2 * cm)]
            continue
        i += 1
        if not s:
            flow.append(Spacer(1, 0.2 * cm))
        elif re.fullmatch(r'-{3,}|\*{3,}', s):
            flow.append(Spacer(1, 0.3 * cm))
        elif s.startswith('### ') or s.startswith('#### '):
            flow.append(Paragraph(clean_text(s), st['h3']))
        elif s.startswith('#'):
            flow.append(Paragraph(clean_text(s), st['h2']))
        elif re.match(r'^([-*+]|\d+[.、)])\s+', s):
            # 列表：保留编号；无序列表的 - * 换成圆点
            s = re.sub(r'^[-*+]\s+', '• ', s)
            flow.append(Paragraph(clean_text(s), st['list']))
        else:
            flow.append(Paragraph(clean_text(s), st['body']))
    return flow


def _page_number(canvas, doc):
    canvas.setFont(FONT_NAME, 9)
    canvas.setFillColor(colors.HexColor('#7f8c8d'))
    canvas.drawCentredString(A4[0] / 2, 20, f'第 {canvas.getPageNumber()} 页')


def export_interview(iv: dict) -> Path:
    _register_fonts()
    st = _styles()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"访谈记录-{iv['id']}.pdf"
    story = [Paragraph(clean_text(f"访谈记录：{iv['topic']}"), st['title']), Spacer(1, 0.2 * cm),
             Paragraph(clean_text(f"开始时间：{iv['created']}　来源：data/interviews/{iv['id']}.json"), st['meta']),
             Spacer(1, 0.4 * cm)]
    for m in iv['messages']:
        if m.get('hidden'):
            continue
        who = '我' if m['role'] == 'user' else 'Claude'
        story.append(Paragraph(clean_text(f"{who}（{m['time']}）"), st['who']))
        story += _content_flow(m['content'], st)
        for s in m.get('suggestions') or []:
            tag = '已采纳' if s.get('applied') else '未采纳'
            story.append(Paragraph(clean_text(f"可沉淀建议（{tag}）：{s.get('name') or ''} {s.get('content', '')}"), st['list']))
        story.append(Spacer(1, 0.3 * cm))
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=3.5 * cm,
                            title=f"访谈记录 {iv['id']}", author='我的交易系统')
    try:
        doc.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    except PermissionError as e:
        raise ValueError(f'{out.name} 被占用（可能在 PDF 阅读器里开着），关掉后再导出') from e
    return out
