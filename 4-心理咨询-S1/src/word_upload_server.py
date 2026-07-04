#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Word文档上传处理服务器
功能：接收Word文档，解析并保留所有格式，转换为HTML
"""

import os
import sys
import io
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from docx import Document
from docx.shared import RGBColor
from docx.enum.text import WD_COLOR_INDEX
from docx.enum.dml import MSO_THEME_COLOR_INDEX

# Windows GBK兼容性处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def rgb_to_hex(rgb_color):
    """将RGB颜色转换为十六进制"""
    if rgb_color is None:
        return None
    try:
        return f'#{rgb_color.r:02x}{rgb_color.g:02x}{rgb_color.b:02x}'
    except:
        return None


def get_highlight_color(highlight):
    """将Word高亮颜色转换为CSS背景色"""
    highlight_map = {
        WD_COLOR_INDEX.YELLOW: '#ffff00',
        WD_COLOR_INDEX.BRIGHT_GREEN: '#00ff00',
        WD_COLOR_INDEX.TURQUOISE: '#00ffff',
        WD_COLOR_INDEX.PINK: '#ff00ff',
        WD_COLOR_INDEX.BLUE: '#0000ff',
        WD_COLOR_INDEX.RED: '#ff0000',
        WD_COLOR_INDEX.DARK_BLUE: '#000080',
        WD_COLOR_INDEX.TEAL: '#008080',
        WD_COLOR_INDEX.GREEN: '#008000',
        WD_COLOR_INDEX.VIOLET: '#800080',
        WD_COLOR_INDEX.DARK_RED: '#800000',
        WD_COLOR_INDEX.DARK_YELLOW: '#808000',
        WD_COLOR_INDEX.GRAY_50: '#808080',
        WD_COLOR_INDEX.GRAY_25: '#c0c0c0',
    }
    return highlight_map.get(highlight, None)


def parse_word_to_html(docx_file):
    """解析Word文档，转换为保留格式的HTML"""
    doc = Document(docx_file)
    html_parts = []

    for para in doc.paragraphs:
        # 处理段落
        if para.style.name.startswith('Heading'):
            level = para.style.name.replace('Heading ', '')
            try:
                h_level = int(level)
                h_tag = f'h{min(h_level + 1, 6)}'  # h1留给页面标题，所以+1
                html_parts.append(f'<{h_tag} style="color: #6366f1; margin-top: 15px; margin-bottom: 10px;">{parse_runs(para.runs)}</{h_tag}>')
            except:
                html_parts.append(f'<p style="margin-bottom: 10px;">{parse_runs(para.runs)}</p>')
        elif para.style.name == 'List Paragraph' or para.text.strip().startswith('•') or para.text.strip().startswith('-'):
            html_parts.append(f'<li>{parse_runs(para.runs)}</li>')
        elif para.text.strip():
            # 普通段落，添加底部间距
            html_parts.append(f'<p style="margin-bottom: 10px;">{parse_runs(para.runs)}</p>')
        else:
            # 空段落保留
            html_parts.append('<p style="margin-bottom: 10px;"><br></p>')

    # 将连续的<li>包装在<ul>中
    html = '\n'.join(html_parts)

    # 简单的列表项合并
    lines = html.split('\n')
    result = []
    in_list = False

    for line in lines:
        if line.strip().startswith('<li>'):
            if not in_list:
                result.append('<ul style="list-style-type: disc; margin-left: 20px;">')
                in_list = True
            result.append(line)
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)

    if in_list:
        result.append('</ul>')

    return '\n'.join(result)


def parse_runs(runs):
    """解析文本运行，保留所有格式"""
    html_parts = []

    for run in runs:
        text = run.text
        if not text:
            continue

        # 构建样式
        styles = []
        tags_open = []
        tags_close = []

        # 加粗
        if run.bold:
            tags_open.append('<strong>')
            tags_close.insert(0, '</strong>')

        # 斜体
        if run.italic:
            tags_open.append('<em>')
            tags_close.insert(0, '</em>')

        # 下划线
        if run.underline:
            tags_open.append('<u>')
            tags_close.insert(0, '</u>')

        # 字体颜色 - 直接从XML读取
        color_hex = None
        if hasattr(run, '_element') and run._element.rPr is not None:
            # 直接从XML中读取 <w:color> 标签
            color_elem = run._element.rPr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color')
            if color_elem is not None:
                color_val = color_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if color_val and color_val != 'auto':
                    color_hex = f'#{color_val}'

        # 备选：使用python-docx API
        if not color_hex and run.font.color:
            if run.font.color.rgb:
                color_hex = rgb_to_hex(run.font.color.rgb)
            elif hasattr(run.font.color, 'theme_color') and run.font.color.theme_color:
                # 主题颜色映射
                theme_color_map = {
                    MSO_THEME_COLOR_INDEX.ACCENT_1: '#4472C4',
                    MSO_THEME_COLOR_INDEX.ACCENT_2: '#ED7D31',
                    MSO_THEME_COLOR_INDEX.ACCENT_3: '#A5A5A5',
                    MSO_THEME_COLOR_INDEX.ACCENT_4: '#FFC000',
                    MSO_THEME_COLOR_INDEX.ACCENT_5: '#5B9BD5',
                    MSO_THEME_COLOR_INDEX.ACCENT_6: '#70AD47',
                    MSO_THEME_COLOR_INDEX.DARK_1: '#000000',
                    MSO_THEME_COLOR_INDEX.DARK_2: '#44546A',
                    MSO_THEME_COLOR_INDEX.LIGHT_1: '#FFFFFF',
                    MSO_THEME_COLOR_INDEX.LIGHT_2: '#E7E6E6',
                }
                color_hex = theme_color_map.get(run.font.color.theme_color)

        if color_hex:
            styles.append(f'color: {color_hex}')

        # 高亮/背景色 - 直接从XML读取
        bg_color = None
        if hasattr(run, '_element') and run._element.rPr is not None:
            # 检查 <w:highlight> 标签
            highlight_elem = run._element.rPr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}highlight')
            if highlight_elem is not None:
                highlight_val = highlight_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if highlight_val:
                    # 高亮颜色映射（使用浅色背景以确保文字可见）
                    highlight_color_map = {
                        'yellow': '#ffff99',      # 浅黄色
                        'green': '#90ee90',       # 浅绿色
                        'cyan': '#afeeee',        # 浅青色
                        'magenta': '#ffb6c1',     # 浅粉色
                        'blue': '#add8e6',        # 浅蓝色
                        'red': '#ffcccb',         # 浅红色（粉色）
                        'darkBlue': '#6495ed',    # 适中蓝色
                        'darkCyan': '#48d1cc',    # 适中青色
                        'darkGreen': '#98fb98',   # 浅绿色
                        'darkMagenta': '#dda0dd', # 浅紫色
                        'darkRed': '#f08080',     # 浅红色
                        'darkYellow': '#f0e68c',  # 卡其色
                        'darkGray': '#d3d3d3',    # 浅灰色
                        'lightGray': '#e8e8e8',   # 更浅的灰色
                    }
                    bg_color = highlight_color_map.get(highlight_val)

            # 检查填充色 <w:shd>
            if not bg_color:
                shd = run._element.rPr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd')
                if shd is not None:
                    fill_color = shd.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                    if fill_color and fill_color != 'auto':
                        bg_color = f'#{fill_color}'

        # 备选：使用python-docx API
        if not bg_color and run.font.highlight_color:
            bg_color = get_highlight_color(run.font.highlight_color)

        if bg_color:
            styles.append(f'background-color: {bg_color}')

        # 组合HTML
        if styles:
            style_attr = f' style="{"; ".join(styles)}"'
            text = f'<span{style_attr}>{text}</span>'

        text = ''.join(tags_open) + text + ''.join(tags_close)
        html_parts.append(text)

    return ''.join(html_parts)


class WordUploadHandler(BaseHTTPRequestHandler):
    """处理Word上传请求"""

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """处理Word文档上传"""
        try:
            # 获取内容长度
            content_length = int(self.headers['Content-Length'])

            # 读取请求体
            post_data = self.rfile.read(content_length)

            # 解析multipart数据
            boundary = self.headers['Content-Type'].split('boundary=')[1].encode()
            parts = post_data.split(b'--' + boundary)

            file_data = None
            for part in parts:
                if b'Content-Disposition' in part and b'filename=' in part:
                    # 提取文件数据
                    file_start = part.find(b'\r\n\r\n') + 4
                    file_end = len(part) - 2  # 去掉末尾的\r\n
                    file_data = part[file_start:file_end]
                    break

            if not file_data:
                self.send_error(400, 'No file data found')
                return

            # 保存临时文件
            temp_path = Path('temp_upload.docx')
            with open(temp_path, 'wb') as f:
                f.write(file_data)

            # 解析Word文档
            html_content = parse_word_to_html(temp_path)

            # 删除临时文件
            temp_path.unlink()

            # 返回HTML
            response = {
                'success': True,
                'html': html_content
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            print(f'错误: {str(e)}', file=sys.stderr)
            import traceback
            traceback.print_exc()

            response = {
                'success': False,
                'error': str(e)
            }

            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        """自定义日志输出"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def start_server(port=8765):
    """启动服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, WordUploadHandler)

    print('=' * 60)
    print(f'Word上传服务器已启动')
    print(f'监听端口: {port}')
    print(f'访问地址: http://localhost:{port}')
    print('=' * 60)
    print('\n按 Ctrl+C 停止服务器\n')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n\n服务器已停止')
        httpd.server_close()


if __name__ == '__main__':
    start_server()
