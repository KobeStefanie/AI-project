#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
录音上传服务器
端口: 8767
功能: 上传、下载、删除录音文件
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import sys
import io
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename

# Windows GBK兼容性处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = Path(__file__).parent.parent
VISITORS_DIR = PROJECT_ROOT / 'data' / 'visitors'

# 允许的音频文件格式
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac', 'wma'}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_visit_json_path(visitor_id, visit_id):
    """获取visit JSON文件路径"""
    return VISITORS_DIR / visitor_id / 'visits' / f'{visit_id}.json'


def get_recordings_dir(visitor_id, visit_id):
    """获取录音文件存储目录"""
    recordings_dir = VISITORS_DIR / visitor_id / 'visits' / visit_id / 'recordings'
    recordings_dir.mkdir(parents=True, exist_ok=True)
    return recordings_dir


@app.route('/upload', methods=['POST'])
def upload_recording():
    """上传录音文件"""
    try:
        # 检查文件是否存在
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            }), 400

        file = request.files['file']
        visitor_id = request.form.get('visitor_id')
        visit_id = request.form.get('visit_id')
        description = request.form.get('description', '')

        if not all([visitor_id, visit_id]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '文件名为空'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'不支持的文件格式，支持的格式：{", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # 读取visit JSON文件
        json_path = get_visit_json_path(visitor_id, visit_id)
        if not json_path.exists():
            return jsonify({
                'success': False,
                'error': f'找不到来访记录: {visitor_id}/{visit_id}'
            }), 404

        with open(json_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        # 确保结构存在
        if 'case_data' not in visit_data:
            visit_data['case_data'] = {}
        if 'recordings' not in visit_data['case_data']:
            visit_data['case_data']['recordings'] = []

        # 生成唯一ID
        existing_ids = [r['id'] for r in visit_data['case_data']['recordings']]
        record_num = 1
        while f"rec_{record_num:03d}" in existing_ids:
            record_num += 1
        recording_id = f"rec_{record_num:03d}"

        # 保存文件
        recordings_dir = get_recordings_dir(visitor_id, visit_id)
        original_filename = file.filename  # 保留原始文件名（包括中文）
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        file_path = recordings_dir / f"{recording_id}.{file_ext}"

        file.save(str(file_path))
        file_size = file_path.stat().st_size

        # 创建录音记录
        now = datetime.now().isoformat()
        new_recording = {
            'id': recording_id,
            'filename': original_filename,  # 使用原始文件名
            'file_path': f"{recording_id}.{file_ext}",
            'file_size': file_size,
            'description': description,
            'uploaded_at': now
        }

        # 添加到列表
        visit_data['case_data']['recordings'].append(new_recording)

        # 更新时间戳
        if 'metadata' not in visit_data:
            visit_data['metadata'] = {}
        visit_data['metadata']['updated_at'] = now

        # 写回文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 已上传录音: {visitor_id}/{visit_id} - {recording_id} ({file_size} bytes)")

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
            'message': '录音上传成功',
            'recording_id': recording_id,
            'file_size': file_size
        })

    except Exception as e:
        print(f"✗ 上传录音失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/download/<visitor_id>/<visit_id>/<recording_id>', methods=['GET'])
def download_recording(visitor_id, visit_id, recording_id):
    """下载录音文件"""
    try:
        # 读取JSON获取文件信息
        json_path = get_visit_json_path(visitor_id, visit_id)
        if not json_path.exists():
            return jsonify({
                'success': False,
                'error': f'找不到来访记录: {visitor_id}/{visit_id}'
            }), 404

        with open(json_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        # 查找录音记录
        recordings = visit_data.get('case_data', {}).get('recordings', [])
        recording = None
        for r in recordings:
            if r['id'] == recording_id:
                recording = r
                break

        if not recording:
            return jsonify({
                'success': False,
                'error': f'找不到录音: {recording_id}'
            }), 404

        # 获取文件路径
        recordings_dir = get_recordings_dir(visitor_id, visit_id)
        file_path = recordings_dir / recording['file_path']

        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': f'录音文件不存在: {recording["file_path"]}'
            }), 404

        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=recording['filename']
        )

    except Exception as e:
        print(f"✗ 下载录音失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/delete', methods=['POST'])
def delete_recording():
    """删除录音文件"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')
        recording_id = data.get('recording_id')

        if not all([visitor_id, visit_id, recording_id]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        # 读取visit JSON文件
        json_path = get_visit_json_path(visitor_id, visit_id)
        if not json_path.exists():
            return jsonify({
                'success': False,
                'error': f'找不到来访记录: {visitor_id}/{visit_id}'
            }), 404

        with open(json_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        # 查找录音记录
        recordings = visit_data.get('case_data', {}).get('recordings', [])
        recording = None
        for r in recordings:
            if r['id'] == recording_id:
                recording = r
                break

        if not recording:
            return jsonify({
                'success': False,
                'error': f'找不到录音: {recording_id}'
            }), 404

        # 删除物理文件
        recordings_dir = get_recordings_dir(visitor_id, visit_id)
        file_path = recordings_dir / recording['file_path']
        if file_path.exists():
            file_path.unlink()
            print(f"✓ 已删除文件: {file_path}")

        # 从JSON中删除记录
        visit_data['case_data']['recordings'] = [
            r for r in recordings if r['id'] != recording_id
        ]

        # 更新时间戳
        if 'metadata' not in visit_data:
            visit_data['metadata'] = {}
        visit_data['metadata']['updated_at'] = datetime.now().isoformat()

        # 写回文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 已删除录音: {visitor_id}/{visit_id} - {recording_id}")

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
            'message': '录音删除成功'
        })

    except Exception as e:
        print(f"✗ 删除录音失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("录音管理服务器")
    print("=" * 60)
    print(f"端口: 8767")
    print(f"数据目录: {VISITORS_DIR}")
    print(f"支持格式: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"API端点:")
    print(f"  - POST /upload                上传录音")
    print(f"  - GET  /download/<visitor_id>/<visit_id>/<recording_id>  下载录音")
    print(f"  - POST /delete                删除录音")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8767, debug=False)
