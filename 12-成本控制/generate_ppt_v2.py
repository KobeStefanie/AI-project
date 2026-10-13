#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
成本分析PPT生成 - 基于完整数据逻辑
"""
import openpyxl
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

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

def add_title_slide(prs, title, subtitle):
    """添加标题页"""
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = title
    slide.placeholders[1].text = subtitle
    return slide

def add_content_slide(prs, title):
    """添加内容页（空白）"""
    slide = prs.slides.add_slide(prs.slide_layouts[5])

    # 标题
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.6))
    title_frame = title_box.text_frame
    title_frame.text = title
    p = title_frame.paragraphs[0]
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0, 51, 102)

    return slide

# 读取Excel数据
summary_file = r'C:\Users\Administrator\Desktop\华盛\成本PPT汇报\成本核算汇总-标准成本 - 加工与自产.xlsx'
wb = openpyxl.load_workbook(summary_file, data_only=True)

# 读取8月数据
ws = wb['8月']
items = []
for row_idx in range(3, ws.max_row + 1):
    name = ws.cell(row_idx, 3).value
    if not name or name == '合计':
        continue

    item = {
        'name': name,
        'type': ws.cell(row_idx, 4).value or '',
        'qty': safe_float(ws.cell(row_idx, 9).value),
        'material': safe_float(ws.cell(row_idx, 47).value),
        'labor': safe_float(ws.cell(row_idx, 54).value),
        'mfg': safe_float(ws.cell(row_idx, 65).value),
        'std_cost': safe_float(ws.cell(row_idx, 66).value),
        'act_cost': safe_float(ws.cell(row_idx, 67).value),
        'std_unit': safe_float(ws.cell(row_idx, 68).value),
        'act_unit': safe_float(ws.cell(row_idx, 69).value),
        'variance': safe_float(ws.cell(row_idx, 70).value),
        # 纱支信息
        'yarn1_name': ws.cell(row_idx, 12).value or '',
        'yarn1_ratio': safe_float(ws.cell(row_idx, 13).value),
        'yarn1_amt': safe_float(ws.cell(row_idx, 21).value),
        'yarn2_name': ws.cell(row_idx, 23).value or '',
        'yarn2_ratio': safe_float(ws.cell(row_idx, 24).value),
        'yarn2_amt': safe_float(ws.cell(row_idx, 32).value),
        'yarn3_name': ws.cell(row_idx, 34).value or '',
        'yarn3_ratio': safe_float(ws.cell(row_idx, 35).value),
        'yarn3_amt': safe_float(ws.cell(row_idx, 43).value),
    }

    if item['qty'] > 0 or item['act_cost'] > 0:
        items.append(item)

print(f"读取8月数据：{len(items)}个品种")

# 计算汇总数据
total_qty = sum(item['qty'] for item in items)
total_material = sum(item['material'] for item in items)
total_labor = sum(item['labor'] for item in items)
total_mfg = sum(item['mfg'] for item in items)
total_cost = total_material + total_labor + total_mfg
total_std = sum(item['std_cost'] for item in items)

print(f"8月总成本：{total_cost/10000:.2f}万元")
print(f"  原材料：{total_material/10000:.2f}万元 ({total_material/total_cost*100:.1f}%)")
print(f"  人工：{total_labor/10000:.2f}万元 ({total_labor/total_cost*100:.1f}%)")
print(f"  制造费用：{total_mfg/10000:.2f}万元 ({total_mfg/total_cost*100:.1f}%)")

# 创建PPT
prs = Presentation()
prs.slide_width = Inches(10)
prs.slide_height = Inches(7.5)

# 第1页：封面
add_title_slide(prs, "织造车间成本管理体系建设", "2026年4-8月成本核算与改善方案\n财务部")

# 第2页：成本核算体系介绍
slide = add_content_slide(prs, "成本核算体系：标准成本法")
left = Inches(0.8)
top = Inches(1.5)
width = Inches(8.5)
height = Inches(5)

textbox = slide.shapes.add_textbox(left, top, width, height)
tf = textbox.text_frame
tf.word_wrap = True

content = f"""核心逻辑：实际成本 = 原材料 + 人工 + 制造费用

【原材料成本】
• 每个品种由1-3种纱支（原纱）组成
• 成本 = Σ(纱支i的实际出库量 × 出库单价)
• 数据来源：ERP出库单、工艺单配比

【人工成本】
• 挡车工、验布工、其他车间人员
• 按产量比例分摊到每个品种

【制造费用】
• 折旧、机物料、水电费、其他费用
• 按分配比例分摊到每个品种

