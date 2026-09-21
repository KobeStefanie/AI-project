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

// ===== AI 复盘代理（v2.14.0）=====
// 浏览器不直接持有 API key：前端 POST /api/chat，由本机服务器转发到模型 API。
// 配置读自项目根 ai-config.json（已 gitignore），也支持环境变量覆盖。
const AI_CONFIG_PATH = path.resolve(__dirname, '..', 'ai-config.json');

function loadAiConfig() {
  let cfg = {};
  try {
    if (fs.existsSync(AI_CONFIG_PATH)) {
      cfg = JSON.parse(fs.readFileSync(AI_CONFIG_PATH, 'utf8'));
    }
  } catch (e) {
    console.error('[AI] ai-config.json 解析失败:', e.message);
  }
  // 环境变量优先级更高，方便临时切换
  const baseUrl = (process.env.ANTHROPIC_BASE_URL || cfg.baseUrl || '').replace(/\/+$/, '');
  const apiKey  = process.env.ANTHROPIC_AUTH_TOKEN || process.env.ANTHROPIC_API_KEY || cfg.apiKey || '';
  const model   = cfg.model || process.env.ANTHROPIC_MODEL || 'claude-opus-5';
  const maxTokens = cfg.maxTokens || 8000;
  return { baseUrl, apiKey, model, maxTokens };
}

// 上游模型 API 调用，返回纯文本
function callModel(messages, system, maxTokens) {
  return new Promise((resolve, reject) => {
    const cfg = loadAiConfig();
    if (!cfg.baseUrl || !cfg.apiKey) {
      reject(new Error('AI 未配置：请在项目根目录的 ai-config.json 中填写 baseUrl 与 apiKey'));
      return;
    }

    const payload = JSON.stringify({
      model: cfg.model,
      max_tokens: maxTokens || cfg.maxTokens,
      system: system || undefined,
      messages: messages
    });

    let target;
    try { target = new URL(cfg.baseUrl + '/v1/messages'); }
    catch (e) { reject(new Error('baseUrl 不是合法地址: ' + cfg.baseUrl)); return; }

    const transport = target.protocol === 'http:' ? http : https;
    const bodyBuf = Buffer.from(payload, 'utf8');

    const upstream = transport.request({
      hostname: target.hostname,
      port: target.port || (target.protocol === 'http:' ? 80 : 443),
      path: target.pathname + target.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': bodyBuf.length,
        'Authorization': 'Bearer ' + cfg.apiKey,
        'x-api-key': cfg.apiKey,
        'anthropic-version': '2023-06-01'
      }
    }, (up) => {
      const chunks = [];
      up.on('data', c => chunks.push(c));
      up.on('end', () => {
        const raw = Buffer.concat(chunks).toString('utf8');
        let parsed;
        try { parsed = JSON.parse(raw); }
        catch (e) { reject(new Error('上游返回非 JSON（HTTP ' + up.statusCode + '）: ' + raw.slice(0, 300))); return; }

        if (parsed.error) {
          reject(new Error('模型接口报错: ' + (parsed.error.message || JSON.stringify(parsed.error))));
          return;
        }
        const text = Array.isArray(parsed.content)
          ? parsed.content.filter(b => b.type === 'text').map(b => b.text).join('')
          : '';
        if (!text) { reject(new Error('模型返回空内容: ' + raw.slice(0, 300))); return; }
        resolve(text);
      });
    });

    upstream.on('error', err => reject(new Error('连接模型接口失败: ' + err.message)));
    upstream.setTimeout(180000, () => {
      upstream.destroy();
      reject(new Error('模型接口超时（180 秒）'));
    });
    upstream.end(bodyBuf);
  });
}

function handleAiChat(req, res) {
  const chunks = [];
  let size = 0;
  req.on('data', chunk => {
    size += chunk.length;
    if (size > 5 * 1024 * 1024) { req.destroy(); return; }
    chunks.push(chunk);
  });
  req.on('end', async () => {
    const reply = (status, obj) => {
      res.writeHead(status, {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-store'
      });
      res.end(JSON.stringify(obj));
    };
    try {
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      if (!Array.isArray(body.messages) || body.messages.length === 0) {
        return reply(400, { error: '缺少 messages' });
      }
      const text = await callModel(body.messages, body.system, body.maxTokens);
      console.log('200 /api/chat → ' + text.length + ' 字');
      reply(200, { text });
    } catch (e) {
      console.error('[AI] /api/chat 失败:', e.message);
      reply(502, { error: e.message });
    }
  });
}

