---
name: token-tracker-rescue
description: Token 成本追踪系统的备份恢复方案和紧急补救措施
metadata:
  type: project
---

# Token 成本追踪系统 - 紧急补救方案

## 项目位置
- **生产目录**: `D:\AI-项目\6-Token成本管理\`
- **配置备份**: `C:\Users\Administrator\.claude\settings.json.backup`

## ⚠️ 如果代理服务器挂了导致无法使用

### 症状
- Claude Code 无法连接 API
- 报错：连接超时或无法访问

### 立即恢复步骤（5秒内恢复）

```bash
# 1. 恢复原配置
cp C:/Users/Administrator/.claude/settings.json.backup C:/Users/Administrator/.claude/settings.json

# 2. 重启 Claude Code
```

### 原始配置内容
```json
{
  "env": {
    "ANTHROPIC_API_KEY": "sk-d285143ff8b40377e38294cc41f2f86b518349f3f6278328c439bfed7d89fdde",
    "ANTHROPIC_BASE_URL": "https://www.catkingai.com",
    "DISABLE_AUTOUPDATER": "1",
    "ANTHROPIC_AUTH_TOKEN": "sk-d285143ff8b40377e38294cc41f2f86b518349f3f6278328c439bfed7d89fdde"
  }
}
```

## 🔄 正常启动/停止流程

### 启动代理服务器
```bash
cd "D:\AI-项目\6-Token成本管理"
node proxy-server.js &
```

### 停止代理服务器
```bash
# 查找进程
ps aux | grep proxy-server

# 停止进程
kill <PID>
```

### 检查服务器状态
- 代理服务器：http://localhost:8888
- Dashboard：http://localhost:3000

## 📊 数据备份

### 定期备份（建议每周）
```bash
# 备份数据库
cp "D:\AI-项目\6-Token成本管理\token-usage.db" "D:\AI-项目\0-config\backups\token-usage-$(date +%Y%m%d).db"
```

### 重装系统前必做
1. 备份数据库：`token-usage.db`
2. 备份配置：`settings.json.backup`
3. 导出统计数据（从 Dashboard）

## 🛠️ 故障排查

### 问题1：代理无响应
```bash
# 检查端口占用
netstat -ano | grep 8888
netstat -ano | grep 3000

# 重启服务器
cd "D:\AI-项目\6-Token成本管理"
node proxy-server.js
```

### 问题2：Dashboard 无数据
- 检查数据库文件是否存在
- 确认代理服务器正在运行
- 刷新浏览器页面

### 问题3：API 调用未被记录
- 确认 ANTHROPIC_BASE_URL 指向 localhost:8888
- 检查代理服务器日志
- 验证 API Key 配置正确

## 🔐 安全注意事项

### API Key 存储位置
- `C:\Users\Administrator\.claude\settings.json`
- `D:\AI-项目\6-Token成本管理\proxy-server.js`（代码中硬编码）

### 不要泄露
- settings.json
- token-usage.db（包含完整调用记录）
- proxy-server.js（包含 API Key 判断逻辑）

## 📋 配置切换速查

### 使用代理（记录 Token）
```json
"ANTHROPIC_BASE_URL": "http://localhost:8888"
```

### 直连 API（不记录）
```json
"ANTHROPIC_BASE_URL": "https://www.catkingai.com"
```

## Why 为什么需要这个系统
- 控制成本：实时监控 Token 消耗
- 对比提供商：选择性价比最优的 API
- 使用分析：了解哪些模型用得最多

## How to apply 应用方式
1. 需要追踪时：启动代理服务器 + 修改配置
2. 不需要时：恢复原配置即可
3. 定期查看 Dashboard 分析成本
