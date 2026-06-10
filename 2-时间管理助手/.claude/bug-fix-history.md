# 🐛 Bug 修复历史

## Bug #1: 服务器不断关闭导致桌面版无法打开 (2026-06-02)

### 现象
- 访问 `http://127.0.0.1:6371/` 无法打开
- node 进程反复启动和关闭
- 任务栏不断弹出 node.exe 和 PowerShell 窗口

### 根因分析

| 问题 | 原因 | 影响 |
|------|------|------|
| 端口检测失败 | `netstat -ano \| Select-String` 在 PowerShell 中正则匹配端口不稳定 | 每 30 秒误判端口离线，反复重启服务 |
| 进程泄漏 | 旧 watchdog 每次检测失败就启动新的 node/PowerShell | 累积 5 个 node + 12 个 PowerShell 进程 |
| 中文路径乱码 | PowerShell `.ps1` 文件无 UTF-8 BOM，Windows 按 GBK 编码读取 | 中文目录路径变成乱码 |
| HTTP HEAD 超时 | sync-server 响应较慢，HTTP HEAD 偶尔超时 | 误判端口不可用 |

### 解决方案

**新建 `daemon.ps1` 静默守护进程（完全替代旧 `watchdog.ps1`）**

核心改进：

1. **TCP Socket 端口检测**（替代 netstat 正则）
   ```powershell
   $client = New-Object System.Net.Sockets.TcpClient
   $result = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
   $success = $result.AsyncWaitHandle.WaitOne($TimeoutMS)
   ```
   - 比 HTTP HEAD 更快、更可靠
   - 内置重试机制（首次失败等 3 秒再试一次）

2. **完全静默进程启动**
   ```powershell
   $psi.CreateNoWindow = $true
   $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
   $psi.UseShellExecute = $false
   ```
   - 零窗口、零任务栏图标

3. **PID 精确追踪**
   - 只管理自己启动的 node 进程
   - 绝不会误杀其他 node 进程

4. **崩溃循环保护**
   - 3 分钟内最多重启 4 次
   - 超过限制后冷却 5 分钟

5. **UTF-8 BOM 编码**
   - 所有 `.ps1` 文件必须带 BOM：`\xEF\xBB\xBF`
   - 解决中文 Windows 下路径乱码

### 修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `daemon.ps1` | **新建** | 静默守护进程（v4 最终版） |
| `watchdog.ps1` | 弃用 | 保留供参考，不再使用 |
| `启动桌面版.bat` | 修改 | 改用 daemon，轮询等待端口后打开浏览器 |
| `启动服务器.bat` | 修改 | 改用 daemon，加入端口验证 |
| `autostart.bat` | 修改 | 简化，改用 daemon |
| `autostart-silent.bat` | 修改 | 改用 daemon，添加日志记录 |
| `update-startup.ps1` | 修改 | 添加 UTF-8 BOM |

### 验证结果

- ✅ 2 个 node.exe 进程稳定运行（静态服务 :6371 / 同步服务 :6372）
- ✅ 两个端口均返回 HTTP 200
- ✅ 35 秒监控周期内无误判重启
- ✅ 任务栏和桌面无任何弹窗
- ✅ 守护日志：`Init: 6371=True 6372=True PID=14596,16916`

### 架构对比

```
之前（watchdog.ps1）：
  netstat 正则 → 误判 → 反复杀死/重启 → 进程泄漏 + 窗口闪现

现在（daemon.ps1）：
  TCP Socket 检测 → 准确判断 → PID 精确管理 → 静默运行 + 崩溃保护
```

### 使用方式

- **手动启动**：双击 `启动桌面版.bat` → 静默启动 → 自动打开浏览器
- **开机自启**：运行 `update-startup.ps1` 创建 Startup 快捷方式
- **静默自启**：`autostart-silent.bat` 写入日志，适合计划任务

---

*最后更新: 2026-06-02*
