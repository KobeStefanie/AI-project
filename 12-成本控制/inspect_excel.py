#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查Excel文件的真实数据结构
"""
import openpyxl

excel_path = r'C:\Users\Administrator\Desktop\华盛\成本PPT汇报\成本核算汇总-标准成本 - 加工与自产.xlsx'

# 打开Excel文件
wb = openpyxl.load_workbook(excel_path, data_only=True)

# 输出文件
output = []
output.append("=" * 80)
output.append("Excel文件结构分析")
output.append("=" * 80)
output.append("")

# 1. 列出所有sheet
output.append(f"Sheet列表（共{len(wb.sheetnames)}个）：")
for i, sheet_name in enumerate(wb.sheetnames, 1):
    output.append(f"  {i}. {sheet_name}")
output.append("")

# 2. 分析每个sheet的结构
for sheet_name in wb.sheetnames:
    output.append("=" * 80)
    output.append(f"Sheet: {sheet_name}")
    output.append("=" * 80)

    ws = wb[sheet_name]
    output.append(f"总行数: {ws.max_row}")
    output.append(f"总列数: {ws.max_column}")
    output.append("")

    # 打印前3行作为标题行
    output.append("前3行（标题行）：")
    for row_idx in range(1, min(4, ws.max_row + 1)):
        row_data = []
        for col_idx in range(1, min(ws.max_column + 1, 80)):  # 最多80列
            cell_value = ws.cell(row_idx, col_idx).value
            if cell_value is not None:
                row_data.append(f"[Col{col_idx}] {cell_value}")
        output.append(f"  Row{row_idx}: {' | '.join(row_data[:10])}")  # 只显示前10列
    output.append("")

    # 打印第4-6行作为数据样本
    output.append("数据样本（第4-6行）：")
    for row_idx in range(4, min(7, ws.max_row + 1)):
        row_data = []
        for col_idx in range(1, min(20, ws.max_column + 1)):  # 只看前20列
            cell_value = ws.cell(row_idx, col_idx).value
            if cell_value is not None:
                row_data.append(f"Col{col_idx}={cell_value}")
        if row_data:
            output.append(f"  Row{row_idx}: {', '.join(row_data[:10])}")
    output.append("")
    output.append("")

# 写入文件
output_file = 'd:/AI-项目/12-成本控制/excel_structure.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Done! Check: {output_file}")
