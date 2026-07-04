#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流派配置管理服务器
提供HTTP API用于读取和保存流派配置
"""

import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import glob
from word_parser import IntakeRecordParser

# Windows UTF-8 输出支持
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPROACHES_DIR = os.path.join(PROJECT_ROOT, 'data', 'config', 'approaches')
TAGS_LIBRARY_FILE = os.path.join(PROJECT_ROOT, 'data', 'config', 'tags_library.json')


class ConfigHandler(BaseHTTPRequestHandler):
    """配置API处理器"""

    def _set_cors_headers(self):
        """设置CORS头，允许跨域"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """处理GET请求 - 读取所有流派配置"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/api/tags-library':
            try:
                # 读取标签库
                with open(TAGS_LIBRARY_FILE, 'r', encoding='utf-8') as f:
                    tags_library = json.load(f)

                self.send_response(200)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()

                response = json.dumps(tags_library, ensure_ascii=False, indent=2)
                self.wfile.write(response.encode('utf-8'))

                print(f"[GET] 成功返回标签库")

            except Exception as e:
                self.send_response(500)
                self._set_cors_headers()
                self.end_headers()
                error_msg = f"读取标签库失败: {str(e)}"
                self.wfile.write(error_msg.encode('utf-8'))
                print(f"[ERROR] {error_msg}")

        elif parsed_path.path == '/api/approaches':
            try:
                approaches = self._load_all_approaches()

                self.send_response(200)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()

                response = json.dumps(approaches, ensure_ascii=False, indent=2)
                self.wfile.write(response.encode('utf-8'))

                print(f"[GET] 成功返回 {len(approaches)} 个流派配置")

            except Exception as e:
                self.send_response(500)
                self._set_cors_headers()
                self.end_headers()
                error_msg = f"读取配置失败: {str(e)}"
                self.wfile.write(error_msg.encode('utf-8'))
                print(f"[ERROR] {error_msg}")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """处理POST请求 - 保存所有流派配置"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/api/word/parse':
            self._handle_word_parse()
        elif parsed_path.path == '/api/approaches':
            try:
                # 读取请求体
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                approaches = json.loads(post_data.decode('utf-8'))

                print(f"[POST] 收到 {len(approaches)} 个流派配置")

                # 验证数据
                if not isinstance(approaches, list):
                    raise ValueError("配置数据必须是数组")

                for approach in approaches:
                    if 'id' not in approach or 'name' not in approach:
                        raise ValueError("每个流派必须包含id和name字段")

                # 保存配置
                self._save_all_approaches(approaches)

                # 自动重新生成来访者库
                print("[AUTO] 自动重新生成来访者库...")
                self._regenerate_visitor_library()

                self.send_response(200)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()

                response = json.dumps({"success": True, "message": "保存成功并已更新来访者库"}, ensure_ascii=False)
                self.wfile.write(response.encode('utf-8'))

                print(f"[POST] 成功保存 {len(approaches)} 个流派配置")

            except Exception as e:
                self.send_response(500)
                self._set_cors_headers()
                self.end_headers()
                error_msg = f"保存配置失败: {str(e)}"
                self.wfile.write(error_msg.encode('utf-8'))
                print(f"[ERROR] {error_msg}")
        else:
            self.send_response(404)
            self.end_headers()

    def _load_all_approaches(self):
        """加载所有流派配置"""
        approaches = []

        # 确保目录存在
        if not os.path.exists(APPROACHES_DIR):
            os.makedirs(APPROACHES_DIR, exist_ok=True)
            return approaches

        # 读取所有JSON文件
        json_files = glob.glob(os.path.join(APPROACHES_DIR, '*.json'))

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    approach = json.load(f)
                    approaches.append(approach)
            except Exception as e:
                print(f"[WARN] 无法读取配置文件 {json_file}: {e}")

        # 按 sort_order 排序
        approaches.sort(key=lambda x: x.get('sort_order', 999))

        return approaches

    def _save_all_approaches(self, approaches):
        """保存所有流派配置 - 合并保留原有字段"""
        # 确保目录存在
        os.makedirs(APPROACHES_DIR, exist_ok=True)

        # 先加载所有现有配置，保留原有字段
        existing_configs = {}
        for json_file in glob.glob(os.path.join(APPROACHES_DIR, '*.json')):
            approach_id = os.path.splitext(os.path.basename(json_file))[0]
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    existing_configs[approach_id] = json.load(f)
            except Exception as e:
                print(f"  [WARN] 无法读取现有配置 {json_file}: {e}")

        # 获取现有文件列表
        existing_files = set(os.path.basename(f) for f in glob.glob(os.path.join(APPROACHES_DIR, '*.json')))
        new_files = set()

        # 保存每个流派配置
        for approach in approaches:
            approach_id = approach['id']
            filename = f"{approach_id}.json"
            filepath = os.path.join(APPROACHES_DIR, filename)

            new_files.add(filename)

            # 如果是已存在的配置，合并保留原有字段
            if approach_id in existing_configs:
                # 用原有配置作为基础
                merged_config = existing_configs[approach_id].copy()
                # 更新界面传来的字段
                merged_config.update(approach)
                final_config = merged_config
            else:
                # 新配置直接使用
                final_config = approach

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(final_config, f, ensure_ascii=False, indent=2)

            print(f"  ✓ 保存配置: {filename}")

        # 删除不再存在的配置文件
        deleted_files = existing_files - new_files
        for filename in deleted_files:
            filepath = os.path.join(APPROACHES_DIR, filename)
            os.remove(filepath)
            print(f"  ✗ 删除配置: {filename}")

    def _handle_word_parse(self):
        """处理Word文档解析请求 - 使用新的解析器"""
        try:
            import tempfile
            from docx import Document

            # 解析multipart/form-data
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self.send_error(400, 'Content-Type must be multipart/form-data')
                return

            # 获取boundary
            boundary = content_type.split('boundary=')[1].encode()
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # 提取文件数据
            parts = post_data.split(b'--' + boundary)
            file_data = None

            for part in parts:
                if b'Content-Disposition' in part and b'filename=' in part:
                    file_start = part.find(b'\r\n\r\n') + 4
                    file_end = len(part) - 2
                    file_data = part[file_start:file_end]
                    break

            if not file_data:
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(b'{"error": "No file data found"}')
                return

            # 保存为临时文件并解析
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
                tmp_file.write(file_data)
                tmp_path = tmp_file.name

            try:
                # 使用新的解析器
                parser = IntakeRecordParser(TAGS_LIBRARY_FILE)
                parsed_data = parser.parse(tmp_path)

                self.send_response(200)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()

                response = json.dumps(parsed_data, ensure_ascii=False, indent=2)
                self.wfile.write(response.encode('utf-8'))

                print(f"[POST] Word文档解析成功")

            finally:
                os.unlink(tmp_path)

        except Exception as e:
            import traceback
            print(f"[ERROR] Word解析失败: {e}")
            traceback.print_exc()

            self.send_response(500)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()

            error_response = json.dumps({"error": str(e)}, ensure_ascii=False)
            self.wfile.write(error_response.encode('utf-8'))

    def _parse_word_document(self, doc):
        """解析Word文档内容 - 智能识别多种格式"""
        result = {
            "basic_info": {},
            "session_info": {},
            "家庭结构": {},
            "既往史": {},
            "tags": {
                "relation": [],
                "symptom": []
            },
            "keywords": []
        }

        # 收集所有文本用于分析
        full_text = ""
        paragraphs = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                full_text += text + "\n"
                paragraphs.append(text)

        # 方法1：尝试结构化解析（标题+冒号格式）
        self._parse_structured_format(paragraphs, result)

        # 方法2：智能提取关键信息（适用于叙事性文本）
        if not result['basic_info'].get('代号') and len(full_text) > 100:
            self._parse_narrative_format(full_text, paragraphs, result)

        # 提取主诉和咨询过程
        if not result.get('主诉'):
            # 从文本中智能提取主诉
            result['主诉'] = self._extract_main_complaint(full_text, paragraphs)

        if not result.get('dialogue'):
            # 提取咨询对话（取主要内容）
            result['dialogue'] = full_text[:1000] if len(full_text) > 100 else full_text

        # AI标签识别
        try:
            tags_and_keywords = self._analyze_tags_with_ai(full_text)
            result['tags'] = tags_and_keywords.get('tags', {"relation": [], "symptom": []})
            result['keywords'] = tags_and_keywords.get('keywords', [])
            result['crisis_level'] = tags_and_keywords.get('crisis_level')
        except Exception as e:
            print(f"[WARN] AI标签识别失败: {e}")
            tags, keywords, crisis_level = self._analyze_tags_with_keywords(full_text)
            result['tags'] = tags
            result['keywords'] = keywords
            result['crisis_level'] = crisis_level

        return result

    def _parse_structured_format(self, paragraphs, result):
        """解析结构化格式（标题：内容）"""
        current_section = None

        for text in paragraphs:
            # 识别标题段落
            if '：' in text or ':' in text:
                # 基本信息字段
                if '案例代号' in text or '代号' in text:
                    value = text.split('：')[-1].split(':')[-1].strip()
                    result['basic_info']['代号'] = value
                elif '性别' in text and len(text) < 20:
                    value = text.split('：')[-1].split(':')[-1].strip()
                    result['basic_info']['性别'] = value
                elif '年龄' in text and len(text) < 20:
                    value = text.split('：')[-1].split(':')[-1].strip()
                    result['basic_info']['年龄'] = value
                elif '职业' in text and len(text) < 30:
                    value = text.split('：')[-1].split(':')[-1].strip()
                    result['basic_info']['职业'] = value
                elif '婚姻' in text and len(text) < 20:
                    value = text.split('：')[-1].split(':')[-1].strip()
                    result['basic_info']['婚姻状况'] = value
                elif '主诉' in text:
                    current_section = '主诉'
                    if '：' in text or ':' in text:
                        value = text.split('：')[-1].split(':')[-1].strip()
                        if value:
                            result['主诉'] = value
                elif '对话' in text or '咨询记录' in text or '时间' in text:
                    current_section = 'dialogue'
                elif '反思' in text or '复盘' in text:
                    current_section = 'counselor_reflection'
            else:
                # 内容段落
                if current_section == '主诉' and not result.get('主诉'):
                    result['主诉'] = text
                    current_section = None
                elif current_section == 'dialogue':
                    if 'dialogue' not in result:
                        result['dialogue'] = text
                    else:
                        result['dialogue'] += '\n' + text
                elif current_section == 'counselor_reflection':
                    if 'counselor_reflection' not in result:
                        result['counselor_reflection'] = text
                    else:
                        result['counselor_reflection'] += '\n' + text

    def _parse_narrative_format(self, full_text, paragraphs, result):
        """解析叙事性格式（从连续文本中提取信息）"""
        import re

        # 提取标题（通常在第一行或第二行）
        if len(paragraphs) > 0:
            title = paragraphs[0]
            result['basic_info']['代号'] = title[:50]  # 使用标题作为代号

        # 提取时间信息
        time_pattern = r'(\d{1,2}[:：]\d{2}[-–—]\d{1,2}[:：]\d{2})'
        time_match = re.search(time_pattern, full_text)
        if time_match:
            result['session_info']['时间'] = time_match.group(1)

        # 提取年龄和性别
        # 匹配：男生：28岁、28岁男、女，28岁等
        age_gender_patterns = [
            r'[男女]生[：:]\s*(\d{1,2})\s*岁',
            r'(\d{1,2})\s*岁.*?([男女])',
            r'([男女]).*?(\d{1,2})\s*岁',
        ]

        for pattern in age_gender_patterns:
            match = re.search(pattern, full_text)
            if match:
                groups = match.groups()
                for g in groups:
                    if g in ['男', '女']:
                        result['basic_info']['性别'] = g
                    elif g.isdigit():
                        result['basic_info']['年龄'] = g
                if result['basic_info'].get('性别') and result['basic_info'].get('年龄'):
                    break

    def _extract_main_complaint(self, full_text, paragraphs):
        """智能提取主诉"""
        # 查找包含关键词的句子
        complaint_keywords = ['主诉', '问题', '困扰', '症状', '求助', '压力', '焦虑', '抑郁', '失眠']

        # 方法1：找第一段包含关键词的段落
        for para in paragraphs[1:6]:  # 搜索前5段
            if any(kw in para for kw in complaint_keywords):
                # 取这一段作为主诉（限制长度）
                return para[:200]

        # 方法2：使用第二或第三段（通常是主要内容）
        if len(paragraphs) > 1:
            return paragraphs[1][:200]

        return ""

    def _analyze_tags_with_keywords(self, text):
        """使用关键词匹配识别标签（后备方案）"""
        tags = {"relation": [], "symptom": []}
        keywords = []

        # 危机等级评估
        crisis_level = None
        crisis_keywords = {
            'S': ['自杀', '遗书', '计划', '手段', '失联', '轻生'],
            'L': ['他杀', '弑母', '弑父', '杀人', '自伤', '幻听', '幻觉', '精神病'],
            'M': ['中度', '功能受损', '创伤', '急性期', '焦虑', '抑郁', '压力大'],
            'C': ['慢性', '关系问题', '成长议题', '长期'],
            'Z': ['正常', '偶发', '一般性']
        }

        # 从高到低检查危机等级
        for level in ['S', 'L', 'M', 'C', 'Z']:
            for keyword in crisis_keywords[level]:
                if keyword in text:
                    crisis_level = level
                    break
            if crisis_level:
                break

        # 扩展的关键词匹配规则（使用标签库格式）
        relation_keywords = {
            "母亲": "家庭关系-亲子关系-父母缺位",
            "父母": "家庭关系-亲子关系-父母控制",
            "父亲": "家庭关系-亲子关系-父母缺位",
            "妈妈": "家庭关系-亲子关系-情感忽视",
            "爸爸": "家庭关系-亲子关系-父母缺位",
            "儿子": "家庭关系-亲子关系-父母控制",
            "女儿": "家庭关系-亲子关系-父母控制",
            "孩子": "家庭关系-亲子关系-父母控制",
            "朋友": "社交关系-友谊-友谊破裂",
            "同学": "社交关系-同伴关系-融入困难",
            "夫妻": "家庭关系-夫妻关系-沟通障碍",
            "配偶": "家庭关系-夫妻关系-沟通障碍",
            "恋爱": "社交关系-恋爱关系-恋爱焦虑",
            "男友": "社交关系-恋爱关系-失恋分手",
            "女友": "社交关系-恋爱关系-失恋分手",
            "同事": "工作关系-职场压力-人际冲突",
            "上级": "工作关系-职场压力-工作压力",
            "领导": "工作关系-职场压力-工作压力",
            "老板": "工作关系-职场压力-工作压力",
            "照顾": "家庭关系-亲子关系-情感忽视",
        }

        symptom_keywords = {
            "自杀": "行为问题-自杀风险-自杀意念",
            "轻生": "行为问题-自杀风险-自杀意念",
            "遗书": "行为问题-自杀风险-自杀计划",
            "弑母": "行为问题-自杀风险-自杀意念",
            "弑父": "行为问题-自杀风险-自杀意念",
            "焦虑": "情绪障碍-焦虑症状-广泛性焦虑",
            "担心": "情绪障碍-焦虑症状-广泛性焦虑",
            "紧张": "情绪障碍-焦虑症状-惊恐发作",
            "抑郁": "情绪障碍-抑郁症状-情绪低落",
            "情绪低落": "情绪障碍-抑郁症状-情绪低落",
            "失眠": "躯体症状-睡眠问题-入睡困难",
            "睡不着": "躯体症状-睡眠问题-入睡困难",
            "早醒": "躯体症状-睡眠问题-早醒",
            "强迫": "情绪障碍-强迫症状-强迫思维",
            "恐惧": "情绪障碍-恐惧症状-特定恐惧",
            "害怕": "情绪障碍-恐惧症状-特定恐惧",
            "哭": "情绪障碍-情绪调节-情绪失控",
            "哭泣": "情绪障碍-情绪调节-情绪失控",
            "压力": "情绪障碍-焦虑症状-广泛性焦虑",
            "完美主义": "人格特质-完美主义",
            "照顾": "情绪障碍-焦虑症状-广泛性焦虑",
            "失业": "工作关系-职场压力-工作压力",
        }

        # 统计关键词出现次数
        keyword_count = {}

        for keyword, tag in relation_keywords.items():
            if keyword in text:
                count = text.count(keyword)
                if tag not in tags["relation"]:
                    tags["relation"].append(tag)
                keyword_count[keyword] = count

        for keyword, tag in symptom_keywords.items():
            if keyword in text:
                count = text.count(keyword)
                if tag not in tags["symptom"]:
                    tags["symptom"].append(tag)
                keyword_count[keyword] = count

        # 提取出现次数最多的关键词
        sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)
        keywords = [kw for kw, count in sorted_keywords[:5]]

        return tags, keywords, crisis_level

    def _analyze_tags_with_ai(self, text):
        """使用AI分析文本生成标签和关键词"""
        import anthropic
        import os

        # 检查是否有API密钥
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise Exception("未设置ANTHROPIC_API_KEY环境变量")

        # 读取标签库
        with open(TAGS_LIBRARY_FILE, 'r', encoding='utf-8') as f:
            tags_library = json.load(f)

        # 构建标签选项
        relation_tags = []
        symptom_tags = []

        for category in tags_library.get('categories', []):
            if category['id'] == 'relation':
                for subcategory in category.get('subcategories', []):
                    for tag in subcategory.get('tags', []):
                        relation_tags.append(f"{subcategory['name']}-{tag['name']}")
            elif category['id'] == 'symptom':
                for subcategory in category.get('subcategories', []):
                    for tag in subcategory.get('tags', []):
                        symptom_tags.append(f"{subcategory['name']}-{tag['name']}")

        prompt = f"""分析以下心理咨询案例文本，识别关键标签和关键词。

