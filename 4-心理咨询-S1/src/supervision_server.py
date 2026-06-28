#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
督导资料管理服务器
提供HTTP API用于上传和管理督导文档、笔记等资料
"""

import sys
import os
import json
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime

# Windows UTF-8 输出支持
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_DIR = os.path.join(PROJECT_ROOT, 'data', 'cases', 'processed')
SUPERVISION_DIR = os.path.join(PROJECT_ROOT, 'data', 'cases', 'supervision')

# 确保督导资料目录存在
os.makedirs(SUPERVISION_DIR, exist_ok=True)


class SupervisionHandler(BaseHTTPRequestHandler):
    """督导资料API处理器"""

    def _set_cors_headers(self):
        """设置CORS头，允许跨域"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
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

        # GET /api/supervision/list?case_id=xxx - 获取指定案例的督导资料
        if path == '/api/supervision/list':
            query_params = parse_qs(parsed_path.query)
            case_id = query_params.get('case_id', [''])[0]

            if not case_id:
                self._send_error(400, "缺少case_id参数")
                return

            try:
                supervision_list = self._get_case_supervision_list(case_id)
                self._send_json(supervision_list)
                print(f"[GET] 返回案例 {case_id} 的 {len(supervision_list)} 个督导资料")
            except Exception as e:
                self._send_error(500, f"获取督导资料失败: {str(e)}")

        # GET /api/supervision/file/{case_id}/{filename} - 获取督导文件
        elif path.startswith('/api/supervision/file/'):
            parts = path.split('/')
            if len(parts) >= 5:
                case_id = parts[4]
                filename = unquote('/'.join(parts[5:]))
                self._serve_supervision_file(case_id, filename)
            else:
                self._send_error(404, "文件路径无效")

        else:
            self._send_error(404, "接口不存在")

    def do_POST(self):
        """处理POST请求 - 上传督导资料"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/api/supervision/upload':
            try:
                # 解析multipart/form-data
                content_type = self.headers['Content-Type']
                if not content_type or not content_type.startswith('multipart/form-data'):
                    self._send_error(400, "必须使用multipart/form-data上传")
                    return

                # 提取boundary
                boundary = content_type.split('boundary=')[1].encode()

                # 读取完整请求体
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)

                # 解析multipart数据
                case_id, filename, file_data, title, note = self._parse_multipart(body, boundary)

                if not case_id or not file_data:
                    self._send_error(400, "缺少case_id或supervision_file")
                    return

                # 保存督导文件
                result = self._save_supervision_file(case_id, filename, file_data, title, note)

                # 更新案例JSON
                self._update_case_json(case_id, result)

                self._send_json(result)
                print(f"[POST] 成功上传督导资料: {case_id}/{result['filename']}")

            except Exception as e:
                self._send_error(500, f"上传失败: {str(e)}")
                import traceback
                traceback.print_exc()

        else:
            self._send_error(404, "接口不存在")

    def do_DELETE(self):
        """处理DELETE请求 - 删除督导资料"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/api/supervision/delete':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self._send_error(400, "缺少请求体")
                    return

                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                case_id = data.get('case_id')
                filename = data.get('filename')

                if not case_id or not filename:
                    self._send_error(400, "缺少case_id或filename")
                    return

                self._delete_supervision_file(case_id, filename)
                self._send_json({"success": True, "message": "删除成功"})
                print(f"[DELETE] 删除督导资料: {case_id}/{filename}")

            except Exception as e:
                self._send_error(500, f"删除失败: {str(e)}")

        else:
            self._send_error(404, "接口不存在")

    def _parse_multipart(self, body, boundary):
        """解析multipart/form-data"""
        parts = body.split(b'--' + boundary)

        case_id = None
        filename = None
        file_data = None
        title = None
        note = None

        for part in parts:
            if b'Content-Disposition' not in part:
                continue

            lines = part.split(b'\r\n')
            disposition_line = None
            data_start = 0

            for i, line in enumerate(lines):
                if b'Content-Disposition' in line:
                    disposition_line = line.decode('utf-8', errors='ignore')
                if line == b'' and disposition_line:
                    data_start = i + 1
                    break

            if not disposition_line:
                continue

            # 提取字段
            if 'name="case_id"' in disposition_line:
                case_id = b'\r\n'.join(lines[data_start:]).strip().decode('utf-8')
            elif 'name="title"' in disposition_line:
                title = b'\r\n'.join(lines[data_start:]).strip().decode('utf-8')
            elif 'name="note"' in disposition_line:
                note = b'\r\n'.join(lines[data_start:]).strip().decode('utf-8')
            elif 'name="supervision_file"' in disposition_line:
                if 'filename="' in disposition_line:
                    filename = disposition_line.split('filename="')[1].split('"')[0]
                file_data = b'\r\n'.join(lines[data_start:])
                if file_data.endswith(b'\r\n'):
                    file_data = file_data[:-2]

        return case_id, filename, file_data, title, note

    def _get_case_supervision_list(self, case_id):
        """获取案例的督导资料列表"""
        case_file = os.path.join(CASES_DIR, f"{case_id}.json")

        if not os.path.exists(case_file):
            return []

        with open(case_file, 'r', encoding='utf-8') as f:
            case_data = json.load(f)

        return case_data.get('supervision_files', [])

    def _save_supervision_file(self, case_id, filename, file_data, title, note):
        """保存督导文件"""
        # 创建案例督导目录
        case_supervision_dir = os.path.join(SUPERVISION_DIR, case_id)
        os.makedirs(case_supervision_dir, exist_ok=True)

        # 如果没有文件名，生成一个
        if not filename:
            filename = f"supervision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        # 保存文件
        file_path = os.path.join(case_supervision_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file_data)

        stat = os.stat(file_path)

        return {
            'filename': filename,
            'title': title or filename,
            'note': note or '',
            'size': stat.st_size,
            'uploaded_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'url': f'/api/supervision/file/{case_id}/{filename}'
        }

    def _update_case_json(self, case_id, supervision_info):
        """更新案例JSON，添加督导资料信息"""
        case_file = os.path.join(CASES_DIR, f"{case_id}.json")

        if not os.path.exists(case_file):
            print(f"[WARN] 案例文件不存在: {case_file}")
            return

        with open(case_file, 'r', encoding='utf-8') as f:
            case_data = json.load(f)

        # 确保有supervision_files字段
        if 'supervision_files' not in case_data:
            case_data['supervision_files'] = []

        # 添加督导资料信息（避免重复）
        existing_filenames = [s['filename'] for s in case_data['supervision_files']]
        if supervision_info['filename'] not in existing_filenames:
            case_data['supervision_files'].append(supervision_info)

        # 更新最后修改时间
        case_data['last_modified'] = datetime.now().isoformat()

        # 保存
        with open(case_file, 'w', encoding='utf-8') as f:
            json.dump(case_data, f, ensure_ascii=False, indent=2)

        print(f"[UPDATE] 更新案例JSON: {case_id}")

    def _delete_supervision_file(self, case_id, filename):
        """删除督导文件"""
        file_path = os.path.join(SUPERVISION_DIR, case_id, filename)

        if os.path.exists(file_path):
            os.remove(file_path)

        # 更新案例JSON
        case_file = os.path.join(CASES_DIR, f"{case_id}.json")
        if os.path.exists(case_file):
            with open(case_file, 'r', encoding='utf-8') as f:
                case_data = json.load(f)

            if 'supervision_files' in case_data:
                case_data['supervision_files'] = [
                    s for s in case_data['supervision_files']
                    if s['filename'] != filename
                ]
                case_data['last_modified'] = datetime.now().isoformat()

                with open(case_file, 'w', encoding='utf-8') as f:
                    json.dump(case_data, f, ensure_ascii=False, indent=2)

    def _serve_supervision_file(self, case_id, filename):
        """提供督导文件下载"""
        file_path = os.path.join(SUPERVISION_DIR, case_id, filename)

        if not os.path.exists(file_path):
            self._send_error(404, "文件不存在")
            return

        # 获取文件扩展名，设置Content-Type
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            '.txt': 'text/plain; charset=utf-8',
            '.md': 'text/markdown; charset=utf-8',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.jpg': 'image/jpeg',
            '.png': 'image/png'
        }
        content_type = content_types.get(ext, 'application/octet-stream')

        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', os.path.getsize(file_path))
        self.end_headers()

        with open(file_path, 'rb') as f:
            shutil.copyfileobj(f, self.wfile)

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
        pass


def run_server(port=8006):
    """启动服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, SupervisionHandler)
    print(f"督导资料管理服务器启动在 http://localhost:{port}")
    print(f"督导资料存储目录: {SUPERVISION_DIR}")
    print("按 Ctrl+C 停止服务器")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")


if __name__ == '__main__':
    run_server()
