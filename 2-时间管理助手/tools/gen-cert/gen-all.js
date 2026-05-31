// 首次安装入口：依次跑 gen-ca.js 与 gen-leaf.js
//
// 之后日常重新生成只需要 gen-leaf.js（CA 已存在,自动跳过）。

const { spawnSync } = require('child_process');
const path = require('path');

function run(file) {
  const r = spawnSync(process.execPath, [path.join(__dirname, file)], {
    stdio: 'inherit',
    cwd: __dirname
  });
  if (r.status !== 0) {
    console.error('\n✗', file, '退出码', r.status);
    process.exit(r.status || 1);
  }
}

run('gen-ca.js');
console.log();
run('gen-leaf.js');
console.log();
console.log('==== 全部完成 ====');
console.log();
console.log('iPhone 装信任 5 步：');
console.log('  1. iPhone Safari 打开 http://<电脑LAN IP>:6371/cert.crt');
console.log('  2. 设置 → 通用 → VPN与设备管理 → 已下载的描述文件 → 安装');
console.log('  3. 设置 → 通用 → 关于本机 → 证书信任设置 → 打开 "Time Planner Personal CA"');
console.log('  4. Safari 打开 https://<电脑LAN IP>:6443/时间管理助手.html → 分享 → 添加到主屏幕');
console.log('  5. 验证：图标是蓝紫渐变；点击是独立全屏；关 WiFi 也能秒开');
