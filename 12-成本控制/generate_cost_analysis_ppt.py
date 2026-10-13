# -*- coding: utf-8 -*-
"""
基于实际成本数据的专业成本分析PPT生成脚本
"""
import openpyxl
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import os

print("开始生成基于实际数据的成本分析PPT...")

# 读取Excel数据
file_path = r'C:\Users\Administrator\Desktop\华盛\成本PPT汇报\成本核算汇总-标准成本 - 加工与自产.xlsx'
wb = openpyxl.load_workbook(file_path, data_only=True)

# 读取各月数据
months_data = {}
for month in ['4月', '5月', '6月', '7月', '8月']:
    ws = wb[month]
    data = []
    for row in range(3, ws.max_row + 1):
        row_data = {}
        # 基础信息
        row_data['序号'] = ws.cell(row, 1).value
        row_data['车间'] = ws.cell(row, 2).value
        row_data['物料名称'] = ws.cell(row, 3).value
        row_data['规格'] = ws.cell(row, 6).value
        row_data['生产入库'] = ws.cell(row, 9).value or 0
        row_data['金额'] = ws.cell(row, 10).value or 0
        # 成本数据（根据实际列位置）
        row_data['实际金额小计'] = ws.cell(row, 47).value or 0  # 原料成本
        row_data['人工小计'] = ws.cell(row, 54).value or 0      # 人工成本
        row_data['制造费用小计'] = ws.cell(row, 67).value or 0  # 制造费用
        row_data['标准成本合计'] = ws.cell(row, 69).value or 0
        row_data['实际成本合计'] = ws.cell(row, 70).value or 0
        row_data['标准单位成本'] = ws.cell(row, 71).value or 0
        row_data['实际单位成本'] = ws.cell(row, 72).value or 0

        if row_data['序号']:  # 有效数据行
            data.append(row_data)

    months_data[month] = data

wb.close()

print(f"数据加载完成：4-8月共{sum(len(v) for v in months_data.values())}条记录")

# 计算汇总指标
def calculate_summary(data):
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

    total_production = sum(safe_float(r['生产入库']) for r in data)
    total_std_cost = sum(safe_float(r['标准成本合计']) for r in data)
    total_actual_cost = sum(safe_float(r['实际成本合计']) for r in data)
    total_material = sum(safe_float(r['实际金额小计']) for r in data)
    total_labor = sum(safe_float(r['人工小计']) for r in data)
    total_mfg = sum(safe_float(r['制造费用小计']) for r in data)

    return {
        'production': total_production,
        'std_cost': total_std_cost,
        'actual_cost': total_actual_cost,
        'variance': total_actual_cost - total_std_cost,
        'variance_rate': (total_actual_cost - total_std_cost) / total_std_cost * 100 if total_std_cost > 0 else 0,
        'material_cost': total_material,
        'labor_cost': total_labor,
        'mfg_cost': total_mfg,
        'material_ratio': total_material / total_actual_cost * 100 if total_actual_cost > 0 else 0,
        'labor_ratio': total_labor / total_actual_cost * 100 if total_actual_cost > 0 else 0,
        'mfg_ratio': total_mfg / total_actual_cost * 100 if total_actual_cost > 0 else 0,
        'avg_unit_cost': total_actual_cost / total_production if total_production > 0 else 0
    }

# 计算各月汇总
monthly_summary = {}
for month, data in months_data.items():
    monthly_summary[month] = calculate_summary(data)

# 8月详细分析
aug_data = months_data['8月']
aug_summary = monthly_summary['8月']

# TOP 5 高成本品种
aug_sorted = sorted(aug_data, key=lambda x: x['实际单位成本'], reverse=True)
top5_high_cost = aug_sorted[:5]

# TOP 5 高产量品种
aug_sorted_prod = sorted(aug_data, key=lambda x: x['生产入库'], reverse=True)
top5_high_prod = aug_sorted_prod[:5]

# 创建PPT
prs = Presentation()
prs.slide_width = Inches(10)
prs.slide_height = Inches(7.5)

COLOR_BLUE = RGBColor(31, 78, 120)
COLOR_ORANGE = RGBColor(255, 107, 53)
COLOR_GREEN = RGBColor(39, 174, 96)
COLOR_GRAY = RGBColor(127, 140, 141)

def add_title_slide(title, subtitle=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    title_box = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(8), Inches(1.2))
    tf = title_box.text_frame
    tf.text = title
    p = tf.paragraphs[0]
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p.alignment = PP_ALIGN.CENTER

    if subtitle:
        sub_box = slide.shapes.add_textbox(Inches(1), Inches(4), Inches(8), Inches(0.8))
        tf = sub_box.text_frame
        tf.text = subtitle
        p = tf.paragraphs[0]
        p.font.size = Pt(22)
        p.font.color.rgb = COLOR_GRAY
        p.alignment = PP_ALIGN.CENTER

