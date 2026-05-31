// 时间管理助手 · 本地静态服务器（仅 Node 内置模块）
//
// v2.11.0：HTTP 6371 + HTTPS 6443 双听
//   - HTTP 仍保留用于桌面本机开发（http://127.0.0.1:6371）
//   - HTTPS 用于 iPhone PWA 安装与离线启动（必须 HTTPS 才能让 iOS Safari 信任 SW
//     并允许 fetch 到同样 HTTPS 的同步服务，避免 mixed content 拦截）
//
// 启动 HTTPS 前提：项目根 certs/ 目录下有 cert.pem 与 key.pem。
// 没有的话先跑：cd tools/gen-cert && npm install && node gen-cert.js

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = parseInt(process.argv[2], 10) || 6371;
const HTTPS_PORT = parseInt(process.argv[3], 10) || 6443;
const ROOT = __dirname; // 服务当前 src/ 目录
const CERT_DIR  = path.resolve(__dirname, '..', 'certs');
const CERT_PATH = path.join(CERT_DIR, 'leaf-cert-chain.pem'); // v2.11.0 改 CA-leaf chain
const KEY_PATH  = path.join(CERT_DIR, 'leaf-key.pem');
const CA_CRT_PATH = path.join(CERT_DIR, 'ca-cert.crt');
const CA_PEM_PATH = path.join(CERT_DIR, 'ca-cert.pem');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg':  'image/svg+xml',
  '.png':  'image/png',
  '.ico':  'image/x-icon',
  '.txt':  'text/plain; charset=utf-8',
  '.crt':  'application/x-x509-ca-cert',
  '.pem':  'application/x-x509-ca-cert'
};

// v2.11.0：分发 CA 证书供 iPhone 装信任。
// 三条 alias 都返回 ca-cert.crt 同一份内容，方便用户拼读。
// 走 HTTP 6371 也能拿（避开未信任 HTTPS 警告，iPhone 首次下载用）。
const CERT_DOWNLOAD_ALIASES = ['/cert.crt', '/cert.pem', '/ca.crt', '/ca.pem'];

function serveCertDownload(req, res) {
  // 优先 .crt（部分客户端识别更稳），不存在再退 .pem
  const src = fs.existsSync(CA_CRT_PATH) ? CA_CRT_PATH
            : fs.existsSync(CA_PEM_PATH) ? CA_PEM_PATH
            : null;
  if (!src) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('CA 证书尚未生成：请先在 tools/gen-cert/ 跑 node gen-all.js');
    console.log('404', req.url, '(no CA cert)');
    return;
  }
  fs.readFile(src, (err, data) => {
    if (err) {
      res.writeHead(500); res.end('read fail'); return;
    }
    res.writeHead(200, {
      'Content-Type': 'application/x-x509-ca-cert',
      'Content-Disposition': 'attachment; filename="time-planner-ca.crt"',
      'Cache-Control': 'no-store'
    });
    res.end(data);
    console.log('200', req.url, '→ CA cert (' + data.length + ' bytes)');
  });
}

function requestHandler(req, res) {
  let pathname;
  try { pathname = decodeURIComponent(url.parse(req.url).pathname); }
  catch (e) { res.writeHead(400); res.end('Bad URL'); return; }

  // CA 下载路由（v2.11.0）
  if (CERT_DOWNLOAD_ALIASES.indexOf(pathname) >= 0) {
    return serveCertDownload(req, res);
  }

  if (pathname === '/' || pathname === '') pathname = '/时间管理助手.html';

  const filePath = path.normalize(path.join(ROOT, pathname));
  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403); res.end('Forbidden'); return;
  }

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not Found: ' + pathname);
      console.log('404', pathname);
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      // 浏览器层禁缓存，把缓存权完全交给 Service Worker
      'Cache-Control': 'no-store'
    });
    res.end(data);
    console.log('200', pathname);
  });
}

function startServer(server, port, label) {
  server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.error('[' + label + '] 端口 ' + port + ' 已被占用。');
    } else {
      console.error('[' + label + ']', err);
    }
  });
  server.listen(port, '0.0.0.0', () => {
    console.log(' [' + label + '] 监听 0.0.0.0:' + port);
  });
}

console.log('================================================');
console.log(' 时间管理助手 · 静态服务器 (src/)');
console.log(' 项目根: ' + path.resolve(__dirname, '..'));
console.log();

// === HTTP 6371（开发/局域网兼容） ===
startServer(http.createServer(requestHandler), PORT, 'HTTP ');
console.log('   电脑访问:           http://127.0.0.1:' + PORT + '/');
console.log('   同 Wi-Fi 手机访问:  http://<电脑LAN IP>:' + PORT + '/');
console.log();

// === HTTPS 6443（iPhone PWA 必经） ===
if (fs.existsSync(CERT_PATH) && fs.existsSync(KEY_PATH)) {
  const httpsOptions = {
    cert: fs.readFileSync(CERT_PATH),
    key: fs.readFileSync(KEY_PATH)
  };
  startServer(https.createServer(httpsOptions, requestHandler), HTTPS_PORT, 'HTTPS');
  console.log('   电脑访问:           https://127.0.0.1:' + HTTPS_PORT + '/');
  console.log('   iPhone 访问:        https://<电脑LAN IP>:' + HTTPS_PORT + '/');
  console.log('   证书 chain:        ' + CERT_PATH);
  if (fs.existsSync(CA_CRT_PATH)) {
    console.log('   CA 下载（iPhone）:   http://<电脑LAN IP>:' + PORT + '/cert.crt');
  }
} else {
  console.log(' [HTTPS] 未找到证书，跳过。');
  console.log('         若需 iPhone PWA：cd tools/gen-cert && node gen-all.js');
}
console.log();
console.log(' 按 Ctrl+C 停止');
console.log('================================================');
