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

        if parsed_path.path == '/api/approaches':
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

                # 自动重新生成案例库
                print("[AUTO] 自动重新生成案例库...")
                self._regenerate_case_library()

                self.send_response(200)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()

                response = json.dumps({"success": True, "message": "保存成功并已更新案例库"}, ensure_ascii=False)
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
        """保存所有流派配置"""
        # 确保目录存在
        os.makedirs(APPROACHES_DIR, exist_ok=True)

        # 获取现有文件列表
        existing_files = set(os.path.basename(f) for f in glob.glob(os.path.join(APPROACHES_DIR, '*.json')))
        new_files = set()

        # 保存每个流派配置
        for approach in approaches:
            approach_id = approach['id']
            filename = f"{approach_id}.json"
            filepath = os.path.join(APPROACHES_DIR, filename)

            new_files.add(filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(approach, f, ensure_ascii=False, indent=2)

            print(f"  ✓ 保存配置: {filename}")

        # 删除不再存在的配置文件
        deleted_files = existing_files - new_files
        for filename in deleted_files:
            filepath = os.path.join(APPROACHES_DIR, filename)
            os.remove(filepath)
            print(f"  ✗ 删除配置: {filename}")

    def _regenerate_case_library(self):
        """重新生成案例库"""
        import subprocess

        try:
            # 调用案例库生成脚本
            generate_script = os.path.join(PROJECT_ROOT, 'src', 'generate_case_library.py')
            result = subprocess.run(
                [sys.executable, generate_script],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if result.returncode == 0:
                print("[AUTO] ✓ 案例库重新生成成功")
                # 打印生成脚本的输出
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        print(f"       {line}")
            else:
                print(f"[AUTO] ✗ 案例库生成失败: {result.stderr}")

        except Exception as e:
            print(f"[AUTO] ✗ 无法执行案例库生成: {e}")

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
