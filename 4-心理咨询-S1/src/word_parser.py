#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的Word文档解析系统
支持识别接访记录的所有字段
"""

import re
from docx import Document
import json
import requests
import time


class IntakeRecordParser:
    """接访记录Word文档解析器"""

    def __init__(self, tags_library_path):
        """初始化解析器"""
        with open(tags_library_path, 'r', encoding='utf-8') as f:
            self.tags_library = json.load(f)

        # CatKingAI API配置
        self.api_key = 'sk-d285143ff8b40377e38294cc41f2f86b518349f3f6278328c439bfed7d89fdde'
        self.api_base = 'https://www.catkingai.com/v1'

        # 危机等级关键词
        self.crisis_keywords = {
            'S': ['自杀', '遗书', '计划', '手段', '失联', '轻生'],
            'L': ['他杀', '弑母', '弑父', '杀人', '自伤', '幻听', '幻觉', '精神病'],
            'M': ['中度', '功能受损', '创伤', '急性期', '焦虑', '抑郁', '压力大'],
            'C': ['慢性', '关系问题', '成长议题', '长期'],
            'Z': ['正常', '偶发', '一般性']
        }

    def parse(self, doc_path):
        """解析Word文档"""
        doc = Document(doc_path)

        result = {
            'basic_info': {},
            'family_structure': {},
            'history': {},
            'medication': {},
            'session_info': {},
            'complaint': '',
            'dialogue': '',
            'counselor_reflection': '',
            'crisis_assessment': {},
            'tags': {'relation': [], 'symptom': []},
            'keywords': []
        }

        # 收集所有文本
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        full_text = '\n'.join(paragraphs)

        # 1. 结构化解析（标题：内容 格式）
        self._parse_structured_fields(paragraphs, result)

        # 2. 智能提取（叙事性文本）
        if not result['basic_info'].get('代号'):
            self._parse_narrative_format(paragraphs, full_text, result)

        # 3. 提取家庭结构
        self._extract_family_structure(full_text, result)

        # 4. 提取既往史和用药
        self._extract_history_and_medication(full_text, result)

        # 5. 危机等级评估
        result['crisis_assessment'] = self._assess_crisis_level(full_text)

        # 6. 标签和关键词识别
        result['tags'], result['keywords'] = self._identify_tags_and_keywords(full_text)

        # 7. 六变三托征兆识别
        result['six_changes_three_entrustments'] = self._detect_six_changes_three_entrustments(full_text)

        # 8. AI智能分析主诉 - 提炼核心诉求
        if result.get('complaint'):
            result['complaint_analysis'] = self._analyze_complaint_with_ai(result['complaint'], full_text)

        return result

    def _parse_structured_fields(self, paragraphs, result):
        """解析结构化字段（标题：内容格式）"""
        current_section = None

        for text in paragraphs:
            # 识别字段
            if '：' in text or ':' in text:
                parts = text.replace(':', '：').split('：', 1)
                if len(parts) == 2:
                    key, value = parts[0].strip(), parts[1].strip()

                    # 基本信息
                    if '代号' in key or '案例代号' in key:
                        result['basic_info']['代号'] = value
                    elif key == '性别':
                        result['basic_info']['性别'] = value
                    elif key == '年龄':
                        result['basic_info']['年龄'] = value
                    elif key == '职业':
                        result['basic_info']['职业'] = value
                    elif '婚姻' in key:
                        result['basic_info']['婚姻状况'] = value
                    elif '性取向' in key:
                        result['basic_info']['性取向'] = value
                    elif '宗教' in key:
                        result['basic_info']['宗教信仰'] = value
                    elif '联系' in key or '电话' in key:
                        result['basic_info']['联系方式'] = value

                    # 时间信息
                    elif '时间' in key or '日期' in key:
                        result['session_info']['时间'] = value

                    # 主诉
                    elif '主诉' in key:
                        result['complaint'] = value
                        current_section = 'complaint'

                    # 咨询对话
                    elif '对话' in key or '咨询记录' in key:
                        result['dialogue'] = value
                        current_section = 'dialogue'

                    # 咨询师反思
                    elif '反思' in key or '复盘' in key or '评估' in key:
                        result['counselor_reflection'] = value
                        current_section = 'reflection'

                    # 既往史
                    elif '既往' in key or '病史' in key:
                        result['history']['既往史'] = value

                    # 用药信息
                    elif '用药' in key or '药物' in key:
                        result['medication']['当前用药'] = value
            else:
                # 内容段落
                if current_section == 'complaint' and result.get('complaint'):
                    result['complaint'] += '\n' + text
                elif current_section == 'dialogue' and result.get('dialogue'):
                    result['dialogue'] += '\n' + text
                elif current_section == 'reflection' and result.get('counselor_reflection'):
                    result['counselor_reflection'] += '\n' + text

    def _parse_narrative_format(self, paragraphs, full_text, result):
        """解析叙事性格式（从连续文本中提取）"""
        # 标题作为代号
        if paragraphs:
            result['basic_info']['代号'] = paragraphs[0][:50]

        # 提取时间（15:45-15:56格式）
        time_match = re.search(r'(\d{1,2}[:：]\d{2}[-–—]\d{1,2}[:：]\d{2})', full_text)
        if time_match:
            result['session_info']['时间'] = time_match.group(1)

        # 提取年龄和性别
        patterns = [
            r'男生[：:]\s*(\d+)\s*岁',
            r'女生[：:]\s*(\d+)\s*岁',
            r'(\d+)\s*岁[，,。、\s]*([男女])',
            r'([男女])[，,。、\s]*(\d+)\s*岁'
        ]

        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                groups = match.groups()
                for g in groups:
                    if g in ['男', '女']:
                        result['basic_info']['性别'] = g
                    elif g.isdigit():
                        result['basic_info']['年龄'] = g

                # 性别推断
                if '男生' in match.group(0):
                    result['basic_info']['性别'] = '男'
                elif '女生' in match.group(0):
                    result['basic_info']['性别'] = '女'

                if result['basic_info'].get('性别') and result['basic_info'].get('年龄'):
                    break

        # 提取主诉（第二或第三段，通常包含主要问题描述）
        if not result.get('complaint') and len(paragraphs) > 1:
            for para in paragraphs[1:4]:
                if len(para) > 50:  # 足够长的段落
                    result['complaint'] = para[:300]
                    break

        # 提取对话记录 - 如果没有明确标题，将主要内容段落作为dialogue
        if not result.get('dialogue') and len(paragraphs) >= 3:
            # 跳过标题和时间，从第3段开始作为对话内容
            dialogue_paragraphs = []
            for i, para in enumerate(paragraphs):
                # 跳过标题（第1段）和时间（第2段，通常很短）
                if i == 0 or (i == 1 and len(para) < 30):
                    continue
                # 跳过最后的咨询师反思段落（通常很短且包含"我不知道"等反思性语言）
                if len(para) < 100 and ('反思' in para or '不知道' in para or '该说什么' in para):
                    result['counselor_reflection'] = para
                    continue
                dialogue_paragraphs.append(para)

            if dialogue_paragraphs:
                result['dialogue'] = '\n\n'.join(dialogue_paragraphs)

    def _extract_family_structure(self, text, result):
        """提取家庭结构信息 - 详细提取年龄、职业、身体情况"""
        family = result['family_structure']

        # 父亲信息
        if '父亲' in text or '爸爸' in text:
            # 提取父亲年龄
            father_age_patterns = [
                r'父亲[：:，,]\s*(\d+)\s*岁',
                r'父亲.*?(\d+)\s*岁',
                r'爸爸[：:，,]\s*(\d+)\s*岁',
            ]
            for pattern in father_age_patterns:
                match = re.search(pattern, text)
                if match:
                    family['父亲年龄'] = match.group(1)
                    break

            # 提取父亲职业
            father_job_patterns = [
                r'父亲[：:]\s*([^，。\n]*?)(工人|农民|教师|医生|公务员|职员|经理|工程师|退休|无业|已故)',
                r'父亲.*?职业[：:]\s*([^，。\n]+)',
            ]
            for pattern in father_job_patterns:
                match = re.search(pattern, text)
                if match:
                    family['父亲职业'] = match.group(1) if len(match.groups()) == 1 else match.group(2)
                    break

            # 提取父亲身体情况
            father_health_keywords = ['健康', '健在', '去世', '已故', '病重', '患病', '残疾']
            for keyword in father_health_keywords:
                if f'父亲' in text and keyword in text:
                    family['父亲身体情况'] = keyword
                    break

        # 母亲信息
        if '母亲' in text or '妈妈' in text:
            # 提取母亲年龄
            mother_age_patterns = [
                r'母亲[：:，,]\s*(\d+)\s*岁',
                r'母亲.*?(\d+)\s*岁',
                r'妈妈[：:，,]\s*(\d+)\s*岁',
            ]
            for pattern in mother_age_patterns:
                match = re.search(pattern, text)
                if match:
                    family['母亲年龄'] = match.group(1)
                    break

            # 提取母亲职业
            mother_job_patterns = [
                r'母亲[：:]\s*([^，。\n]*?)(工人|农民|教师|医生|公务员|职员|经理|工程师|退休|无业|家庭主妇)',
                r'母亲.*?职业[：:]\s*([^，。\n]+)',
            ]
            for pattern in mother_job_patterns:
                match = re.search(pattern, text)
                if match:
                    family['母亲职业'] = match.group(1) if len(match.groups()) == 1 else match.group(2)
                    break

            # 提取母亲身体情况
            mother_health_patterns = [
                r'母亲.*?(病重|重病|癌症|阿尔茨海默|失智|中风|瘫痪|卧床|无法自理)',
                r'母亲.*?(健康|健在|去世|已故)',
            ]
            for pattern in mother_health_patterns:
                match = re.search(pattern, text)
                if match:
                    family['母亲身体情况'] = match.group(1)
                    break

            # 特殊情况：照顾母亲暗示母亲身体不好
            if '照顾' in text and '母亲' in text and not family.get('母亲身体情况'):
                family['母亲身体情况'] = '需要照顾'

        # 父母关系
        parents_relation_keywords = {
            '离异': '离异', '离婚': '离异', '分居': '分居',
            '和睦': '和睦', '关系好': '和睦',
            '争吵': '关系紧张', '冲突': '关系紧张', '不和': '关系紧张'
        }
        for keyword, relation in parents_relation_keywords.items():
            if keyword in text and ('父母' in text or ('父亲' in text and '母亲' in text)):
                family['父母关系'] = relation
                break

        # 兄弟姐妹
        sibling_patterns = [
            r'(独生子女|独生子|独生女)',
            r'有.*?([一二三四五]\个?)(哥哥|姐姐|弟弟|妹妹)',
            r'兄弟姐妹[：:]\s*([^，。\n]+)',
        ]
        for pattern in sibling_patterns:
            match = re.search(pattern, text)
            if match:
                if '独生' in match.group(0):
                    family['兄弟姐妹'] = '独生子女'
                else:
                    family['兄弟姐妹'] = match.group(0)
                break

        # 配偶信息
        if '配偶' in text or '妻子' in text or '丈夫' in text or '已婚' in text or '结婚' in text:
            # 配偶年龄
            spouse_age_match = re.search(r'(配偶|妻子|丈夫)[：:，,]\s*(\d+)\s*岁', text)
            if spouse_age_match:
                family['配偶年龄'] = spouse_age_match.group(2)

            # 配偶职业
            spouse_job_match = re.search(r'(配偶|妻子|丈夫).*?职业[：:]\s*([^，。\n]+)', text)
            if spouse_job_match:
                family['配偶职业'] = spouse_job_match.group(2)

        # 子女信息
        if '儿子' in text or '女儿' in text or '孩子' in text:
            children_patterns = [
                r'([一二三四五]\个?)?[儿女]?[子女孩][：:]\s*([^，。\n]+)',
                r'孩子[：:]\s*([^，。\n]+)',
            ]
            for pattern in children_patterns:
                match = re.search(pattern, text)
                if match:
                    family['孩子信息'] = match.group(0)
                    break

    def _extract_history_and_medication(self, text, result):
        """提取既往史和用药信息"""
        history = result['history']
        medication = result['medication']

        # 既往咨询史
        if '咨询史' in text or '心理咨询' in text:
            if '无咨询史' in text or '未曾咨询' in text:
                history['既往咨询史'] = '无'
            else:
                history_match = re.search(r'既往咨询史[：:]\s*([^，。\n]+)', text)
                if history_match:
                    history['既往咨询史'] = history_match.group(1)
                else:
                    history['既往咨询史'] = '有'

        # 精神科就诊史
        if '精神科' in text or '就诊史' in text:
            if '无就诊史' in text or '未曾就诊' in text:
                history['精神科就诊史'] = '无'
            else:
                history['精神科就诊史'] = '有'

        # 用药信息
        med_keywords = ['服用', '用药', '药物', '抗抑郁', '抗焦虑', '镇静', '安眠']
        for keyword in med_keywords:
            if keyword in text:
                # 提取药物名称和剂量
                med_patterns = [
                    r'([一-龥]+[片胶囊剂])\s*(\d+\.?\d*)\s*(mg|毫克|片)',
                    r'服用([一-龥]+)',
                ]
                matches = []
                for pattern in med_patterns:
                    matches.extend(re.findall(pattern, text))

                if matches:
                    medication['当前用药'] = str(matches)
                    break

    def _assess_crisis_level(self, text):
        """评估危机等级 - 大观学派A-Z 26级体系（关键词匹配 + 语境分析）"""
        matched_levels = []

        # 大观学派A-Z 26级评估体系
        crisis_levels = {
            # 第七等：急迫危机（X-Z）
            'Z': {'name': 'Z-自杀行为', 'keywords': ['正在自杀', '已经服药', '已经跳', '刀割', '上吊', '正在割', '吞药'], 'layer': '急迫危机'},
            'Y': {'name': 'Y-病发失控', 'keywords': ['心率加快', '胸闷', '失控', '呼吸困难', '喘不过气'], 'layer': '急迫危机'},
            'X': {'name': 'X-立刻去死', 'keywords': ['现在就去死', '马上去死', '立刻结束', '现在就跳', '立即自杀'], 'layer': '急迫危机'},

            # 第六等：重度危机-准备进入自杀程序（V-W）
            'W2': {'name': 'W2-临终安排', 'keywords': ['遗嘱', '后事', '葬礼', '告别信', '遗言'], 'layer': '重度危机'},
            'W1': {'name': 'W1-自杀安排', 'keywords': ['计划自杀', '准备好了', '买好药', '找好地方', '准备了绳子'], 'layer': '重度危机'},
            'V2': {'name': 'V2-无法制止', 'keywords': ['拦不住我', '没人能救我', '阻止不了'], 'layer': '重度危机'},
            'V1': {'name': 'V1-自伤经验', 'keywords': ['自杀过', '割腕', '自残', '自虐', '以前自杀', '割过手腕'], 'layer': '重度危机'},

            # 第五等：重度危机-已启动自杀方程式（S-U）
            'U': {'name': 'U-目的性自杀', 'keywords': ['只有我死了', '用死来', '以死相逼', '死了他们才', '用死证明'], 'layer': '重度危机'},
            'T': {'name': 'T-自杀意念', 'keywords': ['就是想死', '活着没意义', '不知为何想死', '总想自杀', '一直想死'], 'layer': '重度危机'},
            'S3': {'name': 'S3-自杀动机(未来)', 'keywords': ['将来会自杀', '以后会死', '迟早要死'], 'layer': '重度危机'},
            'S2': {'name': 'S2-自杀动机(现在)', 'keywords': ['现在想自杀', '我要自杀', '想要自杀'], 'layer': '重度危机'},
            'S1': {'name': 'S1-自杀动机(过去)', 'keywords': ['曾经想自杀', '以前想死过', '那时想死'], 'layer': '重度危机'},

            # 第四等：中度危机-异常情绪困扰（P-R）
            'R2': {'name': 'R2-死了算了', 'keywords': ['死了算了', '常常想去死', '死掉算了', '去死算了'], 'layer': '中度危机'},
            'R1': {'name': 'R1-太痛苦了', 'keywords': ['太痛苦', '受不了', '痛苦极了', '撑不住'], 'layer': '中度危机'},
            'Q2': {'name': 'Q2-活不下去', 'keywords': ['活不下去', '撑不下去', '过不下去', '没法活'], 'layer': '中度危机'},
            'Q1': {'name': 'Q1-不快乐', 'keywords': ['不快乐', '很痛苦', '很难受', '非常难过'], 'layer': '中度危机'},
            'P': {'name': 'P-重郁/狂躁', 'keywords': ['重度抑郁', '大哭', '狂躁', '天天哭', '每天哭'], 'layer': '中度危机'},

            # 第三等：中度危机-异常动机困扰（K-O）
            'O': {'name': 'O-生存信念瓦解', 'keywords': ['活一天算一天', '不知道明天', '坚持不了', '没有希望', '没有未来'], 'layer': '中度危机'},
            'N': {'name': 'N-家庭责任瓦解', 'keywords': ['家里没我也好', '不需要我', '我是负担', '没我更好'], 'layer': '中度危机'},
            'M': {'name': 'M-对生命的敌意', 'keywords': ['为何生下我', '不该出生', '生命无意义', '为什么要出生'], 'layer': '中度危机'},
            'L': {'name': 'L-敌意/报复', 'keywords': ['报复', '恨', '敌意', '攻击', '弑', '杀', '伤害他', '想打', '想揍'], 'layer': '中度危机'},
            'K': {'name': 'K-焦虑恐慌', 'keywords': ['深度焦虑', '恐慌', '畏惧', '强迫', '焦虑不安', '害怕'], 'layer': '中度危机'},

            # 第二等：轻度危机-人际冲突挫败（H-J）
            'J': {'name': 'J-对自己负向观', 'keywords': ['我不行', '我很差', '我失败', '自责', '自卑', '我没用'], 'layer': '轻度危机'},
            'I': {'name': 'I-对他人负向观', 'keywords': ['他们都不好', '批评别人', '排斥', '都是坏人'], 'layer': '轻度危机'},
            'H': {'name': 'H-对环境负向观', 'keywords': ['这世界', '社会不好', '环境恶劣', '泛化', '灾难化', '世界糟糕'], 'layer': '轻度危机'},

            # 第一等：轻度危机-生活事件失控（A-G）
            'G': {'name': 'G-精神困扰', 'keywords': ['睡不好', '吃不下', '精神不好', '控制不了情绪', '失眠'], 'layer': '轻度危机'},
            'F': {'name': 'F-冷漠', 'keywords': ['就这样吧', '无所谓', '冷漠', '麻木', '不在乎'], 'layer': '轻度危机'},
            'E': {'name': 'E-痛苦绝望', 'keywords': ['绝望', '崩溃', '痛苦', '很绝望'], 'layer': '轻度危机'},
            'D': {'name': 'D-忧思苦恼', 'keywords': ['苦恼', '忧愁', '烦恼', '发愁'], 'layer': '轻度危机'},
            'C': {'name': 'C-无解决方案', 'keywords': ['不知道怎么办', '没办法', '无法解决', '解决不了'], 'layer': '轻度危机'},
            'B': {'name': 'B-人际困扰', 'keywords': ['人际关系', '与人冲突', '被孤立', '朋友矛盾'], 'layer': '轻度危机'},
            'A': {'name': 'A-事理不平', 'keywords': ['不公平', '凭什么', '为什么是我', '不应该这样', '太不公'], 'layer': '轻度危机'},
        }

        # 遍历文本，匹配所有可能的等级
        for level_code, level_data in crisis_levels.items():
            for keyword in level_data['keywords']:
                if keyword in text:
                    matched_levels.append({
                        'code': level_code,
                        'name': level_data['name'],
                        'layer': level_data['layer'],
                        'keyword': keyword
                    })

        # 大观学派原则：取最后落脚点（最严重的等级）
        if not matched_levels:
            return {
                'level': None,
                'name': '未评估',
                'layer': '无危机',
                'evidence': [],
                'all_matched': []
            }

        # 按危机严重程度排序（Z最严重，A最轻）
        level_order = ['Z', 'Y', 'X', 'W2', 'W1', 'V2', 'V1', 'U', 'T', 'S3', 'S2', 'S1',
                      'R2', 'R1', 'Q2', 'Q1', 'P', 'O', 'N', 'M', 'L', 'K',
                      'J', 'I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']

        # 找到最严重的等级
        most_severe = None
        for code in level_order:
            for match in matched_levels:
                if match['code'] == code:
                    most_severe = match
                    break
            if most_severe:
                break

        # 收集证据（去重）
        evidence = list(set([m['keyword'] for m in matched_levels]))

        return {
            'level': most_severe['code'],
            'name': most_severe['name'],
            'layer': most_severe['layer'],
            'evidence': evidence,
            'all_matched': list(set([f"{m['code']}-{m['name']}" for m in matched_levels]))
        }

    def _identify_tags_and_keywords(self, text):
        """识别标签和关键词"""
        tags = {'relation': [], 'symptom': []}
        keywords = []

        # 关系标签关键词映射
        relation_map = {
            "母亲": "家庭关系-亲子关系-情感忽视",
            "父亲": "家庭关系-亲子关系-父母缺位",
            "父母": "家庭关系-亲子关系-父母控制",
            "照顾": "家庭关系-亲子关系-角色倒置",
            "夫妻": "家庭关系-夫妻关系-沟通障碍",
            "恋爱": "社交关系-恋爱关系-恋爱焦虑",
            "同事": "工作关系-职场压力-人际冲突",
            "失业": "工作关系-职场压力-失业危机",
        }

        # 症状标签关键词映射
        symptom_map = {
            "自杀": "行为问题-自杀风险-自杀意念",
            "弑母": "行为问题-自杀风险-自杀意念",
            "遗书": "行为问题-自杀风险-自杀计划",
            "焦虑": "情绪障碍-焦虑症状-广泛性焦虑",
            "压力": "情绪障碍-焦虑症状-广泛性焦虑",
            "抑郁": "情绪障碍-抑郁症状-情绪低落",
            "失眠": "躯体症状-睡眠问题-入睡困难",
            "照顾疲劳": "情绪障碍-焦虑症状-广泛性焦虑",
        }

        keyword_count = {}

        # 匹配关系标签
        for kw, tag in relation_map.items():
            if kw in text:
                count = text.count(kw)
                keyword_count[kw] = count
                if tag not in tags['relation']:
                    tags['relation'].append(tag)

        # 匹配症状标签
        for kw, tag in symptom_map.items():
            if kw in text:
                count = text.count(kw)
                keyword_count[kw] = count
                if tag not in tags['symptom']:
                    tags['symptom'].append(tag)

        # 提取高频关键词
        sorted_kw = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)
        keywords = [kw for kw, _ in sorted_kw[:5]]

        return tags, keywords

    def _detect_six_changes_three_entrustments(self, text):
        """识别六变三托征兆"""
        signals = {
            '六变': [],
            '三托': []
        }

        # 六变检测
        six_changes = {
            '性情大变': ['性情大变', '变得沉默', '变得话多', '性格突变', '内向变外向', '外向变内向'],
            '行为大变': ['行为异常', '不按规律', '作息混乱', '突然不上班', '突然不上学'],
            '财务大变': ['突然还债', '突然借钱', '处理财务', '把钱送人', '清理财产'],
            '语言大变': ['谈论死亡', '书写遗言', '说要离开', '告别的话'],
            '身体大变': ['突然消瘦', '突然发胖', '外表大变', '不修边幅'],
            '环境大变': ['突然搬家', '突然转学', '突然辞职', '换工作', '离开熟悉环境']
        }

        for change_type, keywords in six_changes.items():
            for keyword in keywords:
                if keyword in text:
                    signals['六变'].append(change_type)
                    break

        # 三托检测
        three_entrustments = {
            '托人': ['照顾家人', '拜托你', '帮我照顾', '请照看'],
            '托事': ['帮我完成', '代为执行', '帮我处理', '交代后事'],
            '托物': ['帮我保管', '照顾宠物', '保留物品', '打包东西']
        }

        for entrustment_type, keywords in three_entrustments.items():
            for keyword in keywords:
                if keyword in text:
                    signals['三托'].append(entrustment_type)
                    break

        return signals


    def _analyze_complaint_with_ai(self, complaint, full_text):
        """使用AI分析主诉，提炼核心诉求"""
        try:
            # 构建分析提示词
            prompt = f"""你是一位资深心理咨询师，请分析以下来访者的主诉，提炼核心诉求。

