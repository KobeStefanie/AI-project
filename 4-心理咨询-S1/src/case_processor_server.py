#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单案例处理服务器
提供Web界面的案例处理工作流：上传Word → AI分析 → 人工核实 → 上传材料 → 保存
"""

import sys
import os
import json
import shutil
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime
from pathlib import Path
import tempfile

# Windows UTF-8 输出支持
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from docx import Document
except ImportError:
    print("[ERR] 缺少依赖：python-docx")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("[ERR] 缺少依赖：requests")
    sys.exit(1)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CASES_ORIGINAL = DATA_DIR / "cases" / "original"
CASES_PROCESSED = DATA_DIR / "cases" / "processed"
INDEX_DIR = DATA_DIR / "index"
CONFIG_DIR = DATA_DIR / "config"
TAGS_LIBRARY_FILE = CONFIG_DIR / "tags_library.json"

# CatKingAI API 配置
CATKINGAI_ENDPOINT = "https://catkingai.com/v1/messages"
CATKINGAI_API_KEY = os.getenv("CATKINGAI_API_KEY", "")

# 确保目录存在
for dir_path in [CASES_ORIGINAL, CASES_PROCESSED, INDEX_DIR, CONFIG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


def read_word_document(file_path: str) -> str:
    """读取 Word 文档内容"""
    try:
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                full_text.append(text)
        return "\n".join(full_text)
    except Exception as e:
        raise Exception(f"读取 Word 文档失败：{e}")


def generate_case_id() -> str:
    """生成案例编号：C + YYYYMMDD + 3位序号"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"C{today}"

    existing_cases = list(CASES_PROCESSED.glob(f"{prefix}*"))

    if not existing_cases:
        return f"{prefix}001"

    max_seq = 0
    for case_dir in existing_cases:
        case_id = case_dir.name
        try:
            seq = int(case_id[-3:])
            max_seq = max(max_seq, seq)
        except ValueError:
            continue

    new_seq = max_seq + 1
    return f"{prefix}{new_seq:03d}"


def call_ai_analysis(content: str) -> dict:
    """调用 AI 进行案例分析"""
    prompt = f"""你是一位资深的心理咨询督导师，擅长大观学派希望热线技术。请分析以下接访记录：

【案例内容】
{content}

【分析要求】
请从以下维度进行分析，并以 JSON 格式返回：

1. **关系标签**（relation_tags）：识别涉及的关系类型
2. **精神症状标签**（symptom_tags）：识别精神症状
3. **危机等级**（crisis_level）：S/L/M/C/Z
4. **危机判据**（crisis_evidence）：判断依据
5. **关键词**（keywords）：提取5-10个核心关键词
6. **使用的技术**（techniques_used）：
7. **案例摘要**（summary）：200字以内
8. **咨询师优势**（strengths）：3-5条
9. **改进建议**（improvements）：3-5条
10. **下次咨询建议**（recommended_followup）

严格按照 JSON 格式输出，不要有其他文字。"""

    if not CATKINGAI_API_KEY:
        return {
            "relation_tags": [],
            "symptom_tags": [],
            "crisis_level": "C",
            "crisis_evidence": "需要 AI 实际分析",
            "keywords": [],
            "techniques_used": [],
            "summary": "需要 AI 实际分析",
            "strengths": ["需要 AI 实际分析"],
            "improvements": ["需要 AI 实际分析"],
            "recommended_followup": "需要 AI 实际分析"
        }

    try:
        response = requests.post(
            CATKINGAI_ENDPOINT,
            headers={
                "Authorization": f"Bearer {CATKINGAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-opus-4-8",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4000
            },
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group())
        return None
    except Exception as e:
        print(f"[ERR] AI 分析出错：{e}")
        return None


def load_tags_library() -> dict:
    """加载统一标签库"""
    try:
        if not TAGS_LIBRARY_FILE.exists():
            return {"relation_tags": {}, "symptom_tags": {}}

        with open(TAGS_LIBRARY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERR] 加载标签库失败：{e}")
        return {"relation_tags": {}, "symptom_tags": {}}