【标准成本 vs 实际成本】
• 标准成本：按工艺单理论用量计算
• 实际成本：按实际出库量计算
• 变动率 = (实际-标准)/标准，反映成本管控水平"""

for line in content.split('\n'):
    p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(14)
    p.level = 1 if line.startswith('【') else 2
    if line.startswith('【'):
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 51, 102)
    p.space_after = Pt(6)

# 第3页：8月成本数据总览
slide = add_content_slide(prs, "8月成本数据总览")
left = Inches(1)
top = Inches(1.5)
width = Inches(8)
height = Inches(5)

textbox = slide.shapes.add_textbox(left, top, width, height)
tf = textbox.text_frame

content = f"""生产品种：{len(items)}个（自产 + 加工）

总产量：{total_qty:,.0f} KG

实际总成本：{total_cost/10000:.2f}万元
  • 原材料：{total_material/10000:.2f}万元 ({total_material/total_cost*100:.1f}%)
  • 人工：{total_labor/10000:.2f}万元 ({total_labor/total_cost*100:.1f}%)
  • 制造费用：{total_mfg/10000:.2f}万元 ({total_mfg/total_cost*100:.1f}%)

平均单位成本：{total_cost/total_qty:.2f}元/KG

标准总成本：{total_std/10000:.2f}万元
实际 vs 标准差异：{(total_cost-total_std)/10000:.2f}万元"""

for line in content.split('\n'):
    p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(16)
    if '：' in line and not line.startswith(' '):
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 51, 102)
    p.space_after = Pt(10)

# 第4页：成本构成占比（饼图）
slide = add_content_slide(prs, "8月成本构成分析")

chart_data = CategoryChartData()
chart_data.categories = ['原材料', '人工', '制造费用']
chart_data.add_series('成本构成', (total_material, total_labor, total_mfg))

x, y, cx, cy = Inches(2), Inches(2), Inches(6), Inches(4.5)
chart = slide.shapes.add_chart(
    XL_CHART_TYPE.PIE, x, y, cx, cy, chart_data
).chart

chart.has_legend = True
chart.legend.position = XL_LEGEND_POSITION.BOTTOM
chart.legend.include_in_layout = False

# 数据标签
chart.plots[0].has_data_labels = True
data_labels = chart.plots[0].data_labels
data_labels.show_percentage = True
data_labels.show_value = False

# 第5页：TOP5异常品种（变动率）
slide = add_content_slide(prs, "成本异常品种识别（TOP 5）")

# 按变动率绝对值排序
abnormal = sorted([item for item in items if abs(item['variance']) > 0.1],
                  key=lambda x: abs(x['variance']), reverse=True)[:5]

left = Inches(0.8)
top = Inches(1.5)
width = Inches(8.5)
height = Inches(0.8)

# 表头
rows = 6
cols = 5
table = slide.shapes.add_table(rows, cols, left, top, width, height * rows).table

headers = ['品种名称', '产量(KG)', '实际成本(元)', '变动率', '异常原因']
for col_idx, header in enumerate(headers):
    cell = table.cell(0, col_idx)
    cell.text = header
    cell.text_frame.paragraphs[0].font.bold = True
    cell.text_frame.paragraphs[0].font.size = Pt(12)
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(0, 51, 102)
    cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)

for idx, item in enumerate(abnormal, 1):
    # 判断异常原因
    reason = ""
    if item['material'] == 0:
        reason = "领料数据缺失"
    elif abs(item['variance']) > 0.3:
        reason = "实际用量严重偏离标准"
    elif abs(item['variance']) > 0.15:
        reason = "成本差异较大"
    else:
        reason = "成本超支"

    table.cell(idx, 0).text = item['name'][:15]
    table.cell(idx, 1).text = f"{item['qty']:,.0f}"
    table.cell(idx, 2).text = f"{item['act_cost']:,.0f}"
    table.cell(idx, 3).text = f"{item['variance']*100:.1f}%"
    table.cell(idx, 4).text = reason

    for col_idx in range(5):
        table.cell(idx, col_idx).text_frame.paragraphs[0].font.size = Pt(11)

# 第6页：原材料结构示例（纱支配比）
slide = add_content_slide(prs, "原材料成本构成示例：华棉150D")

# 选取华棉150D作为示例
example = next((item for item in items if '华棉150D' in item['name']), items[0])

left = Inches(1)
top = Inches(1.5)
width = Inches(8)
height = Inches(5)

textbox = slide.shapes.add_textbox(left, top, width, height)
tf = textbox.text_frame

yarn_info = []
if example['yarn1_name']:
    yarn_info.append(f"  纱支1：{example['yarn1_name']} ({example['yarn1_ratio']:.2f}%) = {example['yarn1_amt']:,.0f}元")
if example['yarn2_name']:
    yarn_info.append(f"  纱支2：{example['yarn2_name']} ({example['yarn2_ratio']:.2f}%) = {example['yarn2_amt']:,.0f}元")
if example['yarn3_name']:
    yarn_info.append(f"  纱支3：{example['yarn3_name']} ({example['yarn3_ratio']:.2f}%) = {example['yarn3_amt']:,.0f}元")

content = f"""品种：{example['name']}

