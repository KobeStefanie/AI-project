import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# 注册字体
pdfmetrics.registerFont(TTFont('msyh', r'C:\Windows\Fonts\msyh.ttc'))
pdfmetrics.registerFont(TTFont('msyhbd', r'C:\Windows\Fonts\msyhbd.ttc'))
FONT_NAME = 'msyh'
FONT_NAME_BOLD = 'msyhbd'

def clean_text(text):
    """清理markdown语法符号"""
    # 移除粗体标记
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # 移除斜体标记
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # 移除标题标记
    text = re.sub(r'^#+\s+', '', text)
    # 清理其他markdown符号
    text = text.replace('`', '')
    return text.strip()

# 读取原始对话记录，提取新增部分
with open('对话记录-20260711-自我探索.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到分界点
start_index = -1
for i, line in enumerate(lines):
    if '继续更新对话和总结' in line and i > 4800:
        start_index = i
        break

if start_index == -1:
    print("未找到分界点")
    exit(1)

# 提取新增对话
dialogue_rounds = []
current_speaker = None
current_content = []

for i in range(start_index + 1, len(lines)):
    line = lines[i].strip()

    # 跳过非对话内容
    if (line.startswith('[调用工具') or line.startswith('[工具结果]') or
        '<task-notification>' in line or 'API Error:' in line or
        line == '---' or line == ''):
        continue

    # 识别说话人
    if line.startswith('## 👤 用户'):
        if current_speaker and current_content:
            dialogue_rounds.append({'speaker': current_speaker, 'content': '\n'.join(current_content)})
        current_speaker = '来访者'
        current_content = []
        continue
    elif line.startswith('## 🤖 Claude'):
        if current_speaker and current_content:
            dialogue_rounds.append({'speaker': current_speaker, 'content': '\n'.join(current_content)})
        current_speaker = '治疗师'
        current_content = []
        continue

    if current_speaker:
        current_content.append(line)

if current_speaker and current_content:
    dialogue_rounds.append({'speaker': current_speaker, 'content': '\n'.join(current_content)})

print(f"提取到 {len(dialogue_rounds)} 轮新增对话")

# 创建PDF
output_file = '心理探索访谈-新增部分-20260711.pdf'
doc = SimpleDocTemplate(output_file, pagesize=A4, topMargin=2*cm, bottomMargin=35, leftMargin=2*cm, rightMargin=2*cm)

title_style = ParagraphStyle('CustomTitle', fontName=FONT_NAME_BOLD, fontSize=18,
                            textColor=colors.HexColor('#2c3e50'), spaceAfter=12, alignment=TA_CENTER)
body_style = ParagraphStyle('CustomBody', fontName=FONT_NAME, fontSize=11, leading=18,
                           textColor=colors.HexColor('#2c3e50'), spaceAfter=6)
speaker_style = ParagraphStyle('Speaker', fontName=FONT_NAME_BOLD, fontSize=12,
                              textColor=colors.HexColor('#2980b9'), spaceAfter=6)
table_style = ParagraphStyle('TableText', fontName=FONT_NAME, fontSize=10, leading=14,
                            textColor=colors.HexColor('#2c3e50'))

def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"第 {page_num} 页"
    canvas.setFont(FONT_NAME, 9)
    canvas.setFillColor(colors.HexColor('#7f8c8d'))
    canvas.drawCentredString(A4[0] / 2, 20, text)

story = []
story.append(Paragraph('心理探索访谈 - 新增部分', title_style))
story.append(Paragraph('访谈时间：2026年7月11日（续）', body_style))
story.append(Spacer(1, 0.5*cm))

for round_data in dialogue_rounds:
    speaker = round_data['speaker']
    content = round_data['content']

    if not content.strip():
        continue

    # 添加说话人
    story.append(Paragraph(f"{speaker}：", speaker_style))

    # 处理内容中的表格
    lines = content.split('\n')
    table_buffer = []
    text_buffer = []

    for line in lines:
        if '|' in line and line.strip().startswith('|'):
            # 可能是表格行
            table_buffer.append(line)
        else:
            # 先处理之前的表格
            if table_buffer:
                if len(table_buffer) >= 3:
                    # 解析表格
                    table_data = []
                    for tline in table_buffer:
                        if '---' not in tline:
                            cells = [c.strip() for c in tline.split('|')[1:-1]]
                            cell_paragraphs = [Paragraph(clean_text(cell), table_style) for cell in cells]
                            table_data.append(cell_paragraphs)

                    if table_data:
                        t = Table(table_data, colWidths=[15*cm / len(table_data[0])] * len(table_data[0]))
                        t.setStyle(TableStyle([
                            ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                            ('TOPPADDING', (0, 0), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 0.3*cm))
                table_buffer = []

            # 处理文本
            if line.strip():
                text_buffer.append(line)

    # 处理最后的表格或文本
    if table_buffer and len(table_buffer) >= 3:
        table_data = []
        for tline in table_buffer:
            if '---' not in tline:
                cells = [c.strip() for c in tline.split('|')[1:-1]]
                cell_paragraphs = [Paragraph(clean_text(cell), table_style) for cell in cells]
                table_data.append(cell_paragraphs)

        if table_data:
            t = Table(table_data, colWidths=[15*cm / len(table_data[0])] * len(table_data[0]))
            t.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3*cm))

    if text_buffer:
        clean_content = '\n'.join(text_buffer)
        clean_content = clean_text(clean_content)
        story.append(Paragraph(clean_content, body_style))

    story.append(Spacer(1, 0.3*cm))

doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
print(f"新增部分PDF生成: {output_file} ({os.path.getsize(output_file) / 1024:.1f} KB)")
print("已清理markdown语法符号")