案例文本：
{text[:2000]}

请从以下标签库中选择最相关的标签（最多各选5个）：

关系标签：
{', '.join(relation_tags[:30])}

症状标签：
{', '.join(symptom_tags[:30])}

同时提取3-5个关键词概括案例核心问题。

请以JSON格式返回：
{{
    "tags": {{
        "relation": ["标签1", "标签2"],
        "symptom": ["标签1", "标签2"]
    }},
    "keywords": ["关键词1", "关键词2", "关键词3"]
}}"""

        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            # 提取JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise Exception("AI响应格式错误")

        except Exception as e:
            print(f"[ERROR] AI分析失败: {e}")
            raise

    def _regenerate_visitor_library(self):
        """重新生成来访者库（来访者为中心）"""
        import subprocess
        import traceback

        try:
            # 1. 重新生成所有来访者详情页
            print("[AUTO] 正在重新生成来访者详情页...")
            print(f"[AUTO] Python: {sys.executable}")
            print(f"[AUTO] 工作目录: {PROJECT_ROOT}")

            detail_script = os.path.join(PROJECT_ROOT, 'src', 'generate_visit_details.py')
            print(f"[AUTO] 脚本路径: {detail_script}")

            if not os.path.exists(detail_script):
                print(f"[AUTO] ✗ 脚本文件不存在: {detail_script}")
                return

            # Windows环境subprocess配置
            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                [sys.executable, detail_script],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60,  # 60秒超时
                creationflags=creation_flags
            )

            if result.returncode == 0:
                print("[AUTO] ✓ 来访者详情页重新生成成功")
                if result.stdout:
                    print("[AUTO] 输出:")
                    for line in result.stdout.strip().split('\n')[-10:]:  # 显示最后10行
                        print(f"       {line}")
            else:
                print(f"[AUTO] ✗ 详情页生成失败 (返回码: {result.returncode})")
                if result.stderr:
                    print(f"[AUTO] 错误输出:")
                    for line in result.stderr.strip().split('\n'):
                        print(f"       {line}")
                if result.stdout:
                    print(f"[AUTO] 标准输出:")
                    for line in result.stdout.strip().split('\n'):
                        print(f"       {line}")

            # 2. 重新生成来访者库首页
            print("[AUTO] 正在重新生成来访者库首页...")
            visitor_script = os.path.join(PROJECT_ROOT, 'src', 'generate_visitor_library.py')

            if not os.path.exists(visitor_script):
                print(f"[AUTO] ✗ 脚本文件不存在: {visitor_script}")
                return

            result = subprocess.run(
                [sys.executable, visitor_script],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60,
                creationflags=creation_flags
            )

            if result.returncode == 0:
                print("[AUTO] ✓ 来访者库首页重新生成成功")
                if result.stdout:
                    print("[AUTO] 输出:")
                    for line in result.stdout.strip().split('\n')[-5:]:
                        print(f"       {line}")
            else:
                print(f"[AUTO] ✗ 来访者库首页生成失败 (返回码: {result.returncode})")
                if result.stderr:
                    print(f"[AUTO] 错误输出:")
                    for line in result.stderr.strip().split('\n'):
                        print(f"       {line}")

        except subprocess.TimeoutExpired as e:
            print(f"[AUTO] ✗ 生成超时 (60秒): {e}")
        except Exception as e:
            print(f"[AUTO] ✗ 无法执行来访者库生成: {e}")
            print(f"[AUTO] 详细错误:")
            traceback.print_exc()

    def log_message(self, format, *args):
        """禁用默认的访问日志"""
        pass


def main():
    """启动配置服务器"""
    port = 8003

    print("=" * 70)
    print("  流派配置管理服务器")
    print("=" * 70)
    print(f"配置目录: {APPROACHES_DIR}")
    print(f"监听端口: {port}")
    print(f"管理界面: http://localhost:{port}/../config-approaches.html")
    print()
    print("按 Ctrl+C 停止服务器")
    print("=" * 70)

    server = HTTPServer(('localhost', port), ConfigHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] 服务器已停止")
        server.shutdown()


if __name__ == '__main__':
    main()
