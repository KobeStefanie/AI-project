#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
成本分析PPT - 第一版数据（如实呈现问题）
"""
import openpyxl
import pickle
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

def safe_float(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        if val.startswith('#'):
            return 0.0
        try:
            return float(val.replace(',', ''))
        except:
            return 0.0
    return 0.0

# 加载数据
with open(r'd:\AI-项目\12-成本控制\months_data_correct.pkl', 'rb') as f:
    months_data = pickle.load(f)

def add_title_slide(prs, title, subtitle):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = title
    slide.placeholders[1].text = subtitle
    return slide

def add_content_slide(prs, title):
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.6))
    title_frame = title_box.text_frame
    title_frame.text = title
    p = title_frame.paragraphs[0]
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0, 51, 102)
    return slide

# 创建PPT
prs = Presentation()
prs.slide_width = Inches(10)
prs.slide_height = Inches(7.5)

# 第1页：封面
add_title_slide(prs, "织造车间成本管理体系建设", "4-8月成本核算第一版数据汇报\n财务部")

# 第2页：入职时现状（4月）
slide = add_content_slide(prs, "入职时现状（2026年4月）")
left, top = Inches(1), Inches(1.5)
textbox = slide.shapes.add_textbox(left, top, Inches(8), Inches(5))
tf = textbox.text_frame
tf.word_wrap = True

content = """【没有成本核算体系】
• 没有期初存货盘点 → 原材料领用数据不完整
• 没有标准成本 → 无法判断成本异常
• 生产数据散落在多个Excel表，未关联

【数据现状】
• 生产数量：有（ERP胚布入库单）
• 原材料领用：不完整（部分品种未按单领料）
• 人工分摊：粗糙（按产量比例，未考虑工艺差异）
• 制造费用：粗糙（按产量比例分摊）

【急需解决的问题】
• 老板问"哪个品种赚钱"，答不上来
• 原纱采购价格波动，不知道对成本影响多大
• 人工成本不清楚，无法评估自动化改造的价值"""

for line in content.split('\n'):
    p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(14)
    if line.startswith('【'):
        p.font.bold = True
        p.font.color.rgb = RGBColor(204, 0, 0)
        p.space_before = Pt(10)
    p.space_after = Pt(6)

# 第3页：4-8月数据总览（第一版）
slide = add_content_slide(prs, "4-8月成本数据总览（第一版）")
left, top = Inches(0.8), Inches(1.3)
textbox = slide.shapes.add_textbox(left, top, Inches(8.5), Inches(5.5))
tf = textbox.text_frame

# 计算月度汇总
summary_lines = []
summary_lines.append("月份 | 品种数 | 总产量(KG) | 总成本(万元) | 原材料(万元) | 人工(万元) | 制造费用(万元)")
summary_lines.append("-" * 80)

for month in ['4月', '5月', '6月', '7月', '8月']:
    varieties = months_data[month]
    total_qty = sum(v['实收数量'] for v in varieties)
    total_material = sum(v['原材料金额'] for v in varieties)
    total_labor = sum(v['人工小计'] for v in varieties)
    total_mfg = sum(v['制造费用小计'] for v in varieties)
    total_cost = sum(v['实际成本合计'] for v in varieties)

    summary_lines.append(f"{month} | {len(varieties):2d} | {total_qty:>11,.0f} | {total_cost/10000:>11.2f} | {total_material/10000:>11.2f} | {total_labor/10000:>9.2f} | {total_mfg/10000:>12.2f}")

summary_lines.append("")
summary_lines.append("【数据说明】")
summary_lines.append("• 4-6月：没有期初盘点，原材料成本数据不完整")
summary_lines.append("• 7月：完成期初盘点，数据相对完整")
summary_lines.append("• 8月：第一个完整核算周期（期初+期末盘点）")
summary_lines.append("")
summary_lines.append("【数据质量问题】")
summary_lines.append("• 4-8月共168个品种记录")
summary_lines.append("• 其中32个品种原材料金额为0（领料数据缺失）")
summary_lines.append("• 其中21个品种产量<100KG（小批量试产，成本不稳定）")

for line in summary_lines:
    p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(12) if line.startswith('【') else Pt(11)
    if line.startswith('【'):
        p.font.bold = True
        p.font.color.rgb = RGBColor(204, 0, 0)
        p.space_before = Pt(10)
    p.space_after = Pt(4)

# 第4页：7-8月成本对比（相对可信数据）
slide = add_content_slide(prs, "7-8月成本对比（完成盘点后）")

# 计算7-8月汇总
months_compare = []
for month in ['7月', '8月']:
    varieties = months_data[month]
    # 只统计数据完整的品种（原材料>0且产量>=100）
    valid_varieties = [v for v in varieties if v['原材料金额'] > 0 and v['实收数量'] >= 100]

    total_qty = sum(v['实收数量'] for v in valid_varieties)
    total_material = sum(v['原材料金额'] for v in valid_varieties)
    total_labor = sum(v['人工小计'] for v in valid_varieties)
    total_mfg = sum(v['制造费用小计'] for v in valid_varieties)
    total_cost = sum(v['实际成本合计'] for v in valid_varieties)

    months_compare.append({
        '月份': month,
        '品种数': len(valid_varieties),
        '总产量': total_qty,
        '总成本': total_cost,
        '原材料': total_material,
        '人工': total_labor,
        '制造费用': total_mfg,
    })

left, top = Inches(1), Inches(1.5)
textbox = slide.shapes.add_textbox(left, top, Inches(8), Inches(5))
tf = textbox.text_frame

for item in months_compare:
    content = f"""【{item['月份']}】（有效品种{item['品种数']}个）
