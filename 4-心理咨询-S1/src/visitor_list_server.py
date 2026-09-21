#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
来访者列表数据服务
提供来访者列表查询和Excel导出功能
端口: 8770
数据源: data/visitors/ (新格式)
"""

from flask import Flask, jsonify, send_file
from flask_cors import CORS
from pathlib import Path
import json
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from io import BytesIO

app = Flask(__name__)
CORS(app)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
VISITORS_DIR = PROJECT_ROOT / 'data' / 'visitors'


def get_visitor_folders():
    """获取所有来访者文件夹"""
    if not VISITORS_DIR.exists():
        return []

    visitor_folders = []
    for folder in VISITORS_DIR.iterdir():
        if folder.is_dir() and folder.name.startswith('V'):
            visitor_folders.append(folder)

    return sorted(visitor_folders, key=lambda x: x.name, reverse=True)


def load_visitor_data(visitor_id):
    """加载来访者数据（从data/visitors读取）"""
    visitor_dir = VISITORS_DIR / visitor_id
    profile_file = visitor_dir / 'profile.json'

    visitor_data = {
        'visitor_id': visitor_id,
        'name': visitor_id,
        'phone': '',
        'counselor': '',
        'first_visit_date': '',
        'visit_count': 0,
        'last_visit_date': '',
        'crisis_status': '未评估',
        'case_status': '未知',
        'age': '',
        'gender': '',
        'occupation': ''
    }

    if not profile_file.exists():
        return visitor_data

    try:
        # 读取profile.json
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile = json.load(f)

        # 从basic_info中读取基本信息
        basic_info = profile.get('basic_info', {})
        visitor_data['name'] = basic_info.get('name', visitor_id)
        visitor_data['age'] = basic_info.get('age', '')
        visitor_data['gender'] = basic_info.get('gender', '')
        visitor_data['occupation'] = basic_info.get('occupation', '')
        visitor_data['phone'] = basic_info.get('contact_phone', '')

        # 从visit_history中读取咨询师
        visit_history = profile.get('visit_history', [])
        if visit_history:
            visitor_data['counselor'] = visit_history[0].get('counselor', '')

        # 案例状态
        visitor_data['case_status'] = profile.get('case_status', '进行中')

        # 计算来访次数和日期
        visits_dir = visitor_dir / 'visits'
        if visits_dir.exists():
            visit_files = list(visits_dir.glob('visit_*.json'))
            visitor_data['visit_count'] = len(visit_files)

            if visit_files:
                # 第一次来访
                first_visit_file = min(visit_files, key=lambda x: x.name)
                with open(first_visit_file, 'r', encoding='utf-8') as f:
                    first_visit = json.load(f)
                    visitor_data['first_visit_date'] = first_visit.get('visit_date', '')
                    visitor_data['crisis_status'] = first_visit.get('crisis_level', '未评估')

                # 最后一次来访
                last_visit_file = max(visit_files, key=lambda x: x.name)
                with open(last_visit_file, 'r', encoding='utf-8') as f:
                    last_visit = json.load(f)
                    visitor_data['last_visit_date'] = last_visit.get('visit_date', '')
                    visitor_data['case_status'] = last_visit.get('case_status', '进行中')

    except Exception as e:
        print(f"读取来访者数据失败 {visitor_id}: {e}")

    return visitor_data


@app.route('/api/visitors')
def get_visitors():
    """获取所有来访者列表"""
    try:
        visitor_folders = get_visitor_folders()
        visitors = []

        for folder in visitor_folders:
            visitor_id = folder.name
            visitor_data = load_visitor_data(visitor_id)
            visitors.append(visitor_data)

        return jsonify({
            'success': True,
            'total': len(visitors),
            'visitors': visitors
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/export_excel')
def export_excel():
    """导出来访者列表为Excel"""
    try:
        visitor_folders = get_visitor_folders()
        visitors = [load_visitor_data(f.name) for f in visitor_folders]

        # 创建工作簿
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "来访者列表"

        # 设置表头
        headers = ['来访者ID', '姓名', '年龄', '性别', '职业', '联系方式',
                   '咨询师', '首次来访', '最近来访', '来访次数', '危机等级', '案例状态']
        ws.append(headers)

        # 设置表头样式
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_alignment = Alignment(horizontal="center", vertical="center")

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment

        # 填充数据
        for visitor in visitors:
            ws.append([
                visitor['visitor_id'],
                visitor['name'],
                visitor['age'],
                visitor['gender'],
                visitor['occupation'],
                visitor['phone'],
                visitor['counselor'],
                visitor['first_visit_date'],
                visitor['last_visit_date'],
                visitor['visit_count'],
                visitor['crisis_status'],
                visitor['case_status']
            ])

        # 调整列宽
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 8
        ws.column_dimensions['E'].width = 20
        ws.column_dimensions['F'].width = 15
        ws.column_dimensions['G'].width = 10
        ws.column_dimensions['H'].width = 12
        ws.column_dimensions['I'].width = 12
        ws.column_dimensions['J'].width = 10
        ws.column_dimensions['K'].width = 15
        ws.column_dimensions['L'].width = 10

        # 保存到内存
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'来访者列表_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("来访者列表服务器")
    print("端口: 8770")
    print(f"数据源: {VISITORS_DIR}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8770, debug=False)
