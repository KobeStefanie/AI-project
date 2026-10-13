#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查异常品种的原始数据
"""
import pickle

# 加载数据
with open(r'd:\AI-项目\12-成本控制\months_data_correct.pkl', 'rb') as f:
    months_data = pickle.load(f)

# 检查几个异常品种
abnormal_varieties = ['24S棉', '50S拉架平纹', '华棉118D']

for variety_name in abnormal_varieties:
    print(f"\n{'='*80}")
    print(f"品种：{variety_name}")
    print('='*80)
    print(f"{'月份':6s} | {'产量':>10s} | {'总成本':>12s} | {'原材料':>12s} | {'人工':>10s} | {'制造费用':>10s} | {'单位成本':>10s}")
    print('-'*80)

    for month in ['4月', '5月', '6月', '7月', '8月']:
        for item in months_data[month]:
            if item['物料名称'] == variety_name:
                print(f"{month:6s} | {item['实收数量']:10,.0f} | {item['实际成本合计']:12,.2f} | {item['原材料金额']:12,.2f} | {item['人工小计']:10,.2f} | {item['制造费用小计']:10,.2f} | {item['实际单位成本']:10.2f}")

print("\n" + "="*80)
print("发现的问题：")
print("="*80)
print("1. 某些品种的原材料金额为0 → 领料数据缺失")
print("2. 某些品种的产量突然变为个位数 → 数据异常或小批量试产")
print("3. 单位成本暴跌 → 分母（产量）很小，或者原材料缺失")
print("\n结论：不能简单用成本变化率排序，需要先剔除异常数据")