// 供前端探测 AI 是否可用（不泄露 key）
function handleAiStatus(req, res) {
  const cfg = loadAiConfig();
  res.writeHead(200, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store'
  });
  res.end(JSON.stringify({
    ready: Boolean(cfg.baseUrl && cfg.apiKey),
    model: cfg.model,
    baseUrl: cfg.baseUrl
  }));
}


function handleExportExcel(req, res) {
  let body = '';
  req.on('data', chunk => {
    body += chunk.toString();
    if (body.length > 10 * 1024 * 1024) { // 10MB limit
      req.connection.destroy();
      return;
    }
  });

  req.on('end', () => {
    try {
      const data = JSON.parse(body);
      const { filename, content, htmlFilename, htmlContent } = data;

      if (!filename || !content) {
        res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify({ error: '缺少 filename 或 content' }));
        return;
      }

      // 保存到指定目录
      const archiveDir = path.resolve(__dirname, '..', '时间管理助手归档文件');
      if (!fs.existsSync(archiveDir)) {
        fs.mkdirSync(archiveDir, { recursive: true });
      }

      const filePath = path.join(archiveDir, filename);
      const buffer = Buffer.from(content, 'base64');

      fs.writeFile(filePath, buffer, (err) => {
        if (err) {
          console.error('保存文件失败:', err);
          res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' });
          res.end(JSON.stringify({ error: '保存文件失败: ' + err.message }));
          return;
        }

        console.log('文件已保存:', filePath);

        // 如果有HTML内容，也保存HTML文件
        if (htmlFilename && htmlContent) {
          const htmlPath = path.join(archiveDir, htmlFilename);
          fs.writeFile(htmlPath, htmlContent, 'utf8', (htmlErr) => {
            if (htmlErr) {
              console.error('保存HTML文件失败:', htmlErr);
            } else {
              console.log('HTML文件已保存:', htmlPath);
            }
          });
        }

        res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify({ success: true, path: filePath }));
      });

    } catch (e) {
      res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ error: '解析请求失败: ' + e.message }));
    }
  });
}

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

  // AI 复盘代理（v2.14.0）
  if (pathname === '/api/chat' && req.method === 'POST') {
    return handleAiChat(req, res);
  }
  if (pathname === '/api/ai-status' && req.method === 'GET') {
    return handleAiStatus(req, res);
  }

  // 导出Excel到指定目录
  if (pathname === '/export-excel' && req.method === 'POST') {
    return handleExportExcel(req, res);
  }

  // CA 下载路由（v2.11.0）
  if (CERT_DOWNLOAD_ALIASES.indexOf(pathname) >= 0) {
    return serveCertDownload(req, res);
  }

  if (pathname === '/' || pathname === '') pathname = '/时间管理助手.html';

  // 安全：绝不通过静态路由吐出 AI 凭证文件
  if (/ai-config\.json$/i.test(pathname)) {
    res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Forbidden');
    return;
  }

  // 特殊处理：允许访问 sync-data 目录（用于周数据对比功能）
  let filePath;
  if (pathname.startsWith('/sync-data/')) {
    const syncDataRoot = path.resolve(__dirname, '..', 'sync-data');
    filePath = path.normalize(path.join(syncDataRoot, pathname.replace('/sync-data/', '')));
    if (!filePath.startsWith(syncDataRoot)) {
      res.writeHead(403); res.end('Forbidden'); return;
    }
  } else {
    filePath = path.normalize(path.join(ROOT, pathname));
    if (!filePath.startsWith(ROOT)) {
      res.writeHead(403); res.end('Forbidden'); return;
    }
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
      // 允许 Service Worker Cache API 缓存（no-store 会导致 iOS Safari Cache API 拒绝存储）
      'Cache-Control': 'public, max-age=0'
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
