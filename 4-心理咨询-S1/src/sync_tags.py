#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标签同步工具
功能：将已有的索引标签合并到统一标签库，保持标签一致性
"""

import json
import sys
from pathlib import Path
from typing import Dict, Set

# Windows GBK 兼容
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def sp(*args, **kwargs):
    """安全print"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = [str(a).encode('utf-8', errors='replace').decode('utf-8') for a in args]
        print(*safe_args, **kwargs)

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "data" / "config"
INDEX_DIR = PROJECT_ROOT / "data" / "index"

def load_json(file_path: Path) -> Dict:
    """加载JSON文件"""
    if not file_path.exists():
        return {}
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path: Path, data: Dict):
    """保存JSON文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_tags_from_index() -> Dict[str, Set[str]]:
    """从现有索引提取所有标签"""

    # 提取关系标签
    relation_tags_file = INDEX_DIR / "relation_tags.json"
    relation_data = load_json(relation_tags_file)
    relation_tags = set(relation_data.keys())

    # 提取症状标签
    symptom_tags_file = INDEX_DIR / "symptom_tags.json"
    symptom_data = load_json(symptom_tags_file)
    symptom_tags = set(symptom_data.keys())

    return {
        "relation": relation_tags,
        "symptom": symptom_tags
    }

def merge_tags_to_library():
    """合并现有标签到统一标签库"""

    sp("")
    sp("=" * 70)
    sp("  标签同步工具")
    sp("=" * 70)
    sp("")

    # 1. 加载统一标签库
    library_file = CONFIG_DIR / "tags_library.json"
    library = load_json(library_file)

    if not library:
        sp("[ERR] 统一标签库不存在，请先创建")
        return

    # 2. 提取现有索引标签
    sp("[SCAN] 扫描现有索引标签...")
    existing_tags = extract_tags_from_index()

    sp(f"  关系标签: {len(existing_tags['relation'])} 个")
    sp(f"  症状标签: {len(existing_tags['symptom'])} 个")
    sp("")

    # 3. 分析新标签
    sp("[ANALYZE] 分析标签库覆盖率...")

    # 提取标签库中的所有标签（扁平化）
    library_relation_tags = set()
    for category, data in library.get("relation_tags", {}).items():
        for subcategory, tags in data.get("children", {}).items():
            if isinstance(tags, list):
                library_relation_tags.update(tags)

    library_symptom_tags = set()
    for category, data in library.get("symptom_tags", {}).items():
        children = data.get("children", [])
        if isinstance(children, list):
            library_symptom_tags.update(children)
        elif isinstance(children, dict):
            for subcat, tags in children.items():
                library_symptom_tags.update(tags)

    # 找出索引中但不在标签库的标签
    new_relation_tags = existing_tags['relation'] - library_relation_tags
    new_symptom_tags = existing_tags['symptom'] - library_symptom_tags

    sp(f"  标签库中关系标签: {len(library_relation_tags)} 个")
    sp(f"  标签库中症状标签: {len(library_symptom_tags)} 个")
    sp("")

    if new_relation_tags:
        sp("[NEW] 发现新的关系标签（需手动分类）:")
        for tag in sorted(new_relation_tags):
            sp(f"  - {tag}")
        sp("")

    if new_symptom_tags:
        sp("[NEW] 发现新的症状标签（需手动分类）:")
        for tag in sorted(new_symptom_tags):
            sp(f"  - {tag}")
        sp("")

    if not new_relation_tags and not new_symptom_tags:
        sp("[OK] ✅ 所有索引标签都已在标签库中")
    else:
        sp("[WARN] ⚠️  请将上述新标签手动添加到 data/config/tags_library.json")

    sp("")
    sp("=" * 70)
    sp("  同步完成")
    sp("=" * 70)
    sp("")

if __name__ == "__main__":
    merge_tags_to_library()