产量：{example['qty']:,.0f} KG

【原材料成本】= {example['material']:,.0f}元
{chr(10).join(yarn_info)}

【人工成本】= {example['labor']:,.0f}元

【制造费用】= {example['mfg']:,.0f}元

【实际总成本】= {example['act_cost']:,.0f}元
【标准总成本】= {example['std_cost']:,.0f}元
【变动率】= {example['variance']*100:.2f}%"""

for line in content.split('\n'):
    p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(14)
    if line.startswith('【'):
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 51, 102)
    p.space_after = Pt(8)

# 第7页：当前存在的问题
slide = add_content_slide(prs, "当前存在的问题")

# 统计问题
missing_material = sum(1 for item in items if item['material'] == 0)
high_variance = sum(1 for item in items if abs(item['variance']) > 0.15)

left = Inches(1)
top = Inches(1.5)
width = Inches(8)
height = Inches(5)

textbox = slide.shapes.add_textbox(left, top, width, height)
tf = textbox.text_frame

content = f"""问题1：领料数据不完整
• {missing_material}个品种原材料成本为0（领料单未录入ERP）
• 导致成本严重失真，无法准确评估产品盈利性

问题2：成本差异率偏高
• {high_variance}个品种变动率>15%（实际与标准差异大）
• 原因：工艺单理论用量与实际织损率差异、领料不规范

问题3：人工成本分摊粗糙
• 按产量比例分摊，未考虑工艺复杂度差异
• 高难度品种与普通品种人工成本趋同

问题4：成本数据滞后
• 月末3-5天才能出成本报告
• ERP数据需要手工清洗、核对"""

for line in content.split('\n'):
    p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(14)
    if line.startswith('问题'):
        p.font.bold = True
        p.font.color.rgb = RGBColor(204, 0, 0)
        p.space_before = Pt(10)
    p.space_after = Pt(6)

# 第8页：改善计划
slide = add_content_slide(prs, "9-11月改善计划")

left = Inches(1)
top = Inches(1.5)
width = Inches(8)
height = Inches(5)

textbox = slide.shapes.add_textbox(left, top, width, height)
tf = textbox.text_frame

content = """【9月：规范期】
• 推动车间规范领料流程（按生产订单领料）
• 每日核对ERP出库单与实际生产
• 建立BC级次品单独登记表

【10月：精细化期】
• 引入工序采集器数据，精细化人工成本分摊
• 开展品种盈利分析（单位成本 vs 销售单价）
• 优化工艺单理论用量（减少标准与实际的差异）

【11月：系统化期】
• 建立成本预警机制（变动率>10%自动提醒）
• 搭建Power BI成本看板（日报、周报）
• 月度成本分析会制度化

【预期成果】
✓ 成本数据准确率>95%
✓ 成本报告时效缩短至2天
✓ 管理层能实时掌握品种盈利情况"""

for line in content.split('\n'):
    p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(14)
    if line.startswith('【'):
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 102, 51)
        p.space_before = Pt(12)
    elif line.startswith('✓'):
        p.font.color.rgb = RGBColor(0, 153, 0)
    p.space_after = Pt(6)

# 保存PPT
output_path = r'd:\AI-项目\12-成本控制\01-交付物归档\2026-09\织造车间成本管理体系_完整版_202609.pptx'
prs.save(output_path)

print(f"\n✓ PPT生成成功：{output_path}")
print(f"\n包含内容：")
print("1. 封面")
print("2. 成本核算体系介绍（标准成本法逻辑）")
print("3. 8月成本数据总览（总成本、构成）")
print("4. 成本构成占比（饼图）")
print("5. TOP5异常品种（变动率分析）")
print("6. 原材料结构示例（纱支配比）")
print("7. 当前存在的问题（4个核心问题）")
print("8. 9-11月改善计划")

wb.close()
