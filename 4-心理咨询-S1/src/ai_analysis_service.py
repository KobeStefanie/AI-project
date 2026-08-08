#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI分析服务
功能：基于6个流派的Prompt，调用Claude API生成多流派分析
"""

import sys
import os
import json
import anthropic
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Windows UTF-8 输出支持 - 使用更安全的方式
# 不强制包装stdout，避免subprocess环境下的冲突

PROJECT_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = PROJECT_ROOT / 'data' / 'config' / 'prompts'
APPROACHES_DIR = PROJECT_ROOT / 'data' / 'config' / 'approaches'
VISITORS_DIR = PROJECT_ROOT / 'data' / 'visitors'

# 从环境变量读取API Key，或使用默认的CatKing AI配置
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
CATKINGAI_KEY = "sk-d285143ff8b40377e38294cc41f2f86b518349f3f6278328c439bfed7d89fdde"
CATKINGAI_URL = "https://www.catkingai.com"

# 流派ID与Prompt文件的映射
APPROACH_PROMPT_MAP = {
    'daguanpai': 'daguanpai_analysis.md',
    'cbt': 'cbt_analysis.md',
    'psychodynamic': 'psychodynamic_analysis.md',
    'humanistic': 'humanistic_analysis.md',
    'existential': 'existential_analysis.md',
    'ifs': 'ifs_analysis.md'
}

# 中文字段标签映射
_KEY_ZH = {
    'unconscious_conflicts': '潜意识冲突分析',
    'primary_conflicts': '核心冲突',
    'conflict': '冲突',
    'evidence': '案例证据',
    'manifestation': '在咨询中的表现',
    'developmental_origin': '发展起源',
    'id_ego_superego': '人格结构（本我·自我·超我）',
    'id_impulses': '本我冲动',
    'ego_management': '自我功能',
    'superego_voice': '超我声音',
    'defense_mechanisms': '防御机制分析',
    'primary_defenses': '主要防御机制',
    'defense': '防御类型',
    'maturity_level': '成熟度',
    'function': '防御功能',
    'effectiveness': '有效性评估',
    'object_relations': '客体关系模式',
    'internal_objects': '内在客体',
    'relational_pattern': '关系模式',
    'splitting': '分裂现象',
    'transference_countertransference': '移情与反移情',
    'transference': '来访者移情',
    'countertransference': '咨询师反移情',
    'therapeutic_use': '治疗性使用',
    'attachment_pattern': '依恋模式分析',
    'pattern': '依恋类型',
    'triggers': '触发情境',
    'relational_impact': '对关系的影响',
    'psychodynamic_formulation': '精神动力学个案概念化',
    'therapeutic_focus': '治疗焦点',
    'primary_focus': '首要焦点',
    'interpretation_readiness': '解释时机评估',
    'next_session_recommendations': '下次咨询建议',
    'opening_intervention': '开场干预',
    'key_questions': '关键探索问题',
    'avoid': '需要避免的',
    'strengths_and_improvements': '优势与改进建议',
    'strengths': '做得好的地方',
    'improvements': '改进建议',
    'issue': '问题',
    'suggestion': '改进方向',
    'better_example': '更佳示例',
    'supervisor_comments': '督导综合点评',
    # 大观学派
    'crisis_assessment': '危机评估',
    'level': '危机等级',
    'grade': '分级',
    'sor_analysis': 'SOR分析',
    'stimulus': '刺激因素',
    'organism': '机体状态',
    'response': '反应',
    'liu_bian_san_tuo': '六变三托筛查',
    'liu_bian': '六变',
    'san_tuo': '三托',
    'crisis_intervention_plan': '危机干预方案',
    'immediate_actions': '即时行动',
    'safety_plan': '安全计划',
    'follow_up': '后续跟进',
    # CBT
    'cognitive_distortions': '认知扭曲识别',
    'distortion': '扭曲类型',
    'thought': '自动思维',
    'core_beliefs': '核心信念与假设',
    'intermediate_beliefs': '中间信念',
    'core_belief': '核心信念',
    'behavioral_patterns': '行为模式分析',
    'avoidance': '回避行为',
    'safety_behaviors': '安全行为',
    'cbt_formulation': 'CBT个案概念化',
    'treatment_plan': '治疗方案',
    'cognitive_interventions': '认知干预',
    'behavioral_interventions': '行为干预',
    'homework': '家庭作业建议',
    # 人本主义
    'empathy_analysis': '共情分析',
    'unconditional_positive_regard': '无条件积极关注',
    'congruence': '真诚一致性',
    'self_actualization': '自我实现潜能',
    'growth_direction': '成长方向',
    # 存在主义
    'existential_themes': '存在主义主题',
    'death': '死亡议题',
    'freedom': '自由与责任',
    'isolation': '孤独议题',
    'meaninglessness': '意义议题',
    'four_ultimate_concerns': '四大终极关怀',
    # IFS
    'parts_identified': '识别到的部分',
    'part': '部分名称',
    'role': '扮演角色',
    'burden': '承担的重担',
    'exile': '流放者',
    'manager': '管理者',
    'firefighter': '消防员',
    'self_energy': '自我能量评估',
    'unblending_suggestions': '解离建议',
}


def _kz(key: str) -> str:
    """获取中文标签，fallback到英文key的人类可读形式"""
    return _KEY_ZH.get(key, key.replace('_', ' ').title())


def _val_to_html(val, depth: int = 0) -> str:
    """递归将值转为 HTML"""
    if val is None:
        return ''
    if isinstance(val, bool):
        return '<span class="text-green-600 font-medium">是</span>' if val else '<span class="text-gray-400">否</span>'
    if isinstance(val, (int, float)):
        return f'<span class="font-medium">{val}</span>'
    if isinstance(val, str):
        txt = val.strip()
        if not txt:
            return ''
        return f'<p class="text-gray-700 leading-relaxed mb-1">{txt}</p>'
    if isinstance(val, list):
        if not val:
            return ''
        parts = []
        for item in val:
            if isinstance(item, dict):
                parts.append(f'<div class="pl-3 border-l-2 border-indigo-200 mb-3">{_dict_to_html(item, depth+1)}</div>')
            else:
                parts.append(f'<li class="text-gray-700 mb-1">{_val_to_html(item, depth+1)}</li>')
        if all(isinstance(i, dict) for i in val):
            return ''.join(parts)
        return f'<ul class="list-disc pl-5 mb-2 space-y-1">{"".join(parts)}</ul>'
    if isinstance(val, dict):
        return _dict_to_html(val, depth)
    return str(val)


def _dict_to_html(d: dict, depth: int = 0) -> str:
    if not d:
        return ''
    html = ''
    for k, v in d.items():
        label = _kz(k)
        if isinstance(v, (dict, list)) and v:
            tag = 'h4' if depth > 0 else 'h3'
            cls = 'font-semibold text-gray-800 mt-3 mb-1' if depth > 0 else 'font-bold text-indigo-800 text-base mt-4 mb-2'
            html += f'<{tag} class="{cls}">{label}</{tag}>'
            html += _val_to_html(v, depth + 1)
        else:
            rendered = _val_to_html(v, depth + 1)
            if rendered:
                html += f'<div class="mb-2"><span class="font-semibold text-gray-800">{label}：</span>{rendered}</div>'
    return html


def format_analysis_to_html(analysis_text: str) -> str:
    """将AI返回的JSON/Markdown分析文本转换为可读的带格式HTML"""
    import re

    # 如果是之前转换失败产生的垃圾HTML（<p>包裹的JSON），先提取原始文本
    if '<p class="text-gray-700' in analysis_text:
        # 从<p>...</p>里提取所有文本内容，还原为原始文本
        text = re.sub(r'<[^>]+>', ' ', analysis_text)
        text = re.sub(r'\s+', ' ', text).strip()
    else:
        # 已经是格式良好的HTML，直接返回
        if '<div class=' in analysis_text or '<h3 class=' in analysis_text:
            return analysis_text
        text = analysis_text

    # 清除markdown代码块标记
    text = re.sub(r'```\w*', '', text, flags=re.IGNORECASE)
    text = text.strip()

    # 从文本中提取JSON对象（找第一个{到最后一个}）
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        json_str = json_match.group(0)
        # 尝试解析
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and data:
                html = ''
                for k, v in data.items():
                    label = _kz(k)
                    html += f'<div class="mb-5 bg-indigo-50 rounded-lg p-4 border border-indigo-100">'
                    html += f'<h3 class="text-base font-bold text-indigo-900 mb-3 pb-1 border-b border-indigo-200">📌 {label}</h3>'
                    html += _val_to_html(v, depth=1)
                    html += '</div>'
                return html
        except json.JSONDecodeError:
            pass

    # JSON解析失败：用正则从原始文本提取键值对，直接渲染
    return _regex_extract_to_html(text)


def _regex_extract_to_html(text: str) -> str:
    """直接用正则从原始JSON文本提取内容渲染，不依赖json.loads"""
    import re
    html = '<div class="space-y-3">'
    # 提取 "英文key": "中文内容" 模式（字符串值）
    pattern = re.compile(r'"([a-z_]+)"\s*:\s*"((?:[^"\\]|\\.)*)"', re.MULTILINE)
    # 跟踪已输出的顶层key（用于分组）
    last_top_key = None
    for m in pattern.finditer(text):
        key, value = m.group(1), m.group(2)
        if not value.strip():
            continue
        label = _kz(key)
        # 忽略纯英文字段名（没有意义的元数据字段）
        if key in ('id', 'type', 'name'):
            continue
        html += f'<div class="mb-2 pl-2"><span class="font-semibold text-indigo-800">{label}：</span>'
        html += f'<span class="text-gray-700">{value}</span></div>'
    html += '</div>'
    return html
    text = text.strip()
    try:
        data = json.loads(text)
        html = ''
        for k, v in data.items():
            label = _kz(k)
            html += f'<div class="mb-5 bg-indigo-50 rounded-lg p-4 border border-indigo-100">'
            html += f'<h3 class="text-base font-bold text-indigo-900 mb-3 pb-1 border-b border-indigo-200">📌 {label}</h3>'
            html += _val_to_html(v, depth=1)
            html += '</div>'
        return html or '<p class="text-gray-400">（分析内容为空）</p>'
    except Exception:
        # fallback：按行渲染，使用已清理的text（不用原始analysis_text）
        html = ''
        in_list = False
        for line in text.split('\n'):
            line = line.rstrip()
            if not line:
                if in_list:
                    html += '</ul>'
                    in_list = False
                html += '<div class="mb-2"></div>'
                continue
            if line.startswith('### '):
                html += f'<h3 class="font-bold text-indigo-800 text-base mt-4 mb-1">{line[4:]}</h3>'
            elif line.startswith('## '):
                html += f'<h2 class="font-bold text-indigo-900 text-lg mt-5 mb-2">{line[3:]}</h2>'
            elif line.startswith('# '):
                html += f'<h1 class="font-bold text-indigo-900 text-xl mt-5 mb-3">{line[2:]}</h1>'
            elif re.match(r'^\*\*(.+)\*\*$', line):
                html += f'<p class="font-semibold text-gray-800 mb-1">{line[2:-2]}</p>'
            elif line.startswith('- ') or line.startswith('* '):
                if not in_list:
                    html += '<ul class="list-disc pl-5 mb-2">'
                    in_list = True
                html += f'<li class="text-gray-700 mb-1">{line[2:]}</li>'
            else:
                if in_list:
                    html += '</ul>'
                    in_list = False
                html += f'<p class="text-gray-700 leading-relaxed mb-1">{line}</p>'
        if in_list:
            html += '</ul>'
        return html


class AIAnalysisService:
    """AI分析服务类"""

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        初始化AI分析服务

        Args:
            api_key: API Key，默认使用CatKing AI
            base_url: API基础URL，默认使用CatKing AI
        """
        # 优先使用传入的参数，其次用环境变量，最后用CatKing AI默认配置
        self.api_key = api_key or ANTHROPIC_API_KEY or CATKINGAI_KEY
        resolved_url = base_url or (None if ANTHROPIC_API_KEY else CATKINGAI_URL)

        if not self.api_key:
            raise ValueError("未配置API Key")

        if resolved_url:
            self.client = anthropic.Anthropic(api_key=self.api_key, base_url=resolved_url)
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)

        self.model = "claude-opus-4-8"

    def load_prompt_template(self, approach_id: str) -> str:
        """
        加载流派的Prompt模板

        Args:
            approach_id: 流派ID

        Returns:
            Prompt模板内容
        """
        prompt_file = APPROACH_PROMPT_MAP.get(approach_id)
        if not prompt_file:
            raise ValueError(f"Unknown approach: {approach_id}")

        prompt_path = PROMPTS_DIR / prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def get_enabled_approaches(self) -> List[Dict]:
        """
        获取所有启用的流派配置

        Returns:
            启用的流派列表
        """
        approaches = []
        for config_file in APPROACHES_DIR.glob('*.json'):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                if config.get('enabled', True):
                    approaches.append(config)
            except Exception as e:
                print(f"Warning: Failed to load {config_file}: {e}")

        return sorted(approaches, key=lambda x: x.get('sort_order', 999))

    def prepare_analysis_prompt(
        self,
        approach_id: str,
        visitor_profile: Dict,
        transcript: str,
        counselor_review: str = ""
    ) -> str:
        """
        准备分析Prompt（填充模板变量）

        Args:
            approach_id: 流派ID
            visitor_profile: 来访者档案
            transcript: 咨询逐字稿
            counselor_review: 咨询师复盘（可选）

        Returns:
            填充后的Prompt
        """
        template = self.load_prompt_template(approach_id)

        # 格式化来访者档案
        profile_text = json.dumps(visitor_profile, ensure_ascii=False, indent=2)

        # 填充模板变量
        prompt = template.replace('{visitor_profile}', profile_text)
        prompt = prompt.replace('{transcript}', transcript)
        prompt = prompt.replace('{counselor_review}', counselor_review or "（无）")

        return prompt

    def analyze_with_approach(
        self,
        approach_id: str,
        visitor_profile: Dict,
        transcript: str,
        counselor_review: str = "",
        max_tokens: int = 10000
    ) -> Dict:
        """
        使用指定流派分析逐字稿

        Args:
            approach_id: 流派ID
            visitor_profile: 来访者档案
            transcript: 咨询逐字稿
            counselor_review: 咨询师复盘
            max_tokens: 最大输出token数

        Returns:
            分析结果（包含原始输出和元数据）
        """
        print(f"[AI分析] 开始 {approach_id} 流派分析...")

        prompt = self.prepare_analysis_prompt(
            approach_id,
            visitor_profile,
            transcript,
            counselor_review
        )

        try:
            import requests as _requests
            _headers = {
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            }
            _payload = {
                'model': self.model,
                'max_tokens': max_tokens,
                'temperature': 1.0,
                'stream': True,
                'messages': [{'role': 'user', 'content': prompt}]
            }
            base_str = str(self.client.base_url).rstrip('/')
            api_url = f'{base_str}/v1/messages' if '/v1' not in base_str else f'{base_str}/messages'

            _resp = _requests.post(api_url, headers=_headers, json=_payload, timeout=300,
                                   proxies={'http': None, 'https': None}, stream=True)
            _resp.raise_for_status()

            # 解析流式响应
            analysis_text = ''
            for _line in _resp.iter_lines():
                if _line:
                    _line = _line.decode('utf-8')
                    if _line.startswith('data: ') and _line != 'data: [DONE]':
                        try:
                            _chunk = __import__('json').loads(_line[6:])
                            if _chunk.get('type') == 'content_block_delta':
                                analysis_text += _chunk.get('delta', {}).get('text', '')
                        except Exception:
                            pass

            result = {
                "approach_id": approach_id,
                "analysis_text": analysis_text,
                "metadata": {
                    "model": self.model,
                    "generated_at": datetime.now().isoformat(),
                }
            }

            print(f"[AI分析] {approach_id} 完成 - 分析长度: {len(analysis_text)} 字")

            return result

        except Exception as e:
            print(f"[AI分析] {approach_id} 失败: {str(e)}")
            return {
                "approach_id": approach_id,
                "error": str(e),
                "metadata": {
                    "generated_at": datetime.now().isoformat()
                }
            }

    def analyze_all_approaches(
        self,
        visitor_profile: Dict,
        transcript: str,
        counselor_review: str = "",
        approach_ids: List[str] = None
    ) -> Dict[str, Dict]:
        """
        使用所有启用的流派分析（或指定流派）

        Args:
            visitor_profile: 来访者档案
            transcript: 咨询逐字稿
            counselor_review: 咨询师复盘
            approach_ids: 指定要分析的流派ID列表，如为None则使用所有启用的流派

        Returns:
            所有流派的分析结果 {approach_id: result}
        """
        if approach_ids is None:
            enabled_approaches = self.get_enabled_approaches()
            approach_ids = [a['id'] for a in enabled_approaches]

        results = {}
        total = len(approach_ids)

        print(f"[AI分析] 开始多流派分析，共 {total} 个流派...")

        for idx, approach_id in enumerate(approach_ids, 1):
            print(f"\n[AI分析] 进度: {idx}/{total}")
            result = self.analyze_with_approach(
                approach_id,
                visitor_profile,
                transcript,
                counselor_review
            )
            results[approach_id] = result

        print(f"\n[AI分析] 全部完成！")
        return results

    def save_analysis_to_visit(
        self,
        visitor_id: str,
        visit_id: str,
        approach_id: str,
        analysis_text: str
    ) -> bool:
        """
        保存分析结果到visit JSON文件

        Args:
            visitor_id: 来访者ID
            visit_id: 访谈ID
            approach_id: 流派ID
            analysis_text: 分析文本（HTML格式）

        Returns:
            是否保存成功
        """
        visit_json_path = VISITORS_DIR / visitor_id / 'visits' / f'{visit_id}.json'

        if not visit_json_path.exists():
            print(f"[保存失败] Visit文件不存在: {visit_json_path}")
            return False

        try:
            # 读取visit JSON
            with open(visit_json_path, 'r', encoding='utf-8') as f:
                visit_data = json.load(f)

            # 确保结构存在
            if 'case_data' not in visit_data:
                visit_data['case_data'] = {}
            if 'approach_analyses_html' not in visit_data['case_data']:
                visit_data['case_data']['approach_analyses_html'] = {}

            # 保存分析（转换为格式化HTML再存储）
            visit_data['case_data']['approach_analyses_html'][approach_id] = format_analysis_to_html(analysis_text)

            # 更新时间戳
            if 'metadata' not in visit_data:
                visit_data['metadata'] = {}
            visit_data['metadata']['updated_at'] = datetime.now().isoformat()
            visit_data['metadata']['last_ai_analysis'] = datetime.now().isoformat()

            # 写回文件
            with open(visit_json_path, 'w', encoding='utf-8') as f:
                json.dump(visit_data, f, ensure_ascii=False, indent=2)

            print(f"[保存成功] {approach_id} 分析已保存到 {visit_id}.json")
            return True

        except Exception as e:
            print(f"[保存失败] {str(e)}")
            return False


