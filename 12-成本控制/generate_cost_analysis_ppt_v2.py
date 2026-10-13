#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
织造车间成本分析PPT生成脚本 - 基于真实Excel数据
面向老板汇报：成本体系搭建 + 现状分析 + 改善计划 + 考核建议
"""
import openpyxl
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

# 读取Excel数据
excel_path = r'C:\Users\Administrator\Desktop\华盛\成本PPT汇报\成本核算汇总-标准成本 - 加工与自产.xlsx'
wb = openpyxl.load_workbook(excel_path, data_only=True)
ws = wb['8月']

# 安全转换函数
def safe_float(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val.replace(',', ''))
        except:
            return 0.0
    return 0.0

# 提取8月数据
data_list = []
for row in range(3, ws.max_row + 1):
    name = ws.cell(row, 3).value
    if not name:
        continue

    item = {
        'name': name,
        'spec': ws.cell(row, 6).value or '',
        'qty': safe_float(ws.cell(row, 9).value),
        'material_cost': safe_float(ws.cell(row, 47).value),
        'labor_cost': safe_float(ws.cell(row, 54).value),
        'mfg_cost': safe_float(ws.cell(row, 65).value),
        'std_cost': safe_float(ws.cell(row, 66).value),
        'act_cost': safe_float(ws.cell(row, 67).value),
        'unit_cost': safe_float(ws.cell(row, 69).value),
        'variance_rate': safe_float(ws.cell(row, 70).value),
    }
    data_list.append(item)

# 统计汇总
total_qty = sum(item['qty'] for item in data_list)
total_material = sum(item['material_cost'] for item in data_list)
total_labor = sum(item['labor_cost'] for item in data_list)
total_mfg = sum(item['mfg_cost'] for item in data_list)
total_act_cost = sum(item['act_cost'] for item in data_list)
total_std_cost = sum(item['std_cost'] for item in data_list)
variance = total_act_cost - total_std_cost
variance_rate = (variance / total_std_cost * 100) if total_std_cost > 0 else 0

# 成本构成占比
material_pct = (total_material / total_act_cost * 100) if total_act_cost > 0 else 0
labor_pct = (total_labor / total_act_cost * 100) if total_act_cost > 0 else 0
mfg_pct = (total_mfg / total_act_cost * 100) if total_act_cost > 0 else 0

# TOP 5 异常品种（成本差异率绝对值最大）
data_list_sorted = sorted(data_list, key=lambda x: abs(x['variance_rate']), reverse=True)
top5_abnormal = data_list_sorted[:5]

# TOP 5 产量最大品种
data_list_sorted_qty = sorted(data_list, key=lambda x: x['qty'], reverse=True)
top5_qty = data_list_sorted_qty[:5]

# 创建PPT
prs = Presentation()
prs.slide_width = Inches(10)
prs.slide_height = Inches(5.625)

# 配色方案
COLOR_TITLE = RGBColor(31, 73, 125)
COLOR_ACCENT = RGBColor(192, 0, 0)
COLOR_DARK = RGBColor(68, 68, 68)

def add_title_slide(prs, title, subtitle):
    """封面页"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # 标题
    title_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(1))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = COLOR_TITLE
    p.alignment = PP_ALIGN.CENTER

    # 副标题
    subtitle_box = slide.shapes.add_textbox(Inches(1), Inches(3.5), Inches(8), Inches(0.6))
    subtitle_frame = subtitle_box.text_frame
    p = subtitle_frame.paragraphs[0]
    p.text = subtitle
    p.font.size = Pt(24)
    p.font.color.rgb = COLOR_DARK
    p.alignment = PP_ALIGN.CENTER