def update_index(case_id: str, case_data: dict):
    """更新四大索引"""
    # 1. 关系标签索引
    relation_file = INDEX_DIR / "relation_tags.json"
    relation_index = json.loads(relation_file.read_text(encoding='utf-8')) if relation_file.exists() else {}
    for tag in case_data["tags"]["relation"]:
        relation_index.setdefault(tag, [])
        if case_id not in relation_index[tag]:
            relation_index[tag].append(case_id)
    relation_file.write_text(json.dumps(relation_index, ensure_ascii=False, indent=2), encoding='utf-8')

    # 2. 精神症状标签索引
    symptom_file = INDEX_DIR / "symptom_tags.json"
    symptom_index = json.loads(symptom_file.read_text(encoding='utf-8')) if symptom_file.exists() else {}
    for tag in case_data["tags"]["symptom"]:
        symptom_index.setdefault(tag, [])
        if case_id not in symptom_index[tag]:
            symptom_index[tag].append(case_id)
    symptom_file.write_text(json.dumps(symptom_index, ensure_ascii=False, indent=2), encoding='utf-8')

    # 3. 危机等级索引
    crisis_file = INDEX_DIR / "crisis_levels.json"
    crisis_index = json.loads(crisis_file.read_text(encoding='utf-8')) if crisis_file.exists() else {}
    level = case_data["crisis_level"]
    if level:
        crisis_index.setdefault(level, [])
        if case_id not in crisis_index[level]:
            crisis_index[level].append(case_id)
    crisis_file.write_text(json.dumps(crisis_index, ensure_ascii=False, indent=2), encoding='utf-8')

    # 4. 关键词索引
    keyword_file = INDEX_DIR / "keywords.json"
    keyword_index = json.loads(keyword_file.read_text(encoding='utf-8')) if keyword_file.exists() else {}
    for kw in case_data["keywords"]:
        keyword_index.setdefault(kw, [])
        if case_id not in keyword_index[kw]:
            keyword_index[kw].append(case_id)
    keyword_file.write_text(json.dumps(keyword_index, ensure_ascii=False, indent=2), encoding='utf-8')


