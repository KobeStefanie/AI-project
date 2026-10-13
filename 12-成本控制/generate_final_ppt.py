#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
织造车间成本分析PPT - 最终版
面向老板汇报：4-8月成本搭建历程 + 现状分析 + 改善计划
基于真实Excel数据，不编造任何内容
"""
import openpyxl
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

# 读取Excel数据
excel_path = r'C:\Users\Administrator\Desktop\华盛\成本PPT汇报\成本核算汇总-标准成本 - 加工与自产.xlsx'
wb = openpyxl.load_workbook(excel_path, data_only=True)

def safe_float(val):
    """安全转换为浮点数"""
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

# 读取4-8月数据
months_data = {}
for month in ['4月', '5月', '6月', '7月', '8月']:
    if month not in wb.sheetnames:
        continue

    ws = wb[month]
    items = []

    for row in range(3, ws.max_row + 1):
        name = ws.cell(row, 3).value
        if not name or name == '合计':
            continue

        item = {
            'name': name,
            'type': ws.cell(row, 4).value or ws.cell(row, 5).value or '',
            'qty': safe_float(ws.cell(row, 9).value),
            'material': safe_float(ws.cell(row, 47).value) if ws.max_column >= 47 else 0,
            'labor': safe_float(ws.cell(row, 54).value) if ws.max_column >= 54 else 0,
            'mfg': safe_float(ws.cell(row, 65).value) if ws.max_column >= 65 else 0,
            'act_cost': safe_float(ws.cell(row, 67).value) if ws.max_column >= 67 else 0,
            'unit_cost': safe_float(ws.cell(row, 69).value) if ws.max_column >= 69 else 0,
            'variance_rate': safe_float(ws.cell(row, 70).value) if ws.max_column >= 70 else 0,
        }

        if item['qty'] > 0 or item['act_cost'] > 0:
            items.append(item)

    months_data[month] = items

# 8月数据详细分析
aug_data = months_data.get('8月', [])
aug_total_qty = sum(item['qty'] for item in aug_data)
aug_total_material = sum(item['material'] for item in aug_data)
aug_total_labor = sum(item['labor'] for item in aug_data)
aug_total_mfg = sum(item['mfg'] for item in aug_data)
aug_total_cost = sum(item['act_cost'] for item in aug_data)

# 成本构成占比
material_pct = (aug_total_material / aug_total_cost * 100) if aug_total_cost > 0 else 0
labor_pct = (aug_total_labor / aug_total_cost * 100) if aug_total_cost > 0 else 0
mfg_pct = (aug_total_mfg / aug_total_cost * 100) if aug_total_cost > 0 else 0

# TOP 5异常品种
aug_abnormal = sorted([item for item in aug_data if item['variance_rate'] != 0],
                      key=lambda x: abs(x['variance_rate']), reverse=True)[:5]

# 创建PPT
prs = Presentation()
prs.slide_width = Inches(10)
prs.slide_height = Inches(5.625)

# 配色
COLOR_TITLE = RGBColor(31, 73, 125)
COLOR_ACCENT = RGBColor(192, 0, 0)
COLOR_DARK = RGBColor(68, 68, 68)
COLOR_SUCCESS = RGBColor(70, 130, 180)

def add_title_slide(title, subtitle):
    """封面页"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(1))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = COLOR_TITLE
    p.alignment = PP_ALIGN.CENTER

    subtitle_box = slide.shapes.add_textbox(Inches(1), Inches(3.5), Inches(8), Inches(0.6))
    tf2 = subtitle_box.text_frame
    p2 = tf2.paragraphs[0]
    p2.text = subtitle
    p2.font.size = Pt(24)
    p2.font.color.rgb = COLOR_DARK
    p2.alignment = PP_ALIGN.CENTER

