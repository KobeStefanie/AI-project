#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复数据结构问题
1. 将 supervision_records 从 visit.case_data 移到 profile.json 顶层
2. 统一流派命名：大观派 → daguanpai
"""

import json
import os
from datetime import datetime

def fix_visitor_structure(visitor_id, visitors_dir='data/visitors'):
    """修复单个来访者的数据结构"""
    visitor_path = os.path.join(visitors_dir, visitor_id)
    profile_path = os.path.join(visitor_path, 'profile.json')

    print(f"\n处理来访者: {visitor_id}")

    # 1. 读取 profile.json
    with open(profile_path, 'r', encoding='utf-8') as f:
        profile = json.load(f)

    # 2. 初始化 supervision_records（如果不存在）
    if 'supervision_records' not in profile:
        profile['supervision_records'] = []
        print("  [OK] 添加 supervision_records 到 profile.json")

    # 3. 处理所有 visit 文件
    visits_dir = os.path.join(visitor_path, 'visits')
    if os.path.exists(visits_dir):
        for visit_file in sorted(os.listdir(visits_dir)):
            if visit_file.endswith('.json'):
                visit_path = os.path.join(visits_dir, visit_file)

                with open(visit_path, 'r', encoding='utf-8') as f:
                    visit = json.load(f)

                # 4. 修复流派命名：大观派 → daguanpai
                if 'case_data' in visit and 'approach_analyses' in visit['case_data']:
                    analyses = visit['case_data']['approach_analyses']

                    # 检查是否有"大观派"
                    if '大观派' in analyses:
                        analyses['daguanpai'] = analyses.pop('大观派')
                        print(f"  [OK] {visit_file}: 重命名 '大观派' -> 'daguanpai'")

                    # 统一为 daguanpai
                    if '大观学派' in analyses:
                        analyses['daguanpai'] = analyses.pop('大观学派')
                        print(f"  [OK] {visit_file}: 重命名 '大观学派' -> 'daguanpai'")

                # 5. 移除 visit.case_data.supervision_records（如果有的话，未来不再使用）
                if 'case_data' in visit and 'supervision_records' in visit['case_data']:
                    # 保留空数组，但标记为废弃
                    print(f"  [INFO] {visit_file}: case_data.supervision_records 已废弃，现在使用 profile.supervision_records")

                # 6. 更新时间戳
                if 'metadata' not in visit:
                    visit['metadata'] = {}
                visit['metadata']['updated_at'] = datetime.now().isoformat()

                # 7. 保存 visit
                with open(visit_path, 'w', encoding='utf-8') as f:
                    json.dump(visit, f, ensure_ascii=False, indent=2)

    # 8. 更新 profile.json 时间戳
    if 'metadata' not in profile:
        profile['metadata'] = {}
    profile['metadata']['updated_at'] = datetime.now().isoformat()

    # 9. 保存 profile.json
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    print(f"  [DONE] {visitor_id} 数据结构修复完成")

def main():
    """主函数"""
    print("=" * 60)
    print("开始修复数据结构...")
    print("=" * 60)

    visitors_dir = 'data/visitors'

    # 处理所有来访者
    for visitor_id in sorted(os.listdir(visitors_dir)):
        visitor_path = os.path.join(visitors_dir, visitor_id)
        if os.path.isdir(visitor_path):
            fix_visitor_structure(visitor_id, visitors_dir)

    print("\n" + "=" * 60)
    print("[SUCCESS] 所有数据结构修复完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