class CaseProcessorHandler(BaseHTTPRequestHandler):
    """案例处理API处理器"""

    def _set_cors_headers(self):
        """设置CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # 1. 上传Word文档并分析
        if path == '/api/upload-word':
            self._handle_upload_word()

        # 2. 保存案例（包含所有材料）
        elif path == '/api/save-case':
            self._handle_save_case()

        else:
            self._send_error(404, "接口不存在")

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # 获取标签库
        if path == '/api/tags-library':
            self._handle_get_tags_library()
        else:
            self._send_error(404, "接口不存在")

    def _handle_upload_word(self):
        """处理Word文档上传和分析"""
        try:
            content_type = self.headers.get('Content-Type', '')

            if 'multipart/form-data' not in content_type:
                self._send_error(400, "需要 multipart/form-data")
                return

            # 解析 multipart
            boundary = content_type.split('boundary=')[1].encode()
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)

            # 提取文件数据
            parts = body.split(b'--' + boundary)
            file_data = None
            filename = None

            for part in parts:
                if b'Content-Disposition' in part and b'filename=' in part:
                    # 提取文件名
                    header_body = part.split(b'\r\n\r\n', 1)
                    if len(header_body) == 2:
                        header = header_body[0].decode('utf-8', errors='ignore')
                        file_data = header_body[1].rsplit(b'\r\n', 1)[0]

                        filename_match = re.search(r'filename="([^"]+)"', header)
                        if filename_match:
                            filename = filename_match.group(1)

            if not file_data or not filename:
                self._send_error(400, "未找到文件")
                return

            # 保存临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
            temp_file.write(file_data)
            temp_file.close()

            try:
                # 读取Word内容
                content = read_word_document(temp_file.name)

                # AI分析
                ai_analysis = call_ai_analysis(content)
                if not ai_analysis:
                    ai_analysis = {
                        "relation_tags": [],
                        "symptom_tags": [],
                        "crisis_level": "C",
                        "crisis_evidence": "",
                        "keywords": [],
                        "techniques_used": [],
                        "summary": "",
                        "strengths": [],
                        "improvements": [],
                        "recommended_followup": ""
                    }

                # 生成案例编号
                case_id = generate_case_id()

                # 保存Word到临时位置（待确认后再移动）
                temp_word_path = tempfile.gettempdir()
                temp_word_file = os.path.join(temp_word_path, f"{case_id}_temp.docx")
                shutil.copy2(temp_file.name, temp_word_file)

                self._send_json({
                    "success": True,
                    "case_id": case_id,
                    "content": content,
                    "ai_analysis": ai_analysis,
                    "temp_word_file": temp_word_file
                })

            finally:
                os.unlink(temp_file.name)

        except Exception as e:
            self._send_error(500, f"处理失败：{str(e)}")

    def _handle_save_case(self):
        """保存案例（包含所有材料）"""
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))

            case_id = data['case_id']
            temp_word_file = data['temp_word_file']

            # 创建案例文件夹
            case_dir = CASES_PROCESSED / case_id
            case_dir.mkdir(parents=True, exist_ok=True)

            # 1. 移动Word原始文档
            original_dest = CASES_ORIGINAL / f"{case_id}.docx"
            shutil.move(temp_word_file, original_dest)

            # 2. 保存案例JSON
            case_data = {
                "case_id": case_id,
                "source_file": str(original_dest),
                "created_at": datetime.now().isoformat(),
                "basic_info": data.get("basic_info", {}),
                "session_info": data.get("session_info", {}),
                "tags": data.get("tags", {"relation": [], "symptom": []}),
                "crisis_level": data.get("crisis_level", ""),
                "crisis_evidence": data.get("crisis_evidence", ""),
                "keywords": data.get("keywords", []),
                "techniques_used": data.get("techniques_used", []),
                "dialogue": data.get("dialogue", ""),
                "ai_analysis": data.get("ai_analysis", {}),
                "supervision_records": [],
                "audio_files": [],
                "transcripts": [],
                "supervision_files": []
            }

            # 3. 处理录音文件
            for audio in data.get("audio_files", []):
                audio_dir = case_dir / "audio"
                audio_dir.mkdir(exist_ok=True)
                # 这里假设前端已经上传到临时位置，需要移动
                # 实际实现中需要配合前端的文件上传

            # 4. 处理逐字稿
            case_data["transcripts"] = data.get("transcripts", [])

            # 5. 处理督导资料
            for supervision in data.get("supervision_files", []):
                supervision_dir = case_dir / "supervision"
                supervision_dir.mkdir(exist_ok=True)

            # 保存JSON
            case_json = case_dir / f"{case_id}.json"
            case_json.write_text(json.dumps(case_data, ensure_ascii=False, indent=2), encoding='utf-8')

            # 更新索引
            update_index(case_id, case_data)

            self._send_json({
                "success": True,
                "case_id": case_id,
                "message": "案例保存成功"
            })

        except Exception as e:
            self._send_error(500, f"保存失败：{str(e)}")

    def _handle_get_tags_library(self):
        """获取标签库"""
        try:
            tags_library = load_tags_library()
            self._send_json(tags_library)
        except Exception as e:
            self._send_error(500, f"加载失败：{str(e)}")

    def _send_json(self, data: dict):
        """发送JSON响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _send_error(self, code: int, message: str):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({
            "success": False,
            "error": message
        }, ensure_ascii=False).encode('utf-8'))


def main():
    port = 8007
    server = HTTPServer(('0.0.0.0', port), CaseProcessorHandler)
    print(f"[OK] 单案例处理服务器启动")
    print(f"[OK] 监听端口：{port}")
    print(f"[OK] API地址：http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
