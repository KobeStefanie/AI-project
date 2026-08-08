#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除来访者API：删除来访者的所有数据和生成的页面
"""

import json
import os
import sys
import io
import shutil
import subprocess
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

# Windows GBK兼容性处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置
project_root = Path(__file__).parent.parent
VISITORS_DIR = project_root / 'data' / 'visitors'
OUTPUT_DIR = project_root / 'output' / '来访者库'


def regenerate_html():
    """重新生成来访者库HTML"""
    try:
        print("🔄 重新生成来访者库HTML...")
        creation_flags = 0
        if sys.platform == 'win32':
            creation_flags = subprocess.CREATE_NO_WINDOW

        script_path = project_root / 'src' / 'generate_visitor_library.py'
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(project_root),
            creationflags=creation_flags,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("✓ HTML重新生成成功")
            return True
        else:
            print(f"⚠ HTML生成警告: {result.stderr}")
            return True  # 即使有警告也继续
    except Exception as e:
        print(f"⚠ HTML重新生成失败: {e}")
        return False


def delete_visitor(visitor_id):
    """
    删除来访者的所有数据

    Args:
        visitor_id: 来访者ID

    Returns:
        dict: {'success': bool, 'message': str, 'error': str}
    """
    try:
        # 1. 删除数据目录
        visitor_data_dir = VISITORS_DIR / visitor_id
        if visitor_data_dir.exists():
            shutil.rmtree(visitor_data_dir)
            print(f"✓ 已删除数据目录: {visitor_data_dir}")
        else:
            print(f"⚠ 数据目录不存在: {visitor_data_dir}")

        # 2. 删除生成的HTML目录
        visitor_output_dir = OUTPUT_DIR / visitor_id
        if visitor_output_dir.exists():
            shutil.rmtree(visitor_output_dir)
            print(f"✓ 已删除HTML目录: {visitor_output_dir}")
        else:
            print(f"⚠ HTML目录不存在: {visitor_output_dir}")

        # 3. 重新生成来访者库HTML（更新索引页面）
        regenerate_html()

        return {
            'success': True,
            'message': f'成功删除来访者 {visitor_id}'
        }

    except Exception as e:
        error_msg = f'删除失败: {str(e)}'
        print(f"✗ {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }


class DeleteVisitorHandler(BaseHTTPRequestHandler):
    """处理删除来访者的HTTP请求"""

    def do_POST(self):
        """处理POST请求"""
        if self.path == '/api/delete_visitor':
            # 读取请求体
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            visitor_id = data.get('visitor_id')
            if not visitor_id:
                self.send_error(400, 'Missing visitor_id')
                return

            # 执行删除
            result = delete_visitor(visitor_id)

            # 返回结果
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 命令行模式：直接删除指定的visitor_id
        visitor_id = sys.argv[1]
        print(f"\n删除来访者: {visitor_id}")
        print("=" * 60)
        result = delete_visitor(visitor_id)
        print("=" * 60)
        if result['success']:
            print(f"\n✓ {result['message']}")
        else:
            print(f"\n✗ {result['error']}")
            sys.exit(1)
    else:
        # 服务器模式
        PORT = 9001
        server = HTTPServer(('localhost', PORT), DeleteVisitorHandler)
        print(f"\n删除来访者API服务已启动")
        print(f"监听端口: {PORT}")
        print(f"API端点: http://localhost:{PORT}/api/delete_visitor")
        print("\n按 Ctrl+C 停止服务\n")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n\n服务已停止")
            server.shutdown()


if __name__ == '__main__':
    main()
