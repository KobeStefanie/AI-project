#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接访记录保存服务器
端口: 8768
功能: 接收接访记录表单数据，保存到来访者JSON，触发HTML生成
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
import io
from pathlib import Path
from datetime import datetime
import subprocess

# Windows GBK兼容性处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = Path(__file__).parent.parent
VISITORS_DIR = PROJECT_ROOT / 'data' / 'visitors'


def generate_visitor_id(date_str):
    """根据日期生成来访者ID: V20260629001"""
    date_part = date_str.replace('-', '')

    # 查找当天已有的最大序号
    max_num = 0
    if VISITORS_DIR.exists():
        for visitor_dir in VISITORS_DIR.iterdir():
            if visitor_dir.is_dir() and visitor_dir.name.startswith(f'V{date_part}'):
                try:
                    num = int(visitor_dir.name[-3:])
                    max_num = max(max_num, num)
                except:
                    pass

    return f'V{date_part}{max_num + 1:03d}'


def generate_visit_id(visitor_dir):
    """生成来访ID: visit_001"""
    visits_dir = visitor_dir / 'visits'
    if not visits_dir.exists():
        return 'visit_001'

    # 查找已有的最大序号
    max_num = 0
    for visit_file in visits_dir.glob('visit_*.json'):
        try:
            num = int(visit_file.stem.split('_')[1])
            max_num = max(max_num, num)
        except:
            pass

    return f'visit_{max_num + 1:03d}'


