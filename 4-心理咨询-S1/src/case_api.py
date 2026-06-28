"""
心理咨询案例管理 API 后端
提供案例的创建、加载、更新、会谈管理等功能
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
from pathlib import Path
import shutil

app = Flask(__name__)
CORS(app)

# 配置路径
BASE_DIR = Path(__file__).parent.parent
CASES_DIR = BASE_DIR / "data" / "cases"
ACTIVE_DIR = CASES_DIR / "active"
CLOSED_DIR = CASES_DIR / "closed"
PROCESSED_DIR = CASES_DIR / "processed"
BACKUP_DIR = BASE_DIR / "data" / "backup"
PENDING_UPDATES_FILE = BASE_DIR / "data" / "pending_updates.json"

# 确保目录存在
for dir_path in [ACTIVE_DIR, CLOSED_DIR, PROCESSED_DIR, BACKUP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


def get_case_path(case_id, status='active'):
    """获取案例文件路径"""
    if status == 'active':
        return ACTIVE_DIR / f"{case_id}.json"
    elif status == 'closed':
        return CLOSED_DIR / f"{case_id}.json"
    elif status == 'archived':
        return PROCESSED_DIR / f"{case_id}.json"
    return None


def load_case(case_id, status='active'):
    """加载案例数据"""
    case_path = get_case_path(case_id, status)
    if not case_path or not case_path.exists():
        return None

    with open(case_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_case(case_data, backup=True):
    """保存案例数据（支持自动备份）"""
    case_id = case_data['case_id']
    status = case_data['status']
    case_path = get_case_path(case_id, status)

    # 备份旧数据
    if backup and case_path.exists():
        backup_dir = BACKUP_DIR / case_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{timestamp}.json"
        shutil.copy(case_path, backup_path)

    # 更新时间戳
    case_data['last_updated'] = datetime.now().isoformat()

    # 保存数据
    with open(case_path, 'w', encoding='utf-8') as f:
        json.dump(case_data, f, ensure_ascii=False, indent=2)

    return True


def calculate_age(birth_date):
    """根据出生日期计算年龄"""
    if not birth_date:
        return None
    birth = datetime.strptime(birth_date, "%Y-%m-%d")
    today = datetime.now()
    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    return age


# ==================== API 接口 ====================

@app.route('/api/cases', methods=['GET'])
def list_cases():
    """获取所有案例列表"""
    try:
        cases = []

        # 遍历所有状态的案例
        for status, dir_path in [('active', ACTIVE_DIR), ('closed', CLOSED_DIR)]:
            for case_file in dir_path.glob('*.json'):
                with open(case_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 计算年龄
                    age = calculate_age(data['static_info'].get('出生日期'))

                    # 获取最后一次会谈信息
                    last_session = None
                    if data['sessions']:
                        last_session = data['sessions'][-1]

                    cases.append({
                        'case_id': data['case_id'],
                        'status': data['status'],
                        '代号': data['static_info']['代号'],
                        '性别': data['static_info']['性别'],
                        '年龄': age,
                        '主诉简述': data['static_info']['主诉'][:30] + '...' if len(data['static_info']['主诉']) > 30 else data['static_info']['主诉'],
                        'total_sessions': len(data['sessions']),
                        'last_session_date': last_session['date'] if last_session else None,
                        'created_at': data['created_at'],
                        'last_updated': data['last_updated']
                    })

        # 按最后更新时间倒序排序
        cases.sort(key=lambda x: x['last_updated'], reverse=True)

        return jsonify({'success': True, 'cases': cases})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cases', methods=['POST'])
def create_case():
    """创建新案例（首次接访）"""
    try:
        data = request.json

        # 检查案例代号是否已存在
        case_id = data['static_info']['代号']
        if get_case_path(case_id, 'active').exists():
            return jsonify({'success': False, 'error': '案例代号已存在'}), 400

        # 构建案例数据
        now = datetime.now().isoformat()
        case_data = {
            'case_id': case_id,
            'status': 'active',
            'created_at': now,
            'last_updated': now,
            'closed_at': None,
            'closure_reason': None,

            'static_info': data['static_info'],

            'dynamic_info': {
                '咨询目标': {
                    'current': data['dynamic_info']['咨询目标'],
                    'history': [{
                        'value': data['dynamic_info']['咨询目标'],
                        'session': 1,
                        'changed_at': now,
                        'reason': '首次设定'
                    }]
                },
                '用药情况': {
                    'current': data['dynamic_info'].get('用药情况', ''),
                    'history': [{
                        'value': data['dynamic_info'].get('用药情况', ''),
                        'session': 1,
                        'changed_at': now,
                        'reason': '首次记录'
                    }]
                } if data['dynamic_info'].get('用药情况') else {'current': '', 'history': []},
                '紧急联系人': data['dynamic_info'].get('紧急联系人', ''),
                '紧急联系电话': data['dynamic_info'].get('紧急联系电话', ''),
                '来访备注': data['dynamic_info'].get('来访备注', '')
            },

            'sessions': [],

            'closure': {
                'closed_at': None,
                'closed_by': None,
                'closure_reason': None,
                'closure_summary': None,
                'total_sessions': 0
            }
        }

        # 添加第一次会谈记录
        if 'session' in data:
            session_data = data['session']
            session_data['session_number'] = 1
            session_data['previous_summary'] = None
            session_data['created_at'] = now
            session_data['updated_at'] = now
            case_data['sessions'].append(session_data)

        # 保存案例
        save_case(case_data, backup=False)

        return jsonify({'success': True, 'case_id': case_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cases/<case_id>', methods=['GET'])
def get_case(case_id):
    """加载指定案例"""
    try:
        # 先在 active 查找，再在 closed 查找
        case_data = load_case(case_id, 'active')
        if not case_data:
            case_data = load_case(case_id, 'closed')

        if not case_data:
            return jsonify({'success': False, 'error': '案例不存在'}), 404

        # 计算年龄
        age = calculate_age(case_data['static_info'].get('出生日期'))
        case_data['static_info']['年龄'] = age

        return jsonify({'success': True, 'case': case_data})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cases/<case_id>/sessions', methods=['POST'])
def add_session(case_id):
    """添加新会谈记录"""
    try:
        case_data = load_case(case_id, 'active')
        if not case_data:
            return jsonify({'success': False, 'error': '案例不存在或已结案'}), 404

        session_data = request.json
        now = datetime.now().isoformat()

        # 自动递增会谈次数
        session_number = len(case_data['sessions']) + 1

        # 处理咨询目标变化
        if 'goal_change' in session_data:
            goal_change = session_data.pop('goal_change')
            if '咨询目标' not in case_data['dynamic_info']:
                case_data['dynamic_info']['咨询目标'] = {'current': '', 'history': []}

            case_data['dynamic_info']['咨询目标']['history'].append({
                'value': goal_change['new_goal'],
                'session': session_number,
                'changed_at': now,
                'reason': goal_change['reason']
            })
            case_data['dynamic_info']['咨询目标']['current'] = goal_change['new_goal']

        # 处理用药情况变化
        if 'medication_change' in session_data:
            med_change = session_data.pop('medication_change')
            if '用药情况' not in case_data['dynamic_info']:
                case_data['dynamic_info']['用药情况'] = {'current': '', 'history': []}

            case_data['dynamic_info']['用药情况']['history'].append({
                'value': med_change['new_medication'],
                'session': session_number,
                'changed_at': now,
                'reason': med_change['reason']
            })
            case_data['dynamic_info']['用药情况']['current'] = med_change['new_medication']

        # 处理其他动态信息更新
        if 'dynamic_updates' in session_data:
            updates = session_data.pop('dynamic_updates')
            for key, value in updates.items():
                if key in ['紧急联系人', '紧急联系电话', '来访备注']:
                    case_data['dynamic_info'][key] = value

        # 设置会谈编号
        session_data['session_number'] = session_number

        # 加载上次概要
        if case_data['sessions']:
            last_session = case_data['sessions'][-1]
            session_data['previous_summary'] = last_session.get('summary', '')
        else:
            session_data['previous_summary'] = None

        # 添加时间戳
        session_data['created_at'] = now
        session_data['updated_at'] = now

        # 添加到案例
        case_data['sessions'].append(session_data)

        # 保存
        save_case(case_data)

        return jsonify({'success': True, 'session_number': session_number})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cases/<case_id>/sessions/<int:session_num>', methods=['PUT'])
def update_session(case_id, session_num):
    """修改指定会谈记录"""
    try:
        # 先尝试 active，再尝试 closed
        case_data = load_case(case_id, 'active')
        status = 'active'
        if not case_data:
            case_data = load_case(case_id, 'closed')
            status = 'closed'

        if not case_data:
            return jsonify({'success': False, 'error': '案例不存在'}), 404

        # 查找会谈记录
        session_index = session_num - 1
        if session_index < 0 or session_index >= len(case_data['sessions']):
            return jsonify({'success': False, 'error': '会谈记录不存在'}), 404

        # 更新会谈数据
        updated_data = request.json
        session = case_data['sessions'][session_index]

        # 保留原始时间戳，更新修改时间
        updated_data['created_at'] = session['created_at']
        updated_data['updated_at'] = datetime.now().isoformat()
        updated_data['session_number'] = session_num

        case_data['sessions'][session_index] = updated_data

        # 保存
        case_data['status'] = status
        save_case(case_data)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cases/<case_id>/goal', methods=['PUT'])
def update_goal(case_id):
    """更新咨询目标"""
    try:
        case_data = load_case(case_id, 'active')
        if not case_data:
            return jsonify({'success': False, 'error': '案例不存在或已结案'}), 404

        data = request.json
        new_goal = data['value']
        reason = data['reason']

        # 添加到历史
        now = datetime.now().isoformat()
        current_session = len(case_data['sessions']) + 1  # 下次会谈次数

        case_data['dynamic_info']['咨询目标']['history'].append({
            'value': new_goal,
            'session': current_session,
            'changed_at': now,
            'reason': reason
        })

        # 更新当前值
        case_data['dynamic_info']['咨询目标']['current'] = new_goal

        # 保存
        save_case(case_data)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cases/<case_id>/medication', methods=['PUT'])
def update_medication(case_id):
    """更新用药情况"""
    try:
        case_data = load_case(case_id, 'active')
        if not case_data:
            return jsonify({'success': False, 'error': '案例不存在或已结案'}), 404

        data = request.json
        new_medication = data['value']
        reason = data['reason']

        # 添加到历史
        now = datetime.now().isoformat()
        current_session = len(case_data['sessions']) + 1

        if '用药情况' not in case_data['dynamic_info']:
            case_data['dynamic_info']['用药情况'] = {'current': '', 'history': []}

        case_data['dynamic_info']['用药情况']['history'].append({
            'value': new_medication,
            'session': current_session,
            'changed_at': now,
            'reason': reason
        })

        # 更新当前值
        case_data['dynamic_info']['用药情况']['current'] = new_medication

        # 保存
        save_case(case_data)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cases/<case_id>/close', methods=['PUT'])
def close_case(case_id):
    """结案"""
    try:
        case_data = load_case(case_id, 'active')
        if not case_data:
            return jsonify({'success': False, 'error': '案例不存在或已结案'}), 404

        data = request.json

        # 更新结案信息
        now = datetime.now().isoformat()
        case_data['status'] = 'closed'
        case_data['closed_at'] = now
        case_data['closure'] = {
            'closed_at': now,
            'closed_by': data.get('closed_by', ''),
            'closure_reason': data.get('reason', ''),
            'closure_summary': data.get('summary', ''),
            'total_sessions': len(case_data['sessions'])
        }

        # 移动文件从 active 到 closed
        old_path = get_case_path(case_id, 'active')
        new_path = get_case_path(case_id, 'closed')

        # 保存到 closed
        case_data['status'] = 'closed'
        with open(new_path, 'w', encoding='utf-8') as f:
            json.dump(case_data, f, ensure_ascii=False, indent=2)

        # 删除 active 中的文件
        if old_path.exists():
            old_path.unlink()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai/summary', methods=['POST'])
def generate_summary():
    """生成会谈概要（AI）"""
    try:
        data = request.json
        dialogue = data.get('dialogue', '')

        # TODO: 这里接入真实的AI模型生成概要
        # 暂时返回简单截取
        summary = dialogue[:300] if len(dialogue) > 300 else dialogue

        return jsonify({'success': True, 'summary': summary})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pending_updates', methods=['GET'])
def get_pending_updates():
    """获取待处理的更新列表"""
    try:
        if not PENDING_UPDATES_FILE.exists():
            return jsonify([])

        with open(PENDING_UPDATES_FILE, 'r', encoding='utf-8') as f:
            updates = json.load(f)

        return jsonify(updates if isinstance(updates, list) else [])

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pending_updates', methods=['POST'])
def save_pending_updates():
    """保存待处理的更新列表"""
    try:
        updates = request.json

        if not isinstance(updates, list):
            return jsonify({'success': False, 'error': '数据格式错误，应为数组'}), 400

        with open(PENDING_UPDATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(updates, f, ensure_ascii=False, indent=2)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("心理咨询案例管理 API 服务")
    print("=" * 50)
    print(f"数据目录: {CASES_DIR}")
    print(f"Active: {ACTIVE_DIR}")
    print(f"Closed: {CLOSED_DIR}")
    print(f"Backup: {BACKUP_DIR}")
    print("=" * 50)
    print("服务运行在: http://localhost:5001")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5001, debug=True)
