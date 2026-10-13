#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
深度分析：同品种4-8月成本变化趋势
"""
import openpyxl
import pickle
from collections import defaultdict

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

# 加载已读取的数据
with open(r'd:\AI-项目\12-成本控制\months_data_correct.pkl', 'rb') as f:
    months_data = pickle.load(f)

print("=" * 80)
print("分析1：同品种成本趋势（连续出现3个月以上的品种）")
print("=" * 80)

# 统计每个品种在哪些月份出现
variety_months = defaultdict(list)
for month in ['4月', '5月', '6月', '7月', '8月']:
    for item in months_data[month]:
        variety_months[item['物料名称']].append({
            '月份': month,
            '产量': item['实收数量'],
            '单位成本': item['实际单位成本'],
            '总成本': item['实际成本合计'],
            '原材料': item['原材料金额'],
            '人工': item['人工小计'],
            '制造费用': item['制造费用小计'],
        })

# 筛选连续出现3个月以上的品种
continuous_varieties = {name: data for name, data in variety_months.items() if len(data) >= 3}

print(f"\n连续出现3个月以上的品种：{len(continuous_varieties)}个")

# 分析成本变化趋势
cost_analysis = []
for name, data in continuous_varieties.items():
    if len(data) < 2:
        continue

    first_month = data[0]
    last_month = data[-1]

    # 计算成本变化
    cost_change = last_month['单位成本'] - first_month['单位成本']
    cost_change_pct = (cost_change / first_month['单位成本'] * 100) if first_month['单位成本'] > 0 else 0

    # 计算产量变化
    qty_change = last_month['产量'] - first_month['产量']
    qty_change_pct = (qty_change / first_month['产量'] * 100) if first_month['产量'] > 0 else 0

    cost_analysis.append({
        '品种': name,
        '月份数': len(data),
        '起始月': first_month['月份'],
        '结束月': last_month['月份'],
        '起始单位成本': first_month['单位成本'],
        '结束单位成本': last_month['单位成本'],
        '成本变化': cost_change,
        '成本变化率': cost_change_pct,
        '起始产量': first_month['产量'],
        '结束产量': last_month['产量'],
        '产量变化': qty_change,
        '产量变化率': qty_change_pct,
        '月度数据': data,
    })

# 按成本变化率排序
cost_analysis.sort(key=lambda x: abs(x['成本变化率']), reverse=True)

print("\nTOP 10 成本波动最大的品种：")
print("-" * 80)
for i, item in enumerate(cost_analysis[:10], 1):
    print(f"\n{i}. {item['品种']}")
    print(f"   时间跨度：{item['起始月']} → {item['结束月']} ({item['月份数']}个月)")
    print(f"   单位成本：{item['起始单位成本']:.2f}元/KG → {item['结束单位成本']:.2f}元/KG")
    print(f"   成本变化：{item['成本变化']:+.2f}元/KG ({item['成本变化率']:+.1f}%)")
    print(f"   产量变化：{item['起始产量']:,.0f} → {item['结束产量']:,.0f} KG ({item['产量变化率']:+.1f}%)")

print("\n" + "=" * 80)
print("分析2：成本结构变化（原材料/人工/制造费用占比）")
print("=" * 80)

for month in ['4月', '5月', '6月', '7月', '8月']:
    varieties = months_data[month]
    total_material = sum(v['原材料金额'] for v in varieties)
    total_labor = sum(v['人工小计'] for v in varieties)
    total_mfg = sum(v['制造费用小计'] for v in varieties)
    total_cost = sum(v['实际成本合计'] for v in varieties)

    print(f"\n{month}:")
    print(f"  原材料占比：{total_material/total_cost*100:.1f}%")
    print(f"  人工占比：{total_labor/total_cost*100:.1f}%")
    print(f"  制造费用占比：{total_mfg/total_cost*100:.1f}%")

print("\n" + "=" * 80)
print("分析3：典型品种的逐月成本分解（选取华棉118D）")
print("=" * 80)

target_variety = '华棉118D'
if target_variety in variety_months:
    print(f"\n品种：{target_variety}")
    print("-" * 80)
    print(f"{'月份':6s} | {'产量(KG)':>10s} | {'单位成本':>8s} | {'原材料':>8s} | {'人工':>8s} | {'制造费用':>8s}")
    print("-" * 80)

    for data in variety_months[target_variety]:
        qty = data['产量']
        unit_cost = data['单位成本']
        material_per_kg = data['原材料'] / qty if qty > 0 else 0
        labor_per_kg = data['人工'] / qty if qty > 0 else 0
        mfg_per_kg = data['制造费用'] / qty if qty > 0 else 0

        print(f"{data['月份']:6s} | {qty:10,.0f} | {unit_cost:8.2f} | {material_per_kg:8.2f} | {labor_per_kg:8.2f} | {mfg_per_kg:8.2f}")

print("\n" + "=" * 80)
print("分析4：产量规模与单位成本的关系")
print("=" * 80)

# 分析：产量越大，单位成本是否越低（规模效应）
all_records = []
for month in ['4月', '5月', '6月', '7月', '8月']:
    for item in months_data[month]:
        if item['实收数量'] > 0 and item['实际单位成本'] > 0:
            all_records.append({
                '月份': month,
                '品种': item['物料名称'],
                '产量': item['实收数量'],
                '单位成本': item['实际单位成本'],
            })

# 按产量分组
all_records.sort(key=lambda x: x['产量'])
low_qty = all_records[:len(all_records)//3]
mid_qty = all_records[len(all_records)//3:2*len(all_records)//3]
high_qty = all_records[2*len(all_records)//3:]

avg_cost_low = sum(r['单位成本'] for r in low_qty) / len(low_qty)
avg_cost_mid = sum(r['单位成本'] for r in mid_qty) / len(mid_qty)
avg_cost_high = sum(r['单位成本'] for r in high_qty) / len(high_qty)

avg_qty_low = sum(r['产量'] for r in low_qty) / len(low_qty)
avg_qty_mid = sum(r['产量'] for r in mid_qty) / len(mid_qty)
avg_qty_high = sum(r['产量'] for r in high_qty) / len(high_qty)

print(f"\n产量分组分析（共{len(all_records)}条记录）：")
print(f"  低产量组（平均{avg_qty_low:,.0f} KG）：平均单位成本 {avg_cost_low:.2f}元/KG")
print(f"  中产量组（平均{avg_qty_mid:,.0f} KG）：平均单位成本 {avg_cost_mid:.2f}元/KG")
print(f"  高产量组（平均{avg_qty_high:,.0f} KG）：平均单位成本 {avg_cost_high:.2f}元/KG")

# 保存分析结果
analysis_result = {
    'continuous_varieties': continuous_varieties,
    'cost_analysis': cost_analysis,
    'variety_months': dict(variety_months),
}

with open(r'd:\AI-项目\12-成本控制\cost_analysis_result.pkl', 'wb') as f:
    pickle.dump(analysis_result, f)

print("\n分析结果已保存到: cost_analysis_result.pkl")