def main():
    """命令行测试入口"""
    if len(sys.argv) < 3:
        print("用法: python ai_analysis_service.py <visitor_id> <visit_id> [approach_id]")
        print("示例: python ai_analysis_service.py V20260616001 visit_001")
        print("     python ai_analysis_service.py V20260616001 visit_001 daguanpai")
        sys.exit(1)

    visitor_id = sys.argv[1]
    visit_id = sys.argv[2]
    approach_id = sys.argv[3] if len(sys.argv) > 3 else None

    # 初始化服务
    service = AIAnalysisService()

    # 读取visit数据
    visit_json_path = VISITORS_DIR / visitor_id / 'visits' / f'{visit_id}.json'
    if not visit_json_path.exists():
        print(f"错误: Visit文件不存在: {visit_json_path}")
        sys.exit(1)

    with open(visit_json_path, 'r', encoding='utf-8') as f:
        visit_data = json.load(f)

    # 准备分析输入
    visitor_profile = visit_data.get('visitor_profile', {})
    case_data = visit_data.get('case_data', {})
    # dialogue 在 case_data 里，不在顶层
    transcript = (case_data.get('dialogue') or
                  case_data.get('transcript') or
                  visit_data.get('transcript') or
                  visit_data.get('dialogue') or '')
    counselor_review = case_data.get('counselor_review_html', '')

    if not transcript:
        print("错误: 没有找到逐字稿内容")
        sys.exit(1)

    # 执行分析
    if approach_id:
        # 单个流派分析
        result = service.analyze_with_approach(
            approach_id,
            visitor_profile,
            transcript,
            counselor_review
        )

        if 'error' not in result:
            # 保存结果
            service.save_analysis_to_visit(
                visitor_id,
                visit_id,
                approach_id,
                result['analysis_text']
            )
    else:
        # 所有流派分析
        results = service.analyze_all_approaches(
            visitor_profile,
            transcript,
            counselor_review
        )

        # 保存所有结果
        for aid, result in results.items():
            if 'error' not in result:
                service.save_analysis_to_visit(
                    visitor_id,
                    visit_id,
                    aid,
                    result['analysis_text']
                )


if __name__ == '__main__':
    main()
