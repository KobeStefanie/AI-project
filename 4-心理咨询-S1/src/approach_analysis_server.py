#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流派分析内容保存服务器
端口: 8766
功能: 保存编辑/上传的流派分析内容到JSON文件
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
import io
from pathlib import Path
from datetime import datetime

# Windows GBK兼容性处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = Path(__file__).parent.parent
VISITORS_DIR = PROJECT_ROOT / 'data' / 'visitors'


def get_visit_json_path(visitor_id, visit_id):
    """获取visit JSON文件路径"""
    return VISITORS_DIR / visitor_id / 'visits' / f'{visit_id}.json'


@app.route('/save_approach', methods=['POST'])
def save_approach():
    """保存流派分析内容"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')
        approach = data.get('approach')
        content = data.get('content')

        if not all([visitor_id, visit_id, approach, content]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        # 读取visit JSON文件
        json_path = get_visit_json_path(visitor_id, visit_id)

        if not json_path.exists():
            return jsonify({
                'success': False,
                'error': f'找不到文件: {json_path}'
            }), 404

        with open(json_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        # 确保 approach_analyses_html 结构存在
        if 'case_data' not in visit_data:
            visit_data['case_data'] = {}
        if 'approach_analyses_html' not in visit_data['case_data']:
            visit_data['case_data']['approach_analyses_html'] = {}

        # 保存HTML内容
        visit_data['case_data']['approach_analyses_html'][approach] = content

        # 更新时间戳
        if 'metadata' not in visit_data:
            visit_data['metadata'] = {}
        visit_data['metadata']['updated_at'] = datetime.now().isoformat()

        # 写回文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 已保存: {visitor_id}/{visit_id} - {approach}")

        # 自动重新生成该来访者的详情页
        try:
            import subprocess
            script_path = PROJECT_ROOT / 'src' / 'generate_visit_details.py'

            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NO_WINDOW

            subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(PROJECT_ROOT),
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"✓ 已触发重新生成HTML")
        except Exception as e:
            print(f"⚠ 重新生成失败: {e}")

        return jsonify({
            'success': True,
            'message': '保存成功'
        })

    except Exception as e:
        print(f"✗ 保存失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/save_review', methods=['POST'])
def save_review():
    """保存咨询师复盘内容"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')
        content = data.get('content')

        if not all([visitor_id, visit_id, content]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        # 读取visit JSON文件
        json_path = get_visit_json_path(visitor_id, visit_id)

        if not json_path.exists():
            return jsonify({
                'success': False,
                'error': f'找不到文件: {json_path}'
            }), 404

        with open(json_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        # 确保结构存在
        if 'case_data' not in visit_data:
            visit_data['case_data'] = {}

        # 保存HTML内容
        visit_data['case_data']['counselor_review_html'] = content

        # 更新时间戳
        if 'metadata' not in visit_data:
            visit_data['metadata'] = {}
        visit_data['metadata']['updated_at'] = datetime.now().isoformat()

        # 写回文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 已保存复盘: {visitor_id}/{visit_id}")

        # 自动重新生成该来访者的详情页
        try:
            import subprocess
            script_path = PROJECT_ROOT / 'src' / 'generate_visit_details.py'

            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NO_WINDOW

            subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(PROJECT_ROOT),
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"✓ 已触发重新生成HTML")
        except Exception as e:
            print(f"⚠ 重新生成失败: {e}")

        return jsonify({
            'success': True,
            'message': '保存成功'
        })

    except Exception as e:
        print(f"✗ 保存失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/supervision_record/add', methods=['POST'])
def add_supervision_record():
    """添加感悟记录"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')
        approach = data.get('approach')  # 流派视角，可为null
        content = data.get('content')

        if not all([visitor_id, visit_id, content]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        # 读取visit JSON文件
        json_path = get_visit_json_path(visitor_id, visit_id)

        if not json_path.exists():
            return jsonify({
                'success': False,
                'error': f'找不到文件: {json_path}'
            }), 404

        with open(json_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        # 确保结构存在
        if 'case_data' not in visit_data:
            visit_data['case_data'] = {}
        if 'supervision_records' not in visit_data['case_data']:
            visit_data['case_data']['supervision_records'] = []

        # 生成唯一ID
        existing_ids = [r['id'] for r in visit_data['case_data']['supervision_records']]
        record_num = 1
        while f"sr_{record_num:03d}" in existing_ids:
            record_num += 1
        record_id = f"sr_{record_num:03d}"

        # 创建新记录
        now = datetime.now().isoformat()
        new_record = {
            'id': record_id,
            'approach': approach,  # 可以为null
            'content': content,
            'created_at': now,
            'updated_at': now
        }

        # 添加到列表
        visit_data['case_data']['supervision_records'].append(new_record)

        # 更新时间戳
        if 'metadata' not in visit_data:
            visit_data['metadata'] = {}
        visit_data['metadata']['updated_at'] = now

        # 写回文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 已添加感悟: {visitor_id}/{visit_id} - {record_id} ({approach or '无流派'})")

        # 自动重新生成HTML
        try:
            import subprocess
            script_path = PROJECT_ROOT / 'src' / 'generate_visit_details.py'

            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NO_WINDOW

            subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(PROJECT_ROOT),
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"✓ 已触发重新生成HTML")
        except Exception as e:
            print(f"⚠ 重新生成失败: {e}")

        return jsonify({
            'success': True,
            'message': '感悟添加成功',
            'record_id': record_id
        })

    except Exception as e:
        print(f"✗ 添加感悟失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/supervision_record/edit', methods=['POST'])
def edit_supervision_record():
    """编辑感悟记录"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')
        record_id = data.get('record_id')
        approach = data.get('approach')
        content = data.get('content')

        if not all([visitor_id, visit_id, record_id, content]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        # 读取visit JSON文件
        json_path = get_visit_json_path(visitor_id, visit_id)

        if not json_path.exists():
            return jsonify({
                'success': False,
                'error': f'找不到文件: {json_path}'
            }), 404

        with open(json_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        # 查找并更新记录
        records = visit_data.get('case_data', {}).get('supervision_records', [])
        record_found = False

        for record in records:
            if record['id'] == record_id:
                record['approach'] = approach
                record['content'] = content
                record['updated_at'] = datetime.now().isoformat()
                record_found = True
                break

        if not record_found:
            return jsonify({
                'success': False,
                'error': f'找不到感悟记录: {record_id}'
            }), 404

        # 更新时间戳
        if 'metadata' not in visit_data:
            visit_data['metadata'] = {}
        visit_data['metadata']['updated_at'] = datetime.now().isoformat()

        # 写回文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 已编辑感悟: {visitor_id}/{visit_id} - {record_id}")

        # 自动重新生成HTML
        try:
            import subprocess
            script_path = PROJECT_ROOT / 'src' / 'generate_visit_details.py'

            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NO_WINDOW

            subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(PROJECT_ROOT),
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"✓ 已触发重新生成HTML")
        except Exception as e:
            print(f"⚠ 重新生成失败: {e}")

        return jsonify({
            'success': True,
            'message': '感悟编辑成功'
        })

    except Exception as e:
        print(f"✗ 编辑感悟失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/supervision_record/delete', methods=['POST'])
def delete_supervision_record():
    """删除感悟记录"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')
        record_id = data.get('record_id')

        if not all([visitor_id, visit_id, record_id]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        # 读取visit JSON文件
        json_path = get_visit_json_path(visitor_id, visit_id)

        if not json_path.exists():
            return jsonify({
                'success': False,
                'error': f'找不到文件: {json_path}'
            }), 404

        with open(json_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        # 删除记录
        records = visit_data.get('case_data', {}).get('supervision_records', [])
        original_length = len(records)

        visit_data['case_data']['supervision_records'] = [
            r for r in records if r['id'] != record_id
        ]

        if len(visit_data['case_data']['supervision_records']) == original_length:
            return jsonify({
                'success': False,
                'error': f'找不到感悟记录: {record_id}'
            }), 404

        # 更新时间戳
        if 'metadata' not in visit_data:
            visit_data['metadata'] = {}
        visit_data['metadata']['updated_at'] = datetime.now().isoformat()

        # 写回文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 已删除感悟: {visitor_id}/{visit_id} - {record_id}")

        # 自动重新生成HTML
        try:
            import subprocess
            script_path = PROJECT_ROOT / 'src' / 'generate_visit_details.py'

            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NO_WINDOW

            subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(PROJECT_ROOT),
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"✓ 已触发重新生成HTML")
        except Exception as e:
            print(f"⚠ 重新生成失败: {e}")

        return jsonify({
            'success': True,
            'message': '感悟删除成功'
        })

    except Exception as e:
        print(f"✗ 删除感悟失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("流派分析保存服务器 + 感悟管理")
    print("=" * 60)
    print(f"端口: 8766")
    print(f"数据目录: {VISITORS_DIR}")
    print(f"API端点:")
    print(f"  - POST /save_approach           保存流派分析")
    print(f"  - POST /save_review             保存咨询师复盘")
    print(f"  - POST /supervision_record/add  添加感悟")
    print(f"  - POST /supervision_record/edit 编辑感悟")
    print(f"  - POST /supervision_record/delete 删除感悟")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8766, debug=False)