def add_content_slide(prs, title, content_func):
    """内容页"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # 标题
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.6))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = COLOR_TITLE

    # 内容由回调函数生成
    content_func(slide)

# 第1页：封面
add_title_slide(prs, "织造车间成本分析报告", "2026年8月 | 财务部")

# 第2页：成本体系搭建历程
def content_page2(slide):
    left = Inches(1)
    top = Inches(1.2)

    text_box = slide.shapes.add_textbox(left, top, Inches(8), Inches(3.5))
    tf = text_box.text_frame
    tf.word_wrap = True

    sections = [
        ("入职前（7月）", [
            "无成本核算体系",
            "领料混乱，无法追溯到订单",
            "次品未登记，成本虚高",
            "厂长无考核指标"
        ]),
        ("搭建期（8月）", [
            "建立标准成本卡（基于工艺单）",
            "规范ABC分级管理",
            "按品种核算单位成本",
            "建立成本差异分析机制"
        ]),
        ("8月成果", [
            f"完成{len(data_list)}个品种的成本核算",
            f"总产量{total_qty/1000:.1f}吨",
            f"识别成本差异{variance_rate:.1f}%",
            "建立厂长考核指标体系"
        ])
    ]

    for i, (section_title, items) in enumerate(sections):
        p = tf.add_paragraph()
        p.text = section_title
        p.font.size = Pt(18)
        p.font.bold = True
        p.font.color.rgb = COLOR_ACCENT
        p.space_after = Pt(6)

        for item in items:
            p = tf.add_paragraph()
            p.text = f"  • {item}"
            p.font.size = Pt(14)
            p.font.color.rgb = COLOR_DARK
            p.level = 1
            p.space_after = Pt(3)

        if i < len(sections) - 1:
            tf.add_paragraph().space_after = Pt(12)

add_content_slide(prs, "一、成本体系搭建历程", content_page2)

# 第3页：8月成本总览
def content_page3(slide):
    left = Inches(1)
    top = Inches(1.2)

    items = [
        ("生产品种", f"{len(data_list)}个"),
        ("总产量", f"{total_qty/1000:.1f}吨"),
        ("实际总成本", f"{total_act_cost/10000:.1f}万元"),
        ("标准总成本", f"{total_std_cost/10000:.1f}万元"),
        ("成本差异", f"{variance/10000:+.1f}万元 ({variance_rate:+.1f}%)"),
        ("平均单位成本", f"{total_act_cost/total_qty:.2f}元/kg"),
    ]

    box_width = Inches(3.5)
    box_height = Inches(1)
    spacing_x = Inches(0.3)
    spacing_y = Inches(0.2)

    for i, (label, value) in enumerate(items):
        row = i // 2
        col = i % 2

        x = left + col * (box_width + spacing_x)
        y = top + row * (box_height + spacing_y)

        # 背景框
        shape = slide.shapes.add_shape(
            1,  # 矩形
            x, y, box_width, box_height
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(240, 240, 240)
        shape.line.color.rgb = RGBColor(200, 200, 200)

        # 标签
        text_box = slide.shapes.add_textbox(x, y + Inches(0.15), box_width, Inches(0.3))
        tf = text_box.text_frame
        p = tf.paragraphs[0]
        p.text = label
        p.font.size = Pt(14)
        p.font.color.rgb = COLOR_DARK
        p.alignment = PP_ALIGN.CENTER

        # 数值
        text_box2 = slide.shapes.add_textbox(x, y + Inches(0.5), box_width, Inches(0.4))
        tf2 = text_box2.text_frame
        p2 = tf2.paragraphs[0]
        p2.text = value
        p2.font.size = Pt(20)
        p2.font.bold = True
        p2.font.color.rgb = COLOR_ACCENT if "差异" in label else COLOR_TITLE
        p2.alignment = PP_ALIGN.CENTER

add_content_slide(prs, "二、8月成本总览", content_page3)

# 第4页：成本构成分析
def content_page4(slide):
    left = Inches(1.5)
    top = Inches(1.5)
    width = Inches(7)

    items = [
        ("原材料成本", total_material, material_pct),
        ("直接人工", total_labor, labor_pct),
        ("制造费用", total_mfg, mfg_pct),
    ]

    bar_height = Inches(0.6)
    spacing = Inches(0.4)

    for i, (label, amount, pct) in enumerate(items):
        y = top + i * (bar_height + spacing)

        # 标签
        text_box = slide.shapes.add_textbox(left - Inches(1.2), y, Inches(1), bar_height)
        tf = text_box.text_frame
        tf.vertical_anchor = 1  # 居中
        p = tf.paragraphs[0]
        p.text = label
        p.font.size = Pt(16)
        p.font.color.rgb = COLOR_DARK
        p.alignment = PP_ALIGN.RIGHT

        # 背景条
        bg_shape = slide.shapes.add_shape(
            1,  # 矩形
            left, y, width, bar_height
        )
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = RGBColor(230, 230, 230)
        bg_shape.line.width = Pt(0)

        # 数据条
        data_width = width * (pct / 100)
        data_shape = slide.shapes.add_shape(
            1,  # 矩形
            left, y, data_width, bar_height
        )
        data_shape.fill.solid()
        colors = [
            RGBColor(70, 130, 180),
            RGBColor(220, 130, 50),
            RGBColor(100, 160, 100),
        ]
        data_shape.fill.fore_color.rgb = colors[i]
        data_shape.line.width = Pt(0)

        # 百分比标签
        text_box2 = slide.shapes.add_textbox(left + data_width + Inches(0.1), y, Inches(2), bar_height)
        tf2 = text_box2.text_frame
        tf2.vertical_anchor = 1
        p2 = tf2.paragraphs[0]
        p2.text = f"{pct:.1f}% ({amount/10000:.1f}万元)"
        p2.font.size = Pt(14)
        p2.font.bold = True
        p2.font.color.rgb = colors[i]

add_content_slide(prs, "三、成本构成分析", content_page4)

# 第5页：TOP 5异常品种
def content_page5(slide):
    left = Inches(0.8)
    top = Inches(1.3)

    # 表头
    headers = ["品种", "产量(kg)", "实际成本(元)", "差异率"]
    col_widths = [Inches(3), Inches(1.5), Inches(2), Inches(1.5)]

    row_height = Inches(0.4)

    # 绘制表头
    x = left
    for i, (header, width) in enumerate(zip(headers, col_widths)):
        shape = slide.shapes.add_shape(1, x, top, width, row_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = COLOR_TITLE
        shape.line.color.rgb = RGBColor(255, 255, 255)

        text_box = slide.shapes.add_textbox(x, top, width, row_height)
        tf = text_box.text_frame
        tf.vertical_anchor = 1
        p = tf.paragraphs[0]
        p.text = header
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.CENTER

        x += width

    # 绘制数据行
    for i, item in enumerate(top5_abnormal):
        y = top + (i + 1) * row_height

        values = [
            f"{item['name'][:15]}...",
            f"{item['qty']:.0f}",
            f"{item['act_cost']:.0f}",
            f"{item['variance_rate']*100:+.1f}%"
        ]

        x = left
        for j, (value, width) in enumerate(zip(values, col_widths)):
            # 背景
            shape = slide.shapes.add_shape(1, x, y, width, row_height)
            shape.fill.solid()
            bg_color = RGBColor(250, 250, 250) if i % 2 == 0 else RGBColor(240, 240, 240)
            shape.fill.fore_color.rgb = bg_color
            shape.line.color.rgb = RGBColor(220, 220, 220)

            # 文本
            text_box = slide.shapes.add_textbox(x, y, width, row_height)
            tf = text_box.text_frame
            tf.vertical_anchor = 1
            p = tf.paragraphs[0]
            p.text = value
            p.font.size = Pt(12)
            p.font.color.rgb = COLOR_ACCENT if j == 3 else COLOR_DARK
            p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT

            x += width

add_content_slide(prs, "四、TOP 5成本异常品种", content_page5)

# 第6页：问题诊断
def content_page6(slide):
    left = Inches(1)
    top = Inches(1.2)

    text_box = slide.shapes.add_textbox(left, top, Inches(8), Inches(3.5))
    tf = text_box.text_frame
    tf.word_wrap = True

    problems = [
        ("问题1：领料混乱", [
            "现象：车间随意领料，不按订单领用",
            "影响：无法准确追溯材料成本到具体品种",
            "解决：推行按单领料，ERP系统强制绑定订单号"
        ]),
        ("问题2：次品未登记", [
            "现象：BC级次品一直没有入库登记",
            "影响：成本虚高5-10%，存货盘点账实不符",
            "解决：建立次品仓，规范ABC分级管理"
        ]),
        ("问题3：人工分摊粗糙", [
            "现象：挡车工按产量均摊，无法细分到品种",
            "影响：复杂品种与简单品种成本失真",
            "解决：10月启用采集器数据，按品种分摊"
        ])
    ]

    for i, (problem_title, items) in enumerate(problems):
        p = tf.add_paragraph()
        p.text = problem_title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_ACCENT
        p.space_after = Pt(6)

        for item in items:
            p = tf.add_paragraph()
            p.text = f"  {item}"
            p.font.size = Pt(13)
            p.font.color.rgb = COLOR_DARK
            p.level = 1
            p.space_after = Pt(3)

        if i < len(problems) - 1:
            tf.add_paragraph().space_after = Pt(10)

add_content_slide(prs, "五、问题诊断", content_page6)

# 第7页：改善计划
def content_page7(slide):
    left = Inches(1)
    top = Inches(1.2)

    text_box = slide.shapes.add_textbox(left, top, Inches(8), Inches(3.5))
    tf = text_box.text_frame
    tf.word_wrap = True

    plans = [
        ("9月（规范期）", [
            "完成次品仓建立，所有BC级次品入库登记",
            "推行按单领料，试点3个主力品种",
            "建立月度成本差异分析报告机制"
        ]),
        ("10月（优化期）", [
            "启用采集器数据，实现挡车工成本按品种分摊",
            "全面推行按单领料，覆盖所有品种",
            "建立品种盈利能力排行榜，淘汰亏损品种"
        ]),
        ("11月（考核期）", [
            "启动厂长成本考核（织损率、次品率、成本达成率）",
            "建立成本预警机制，差异>10%自动预警",
            "实现成本数据实时看板（Power BI）"
        ])
    ]

    for i, (plan_title, items) in enumerate(plans):
        p = tf.add_paragraph()
        p.text = plan_title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_TITLE
        p.space_after = Pt(6)

        for item in items:
            p = tf.add_paragraph()
            p.text = f"  • {item}"
            p.font.size = Pt(13)
            p.font.color.rgb = COLOR_DARK
            p.level = 1
            p.space_after = Pt(3)

        if i < len(plans) - 1:
            tf.add_paragraph().space_after = Pt(10)

add_content_slide(prs, "六、三个月改善计划", content_page7)

# 第8页：厂长考核建议
def content_page8(slide):
    left = Inches(1)
    top = Inches(1.3)

    # 表头
    headers = ["考核指标", "当前值", "目标值", "权重"]
    col_widths = [Inches(2.5), Inches(2), Inches(2), Inches(1.5)]

    row_height = Inches(0.5)

    # 绘制表头
    x = left
    for i, (header, width) in enumerate(zip(headers, col_widths)):
        shape = slide.shapes.add_shape(1, x, top, width, row_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = COLOR_TITLE
        shape.line.color.rgb = RGBColor(255, 255, 255)

        text_box = slide.shapes.add_textbox(x, top, width, row_height)
        tf = text_box.text_frame
        tf.vertical_anchor = 1
        p = tf.paragraphs[0]
        p.text = header
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.CENTER

        x += width

    # 数据行
    kpi_data = [
        ("织损率", "待统计", "≤3%", "20%"),
        ("次品率", "待统计", "≤5%", "25%"),
        ("成本达成率", f"{variance_rate:+.1f}%", "≤标准成本", "30%"),
        ("按单领料执行率", "0%", "100%", "15%"),
        ("成本数据及时性", "待评估", "T+3日", "10%"),
    ]

    for i, (kpi, current, target, weight) in enumerate(kpi_data):
        y = top + (i + 1) * row_height

        values = [kpi, current, target, weight]

        x = left
        for j, (value, width) in enumerate(zip(values, col_widths)):
            # 背景
            shape = slide.shapes.add_shape(1, x, y, width, row_height)
            shape.fill.solid()
            bg_color = RGBColor(250, 250, 250) if i % 2 == 0 else RGBColor(240, 240, 240)
            shape.fill.fore_color.rgb = bg_color
            shape.line.color.rgb = RGBColor(220, 220, 220)

            # 文本
            text_box = slide.shapes.add_textbox(x, y, width, row_height)
            tf = text_box.text_frame
            tf.vertical_anchor = 1
            p = tf.paragraphs[0]
            p.text = value
            p.font.size = Pt(13)
            p.font.color.rgb = COLOR_DARK
            p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT

            x += width

add_content_slide(prs, "七、厂长考核指标建议", content_page8)

# 保存PPT
output_path = 'd:/AI-项目/12-成本控制/01-交付物归档/2026-09/织造车间成本分析_202609_v2.pptx'
prs.save(output_path)

print(f"Done: {output_path}")