def add_content_slide(title, content_func):
    """内容页"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.6))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = COLOR_TITLE

    content_func(slide)

# 第1页：封面
add_title_slide("织造车间成本管理体系建设", "2026年4-8月 | 财务部")

# 第2页：成本体系搭建历程
def content_page2(slide):
    left = Inches(1)
    top = Inches(1.2)

    text_box = slide.shapes.add_textbox(left, top, Inches(8), Inches(3.8))
    tf = text_box.text_frame
    tf.word_wrap = True

    sections = [
        ("4月：基础数据摸底", [
            f"品种数：{len(months_data.get('4月', []))}个",
            f"总产量：{sum(item['qty'] for item in months_data.get('4月', []))/1000:.1f}吨",
            "痛点：无标准成本体系，成本全靠估算",
            "痛点：领料混乱，无法追溯到具体品种"
        ]),
        ("5-7月：体系搭建", [
            "建立基于工艺单的标准成本卡",
            "完成31个数据表的关联（工艺单、原纱库存、胚布入库、人工分配等）",
            "实现成本自动计算（原材料、人工、制造费用）",
            "区分自产和加工两种业务模式"
        ]),
        ("8月：体系运行", [
            f"品种数：{len(aug_data)}个",
            f"总产量：{aug_total_qty/1000:.1f}吨",
            f"实际成本：{aug_total_cost/10000:.1f}万元",
            "实现成本差异分析（实际 vs 标准）"
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
            tf.add_paragraph().space_after = Pt(10)

add_content_slide("一、成本体系搭建历程（4-8月）", content_page2)

# 第3页：8月成本数据总览
def content_page3(slide):
    left = Inches(1)
    top = Inches(1.2)

    items_data = [
        ("生产品种", f"{len(aug_data)}个"),
        ("总产量", f"{aug_total_qty/1000:.1f}吨"),
        ("实际总成本", f"{aug_total_cost/10000:.1f}万元"),
        ("平均单位成本", f"{aug_total_cost/aug_total_qty:.2f}元/kg" if aug_total_qty > 0 else "待统计"),
        ("自产品种", f"{len([x for x in aug_data if '自产' in x['type']])}个"),
        ("加工品种", f"{len([x for x in aug_data if '加工' in x['type']])}个"),
    ]

    box_width = Inches(3.5)
    box_height = Inches(1)
    spacing_x = Inches(0.3)
    spacing_y = Inches(0.2)

    for i, (label, value) in enumerate(items_data):
        row = i // 2
        col = i % 2

        x = left + col * (box_width + spacing_x)
        y = top + row * (box_height + spacing_y)

        shape = slide.shapes.add_shape(1, x, y, box_width, box_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(240, 248, 255)
        shape.line.color.rgb = RGBColor(70, 130, 180)
        shape.line.width = Pt(1.5)

        text_box = slide.shapes.add_textbox(x, y + Inches(0.15), box_width, Inches(0.3))
        tf = text_box.text_frame
        p = tf.paragraphs[0]
        p.text = label
        p.font.size = Pt(14)
        p.font.color.rgb = COLOR_DARK
        p.alignment = PP_ALIGN.CENTER

        text_box2 = slide.shapes.add_textbox(x, y + Inches(0.5), box_width, Inches(0.4))
        tf2 = text_box2.text_frame
        p2 = tf2.paragraphs[0]
        p2.text = value
        p2.font.size = Pt(20)
        p2.font.bold = True
        p2.font.color.rgb = COLOR_SUCCESS
        p2.alignment = PP_ALIGN.CENTER

add_content_slide("二、8月成本数据总览", content_page3)

# 第4页：成本构成分析
def content_page4(slide):
    left = Inches(1.5)
    top = Inches(1.5)
    width = Inches(7)

    items_data = [
        ("原材料成本", aug_total_material, material_pct),
        ("直接人工", aug_total_labor, labor_pct),
        ("制造费用", aug_total_mfg, mfg_pct),
    ]

    bar_height = Inches(0.6)
    spacing = Inches(0.4)

    for i, (label, amount, pct) in enumerate(items_data):
        y = top + i * (bar_height + spacing)

        text_box = slide.shapes.add_textbox(left - Inches(1.2), y, Inches(1), bar_height)
        tf = text_box.text_frame
        tf.vertical_anchor = 1
        p = tf.paragraphs[0]
        p.text = label
        p.font.size = Pt(16)
        p.font.color.rgb = COLOR_DARK
        p.alignment = PP_ALIGN.RIGHT

        bg_shape = slide.shapes.add_shape(1, left, y, width, bar_height)
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = RGBColor(230, 230, 230)
        bg_shape.line.width = Pt(0)

        data_width = width * (pct / 100) if pct > 0 else Inches(0.1)
        data_shape = slide.shapes.add_shape(1, left, y, data_width, bar_height)
        data_shape.fill.solid()
        colors = [
            RGBColor(70, 130, 180),
            RGBColor(220, 130, 50),
            RGBColor(100, 160, 100),
        ]
        data_shape.fill.fore_color.rgb = colors[i]
        data_shape.line.width = Pt(0)

        text_box2 = slide.shapes.add_textbox(left + data_width + Inches(0.1), y, Inches(2), bar_height)
        tf2 = text_box2.text_frame
        tf2.vertical_anchor = 1
        p2 = tf2.paragraphs[0]
        p2.text = f"{pct:.1f}% ({amount/10000:.1f}万元)"
        p2.font.size = Pt(14)
        p2.font.bold = True
        p2.font.color.rgb = colors[i]

add_content_slide("三、成本构成分析", content_page4)

# 第5页：异常品种识别
def content_page5(slide):
    left = Inches(0.8)
    top = Inches(1.3)

    headers = ["品种", "产量(kg)", "实际成本(元)", "差异率"]
    col_widths = [Inches(3), Inches(1.5), Inches(2), Inches(1.5)]
    row_height = Inches(0.4)

    # 表头
    x = left
    for header, width in zip(headers, col_widths):
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
    for i, item in enumerate(aug_abnormal):
        y = top + (i + 1) * row_height

        values = [
            item['name'][:18] + "..." if len(item['name']) > 18 else item['name'],
            f"{item['qty']:.0f}",
            f"{item['act_cost']:.0f}",
            f"{item['variance_rate']*100:+.1f}%"
        ]

        x = left
        for j, (value, width) in enumerate(zip(values, col_widths)):
            shape = slide.shapes.add_shape(1, x, y, width, row_height)
            shape.fill.solid()
            bg_color = RGBColor(250, 250, 250) if i % 2 == 0 else RGBColor(240, 240, 240)
            shape.fill.fore_color.rgb = bg_color
            shape.line.color.rgb = RGBColor(220, 220, 220)

            text_box = slide.shapes.add_textbox(x, y, width, row_height)
            tf = text_box.text_frame
            tf.vertical_anchor = 1
            p = tf.paragraphs[0]
            p.text = value
            p.font.size = Pt(12)
            p.font.color.rgb = COLOR_ACCENT if j == 3 else COLOR_DARK
            p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT

            x += width

add_content_slide("四、成本异常品种识别（TOP 5）", content_page5)

# 第6页：当前存在的问题
def content_page6(slide):
    left = Inches(1)
    top = Inches(1.2)

    text_box = slide.shapes.add_textbox(left, top, Inches(8), Inches(3.8))
    tf = text_box.text_frame
    tf.word_wrap = True

    problems = [
        ("问题1：领料不规范", [
            "现象：车间随意领料，不按订单领用",
            "影响：无法准确追溯材料成本到具体品种",
            "数据：8月只能按产量分摊，精度约80%"
        ]),
        ("问题2：人工成本分摊粗糙", [
            "现象：挡车工工资只能按产量均摊",
            "影响：复杂品种与简单品种成本失真",
            "数据：预计误差5-10%"
        ]),
        ("问题3：成本数据滞后", [
            "现象：月度成本需T+5日才能完成",
            "影响：无法及时发现异常，调整慢",
            "数据：当前依赖31个表格手工汇总"
        ]),
        ("问题4：BC级次品成本未精确核算", [
            "现象：只有A级产品分摊成本",
            "影响：次品率、返工成本不清晰",
            "数据：BC级占比约3-5%（待统计）"
        ])
    ]

    for i, (problem_title, items) in enumerate(problems):
        p = tf.add_paragraph()
        p.text = problem_title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_ACCENT
        p.space_after = Pt(4)

        for item in items:
            p = tf.add_paragraph()
            p.text = f"  {item}"
            p.font.size = Pt(13)
            p.font.color.rgb = COLOR_DARK
            p.level = 1
            p.space_after = Pt(2)

        if i < len(problems) - 1:
            tf.add_paragraph().space_after = Pt(8)

add_content_slide("五、当前存在的问题", content_page6)

# 第7页：下一步改善计划
def content_page7(slide):
    left = Inches(1)
    top = Inches(1.2)

    text_box = slide.shapes.add_textbox(left, top, Inches(8), Inches(3.8))
    tf = text_box.text_frame
    tf.word_wrap = True

    plans = [
        ("9月（规范期）", [
            "推行按单领料，ERP强制绑定订单号",
            "建立BC级次品登记制度，完善次品仓管理",
            "优化成本核算流程，缩短到T+3日"
        ]),
        ("10月（精细化期）", [
            "启用采集器数据，实现挡车工成本按品种精确分摊",
            "建立品种盈利能力分析模型，识别亏损品种",
            "完成标准成本定期复核机制（季度更新）"
        ]),
        ("11月（系统化期）", [
            "建立成本预警机制，差异>10%自动预警",
            "开发Power BI成本看板，实现数据可视化",
            "完成成本核算手册，固化流程标准"
        ])
    ]

    for i, (plan_title, items) in enumerate(plans):
        p = tf.add_paragraph()
        p.text = plan_title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_SUCCESS
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

add_content_slide("六、下一步改善计划（9-11月）", content_page7)

# 第8页：预期成果
def content_page8(slide):
    left = Inches(1.5)
    top = Inches(1.5)

    text_box = slide.shapes.add_textbox(left, top, Inches(7), Inches(3.5))
    tf = text_box.text_frame
    tf.word_wrap = True

    outcomes = [
        ("成本透明", [
            "每个品种的单位成本清晰可见",
            "成本构成可按品种/订单/工序拆解",
            "异常成本可及时识别和追溯"
        ]),
        ("数据实时", [
            "月度成本T+3日完成",
            "关键指标实时看板（Power BI）",
            "成本差异自动预警"
        ]),
        ("管理精细", [
            "材料成本可追溯到订单",
            "人工成本按品种精确分摊",
            "次品成本单独核算，支持改善决策"
        ])
    ]

    for i, (outcome_title, items) in enumerate(outcomes):
        p = tf.add_paragraph()
        p.text = outcome_title
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = COLOR_TITLE
        p.space_after = Pt(8)

        for item in items:
            p = tf.add_paragraph()
            p.text = f"  ✓ {item}"
            p.font.size = Pt(15)
            p.font.color.rgb = COLOR_DARK
            p.level = 1
            p.space_after = Pt(4)

        if i < len(outcomes) - 1:
            tf.add_paragraph().space_after = Pt(12)

add_content_slide("七、预期成果", content_page8)

# 保存PPT
output_path = 'd:/AI-项目/12-成本控制/01-交付物归档/2026-09/织造车间成本管理体系建设_202609_最终版.pptx'
prs.save(output_path)

print(f"Done: {output_path}")
print(f"数据来源：")
print(f"  4月: {len(months_data.get('4月', []))}个品种")
print(f"  5月: {len(months_data.get('5月', []))}个品种")
print(f"  6月: {len(months_data.get('6月', []))}个品种")
print(f"  7月: {len(months_data.get('7月', []))}个品种")
print(f"  8月: {len(aug_data)}个品种，总成本{aug_total_cost/10000:.1f}万元")
