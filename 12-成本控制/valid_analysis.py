#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
有效分析：剔除异常数据后的成本趋势
"""
import pickle
from collections import defaultdict

# 加载数据
with open(r'd:\AI-项目\12-成本控制\months_data_correct.pkl', 'rb') as f:
    months_data = pickle.load(f)

print("=" * 80)
print("有效分析：剔除异常数据")
print("=" * 80)

# 统计每个品种的月度数据
variety_months = defaultdict(list)
for month in ['4月', '5月', '6月', '7月', '8月']:
    for item in months_data[month]:
        # 剔除异常数据：原材料为0或产量<100KG
        if item['原材料金额'] == 0 or item['实收数量'] < 100:
            continue

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

print(f"\n有效品种（连续3个月以上，且数据完整）：{len(continuous_varieties)}个")

# 分析成本变化
cost_analysis = []
for name, data in continuous_varieties.items():
    if len(data) < 2:
        continue

    first_month = data[0]
    last_month = data[-1]

    cost_change = last_month['单位成本'] - first_month['单位成本']
    cost_change_pct = (cost_change / first_month['单位成本'] * 100) if first_month['单位成本'] > 0 else 0

    # 计算平均单位成本
    avg_unit_cost = sum(d['单位成本'] for d in data) / len(data)

    # 计算原材料/人工/制造费用的单位成本
    avg_material_per_kg = sum(d['原材料']/d['产量'] for d in data) / len(data)
    avg_labor_per_kg = sum(d['人工']/d['产量'] for d in data) / len(data)
    avg_mfg_per_kg = sum(d['制造费用']/d['产量'] for d in data) / len(data)

    cost_analysis.append({
        '品种': name,
        '月份数': len(data),
        '起始月': first_month['月份'],
        '结束月': last_month['月份'],
        '起始单位成本': first_month['单位成本'],
        '结束单位成本': last_month['单位成本'],
        '平均单位成本': avg_unit_cost,
        '成本变化': cost_change,
        '成本变化率': cost_change_pct,
        '总产量': sum(d['产量'] for d in data),
        '平均原材料单位成本': avg_material_per_kg,
        '平均人工单位成本': avg_labor_per_kg,
        '平均制造费用单位成本': avg_mfg_per_kg,
        '月度数据': data,
    })

# 按成本变化率排序（上升最多的）
cost_rising = sorted([x for x in cost_analysis if x['成本变化率'] > 5],
                     key=lambda x: x['成本变化率'], reverse=True)

cost_falling = sorted([x for x in cost_analysis if x['成本变化率'] < -5],
                      key=lambda x: x['成本变化率'])

print("\n" + "=" * 80)
print(f"成本上升品种（变化率>5%）：{len(cost_rising)}个")
print("=" * 80)

for i, item in enumerate(cost_rising[:5], 1):
    print(f"\n{i}. {item['品种']}")
    print(f"   {item['起始月']}→{item['结束月']}: {item['起始单位成本']:.2f}元/KG → {item['结束单位成本']:.2f}元/KG ({item['成本变化率']:+.1f}%)")
    print(f"   成本构成：原材料{item['平均原材料单位成本']:.2f} + 人工{item['平均人工单位成本']:.2f} + 制造{item['平均制造费用单位成本']:.2f} = {item['平均单位成本']:.2f}元/KG")

print("\n" + "=" * 80)
print(f"成本下降品种（变化率<-5%）：{len(cost_falling)}个")
print("=" * 80)

for i, item in enumerate(cost_falling[:5], 1):
    print(f"\n{i}. {item['品种']}")
    print(f"   {item['起始月']}→{item['结束月']}: {item['起始单位成本']:.2f}元/KG → {item['结束单位成本']:.2f}元/KG ({item['成本变化率']:+.1f}%)")
    print(f"   成本构成：原材料{item['平均原材料单位成本']:.2f} + 人工{item['平均人工单位成本']:.2f} + 制造{item['平均制造费用单位成本']:.2f} = {item['平均单位成本']:.2f}元/KG")

print("\n" + "=" * 80)
print("重点品种：华棉系列成本对比")
print("=" * 80)

huamian_varieties = {k: v for k, v in cost_analysis if '华棉' in k}
for item in sorted([x for x in cost_analysis if '华棉' in x['品种']],
                   key=lambda x: x['平均单位成本'], reverse=True):
    print(f"{item['品种']:20s}: 平均{item['平均单位成本']:6.2f}元/KG | 材料{item['平均原材料单位成本']:6.2f} + 人工{item['平均人工单位成本']:5.2f} + 制造{item['平均制造费用单位成本']:5.2f}")

# 保存有效分析结果
valid_analysis = {
    'continuous_varieties': continuous_varieties,
    'cost_rising': cost_rising,
    'cost_falling': cost_falling,
    'all_analysis': cost_analysis,
}

with open(r'd:\AI-项目\12-成本控制\valid_cost_analysis.pkl', 'wb') as f:
    pickle.dump(valid_analysis, f)

print("\n有效分析结果已保存到: valid_cost_analysis.pkl")