总产量：{item['总产量']:,.0f} KG
总成本：{item['总成本']/10000:.2f}万元
  原材料：{item['原材料']/10000:.2f}万元 ({item['原材料']/item['总成本']*100:.1f}%)
  人工：{item['人工']/10000:.2f}万元 ({item['人工']/item['总成本']*100:.1f}%)
  制造费用：{item['制造费用']/10000:.2f}万元 ({item['制造费用']/item['总成本']*100:.1f}%)
平均单位成本：{item['总成本']/item['总产量']:.2f}元/KG
"""
    for line in content.split('\n'):
        p = tf.add_paragraph()
        p.text = line
        p.font.size = Pt(14)
        if line.startswith('【'):
            p.font.bold = True
            p.font.color.rgb = RGBColor(0, 51, 102)
            p.space_before = Pt(12)
        p.space_after = Pt(6)

# 第5页：典型品种成本分析（华棉118D）
slide = add_content_slide(prs, "典型品种：华棉118D（4-8月成本变化）")

# 提取华棉118D数据
huamian_data = []
for month in ['4月', '5月', '6月', '7月', '8月']:
    for item in months_data[month]:
        if item['物料名称'] == '华棉118D':
            qty = item['实收数量']
            if qty > 0:
                huamian_data.append({
                    '月份': month,
                    '产量': qty,
                    '单位成本': item['实际单位成本'],
                    '原材料单位': item['原材料金额'] / qty,
                    '人工单位': item['人工小计'] / qty,
                    '制造费用单位': item['制造费用小计'] / qty,
                })

left, top = Inches(1), Inches(1.5)
textbox = slide.shapes.add_textbox(left, top, Inches(8), Inches(5))
tf = textbox.text_frame

p = tf.add_paragraph()
p.text = "品种特征：棉纱+低弹丝混纺，主力品种，产量稳定"
p.font.size = Pt(13)
p.font.italic = True
p.space_after = Pt(12)

# 表格数据
p = tf.add_paragraph()
p.text = "月份 | 产量(KG) | 单位成本 | 原材料 | 人工 | 制造费用"
p.font.size = Pt(12)
p.font.bold = True

p = tf.add_paragraph()
p.text = "-" * 60
p.font.size = Pt(12)

for data in huamian_data:
    p = tf.add_paragraph()
    p.text = f"{data['月份']} | {data['产量']:>8,.0f} | {data['单位成本']:>7.2f} | {data['原材料单位']:>7.2f} | {data['人工单位']:>5.2f} | {data['制造费用单位']:>7.2f}"
    p.font.size = Pt(12)
    p.space_after = Pt(4)

p = tf.add_paragraph()
p.text = "\n成本分析："
p.font.size = Pt(13)
p.font.bold = True
p.space_before = Pt(15)

p = tf.add_paragraph()
p.text = "• 单位成本：15.33-17.88元/KG，相对稳定"
p.font.size = Pt(13)

p = tf.add_paragraph()
p.text = "• 原材料占比：约92%，是成本核心"
p.font.size = Pt(13)

p = tf.add_paragraph()
p.text = "• 人工+制造费用：约8%，相对固定"
p.font.size = Pt(13)

# 第6页：当前存在的问题
slide = add_content_slide(prs, "当前存在的问题")
left, top = Inches(1), Inches(1.5)
textbox = slide.shapes.add_textbox(left, top, Inches(8), Inches(5))
tf = textbox.text_frame

# 统计问题
all_varieties = []
missing_material = 0
small_qty = 0
for month in ['4月', '5月', '6月', '7月', '8月']:
    for item in months_data[month]:
        all_varieties.append(item)
        if item['原材料金额'] == 0:
            missing_material += 1
        if item['实收数量'] < 100:
            small_qty += 1

content = f"""问题1：领料数据不完整（影响成本准确性）
• 4-8月共{len(all_varieties)}条品种记录
• 其中{missing_material}条原材料金额为0（占{missing_material/len(all_varieties)*100:.1f}%）
• 原因：部分品种未按生产订单领料，导致无法追溯