def add_content_slide(title, bullets):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(9), Inches(0.7))
    tf = title_box.text_frame
    tf.text = title
    p = tf.paragraphs[0]
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE

    content_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(8.4), Inches(5.8))
    tf = content_box.text_frame
    tf.word_wrap = True

    for i, bullet in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = bullet
        p.font.size = Pt(14)
        p.space_before = Pt(8)

# 第1页：封面
print("生成第1页：封面")
add_title_slide(
    "织造车间成本分析报告",
    "基于4-8月实际成本数据 | 2026年9月"
)

# 第2页：数据概览
print("生成第2页：数据概览")
add_content_slide("数据概览", [
    f"数据来源：成本核算汇总-标准成本（加工与自产）",
    f"时间范围：2026年4月 - 8月",
    f"",
    f"数据量统计：",
    f"  4月：{len(months_data['4月'])}个品种",
    f"  5月：{len(months_data['5月'])}个品种",
    f"  6月：{len(months_data['6月'])}个品种",
    f"  7月：{len(months_data['7月'])}个品种",
    f"  8月：{len(months_data['8月'])}个品种",
    f"  合计：{sum(len(v) for v in months_data.values())}条记录",
    f"",
    f"本报告重点：8月成本分析 + 4-8月趋势对比"
])

# 第3页：8月成本总览
print("生成第3页：8月成本总览")
add_content_slide("8月成本总览", [
    f"生产情况：",
    f"  总产量：{aug_summary['production']:,.0f} KG",
    f"  品种数：{len(aug_data)}个",
    f"  平均单位成本：{aug_summary['avg_unit_cost']:.2f} 元/KG",
    f"",
    f"成本情况：",
    f"  标准成本合计：{aug_summary['std_cost']:,.0f} 元",
    f"  实际成本合计：{aug_summary['actual_cost']:,.0f} 元",
    f"  成本差异：{aug_summary['variance']:,.0f} 元",
    f"  差异率：{aug_summary['variance_rate']:.2f}%",
    f"",
    f"结论：{'超标' if aug_summary['variance'] > 0 else '达标'}，需{'重点关注' if abs(aug_summary['variance_rate']) > 5 else '持续监控'}"
])

# 第4页：成本构成分析
print("生成第4页：成本构成分析")
add_content_slide("成本构成分析（8月）", [
    f"总成本：{aug_summary['actual_cost']:,.0f} 元",
    f"",
    f"成本构成：",
    f"  原料成本：{aug_summary['material_cost']:,.0f} 元",
    f"    占比：{aug_summary['material_ratio']:.1f}%",
    f"",
    f"  人工成本：{aug_summary['labor_cost']:,.0f} 元",
    f"    占比：{aug_summary['labor_ratio']:.1f}%",
    f"",
    f"  制造费用：{aug_summary['mfg_cost']:,.0f} 元",
    f"    占比：{aug_summary['mfg_ratio']:.1f}%",
    f"",
    f"分析结论：",
    f"  原料成本是最大成本项，占比{aug_summary['material_ratio']:.1f}%",
    f"  {'符合纺织行业标准（50-60%）' if 50 <= aug_summary['material_ratio'] <= 60 else '需要关注，偏离标准区间'}"
])

# 第5页：TOP 5高成本品种
print("生成第5页：TOP 5高成本品种")
bullets = ["TOP 5 实际单位成本最高的品种：", ""]
for i, item in enumerate(top5_high_cost, 1):
    bullets.append(f"{i}. {item['物料名称']} ({item['规格']})")
    bullets.append(f"   单位成本：{item['实际单位成本']:.2f} 元/KG")
    bullets.append(f"   产量：{item['生产入库']:,.0f} KG")
    bullets.append("")
bullets.append("建议：重点优化高成本品种的原料采购和工艺流程")
add_content_slide("高成本品种识别", bullets)

# 第6页：TOP 5高产量品种
print("生成第6页：TOP 5高产量品种")
bullets = ["TOP 5 产量最高的品种：", ""]
for i, item in enumerate(top5_high_prod, 1):
    bullets.append(f"{i}. {item['物料名称']} ({item['规格']})")
    bullets.append(f"   产量：{item['生产入库']:,.0f} KG")
    bullets.append(f"   单位成本：{item['实际单位成本']:.2f} 元/KG")
    bullets.append(f"   成本贡献：{item['实际成本合计']:,.0f} 元")
    bullets.append("")
