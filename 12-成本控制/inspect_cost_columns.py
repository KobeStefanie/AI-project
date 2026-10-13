#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专门检查成本相关列
"""
import openpyxl

excel_path = r'C:\Users\Administrator\Desktop\华盛\成本PPT汇报\成本核算汇总-标准成本 - 加工与自产.xlsx'
wb = openpyxl.load_workbook(excel_path, data_only=True)

output = []
output.append("8月成本相关列分析")
output.append("=" * 100)

ws = wb['8月']

# 打印Row1的所有列标题，找包含"成本"的列
output.append("\n【Row1 所有列标题】：")
for col_idx in range(1, ws.max_column + 1):
    cell_value = ws.cell(1, col_idx).value
    if cell_value:
        # 如果包含"成本"、"金额"、"差异"等关键词，标记出来
        mark = ""
        if cell_value and any(keyword in str(cell_value) for keyword in ['成本', '金额', '差异', '单价', '费用']):
            mark = " ⭐⭐⭐"
        output.append(f"  Col{col_idx}: {cell_value}{mark}")

# 打印Row2的所有列标题
output.append("\n【Row2 子标题】：")
for col_idx in range(1, ws.max_column + 1):
    cell_value = ws.cell(2, col_idx).value
    if cell_value:
        mark = ""
        if cell_value and any(keyword in str(cell_value) for keyword in ['成本', '金额', '差异', '单价', '费用']):
            mark = " ⭐⭐⭐"
        output.append(f"  Col{col_idx}: {cell_value}{mark}")

# 打印Row3（第一条数据）的后50列数值
output.append("\n【Row3 数据样本（Col40-71）】：")
for col_idx in range(40, ws.max_column + 1):
    cell_value = ws.cell(3, col_idx).value
    col_title = ws.cell(1, col_idx).value or ws.cell(2, col_idx).value
    if cell_value or col_title:
        output.append(f"  Col{col_idx} ({col_title}): {cell_value}")

# 写入文件
output_file = 'd:/AI-项目/12-成本控制/cost_columns_detail.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Done! Check: {output_file}")
