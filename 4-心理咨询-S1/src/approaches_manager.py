#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流派配置管理器
负责加载、验证和提供流派配置信息
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class ApproachesManager:
    """流派配置管理器"""

    def __init__(self, config_dir: str = None):
        """
        初始化流派管理器

        Args:
            config_dir: 配置目录路径，默认为 data/config/approaches/
        """
        if config_dir is None:
            base_dir = Path(__file__).parent.parent
            config_dir = base_dir / "data" / "config" / "approaches"

        self.config_dir = Path(config_dir)
        self.approaches = {}
        self._load_approaches()

    def _load_approaches(self):
        """加载所有流派配置"""
        if not self.config_dir.exists():
            print(f"警告：流派配置目录不存在：{self.config_dir}")
            return

        for json_file in self.config_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    approach_data = json.load(f)

                approach_id = approach_data.get('id')
                if approach_id:
                    self.approaches[approach_id] = approach_data
                else:
                    print(f"警告：{json_file.name} 缺少 'id' 字段")

            except Exception as e:
                print(f"警告：加载 {json_file.name} 失败：{e}")

    def get_approach(self, approach_id: str) -> Optional[Dict]:
        """
        获取指定流派的配置

        Args:
            approach_id: 流派ID（如 'daguanpai', 'cbt'）

        Returns:
            流派配置字典，如果不存在则返回None
        """
        return self.approaches.get(approach_id)

    def get_enabled_approaches(self) -> List[Dict]:
        """
        获取所有已启用的流派

        Returns:
            已启用流派配置列表，按sort_order排序
        """
        enabled = [
            approach for approach in self.approaches.values()
            if approach.get('enabled', False)
        ]

        # 按sort_order排序
        enabled.sort(key=lambda x: x.get('sort_order', 999))
        return enabled

    def get_all_approaches(self) -> List[Dict]:
        """
        获取所有流派配置

        Returns:
            所有流派配置列表，按sort_order排序
        """
        all_approaches = list(self.approaches.values())
        all_approaches.sort(key=lambda x: x.get('sort_order', 999))
        return all_approaches

    def is_enabled(self, approach_id: str) -> bool:
        """
        检查指定流派是否已启用

        Args:
            approach_id: 流派ID

        Returns:
            True如果已启用，否则False
        """
        approach = self.get_approach(approach_id)
        return approach.get('enabled', False) if approach else False

    def get_approach_name(self, approach_id: str) -> str:
        """
        获取流派名称

        Args:
            approach_id: 流派ID

        Returns:
            流派名称，如果不存在返回ID本身
        """
        approach = self.get_approach(approach_id)
        return approach.get('name', approach_id) if approach else approach_id

    def get_approach_color(self, approach_id: str) -> str:
        """
        获取流派颜色

        Args:
            approach_id: 流派ID

        Returns:
            流派颜色代码，默认为灰色
        """
        approach = self.get_approach(approach_id)
        return approach.get('color', '#6b7280') if approach else '#6b7280'

    def validate_case_analyses(self, case_data: Dict) -> Dict:
        """
        验证案例的analyses字段

        Args:
            case_data: 案例数据

        Returns:
            验证结果字典 {valid: bool, issues: List[str]}
        """
        issues = []

        if 'analyses' not in case_data:
            issues.append("缺少 'analyses' 字段")
            return {'valid': False, 'issues': issues}

        analyses = case_data['analyses']

        if not isinstance(analyses, dict):
            issues.append("'analyses' 必须是字典类型")
            return {'valid': False, 'issues': issues}

        # 检查每个流派分析
        for approach_id, analysis in analyses.items():
            if approach_id not in self.approaches:
                issues.append(f"未知的流派ID: {approach_id}")

            # 验证分析结构
            required_fields = ['tags', 'keywords']
            for field in required_fields:
                if field not in analysis:
                    issues.append(f"{approach_id} 缺少必需字段: {field}")

        return {
            'valid': len(issues) == 0,
            'issues': issues
        }

    def get_summary(self) -> Dict:
        """
        获取流派配置摘要

        Returns:
            摘要信息字典
        """
        enabled = self.get_enabled_approaches()
        return {
            'total_approaches': len(self.approaches),
            'enabled_count': len(enabled),
            'enabled_list': [a['id'] for a in enabled],
            'all_approaches': [
                {
                    'id': a['id'],
                    'name': a['name'],
                    'enabled': a.get('enabled', False)
                }
                for a in self.get_all_approaches()
            ]
        }


# 单例实例
_manager_instance = None


def get_manager() -> ApproachesManager:
    """获取流派管理器单例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ApproachesManager()
    return _manager_instance


if __name__ == "__main__":
    # 测试代码
    manager = ApproachesManager()

    print("流派配置摘要")
    print("=" * 60)

    summary = manager.get_summary()
    print(f"总流派数：{summary['total_approaches']}")
    print(f"已启用：{summary['enabled_count']}")
    print()

    print("所有流派：")
    for approach in summary['all_approaches']:
        status = "[Y]" if approach['enabled'] else "[N]"
        print(f"  {status} {approach['name']} ({approach['id']})")

    print()
    print("=" * 60)

    # 测试案例验证
    test_case = {
        "case_id": "TEST001",
        "version": "2.0",
        "analyses": {
            "daguanpai": {
                "tags": {},
                "keywords": []
            }
        }
    }

    result = manager.validate_case_analyses(test_case)
    print(f"\n案例验证结果：{'通过' if result['valid'] else '失败'}")
    if result['issues']:
        print("问题：")
        for issue in result['issues']:
            print(f"  - {issue}")
