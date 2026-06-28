#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐字稿管理服务器
提供HTTP API用于管理案例逐字稿
"""

import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Windows UTF-8 输出支持
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_DIR = os.path.join(PROJECT_ROOT, 'data', 'cases', 'processed')


class TranscriptHandler(BaseHTTPRequestHandler):
    """逐字稿API处理器"""

    def _set_cors_headers(self):
        """设置CORS头，允许跨域"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # GET /api/transcript?case_id=xxx - 获取案例逐字稿
        if path == '/api/transcript':
            query_params = parse_qs(parsed_path.query)
            case_id = query_params.get('case_id', [''])[0]

            if not case_id:
                self._send_error(400, "缺少case_id参数")
                return

            try:
                transcripts = self._get_case_transcripts(case_id)
                self._send_json(transcripts)
                print(f"[GET] 返回案例 {case_id} 的 {len(transcripts)} 条逐字稿")
            except Exception as e:
                self._send_error(500, f"获取逐字稿失败: {str(e)}")

        else:
            self._send_error(404, "接口不存在")

    def do_POST(self):
        """处理POST请求 - 添加逐字稿"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/api/transcript':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self._send_error(400, "缺少请求体")
                    return

                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                case_id = data.get('case_id')
                content = data.get('content')
                audio_filename = data.get('audio_filename', '')
                timestamps = data.get('timestamps', [])

                if not case_id or not content:
                    self._send_error(400, "缺少case_id或content")
                    return

                result = self._add_transcript(case_id, content, audio_filename, timestamps)
                self._send_json(result)
                print(f"[POST] 添加逐字稿: {case_id}")

            except Exception as e:
                self._send_error(500, f"添加逐字稿失败: {str(e)}")
                import traceback
                traceback.print_exc()

        else:
            self._send_error(404, "接口不存在")

    def do_PUT(self):
        """处理PUT请求 - 更新逐字稿"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/api/transcript':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self._send_error(400, "缺少请求体")
                    return

                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                case_id = data.get('case_id')
                transcript_id = data.get('transcript_id')
                content = data.get('content')
                timestamps = data.get('timestamps', [])

                if not case_id or not transcript_id or not content:
                    self._send_error(400, "缺少case_id、transcript_id或content")
                    return

                result = self._update_transcript(case_id, transcript_id, content, timestamps)
                self._send_json(result)
                print(f"[PUT] 更新逐字稿: {case_id}/{transcript_id}")

            except Exception as e:
                self._send_error(500, f"更新逐字稿失败: {str(e)}")

        else:
            self._send_error(404, "接口不存在")

    def do_DELETE(self):
        """处理DELETE请求 - 删除逐字稿"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/api/transcript':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self._send_error(400, "缺少请求体")
                    return

                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                case_id = data.get('case_id')
                transcript_id = data.get('transcript_id')

                if not case_id or not transcript_id:
                    self._send_error(400, "缺少case_id或transcript_id")
                    return

                self._delete_transcript(case_id, transcript_id)
                self._send_json({"success": True, "message": "删除成功"})
                print(f"[DELETE] 删除逐字稿: {case_id}/{transcript_id}")

            except Exception as e:
                self._send_error(500, f"删除逐字稿失败: {str(e)}")

        else:
            self._send_error(404, "接口不存在")

    def _get_case_transcripts(self, case_id):
        """获取案例的逐字稿列表"""
        case_file = os.path.join(CASES_DIR, f"{case_id}.json")

        if not os.path.exists(case_file):
            return []

        with open(case_file, 'r', encoding='utf-8') as f:
            case_data = json.load(f)

        return case_data.get('transcripts', [])

    def _add_transcript(self, case_id, content, audio_filename, timestamps):
        """添加逐字稿"""
        case_file = os.path.join(CASES_DIR, f"{case_id}.json")

        if not os.path.exists(case_file):
            raise FileNotFoundError(f"案例文件不存在: {case_file}")

        with open(case_file, 'r', encoding='utf-8') as f:
            case_data = json.load(f)

        # 确保有transcripts字段
        if 'transcripts' not in case_data:
            case_data['transcripts'] = []

        # 生成逐字稿ID
        transcript_id = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 创建逐字稿对象
        transcript = {
            'id': transcript_id,
            'content': content,
            'audio_filename': audio_filename,
            'timestamps': timestamps,
            'created_at': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat()
        }

        case_data['transcripts'].append(transcript)
        case_data['last_modified'] = datetime.now().isoformat()

        # 保存
        with open(case_file, 'w', encoding='utf-8') as f:
            json.dump(case_data, f, ensure_ascii=False, indent=2)

        return transcript

    def _update_transcript(self, case_id, transcript_id, content, timestamps):
        """更新逐字稿"""
        case_file = os.path.join(CASES_DIR, f"{case_id}.json")

        if not os.path.exists(case_file):
            raise FileNotFoundError(f"案例文件不存在: {case_file}")

        with open(case_file, 'r', encoding='utf-8') as f:
            case_data = json.load(f)

        transcripts = case_data.get('transcripts', [])
        found = False

        for transcript in transcripts:
            if transcript['id'] == transcript_id:
                transcript['content'] = content
                transcript['timestamps'] = timestamps
                transcript['last_modified'] = datetime.now().isoformat()
                found = True
                break

        if not found:
            raise ValueError(f"逐字稿不存在: {transcript_id}")

        case_data['last_modified'] = datetime.now().isoformat()

        # 保存
        with open(case_file, 'w', encoding='utf-8') as f:
            json.dump(case_data, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "更新成功"}

    def _delete_transcript(self, case_id, transcript_id):
        """删除逐字稿"""
        case_file = os.path.join(CASES_DIR, f"{case_id}.json")

        if not os.path.exists(case_file):
            raise FileNotFoundError(f"案例文件不存在: {case_file}")

        with open(case_file, 'r', encoding='utf-8') as f:
            case_data = json.load(f)

        transcripts = case_data.get('transcripts', [])
        case_data['transcripts'] = [t for t in transcripts if t['id'] != transcript_id]
        case_data['last_modified'] = datetime.now().isoformat()

        # 保存
        with open(case_file, 'w', encoding='utf-8') as f:
            json.dump(case_data, f, ensure_ascii=False, indent=2)

    def _send_json(self, data):
        """发送JSON响应"""
        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response.encode('utf-8'))

    def _send_error(self, code, message):
        """发送错误响应"""
        self.send_response(code)
        self._set_cors_headers()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        response = json.dumps({"error": message}, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))
        print(f"[ERROR {code}] {message}")

    def log_message(self, format, *args):
        """覆盖默认日志，使用自定义格式"""
        pass  # 我们使用自己的print语句


def run_server(port=8005):
    """启动服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, TranscriptHandler)
    print(f"逐字稿管理服务器启动在 http://localhost:{port}")
    print("按 Ctrl+C 停止服务器")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")


if __name__ == '__main__':
    run_server()