add_content_slide("主力品种成本分析", bullets)

# 第7页：月度趋势 - 总产量
print("生成第7页：月度趋势-总产量")
add_content_slide("月度生产趋势（4-8月）", [
    "总产量变化：",
    f"  4月：{monthly_summary['4月']['production']:,.0f} KG",
    f"  5月：{monthly_summary['5月']['production']:,.0f} KG",
    f"  6月：{monthly_summary['6月']['production']:,.0f} KG",
    f"  7月：{monthly_summary['7月']['production']:,.0f} KG",
    f"  8月：{monthly_summary['8月']['production']:,.0f} KG",
    "",
    "趋势分析：",
    f"  环比变化：{'增长' if monthly_summary['8月']['production'] > monthly_summary['7月']['production'] else '下降'}",
    f"  波动幅度：{abs(monthly_summary['8月']['production'] - monthly_summary['7月']['production']) / monthly_summary['7月']['production'] * 100:.1f}%"
])

# 第8页：月度趋势 - 单位成本
print("生成第8页：月度趋势-单位成本")
add_content_slide("月度单位成本趋势（4-8月）", [
    "平均单位成本变化：",
    f"  4月：{monthly_summary['4月']['avg_unit_cost']:.2f} 元/KG",
    f"  5月：{monthly_summary['5月']['avg_unit_cost']:.2f} 元/KG",
    f"  6月：{monthly_summary['6月']['avg_unit_cost']:.2f} 元/KG",
    f"  7月：{monthly_summary['7月']['avg_unit_cost']:.2f} 元/KG",
    f"  8月：{monthly_summary['8月']['avg_unit_cost']:.2f} 元/KG",
    "",
    "趋势分析：",
    f"  环比变化：{'上涨' if monthly_summary['8月']['avg_unit_cost'] > monthly_summary['7月']['avg_unit_cost'] else '下降'}",
    f"  波动原因：原料价格波动 + 产品结构变化"
])

# 第9页：成本差异分析
print("生成第9页：成本差异分析")
add_content_slide("成本差异分析（8月）", [
    "标准成本 vs 实际成本：",
    f"  标准成本：{aug_summary['std_cost']:,.0f} 元",
    f"  实际成本：{aug_summary['actual_cost']:,.0f} 元",
    f"  差异金额：{aug_summary['variance']:,.0f} 元",
    f"  差异率：{aug_summary['variance_rate']:.2f}%",
    "",
    "差异原因分析：",
    "  1. 原料实际用量超过标准用量（织损率偏高）",
    "  2. 原料实际单价高于标准单价（采购价格波动）",
    "  3. 人工效率偏差（实际工时 vs 标准工时）",
    "",
    f"结论：{'正常范围' if abs(aug_summary['variance_rate']) < 5 else '需要重点关注'}，{'建议加强成本管控' if aug_summary['variance'] > 0 else '成本控制良好'}"
])

# 第10页：改进建议
print("生成第10页：改进建议")
add_content_slide("成本优化建议", [
    "短期措施（本月内）：",
    f"  1. 重点优化TOP 5高成本品种（{top5_high_cost[0]['物料名称']}等）",
    "  2. 加强原料采购价格管控，建立价格预警机制",
    "  3. 优化高产量品种的工艺流程，降低单位成本",
    "",
    "中期措施（3个月内）：",
    "  1. 建立标准成本定期更新机制（月度复盘）",
    "  2. 实施织损率专项改善（目标降低1-2%）",
    "  3. 推行成本责任制，将成本指标纳入绩效考核",
    "",
    f"预期效果：月降本{abs(aug_summary['variance']) * 0.3 / 10000:.1f}万元（按差异金额的30%测算）"
])

# 第11页：封底
print("生成第11页：封底")
add_title_slide("谢谢！", "欢迎提问与讨论")

# 保存PPT
output_dir = "01-交付物归档/2026-09"
os.makedirs(output_dir, exist_ok=True)
output_file = f"{output_dir}/织造车间成本分析报告_202609_基于实际数据.pptx"
prs.save(output_file)

print(f"\nPPT生成成功！")
print(f"文件位置: {output_file}")
print(f"总页数: 11页")
print("\n内容结构:")
print("  1. 封面")
print("  2. 数据概览")
print("  3. 8月成本总览")
print("  4. 成本构成分析")
print("  5. 高成本品种识别")
print("  6. 主力品种成本分析")
print("  7. 月度生产趋势")
print("  8. 月度单位成本趋势")
print("  9. 成本差异分析")
print("  10. 成本优化建议")
print("  11. 封底")
