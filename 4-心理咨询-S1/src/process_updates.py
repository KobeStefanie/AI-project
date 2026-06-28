#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理案例更新请求
功能：读取 pending_updates.json，更新案例JSON，重新生成HTML
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# ---- Windows GBK 兼容处理 ----
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def sp(*args, **kwargs):
    """安全 print：自动处理编码问题"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = []
        for a in args:
            s = str(a)
            safe_args.append(s.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
        print(*safe_args, **kwargs)


# ==================== 配置 ====================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CASES_PROCESSED = DATA_DIR / "cases" / "processed"
PENDING_UPDATES_FILE = DATA_DIR / "pending_updates.json"


# ==================== 工具函数 ====================

def load_pending_updates():
    """加载待处理的更新请求"""
    if not PENDING_UPDATES_FILE.exists():
        return []

    try:
        with open(PENDING_UPDATES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        sp(f"[ERROR] 读取 pending_updates.json 失败：{e}")
        return []


def save_case(case_id, case_data):
    """保存案例JSON文件"""
    case_file = CASES_PROCESSED / f"{case_id}.json"

    try:
        with open(case_file, 'w', encoding='utf-8') as f:
            json.dump(case_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        sp(f"[ERROR] 保存案例 {case_id} 失败：{e}")
        return False


def load_case(case_id):
    """加载案例JSON文件"""
    case_file = CASES_PROCESSED / f"{case_id}.json"

    if not case_file.exists():
        sp(f"[ERROR] 案例文件不存在：{case_id}")
        return None

    try:
        with open(case_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        sp(f"[ERROR] 读取案例 {case_id} 失败：{e}")
        return None


def generate_record_id(case_data):
    """生成历次感悟的唯一ID"""
    existing_records = case_data.get('supervision_records', [])
    max_id = 0
    for record in existing_records:
        record_id = record.get('record_id', '')
        if record_id.startswith('sr_'):
            try:
                num = int(record_id.split('_')[1])
                max_id = max(max_id, num)
            except:
                pass

    return f"sr_{max_id + 1:03d}"


def process_supervision_record_add(update):
    """处理添加历次感悟请求"""
    case_id = update.get('case_id')
    content = update.get('content', '')
    approach = update.get('approach')  # 可以为 null

    if not case_id or not content:
        sp(f"[SKIP] 添加感悟请求缺少必要字段")
        return False

    # 加载案例
    case_data = load_case(case_id)
    if not case_data:
        return False

    # 确保 supervision_records 字段存在
    if 'supervision_records' not in case_data:
        case_data['supervision_records'] = []

    # 生成新记录
    now = datetime.now().isoformat()
    new_record = {
        'record_id': generate_record_id(case_data),
        'content': content,
        'approach': approach,
        'created_at': now,
        'updated_at': now
    }

    # 添加记录
    case_data['supervision_records'].append(new_record)

    # 保存案例
    if save_case(case_id, case_data):
        sp(f"[SUCCESS] 添加感悟：{case_id} - {new_record['record_id']}")
        return True
    else:
        return False


def process_supervision_record_edit(update):
    """处理编辑历次感悟请求"""
    case_id = update.get('case_id')
    record_id = update.get('record_id')
    content = update.get('content', '')
    approach = update.get('approach')

    if not case_id or not record_id:
        sp(f"[SKIP] 编辑感悟请求缺少必要字段")
        return False

    # 加载案例
    case_data = load_case(case_id)
    if not case_data:
        return False

    # 查找并更新记录
    records = case_data.get('supervision_records', [])
    found = False
    for record in records:
        if record.get('record_id') == record_id:
            record['content'] = content
            record['approach'] = approach
            record['updated_at'] = datetime.now().isoformat()
            found = True
            break

    if not found:
        sp(f"[ERROR] 未找到感悟记录：{record_id}")
        return False

    # 保存案例
    if save_case(case_id, case_data):
        sp(f"[SUCCESS] 编辑感悟：{case_id} - {record_id}")
        return True
    else:
        return False


def process_supervision_record_delete(update):
    """处理删除历次感悟请求"""
    case_id = update.get('case_id')
    record_id = update.get('record_id')

    if not case_id or not record_id:
        sp(f"[SKIP] 删除感悟请求缺少必要字段")
        return False

    # 加载案例
    case_data = load_case(case_id)
    if not case_data:
        return False

    # 删除记录
    records = case_data.get('supervision_records', [])
    original_count = len(records)
    case_data['supervision_records'] = [r for r in records if r.get('record_id') != record_id]

    if len(case_data['supervision_records']) == original_count:
        sp(f"[ERROR] 未找到感悟记录：{record_id}")
        return False

    # 保存案例
    if save_case(case_id, case_data):
        sp(f"[SUCCESS] 删除感悟：{case_id} - {record_id}")
        return True
    else:
        return False


def process_update(update):
    """处理单个更新请求"""
    update_type = update.get('type')

    if update_type == 'supervision_record_add':
        return process_supervision_record_add(update)
    elif update_type == 'supervision_record_edit':
        return process_supervision_record_edit(update)
    elif update_type == 'supervision_record_delete':
        return process_supervision_record_delete(update)
    else:
        sp(f"[SKIP] 未知的更新类型：{update_type}")
        return False


def regenerate_html():
    """重新生成案例库HTML"""
    sp("\n[INFO] 重新生成案例库HTML...")
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "src" / "generate_case_library.py")],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            sp("[SUCCESS] HTML生成成功")
            return True
        else:
            sp(f"[ERROR] HTML生成失败：{result.stderr}")
            return False
    except Exception as e:
        sp(f"[ERROR] 调用生成脚本失败：{e}")
        return False


def clear_pending_updates():
    """清空待处理更新列表"""
    try:
        with open(PENDING_UPDATES_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        sp(f"[ERROR] 清空 pending_updates.json 失败：{e}")
        return False


# ==================== 主程序 ====================

def main():
    sp("=" * 60)
    sp("案例更新处理脚本")
    sp("=" * 60)

    # 加载待处理更新
    updates = load_pending_updates()

    if not updates:
        sp("[INFO] 没有待处理的更新")
        return

    sp(f"[INFO] 发现 {len(updates)} 个待处理更新")

    # 处理每个更新
    success_count = 0
    for i, update in enumerate(updates, 1):
        sp(f"\n[{i}/{len(updates)}] 处理更新：{update.get('type', 'unknown')}")
        if process_update(update):
            success_count += 1

    sp(f"\n[INFO] 处理完成：{success_count}/{len(updates)} 成功")

    # 如果有成功的更新，重新生成HTML
    if success_count > 0:
        if regenerate_html():
            # 清空待处理更新
            clear_pending_updates()
            sp("\n[SUCCESS] 所有更新已处理完成！")
            sp("[INFO] 请刷新浏览器查看更新")
        else:
            sp("\n[WARN] HTML生成失败，pending_updates.json 未清空")
    else:
        sp("\n[WARN] 没有成功的更新，不重新生成HTML")


if __name__ == '__main__':
    main()