【来访者主诉原文】
{complaint}

【完整咨询记录】
{full_text[:1000]}

请按以下格式输出分析结果（JSON格式）：
{{
  "core_issue": "核心问题（一句话概括，20字以内）",
  "emotional_state": "情绪状态（如：焦虑、抑郁、愤怒、绝望等）",
  "help_seeking_motivation": "求助动机（为什么来咨询）",
  "key_conflicts": ["关键冲突1", "关键冲突2"],
  "summarized_complaint": "提炼后的主诉（简洁版，50-100字）"
}}

注意：
1. core_issue要高度凝练，直击问题核心
2. summarized_complaint要保留关键信息，去除冗余描述
3. 必须返回有效的JSON格式"""

            # 调用CatKingAI API - 使用GPT-5.5分析主诉，添加重试机制
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        f'{self.api_base}/chat/completions',
                        headers={
                            'Authorization': f'Bearer {self.api_key}',
                            'Content-Type': 'application/json'
                        },
                        json={
                            'model': 'gpt-5.5',
                            'messages': [
                                {'role': 'user', 'content': prompt}
                            ],
                            'temperature': 0.3,
                            'max_tokens': 1000
                        },
                        timeout=15
                    )

                    if response.status_code == 200:
                        result = response.json()
                        content = result['choices'][0]['message']['content']

                        # 提取JSON内容（处理可能的markdown代码块包裹）
                        if '```json' in content:
                            content = content.split('```json')[1].split('```')[0].strip()
                        elif '```' in content:
                            content = content.split('```')[1].split('```')[0].strip()

                        analysis = json.loads(content)
                        print(f"[AI分析] 主诉分析完成: {analysis.get('core_issue', '未知')}")
                        return analysis
                    else:
                        print(f"[AI分析] API调用失败: {response.status_code}, 尝试 {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            time.sleep(1)  # 重试前等待1秒
                        continue
                except requests.exceptions.RequestException as e:
                    print(f"[AI分析] 网络错误: {str(e)}, 尝试 {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                    continue

            # AI分析失败，使用规则提炼
            print(f"[AI分析] API调用失败，使用规则提炼主诉")
            return self._fallback_analyze_complaint(complaint, full_text)

        except Exception as e:
            print(f"[AI分析] 分析失败: {str(e)}")
            return self._fallback_analyze_complaint(complaint, full_text)

    def _fallback_analyze_complaint(self, complaint, full_text):
        """降级方案：使用规则提炼主诉核心思想"""
        try:
            # 提取关键信息
            text_to_analyze = complaint + '\n' + full_text[:500]

            # 1. 提取年龄、性别、职业等基本信息
            age_match = re.search(r'(\d+)\s*岁', text_to_analyze)
            age = age_match.group(1) if age_match else ''

            gender_match = re.search(r'(男|女)生', text_to_analyze)
            gender = gender_match.group(1) if gender_match else ''

            # 2. 提取核心问题关键词
            core_issues = []
            issue_patterns = {
                '照顾压力': ['照顾', '护理', '照看'],
                '情感困境': ['想.*母', '弑', '杀', '恨'],
                '经济困难': ['失业', '收入', '经济', '钱', '负担不起'],
                '身体疾病': ['疾病', '生病', '失禁', '卧床', '老年痴呆'],
                '精神压力': ['压力', '撑不住', '无助', '绝望', '崩溃'],
                '人际冲突': ['冲突', '矛盾', '争吵', '关系'],
                '情绪问题': ['焦虑', '抑郁', '愤怒', '恐惧', '害怕']
            }

            for issue, keywords in issue_patterns.items():
                if any(kw in text_to_analyze for kw in keywords):
                    core_issues.append(issue)

            # 3. 提取情绪关键词
            emotions = []
            emotion_keywords = {
                '焦虑': ['焦虑', '担心', '害怕', '恐惧', '紧张'],
                '抑郁': ['抑郁', '难过', '悲伤', '痛苦', '绝望'],
                '愤怒': ['愤怒', '生气', '恼火', '暴躁', '恨'],
                '无助': ['无助', '无力', '迷茫', '不知所措', '撑不住', '蒙了']
            }

            for emotion, keywords in emotion_keywords.items():
                if any(kw in text_to_analyze for kw in keywords):
                    emotions.append(emotion)

            # 4. 生成核心诉求摘要
            summary_parts = []
            if age and gender:
                summary_parts.append(f'{age}岁{gender}性')

            # 提取主要困境（取前两个核心问题）
            if core_issues:
                summary_parts.append('面临' + '与'.join(core_issues[:2]))

            # 构建简洁主诉
            if summary_parts:
                core_summary = '、'.join(summary_parts) + '的困境'
            else:
                core_summary = '寻求心理支持'

            # 提取最关键的一句话（包含"想"、"不知道"、"怎么办"等求助性语句）
            key_sentences = []
            sentences = re.split(r'[。！？]', text_to_analyze)
            for sent in sentences:
                if any(kw in sent for kw in ['想', '不知道', '怎么办', '该', '问', '求助']):
                    if len(sent) > 10 and len(sent) < 100:
                        key_sentences.append(sent.strip())

            if key_sentences:
                summarized = core_summary + '。' + key_sentences[0]
            else:
                summarized = core_summary

            return {
                'core_issue': core_summary,
                'emotional_state': '、'.join(emotions) if emotions else '情绪困扰',
                'help_seeking_motivation': '寻求专业心理支持和指导',
                'key_conflicts': core_issues[:3],
                'summarized_complaint': summarized[:150]  # 限制150字
            }
        except Exception as e:
            print(f"[降级分析] 失败: {e}")
            # 最终降级：返回简短摘要
            return {
                'core_issue': '心理困扰求助',
                'emotional_state': '情绪压力',
                'help_seeking_motivation': '寻求帮助',
                'key_conflicts': [],
                'summarized_complaint': complaint[:80] if complaint else '待补充'
            }


# 测试代码
if __name__ == '__main__':
    parser = IntakeRecordParser('data/config/tags_library.json')
    result = parser.parse('real_case.docx')

    print(json.dumps(result, ensure_ascii=False, indent=2))
