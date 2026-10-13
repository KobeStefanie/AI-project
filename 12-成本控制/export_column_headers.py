#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导出8月sheet的完整列标题清单
"""
import openpyxl

excel_path = r'C:\Users\Administrator\Desktop\华盛\成本PPT汇报\成本核算汇总-标准成本 - 加工与自产.xlsx'
wb = openpyxl.load_workbook(excel_path, data_only=True)
ws = wb['8月']

output = []
output.append("=" * 80)
output.append("8月sheet完整列标题清单（71列）")
output.append("=" * 80)
output.append("")

# 读取Row1和Row2的所有列标题
for col_idx in range(1, ws.max_column + 1):
    row1_val = ws.cell(1, col_idx).value
    row2_val = ws.cell(2, col_idx).value

    # 如果Row1和Row2都有值，说明是双层标题
    if row1_val or row2_val:
        output.append(f"Col{col_idx:02d}:")
        if row1_val:
            output.append(f"  Row1: {row1_val}")
        if row2_val:
            output.append(f"  Row2: {row2_val}")
        output.append("")

output.append("=" * 80)
output.append("数据样本（Row3第一条数据的前20列）：")
output.append("")

for col_idx in range(1, min(21, ws.max_column + 1)):
    row1_val = ws.cell(1, col_idx).value or ws.cell(2, col_idx).value or f"Col{col_idx}"
    row3_val = ws.cell(3, col_idx).value
    output.append(f"Col{col_idx:02d} ({row1_val}): {row3_val}")

# 写入文件
output_file = 'd:/AI-项目/12-成本控制/excel_column_headers.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Done: {output_file}")