def trigger_html_generation():
    """触发HTML生成：先生成详情页，再生成索引页"""
    try:
        creation_flags = 0
        if sys.platform == 'win32':
            creation_flags = subprocess.CREATE_NO_WINDOW

        # 1. 生成来访详情页
        script_path1 = PROJECT_ROOT / 'src' / 'generate_visit_details.py'
        subprocess.Popen(
            [sys.executable, str(script_path1)],
            cwd=str(PROJECT_ROOT),
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 2. 生成来访者库索引和档案页
        script_path2 = PROJECT_ROOT / 'src' / 'generate_visitor_library.py'
        subprocess.Popen(
            [sys.executable, str(script_path2)],
            cwd=str(PROJECT_ROOT),
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        print(f"✓ 已触发HTML生成（详情页 + 索引页）")
    except Exception as e:
        print(f"⚠ HTML生成触发失败: {e}")


@app.route('/save_new_case', methods=['POST'])
def save_new_case():
    """保存新案例（首次接访）"""
    try:
        data = request.json

        # 生成来访者ID和来访ID
        visit_date = data['session_info']['接访日期']
        visitor_id = generate_visitor_id(visit_date)

        # 创建来访者目录
        visitor_dir = VISITORS_DIR / visitor_id
        visitor_dir.mkdir(parents=True, exist_ok=True)

        # 创建profile.json
        profile_data = {
            'visitor_id': visitor_id,
            'case_status': data['session_info'].get('案例状态', '进行中'),  # 案例状态
            'basic_info': {
                'name': data['basic_info']['代号'],
                'gender': data['basic_info']['性别'],
                'age': data['basic_info']['年龄'],
                'birth_date': data['basic_info'].get('出生日期', ''),
                'occupation': data['basic_info']['职业'],
                'marital_status': data['basic_info']['婚姻状况'],
                'sexual_orientation': data['basic_info']['性取向'],
                'religion': data['basic_info']['宗教信仰'],
                'contact_phone': data['basic_info'].get('来访者联系电话', ''),
                'emergency_contact': data['basic_info']['紧急联系人'],
                'emergency_contact_relation': data['basic_info']['紧急联系人关系'],
                'emergency_contact_phone': data['basic_info']['紧急联系人电话'],
                'medication': data['basic_info'].get('用药情况', ''),
                'notes': data['basic_info'].get('来访备注', ''),
                'background': data['basic_info'].get('background', ''),  # 背景信息
                'initial_complaint': data['主诉'],  # 来访主诉
                'counseling_goal': data.get('咨询目标', ''),  # 整体咨询目标
                'counseling_progress': data.get('咨询进度', '')  # 咨询进度
            },
            'family_structure': {
                'father_age': data['家庭结构']['父亲年龄'],
                'father_occupation': data['家庭结构']['父亲职业'],
                'father_health': data['家庭结构']['父亲身体情况'],
                'mother_age': data['家庭结构']['母亲年龄'],
                'mother_occupation': data['家庭结构']['母亲职业'],
                'mother_health': data['家庭结构']['母亲身体情况'],
                'parents_relationship': data['家庭结构']['父母关系'],
                'siblings': data['家庭结构']['兄弟姐妹'],
                'spouse_gender': data['家庭结构']['配偶性别'],
                'spouse_age': data['家庭结构']['配偶年龄'],
                'spouse_occupation': data['家庭结构']['配偶职业'],
                'spouse_health': data['家庭结构']['配偶身体情况'],
                'children': data['家庭结构'].get('孩子列表', []),
                'family_notes': data['家庭结构'].get('家庭备注', '')
            },
            'history': {
                'complaint': data['主诉'],
                'past_history': data['既往史']
            },
            'psych_tests': data.get('心理测评', []),
            'visit_history': [
                {
                    'visit_id': 'visit_001',
                    'visit_number': 1,
                    'date': visit_date,
                    'counselor': data['session_info']['咨询师姓名'],
                    'channel': data['session_info'].get('咨询渠道', ''),
                    'duration': int(data['session_info']['通话时长']) if data['session_info']['通话时长'] else 0
                }
            ],
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        }

        profile_path = visitor_dir / 'profile.json'
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)

        # 创建visits目录
        visits_dir = visitor_dir / 'visits'
        visits_dir.mkdir(exist_ok=True)

        visit_id = 'visit_001'

        # 创建visit JSON
        visit_data = {
            'visit_id': visit_id,
            'visitor_id': visitor_id,
            'visit_number': 1,
            'date': visit_date,
            'visit_summary': {
                'complaint': data['主诉'],
                'session_goal': data.get('本次目标', ''),  # 本次目标
                'consultation_result': data.get('consultation_result', ''),  # 咨询结果
                'assigned_tasks': data.get('assigned_tasks', ''),  # 布置任务
                'next_step_plan': data.get('next_step_plan', ''),  # 下一步计划
                'symptom_changes': data.get('symptom_changes', ''),  # 症状变化
                'counselor': data['session_info']['咨询师姓名'],
                'duration': int(data['session_info']['通话时长']) if data['session_info']['通话时长'] else 0
            },
            'case_data': {
                'case_id': visitor_id,  # 使用visitor_id作为case_id
                'case_summary': data['主诉'],
                'counselor_review': data['dialogue'],  # 使用咨询师复盘（完整对话）
                'counselor_review_html': f'<p>{data["dialogue"].replace(chr(10), "<br>")}</p>',
                'recordings': [],  # 录音将在后续通过录音服务器上传
                'transcript': [],  # 逐字稿
                'dialogue': data['dialogue'],
                'consultation_result': data.get('consultation_result', ''),  # 咨询结果
                'assigned_tasks': data.get('assigned_tasks', ''),  # 布置任务
                'next_step_plan': data.get('next_step_plan', ''),  # 下一步计划
                'symptom_changes': data.get('symptom_changes', ''),  # 症状变化
                'counselor_reflection': data['counselor_reflection'],  # 保存咨询师小结
                'tags': {
                    'relation': data['tags']['relation'],
                    'symptom': data['tags']['symptom']
                },
                'techniques_used': data['techniques_used'],
                'keywords': data['keywords'],
                'crisis_assessment': data['危机评估'],
                'next_session_plan': data['next_session_plan'],
                'supervision': data['督导信息'],
                'approach_analyses': {},
                'approach_analyses_html': {},
                'supervision_records': []
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        }

        visit_path = visits_dir / f'{visit_id}.json'
        with open(visit_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 已创建新案例: {visitor_id}/{visit_id}")

        # 自动重新生成HTML
        trigger_html_generation()

        return jsonify({
            'success': True,
            'message': '案例创建成功',
            'visitor_id': visitor_id,
            'visit_id': visit_id,
            'case_id': visitor_id
        })

    except Exception as e:
        print(f"✗ 保存案例失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/save_follow_up', methods=['POST'])
def save_follow_up():
    """保存后续会谈"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')

        if not visitor_id:
            return jsonify({
                'success': False,
                'error': '缺少visitor_id'
            }), 400

        visitor_dir = VISITORS_DIR / visitor_id
        if not visitor_dir.exists():
            return jsonify({
                'success': False,
                'error': f'找不到来访者: {visitor_id}'
            }), 404

        # 生成新的visit_id
        visit_id = generate_visit_id(visitor_dir)
        visits_dir = visitor_dir / 'visits'

        # 获取来访次数
        visit_number = int(visit_id.split('_')[1])

        # 创建visit JSON
        visit_data = {
            'visit_id': visit_id,
            'visitor_id': visitor_id,
            'visit_number': visit_number,
            'date': data['session_info']['接访日期'],
            'visit_summary': {
                'complaint': data['主诉'],
                'session_goal': data.get('本次目标', ''),  # 本次目标
                'consultation_result': data.get('consultation_result', ''),  # 咨询结果
                'assigned_tasks': data.get('assigned_tasks', ''),  # 布置任务
                'next_step_plan': data.get('next_step_plan', ''),  # 下一步计划
                'symptom_changes': data.get('symptom_changes', ''),  # 症状变化
                'counselor': data['session_info']['咨询师姓名'],
                'duration': int(data['session_info']['通话时长']) if data['session_info']['通话时长'] else 0
            },
            'case_data': {
                'case_id': visitor_id,
                'case_summary': data['主诉'],
                'counselor_review': data['dialogue'],  # 使用咨询师复盘（完整对话）
                'counselor_review_html': f'<p>{data["dialogue"].replace(chr(10), "<br>")}</p>',
                'recordings': [],
                'transcript': [],
                'dialogue': data['dialogue'],
                'consultation_result': data.get('consultation_result', ''),  # 咨询结果
                'assigned_tasks': data.get('assigned_tasks', ''),  # 布置任务
                'next_step_plan': data.get('next_step_plan', ''),  # 下一步计划
                'symptom_changes': data.get('symptom_changes', ''),  # 症状变化
                'counselor_reflection': data['counselor_reflection'],  # 保存咨询师小结
                'tags': {
                    'relation': data['tags']['relation'],
                    'symptom': data['tags']['symptom']
                },
                'techniques_used': data['techniques_used'],
                'keywords': data['keywords'],
                'crisis_assessment': data['危机评估'],
                'next_session_plan': data['next_session_plan'],
                'supervision': data['督导信息'],
                'approach_analyses': {},
                'approach_analyses_html': {},
                'supervision_records': []
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        }

        visit_path = visits_dir / f'{visit_id}.json'
        with open(visit_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)
        print(f"✓ 保存visit文件: {visit_path}")

        # 更新 profile.json - 添加详细日志
        profile_path = visitor_dir / 'profile.json'
        print(f"[DEBUG] 开始更新profile.json: {profile_path}")

        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)

        print(f"[DEBUG] 读取profile.json成功，当前visit_history长度: {len(profile_data.get('visit_history', []))}")

        # 添加到 visit_history
        if 'visit_history' not in profile_data:
            profile_data['visit_history'] = []
            print(f"[DEBUG] 初始化visit_history")

        # 检查是否已存在该visit_id（避免重复添加）
        existing_visit_ids = [v['visit_id'] for v in profile_data['visit_history']]
        if visit_id in existing_visit_ids:
            print(f"[WARN] visit_id {visit_id} 已存在于visit_history中，跳过添加")
        else:
            new_visit_record = {
                'visit_id': visit_id,
                'visit_number': visit_number,
                'date': data['session_info']['接访日期'],
                'counselor': data['session_info']['咨询师姓名'],
                'channel': data['session_info'].get('咨询渠道', ''),
                'duration': int(data['session_info']['通话时长']) if data['session_info']['通话时长'] else 0
            }
            profile_data['visit_history'].append(new_visit_record)
            print(f"[DEBUG] 添加新visit记录: {visit_id}, 更新后长度: {len(profile_data['visit_history'])}")

        # 更新咨询进度（如果提供了）
        if data.get('咨询进度'):
            profile_data['basic_info']['counseling_progress'] = data['咨询进度']
            print(f"[DEBUG] 更新咨询进度: {data['咨询进度']}")

        # 更新动态信息
        if data.get('basic_info'):
            if data['basic_info'].get('来访者联系电话'):
                profile_data['basic_info']['contact_phone'] = data['basic_info']['来访者联系电话']
            if data['basic_info'].get('紧急联系人'):
                profile_data['basic_info']['emergency_contact'] = data['basic_info']['紧急联系人']
            if data['basic_info'].get('紧急联系人关系'):
                profile_data['basic_info']['emergency_contact_relation'] = data['basic_info']['紧急联系人关系']
            if data['basic_info'].get('紧急联系人电话'):
                profile_data['basic_info']['emergency_contact_phone'] = data['basic_info']['紧急联系人电话']
            if data['basic_info'].get('用药情况'):
                profile_data['basic_info']['medication'] = data['basic_info']['用药情况']
            if data['basic_info'].get('来访备注'):
                profile_data['basic_info']['notes'] = data['basic_info']['来访备注']

        profile_data['metadata']['updated_at'] = datetime.now().isoformat()
        # 更新案例状态
        if data['session_info'].get('案例状态'):
            profile_data['case_status'] = data['session_info']['案例状态']

        # 保存profile.json
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)

        print(f"✓ profile.json保存成功")
        print(f"✓ 已添加后续会谈: {visitor_id}/{visit_id} (第{visit_number}次)")

        # 自动重新生成HTML
        trigger_html_generation()

        return jsonify({
            'success': True,
            'message': '会谈记录保存成功',
            'visitor_id': visitor_id,
            'visit_id': visit_id,
            'visit_number': visit_number
        })

    except Exception as e:
        print(f"✗ 保存会谈失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/update_profile_field', methods=['POST'])
def update_profile_field():
    """更新来访者档案字段（背景信息、来访主诉、咨询目标）"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        field_name = data.get('field_name')
        content = data.get('content')

        if not visitor_id or not field_name:
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        # 读取profile.json
        visitor_dir = VISITORS_DIR / visitor_id
        profile_file = visitor_dir / 'profile.json'

        if not profile_file.exists():
            return jsonify({
                'success': False,
                'error': f'来访者 {visitor_id} 不存在'
            }), 404

        with open(profile_file, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)

        # 更新字段到basic_info
        if 'basic_info' not in profile_data:
            profile_data['basic_info'] = {}

        profile_data['basic_info'][field_name] = content
        profile_data['metadata']['updated_at'] = datetime.now().isoformat()

        # 保存profile.json
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)

        # 重新生成来访者库
        try:
            subprocess.run(
                ['python', str(PROJECT_ROOT / 'src' / 'generate_visitor_library.py')],
                cwd=str(PROJECT_ROOT / 'src'),
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )
        except Exception as gen_error:
            print(f"重新生成来访者库失败: {gen_error}")

        return jsonify({
            'success': True,
            'message': f'字段 {field_name} 更新成功'
        })

    except Exception as e:
        print(f"更新profile字段失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/load_case/<visitor_id>', methods=['GET'])
def load_case(visitor_id):
    """加载来访者案例数据（用于后续接访）"""
    try:
        visitor_dir = VISITORS_DIR / visitor_id
        profile_file = visitor_dir / 'profile.json'

        if not profile_file.exists():
            return jsonify({
                'success': False,
                'error': f'找不到来访者: {visitor_id}'
            }), 404

        # 读取profile.json
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)

        # 构建静态信息（只读字段）
        basic_info = profile_data.get('basic_info', {})
        static_info = {
            '代号': basic_info.get('name', ''),
            '性别': basic_info.get('gender', ''),
            '年龄': basic_info.get('age', ''),
            '出生日期': basic_info.get('birth_date', ''),
            '职业': basic_info.get('occupation', ''),
            '婚姻状况': basic_info.get('marital_status', ''),
            '性取向': basic_info.get('sexual_orientation', ''),
            '宗教信仰': basic_info.get('religion', ''),
            '联系方式': basic_info.get('contact_phone', ''),
            'background': basic_info.get('background', ''),  # 背景信息
            'counseling_goal': basic_info.get('counseling_goal', ''),  # 整体咨询目标
            '主诉': basic_info.get('initial_complaint', ''),
            '既往史': profile_data.get('history', {}).get('past_history', {}),
            '家庭结构': profile_data.get('family_structure', {})
        }

        # 构建动态信息（可修改字段）
        dynamic_info = {
            '紧急联系人': basic_info.get('emergency_contact', ''),
            '紧急联系人关系': basic_info.get('emergency_contact_relation', ''),
            '紧急联系人电话': basic_info.get('emergency_contact_phone', ''),
            '用药情况': {'current': basic_info.get('medication', '')},
            '来访备注': basic_info.get('notes', ''),
            '咨询目标': {'current': basic_info.get('counseling_goal', '')}  # 用于兼容
        }

        # 获取访问历史，计算下次会谈编号
        visit_history = profile_data.get('visit_history', [])
        total_sessions = len(visit_history)
        next_session = total_sessions + 1

        # 返回数据
        return jsonify({
            'success': True,
            'case_id': visitor_id,
            'static_info': static_info,
            'dynamic_info': dynamic_info,
            'total_sessions': total_sessions,
            'next_session': next_session
        })

    except Exception as e:
        print(f"✗ 加载案例失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/delete_visitor', methods=['POST'])
def delete_visitor():
    """删除来访者及其所有数据"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')

        if not visitor_id:
            return jsonify({
                'success': False,
                'error': '缺少visitor_id参数'
            }), 400

        visitor_dir = VISITORS_DIR / visitor_id

        if not visitor_dir.exists():
            return jsonify({
                'success': False,
                'error': f'来访者 {visitor_id} 不存在'
            }), 404

        # 删除整个来访者目录
        import shutil
        shutil.rmtree(visitor_dir)

        print(f"✓ 已删除来访者: {visitor_id}")

        # 重新生成来访者库
        trigger_html_generation()

        return jsonify({
            'success': True,
            'message': f'来访者 {visitor_id} 已删除'
        })

    except Exception as e:
        print(f"✗ 删除来访者失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/add_insight', methods=['POST'])
def add_insight():
    """添加感悟记录（支持AI对话保存）"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')
        approach = data.get('approach', '')
        content = data.get('content', '')
        source = data.get('source', 'manual')  # manual | ai_chat

        if not all([visitor_id, visit_id, content]):
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        visit_path = VISITORS_DIR / visitor_id / 'visits' / f'{visit_id}.json'
        if not visit_path.exists():
            return jsonify({'success': False, 'error': f'找不到记录: {visitor_id}/{visit_id}'}), 404

        with open(visit_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        if 'case_data' not in visit_data:
            visit_data['case_data'] = {}
        if 'supervision_records' not in visit_data['case_data']:
            visit_data['case_data']['supervision_records'] = []

        import uuid
        record = {
            'id': str(uuid.uuid4())[:8],
            'approach': approach,
            'content': content,
            'source': source,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        visit_data['case_data']['supervision_records'].append(record)

        with open(visit_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)

        trigger_html_generation()
        print(f"✓ 添加感悟: {visitor_id}/{visit_id} [{approach}]")
        return jsonify({'success': True, 'record_id': record['id']})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete_insight', methods=['POST'])
def delete_insight_api():
    """删除感悟记录"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')
        record_id = data.get('record_id')

        if not all([visitor_id, visit_id, record_id]):
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        visit_path = VISITORS_DIR / visitor_id / 'visits' / f'{visit_id}.json'
        if not visit_path.exists():
            return jsonify({'success': False, 'error': '找不到记录'}), 404

        with open(visit_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        records = visit_data.get('case_data', {}).get('supervision_records', [])
        before = len(records)
        records = [r for r in records if r.get('id') != record_id]
        visit_data['case_data']['supervision_records'] = records

        if len(records) == before:
            return jsonify({'success': False, 'error': '未找到该感悟记录'}), 404

        with open(visit_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)

        trigger_html_generation()
        print(f"✓ 删除感悟: {record_id}")
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/add_supervisor_record', methods=['POST'])
def add_supervisor_record():
    """添加督导记录（跨流派综合督导对话保存）"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')
        content = data.get('content', '')
        approaches_covered = data.get('approaches_covered', [])

        if not all([visitor_id, visit_id, content]):
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        visit_path = VISITORS_DIR / visitor_id / 'visits' / f'{visit_id}.json'
        if not visit_path.exists():
            return jsonify({'success': False, 'error': f'找不到记录: {visitor_id}/{visit_id}'}), 404

        with open(visit_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        if 'case_data' not in visit_data:
            visit_data['case_data'] = {}
        if 'supervisor_records' not in visit_data['case_data']:
            visit_data['case_data']['supervisor_records'] = []

        import uuid
        record = {
            'id': str(uuid.uuid4())[:8],
            'content': content,
            'approaches_covered': approaches_covered,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        visit_data['case_data']['supervisor_records'].append(record)

        with open(visit_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)

        trigger_html_generation()
        print(f"✓ 添加督导记录: {visitor_id}/{visit_id}")
        return jsonify({'success': True, 'record_id': record['id']})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete_supervisor_record', methods=['POST'])
def delete_supervisor_record():
    """删除督导记录"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')
        record_id = data.get('record_id')

        if not all([visitor_id, visit_id, record_id]):
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        visit_path = VISITORS_DIR / visitor_id / 'visits' / f'{visit_id}.json'
        if not visit_path.exists():
            return jsonify({'success': False, 'error': '找不到记录'}), 404

        with open(visit_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        records = visit_data.get('case_data', {}).get('supervisor_records', [])
        before = len(records)
        records = [r for r in records if r.get('id') != record_id]
        visit_data['case_data']['supervisor_records'] = records

        if len(records) == before:
            return jsonify({'success': False, 'error': '未找到该督导记录'}), 404

        with open(visit_path, 'w', encoding='utf-8') as f:
            json.dump(visit_data, f, ensure_ascii=False, indent=2)

        trigger_html_generation()
        print(f"✓ 删除督导记录: {record_id}")
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("接访记录保存服务器")
    print("=" * 60)
    print(f"端口: 8768")
    print(f"数据目录: {VISITORS_DIR}")
    print(f"API端点:")
    print(f"  - POST /save_new_case      保存新案例（首次接访）")
    print(f"  - POST /save_follow_up     保存后续会谈")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8768, debug=False)
