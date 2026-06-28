#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
案例处理系统诊断脚本
检查所有服务、端口、文件、权限
"""

import os
import sys
import json
import socket
from pathlib import Path

# Windows UTF-8 输出支持
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent.parent
print(f"项目根目录: {PROJECT_ROOT}")
print("=" * 60)

# 1. 检查必要目录
print("\n[1] 检查目录结构")
required_dirs = [
    "data/cases/processed",
    "data/cases/original",
    "data/cases/audio",
    "data/cases/supervision",
    "data/index",
    "data/config",
    "output/接访记录",
    "output/案例库",
    "src"
]

for dir_path in required_dirs:
    full_path = PROJECT_ROOT / dir_path
    status = "✓" if full_path.exists() else "✗"
    print(f"  {status} {dir_path}")

# 2. 检查关键文件
print("\n[2] 检查关键文件")
required_files = [
    "src/case_processor_server.py",
    "src/audio_server.py",
    "src/transcript_server.py",
    "src/supervision_server.py",
    "src/config_server.py",
    "output/case-processor.html",
    "output/case-processor.js",
    "output/接访记录/intake-record-manager.html",
    "data/config/tags_library.json"
]

for file_path in required_files:
    full_path = PROJECT_ROOT / file_path
    status = "✓" if full_path.exists() else "✗"
    print(f"  {status} {file_path}")

# 3. 检查端口占用
print("\n[3] 检查端口状态")
ports = {
    8003: "配置服务",
    8004: "录音服务",
    8005: "逐字稿服务",
    8006: "督导资料服务",
    8007: "单案例处理服务"
}

def check_port(port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

for port, name in ports.items():
    status = "运行中" if check_port(port) else "未启动"
    symbol = "✓" if status == "运行中" else "✗"
    print(f"  {symbol} 端口 {port} ({name}): {status}")

# 4. 检查Python依赖
print("\n[4] 检查Python依赖")
dependencies = ["docx", "requests"]

for dep in dependencies:
    try:
        __import__(dep)
        print(f"  ✓ {dep}")
    except ImportError:
        print(f"  ✗ {dep} (未安装)")

# 5. 检查标签库
print("\n[5] 检查标签库")
tags_file = PROJECT_ROOT / "data/config/tags_library.json"
if tags_file.exists():
    try:
        with open(tags_file, 'r', encoding='utf-8') as f:
            tags = json.load(f)
        relation_count = len(tags.get("relation_tags", {}))
        symptom_count = len(tags.get("symptom_tags", {}))
        print(f"  ✓ 关系标签类别: {relation_count}")
        print(f"  ✓ 症状标签类别: {symptom_count}")
    except Exception as e:
        print(f"  ✗ 标签库读取失败: {e}")
else:
    print(f"  ✗ 标签库文件不存在")

# 6. 检查已有案例
print("\n[6] 检查已有案例")
processed_dir = PROJECT_ROOT / "data/cases/processed"
if processed_dir.exists():
    cases = list(processed_dir.glob("C*"))
    print(f"  ✓ 已处理案例数: {len(cases)}")
    for case_dir in cases[:3]:
        print(f"    - {case_dir.name}")
    if len(cases) > 3:
        print(f"    ... 还有 {len(cases) - 3} 个案例")
else:
    print(f"  ✗ 案例目录不存在")

# 7. 环境变量
print("\n[7] 环境变量")
api_key = os.getenv("CATKINGAI_API_KEY", "")
if api_key:
    print(f"  ✓ CATKINGAI_API_KEY: {api_key[:10]}...{api_key[-4:]}")
else:
    print(f"  ✗ CATKINGAI_API_KEY 未设置（将使用mock数据）")

print("\n" + "=" * 60)
print("诊断完成！")
