#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查4-7月的列结构，找到正确的成本列位置
"""
import openpyxl

excel_file = r'C:\Users\Administrator\Desktop\华盛\成本PPT汇报\成本核算汇总-标准成本 - 加工与自产.xlsx'
wb = openpyxl.load_workbook(excel_file, data_only=True)

for month in ['4月', '5月', '6月', '7月', '8月']:
    print(f"\n{'='*80}")
    print(f"{month}的列结构")
    print('='*80)

    ws = wb[month]

    # 读取前2行表头
    print("\n关键列的表头（可能的成本列）：")

    # 搜索包含"成本"、"金额"、"小计"的列
    cost_cols = []
    for col in range(1, ws.max_column + 1):
        h1 = ws.cell(1, col).value or ""
        h2 = ws.cell(2, col).value or ""

        if any(keyword in str(h1) + str(h2) for keyword in ['成本', '金额', '小计', '人工', '制造费用']):
            cost_cols.append((col, h1, h2))

    for col, h1, h2 in cost_cols:
        print(f"  Col{col:2d}: [{h1}] / [{h2}]")

    # 读取第3行的实际数据（第一个品种）
    print(f"\n第一个品种（Row3）的成本数据：")
    print(f"  品种名称(Col3): {ws.cell(3, 3).value}")
    print(f"  实收数量(Col9): {ws.cell(3, 9).value}")

    for col, h1, h2 in cost_cols[-5:]:  # 只看最后5个成本相关列
        val = ws.cell(3, col).value
        print(f"  Col{col}({h2}): {val}")

wb.close()