问题2：小批量试产多（成本不稳定）
• {small_qty}条记录产量<100KG（占{small_qty/len(all_varieties)*100:.1f}%）
• 小批量生产分摊的人工和制造费用高，单位成本失真

问题3：人工成本分摊粗糙
• 按产量比例分摊，未考虑工艺复杂度差异
• 导致复杂品种成本被低估，简单品种被高估

问题4：成本数据滞后
• 月末需要3-5天手工核对、清洗数据
• 无法实时掌握成本异常"""

for line in content.split('\n'):
    p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(14)
    if line.startswith('问题'):
        p.font.bold = True
        p.font.color.rgb = RGBColor(204, 0, 0)
        p.space_before = Pt(12)
    p.space_after = Pt(6)

# 第7页：改善计划
slide = add_content_slide(prs, "9-11月改善计划")
left, top = Inches(1), Inches(1.5)
textbox = slide.shapes.add_textbox(left, top, Inches(8), Inches(5))
tf = textbox.text_frame

content = """【9月：数据规范期】
目标：提升数据完整率到90%以上
• 推动车间按生产订单领料（与生产部协商流程）
• 每日核对ERP出库单与实际生产（发现问题当天解决）
• 建立BC级次品单独登记表

【10月：精细化期】
目标：成本分摊更准确
• 引入工序采集器数据，精细化人工成本分摊
• 开展品种盈利分析（单位成本 vs 销售单价）
• 优化工艺单理论用量（减少标准与实际差异）

【11月：系统化期】
目标：实时监控+预警
• 建立成本预警机制（变动率>10%自动提醒）
• 搭建Power BI成本看板（日报、周报）
• 月度成本分析会制度化

【预期成果】
成本数据准确率：60% → 95%
成本报告时效：5天 → 2天
管理决策支持：事后分析 → 事前预警"""

for line in content.split('\n'):
    p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(13)
    if line.startswith('【'):
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 102, 51)
        p.space_before = Pt(12)
    elif line.startswith('目标') or line.startswith('成本'):
        p.font.bold = True
    p.space_after = Pt(5)

# 第8页：总结
slide = add_content_slide(prs, "总结")
left, top = Inches(1.5), Inches(2)
textbox = slide.shapes.add_textbox(left, top, Inches(7), Inches(4))
tf = textbox.text_frame

content = """【成本体系从无到有】
4月：没有成本核算体系
8月：建立31张表的标准成本核算模型

【第一版数据，如实呈现】
数据不完美，但这是真实现状
找到了问题，才能有针对性改善

【下一步重点】
规范领料流程 → 提升数据质量 → 精细化分摊 → 实时监控

织造车间成本，从"一笔糊涂账"到"心中有数"
这是第一步。"""

for line in content.split('\n'):
    p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(16)
    if line.startswith('【'):
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 51, 102)
        p.space_before = Pt(15)
    p.alignment = PP_ALIGN.CENTER
    p.space_after = Pt(8)

# 保存PPT
output_path = r'd:\AI-项目\12-成本控制\01-交付物归档\2026-09\织造车间成本体系建设_第一版数据_202609.pptx'
prs.save(output_path)

print(f"PPT生成成功：{output_path}")
print("\nPPT内容：")
print("1. 封面")
print("2. 入职时现状（4月）")
print("3. 4-8月数据总览（如实说明数据问题）")
print("4. 7-8月成本对比（完成盘点后）")
print("5. 典型品种：华棉118D成本分析")
print("6. 当前存在的问题")
print("7. 9-11月改善计划")
print("8. 总结")
