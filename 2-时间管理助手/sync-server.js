// 时间管理助手 · 本地同步服务（阶段 3.1 同步骨架）
//
// 设计原则：
//   - 仅依赖 Node.js 内置模块（http / fs / path / os / url / crypto），零 npm 依赖。
//   - 端口 6372（与静态服务 6371 邻位，便于记忆）。
//   - 端点（3.1 范围）：
//       GET  /info                          ← 主机自我描述
//       GET  /weeks                         ← 列出已存在的 (year, week)
//       GET  /weeks/:year/:week             ← 拉整周快照
//       POST /weeks/:year/:week/changes     ← 上传变更（merge 写回）
//   - 持久化目录：./sync-data/<year>/w<NN>.json + ./sync-data/meta.json
//   - 写文件统一 "先写 .tmp 再 rename" 原子化。
//   - 3.1 阶段不强制鉴权（开放局域网任意访问，由网络隔离兜底）。
//   - 3.3 / 3.4 / 3.5 见需求文档 §20.7 / §20.10。
//
// 用法：
//   node sync-server.js              # 默认端口 6372
//   node sync-server.js 6373         # 指定端口

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const os = require('os');
const url = require('url');
const crypto = require('crypto');

const PROTOCOL_VERSION = 1;
const PORT = parseInt(process.argv[2], 10) || 6372;
const HTTPS_PORT = parseInt(process.argv[3], 10) || 6444;
const PROJECT_ROOT = __dirname;
const DATA_DIR = path.join(PROJECT_ROOT, 'sync-data');
const META_FILE = path.join(DATA_DIR, 'meta.json');
const CERT_DIR = path.join(PROJECT_ROOT, 'certs');
const CERT_PATH = path.join(CERT_DIR, 'leaf-cert-chain.pem'); // v2.11.0 CA-leaf chain
const KEY_PATH  = path.join(CERT_DIR, 'leaf-key.pem');
const MAX_BODY = 5 * 1024 * 1024; // 5 MB

// -------- 工具：目录/文件 --------

function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

function loadMeta() {
  ensureDataDir();
  try {
    const raw = fs.readFileSync(META_FILE, 'utf8');
    const meta = JSON.parse(raw);
    if (!meta.hostId) meta.hostId = crypto.randomUUID();
    meta.protocolVersion = PROTOCOL_VERSION;
    meta.lastBootAt = Date.now();
    writeAtomic(META_FILE, JSON.stringify(meta, null, 2));
    return meta;
  } catch (e) {
    const meta = {
      hostId: crypto.randomUUID(),
      protocolVersion: PROTOCOL_VERSION,
      createdAt: Date.now(),
      lastBootAt: Date.now()
    };
    writeAtomic(META_FILE, JSON.stringify(meta, null, 2));
    return meta;
  }
}

function writeAtomic(filePath, content) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  const tmp = filePath + '.tmp';
  fs.writeFileSync(tmp, content, 'utf8');
  fs.renameSync(tmp, filePath);
}

// -------- 设备管理（v2.13.0） --------

const DEVICES_FILE = path.join(DATA_DIR, 'devices.json');
// 临时配对码（内存存储，服务重启后清空，有效期 5 分钟）
const pairCodes = new Map(); // code → { deviceName, createdAt, expiresAt }
// lastSyncAt 写盘节流（token → 上次写盘时间戳，内存存储）
const lastSyncFlushMap = new Map();

function loadDevices() {
  ensureDataDir();
  try {
    if (fs.existsSync(DEVICES_FILE)) return JSON.parse(fs.readFileSync(DEVICES_FILE, 'utf8'));
  } catch (e) { console.error('读取 devices.json 失败:', e.message); }
  return { devices: [] };
}

function saveDevices(data) {
  writeAtomic(DEVICES_FILE, JSON.stringify(data, null, 2));
}

function findDeviceByToken(token) {
  const data = loadDevices();
  return data.devices.find(d => d.token === token);
}

// v2.13.0：鉴权——除 /pair/start /pair/confirm / /info（探测用）外，验证 X-Device-Token
function authenticate(req, meta) {
  const parsed = url.parse(req.url, true);
  const p = parsed.pathname;
  // 公开端点（无需令牌）
  if (p === '/pair/start' || p === '/pair/confirm') return true;
  if (req.method === 'GET' && (p === '/' || p === '/info')) return true;
  // 本机请求免鉴权（桌面浏览器从 127.0.0.1 / localhost 访问）
  const remoteIP = (req.socket && req.socket.remoteAddress) || '';
  if (remoteIP === '127.0.0.1' || remoteIP === '::1' || remoteIP === '::ffff:127.0.0.1') return true;
  // v2.13.0 过渡期：若无已绑定设备，允许无令牌访问（首次部署）
  const data = loadDevices();
  if (data.devices.length === 0) return true;
  // 验证 X-Device-Token
  const token = req.headers['x-device-token'];
  if (!token) return false;
  const dev = findDeviceByToken(token);
  if (!dev) return false;
  // 更新最后同步时间（节流：30s 内不重复写盘，用独立 Map 避免泄漏到 JSON）
  const now = Date.now();
  const lastFlush = lastSyncFlushMap.get(token) || 0;
  if (now - lastFlush > 30000) {
    dev.lastSyncAt = now;
    lastSyncFlushMap.set(token, now);
    saveDevices(data);
  }
  return true;
}

function generatePairCode() {
  const code = String(Math.floor(100000 + Math.random() * 900000)); // 6 位数字
  const now = Date.now();
  pairCodes.set(code, { createdAt: now, expiresAt: now + 5 * 60 * 1000 });
  // 清理过期码
  for (const [k, v] of pairCodes) {
    if (v.expiresAt < now) pairCodes.delete(k);
  }
  return code;
}

function validatePairCode(code) {
  const entry = pairCodes.get(code);
  if (!entry) return false;
  if (entry.expiresAt < Date.now()) { pairCodes.delete(code); return false; }
  return true;
}

function addDevice(deviceName, platform) {
  const data = loadDevices();
  if (data.devices.length >= 4) return null; // 最多 4 台
  const device = {
    id: crypto.randomUUID(),
    name: deviceName || '未知设备',
    platform: platform || 'unknown',
    token: 'tok-' + crypto.randomBytes(16).toString('hex'),
    boundAt: Date.now(),
    lastSyncAt: Date.now()
  };
  data.devices.push(device);
  saveDevices(data);
  return device;
}

function weekDir(year) {
  return path.join(DATA_DIR, String(year));
}

function weekFile(year, week) {
  return path.join(weekDir(year), `w${String(week).padStart(2, '0')}.json`);
}

function readWeek(year, week) {
  const file = weekFile(year, week);
  if (!fs.existsSync(file)) return null;
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (e) {
    console.error(`读取损坏 ${file}: ${e.message}`);
    return null;
  }
}

function emptyWeek(year, week) {
  return {
    year,
    week,
    config: null,
    cells: {},
    keyitems: {},
    keyitemStatus: {},
    review: null,
    archived: false,
    archivedAt: null,
    weekUpdatedAt: 0
  };
}

function writeWeek(year, week, data) {
  writeAtomic(weekFile(year, week), JSON.stringify(data, null, 2));
}

function listWeeks() {
  ensureDataDir();
  const out = [];
  if (!fs.existsSync(DATA_DIR)) return out;
  for (const yearName of fs.readdirSync(DATA_DIR)) {
    if (!/^\d{4}$/.test(yearName)) continue;
    const yPath = path.join(DATA_DIR, yearName);
    if (!fs.statSync(yPath).isDirectory()) continue;
    for (const fn of fs.readdirSync(yPath)) {
      const m = /^w(\d{1,2})\.json$/i.exec(fn);
      if (!m) continue;
      const fp = path.join(yPath, fn);
      const stat = fs.statSync(fp);
      const data = readWeek(parseInt(yearName, 10), parseInt(m[1], 10));
      out.push({
        year: parseInt(yearName, 10),
        week: parseInt(m[1], 10),
        weekUpdatedAt: (data && data.weekUpdatedAt) || stat.mtimeMs,
        archived: !!(data && data.archived),
        size: stat.size
      });
    }
  }
  out.sort((a, b) => a.year - b.year || a.week - b.week);
  return out;
}

// -------- 工具：网络 --------

function getLanIPs() {
  const ifaces = os.networkInterfaces();
  const ips = [];
  for (const name of Object.keys(ifaces)) {
    for (const ifc of ifaces[name]) {
      if (ifc.family === 'IPv4' && !ifc.internal) {
        ips.push({ ip: ifc.address, iface: name });
      }
    }
  }
  return ips;
}

// -------- 合并逻辑（last-write-wins，按粒度比较 updatedAt）--------

function mergeChanges(existing, changes) {
  const now = Date.now();
  const out = existing || emptyWeek(changes.year, changes.week);
  out.year = changes.year;
  out.week = changes.week;

  // config: 最新覆盖（3.4 后客户端层面强制 Windows 才能写）
  if (changes.config && typeof changes.config === 'object') {
    const newAt = changes.config.updatedAt || now;
    const oldAt = (out.config && out.config.updatedAt) || 0;
    if (newAt >= oldAt) out.config = changes.config;
  }

  // cells: 按单元格 last-write-wins
  if (changes.cells && typeof changes.cells === 'object') {
    out.cells = out.cells || {};
    for (const [k, v] of Object.entries(changes.cells)) {
      if (!v || typeof v !== 'object') continue;
      const existingCell = out.cells[k];
      const newAt = v.updatedAt || now;
      const oldAt = (existingCell && existingCell.updatedAt) || 0;
      if (!existingCell || newAt >= oldAt) {
        out.cells[k] = { ...v, updatedAt: newAt };
      }
    }
  }

  // keyitems: 按 key（日期|行名）last-write-wins
  if (changes.keyitems && typeof changes.keyitems === 'object') {
    out.keyitems = out.keyitems || {};
    for (const [k, v] of Object.entries(changes.keyitems)) {
      if (!v || typeof v !== 'object') continue;
      const existingItem = out.keyitems[k];
      const newAt = v.updatedAt || now;
      const oldAt = (existingItem && existingItem.updatedAt) || 0;
      if (!existingItem || newAt >= oldAt) {
        out.keyitems[k] = { ...v, updatedAt: newAt };
      }
    }
  }

  // keyitemStatus: 按 key last-write-wins（v2.13.1 新增）
  if (changes.keyitemStatus && typeof changes.keyitemStatus === 'object') {
    out.keyitemStatus = out.keyitemStatus || {};
    for (const [k, v] of Object.entries(changes.keyitemStatus)) {
      if (!v || typeof v !== 'object') continue;
      const existingSt = out.keyitemStatus[k];
      const newAt = v.updatedAt || now;
      const oldAt = (existingSt && existingSt.updatedAt) || 0;
      if (!existingSt || newAt >= oldAt) {
        out.keyitemStatus[k] = { ...v, updatedAt: newAt };
      }
    }
  }

  // review: 整体 last-write-wins
  if (changes.review && typeof changes.review === 'object') {
    const newAt = changes.review.updatedAt || now;
    const oldAt = (out.review && out.review.updatedAt) || 0;
    if (newAt >= oldAt) out.review = changes.review;
  }

  // archived: 一旦 true 即粘连，不能回退
  if (changes.archived === true && !out.archived) {
    out.archived = true;
    out.archivedAt = changes.archivedAt || now;
  }

  out.weekUpdatedAt = Math.max(out.weekUpdatedAt || 0, now);
  return out;
}

// -------- HTTP --------

function json(res, status, data) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(data, null, 2));
}

function text(res, status, body, contentType) {
  res.writeHead(status, { 'Content-Type': contentType || 'text/plain; charset=utf-8' });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    let size = 0;
    req.on('data', chunk => {
      size += chunk.length;
      if (size > MAX_BODY) {
        reject(new Error('payload too large'));
        req.destroy();
        return;
      }
      data += chunk;
    });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

function setCors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Device-Token');
  res.setHeader('Cache-Control', 'no-store');
}

async function route(req, res, meta) {
  setCors(res);
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const parsed = url.parse(req.url, true);
  const pathname = parsed.pathname;

  // v2.13.0：鉴权（除公开端点外）
  if (!authenticate(req, meta)) {
    return json(res, 401, { error: 'unauthorized', hint: '请通过扫码绑定设备获取令牌' });
  }

  // GET /
  if (req.method === 'GET' && pathname === '/') {
    const lan = getLanIPs().map(x => `<li>http://${x.ip}:${PORT}/ <small>(${x.iface})</small></li>`).join('');
    return text(res, 200, `<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>时间管理助手 · 同步服务</title></head>
<body style="font-family:system-ui,sans-serif;max-width:720px;margin:30px auto;padding:0 16px;color:#222">
  <h1>时间管理助手 · 同步服务</h1>
  <p>主机：<b>${os.hostname()}</b> · 端口：<b>${PORT}</b> · 协议：v${PROTOCOL_VERSION}</p>
  <p>HostID：<code>${meta.hostId}</code></p>
  <p>数据目录：<code>${DATA_DIR}</code></p>
  <h3>端点（GET）</h3>
  <ul>
    <li><a href="/info">/info</a></li>
    <li><a href="/weeks">/weeks</a></li>
    <li>/weeks/:year/:week</li>
    <li>POST /weeks/:year/:week/changes</li>
  </ul>
  <h3>局域网访问</h3>
  <ul>${lan || '<li>未发现可用网卡</li>'}</ul>
</body></html>`, 'text/html; charset=utf-8');
  }

  // GET /info
  if (req.method === 'GET' && pathname === '/info') {
    return json(res, 200, {
      hostname: os.hostname(),
      hostnameLocal: os.hostname() + '.local',
      lanIPs: getLanIPs(),
      port: PORT,
      protocolVersion: PROTOCOL_VERSION,
      hostId: meta.hostId,
      bootAt: meta.lastBootAt
    });
  }

  // GET /weeks
  if (req.method === 'GET' && pathname === '/weeks') {
    return json(res, 200, { weeks: listWeeks() });
  }

  // GET /weeks/:year/:week
  let m = /^\/weeks\/(\d{4})\/(\d{1,2})$/.exec(pathname);
  if (m && req.method === 'GET') {
    const year = parseInt(m[1], 10);
    const week = parseInt(m[2], 10);
    const data = readWeek(year, week);
    if (!data) return json(res, 404, { error: 'week not found', year, week });
    return json(res, 200, data);
  }

  // POST /weeks/:year/:week/changes
  m = /^\/weeks\/(\d{4})\/(\d{1,2})\/changes$/.exec(pathname);
  if (m && req.method === 'POST') {
    const year = parseInt(m[1], 10);
    const week = parseInt(m[2], 10);
    let body;
    try {
      body = await readBody(req);
    } catch (e) {
      return json(res, 413, { error: e.message });
    }
    let changes;
    try {
      changes = JSON.parse(body || '{}');
    } catch (e) {
      return json(res, 400, { error: 'invalid JSON', detail: e.message });
    }
    if (typeof changes !== 'object' || changes === null || Array.isArray(changes)) {
      return json(res, 400, { error: 'changes must be a JSON object' });
    }
    changes.year = year;
    changes.week = week;
    const existing = readWeek(year, week);
    const merged = mergeChanges(existing, changes);
    try {
      writeWeek(year, week, merged);
    } catch (e) {
      return json(res, 500, { error: 'write failed', detail: e.message });
    }
    // v2.12.0：广播变更到所有 WebSocket 客户端
    wsBroadcast({
      type: 'week-changed',
      year,
      week,
      weekUpdatedAt: merged.weekUpdatedAt
    });
    return json(res, 200, {
      ok: true,
      year,
      week,
      weekUpdatedAt: merged.weekUpdatedAt,
      cellsCount: Object.keys(merged.cells || {}).length,
      keyitemsCount: Object.keys(merged.keyitems || {}).length,
      keyitemStatusCount: Object.keys(merged.keyitemStatus || {}).length,
      hasReview: !!merged.review,
      hasConfig: !!merged.config,
      archived: !!merged.archived
    });
  }

  // v2.13.0：配对与设备管理端点

  // POST /pair/start
  if (req.method === 'POST' && pathname === '/pair/start') {
    const code = generatePairCode();
    console.log('[PAIR] 生成配对码:', code);
    return json(res, 200, {
      pairCode: code,
      expiresAt: pairCodes.get(code).expiresAt,
      hostname: os.hostname(),
      lanIPs: getLanIPs(),
      port: PORT,
      httpsPort: fs.existsSync(CERT_PATH) ? HTTPS_PORT : null
    });
  }

  // POST /pair/confirm
  if (req.method === 'POST' && pathname === '/pair/confirm') {
    let body;
    try { body = await readBody(req); } catch (e) { return json(res, 413, { error: e.message }); }
    let params;
    try { params = JSON.parse(body || '{}'); } catch (e) { return json(res, 400, { error: 'invalid JSON' }); }
    if (!params.code || !validatePairCode(params.code)) {
      return json(res, 400, { error: '配对码无效或已过期' });
    }
    const device = addDevice(params.deviceName || '手机', params.platform || 'unknown');
    if (!device) {
      return json(res, 400, { error: '设备数量已达上限（4 台）' });
    }
    pairCodes.delete(params.code);
    console.log('[PAIR] 设备已绑定:', device.name, '(' + device.platform + ')', 'token:', device.token.slice(0, 8) + '...');
    return json(res, 200, { deviceId: device.id, token: device.token, name: device.name });
  }

  // POST /pair/register-desktop（仅无设备时允许桌面自注册）
  if (req.method === 'POST' && pathname === '/pair/register-desktop') {
    const data = loadDevices();
    if (data.devices.length > 0) return json(res, 400, { error: '已有绑定设备，桌面请使用主机令牌' });
    let body;
    try { body = await readBody(req); } catch (e) { return json(res, 413, { error: e.message }); }
    let params;
    try { params = JSON.parse(body || '{}'); } catch (e) { params = {}; }
    const device = addDevice(params.deviceName || os.hostname(), 'windows');
    if (!device) return json(res, 500, { error: '注册失败' });
    console.log('[PAIR] 桌面设备已自注册:', device.name, 'token:', device.token.slice(0, 8) + '...');
    return json(res, 200, { deviceId: device.id, token: device.token, name: device.name });
  }

  // GET /devices
  if (req.method === 'GET' && pathname === '/devices') {
    const data = loadDevices();
    return json(res, 200, data.devices.map(d => ({
      id: d.id, name: d.name, platform: d.platform,
      boundAt: d.boundAt, lastSyncAt: d.lastSyncAt
    })));
  }

  // DELETE /devices/:id
  let dm = /^\/devices\/([a-f0-9-]+)$/.exec(pathname);
  if (dm && req.method === 'DELETE') {
    const devId = dm[1];
    const data = loadDevices();
    const idx = data.devices.findIndex(d => d.id === devId);
    if (idx < 0) return json(res, 404, { error: 'device not found' });
    const removed = data.devices.splice(idx, 1)[0];
    saveDevices(data);
    console.log('[PAIR] 设备已解绑:', removed.name, '(' + removed.platform + ')');
    return json(res, 200, { ok: true, removed: { id: removed.id, name: removed.name } });
  }

  return json(res, 404, { error: 'not found', method: req.method, path: pathname });
}

// -------- 启动 --------

const meta = loadMeta();

// ======== WebSocket（v2.12.0 / 阶段 3.3）========
//
// 自实现 RFC6455 WebSocket 握手与帧编解码，零 npm 依赖。
// 客户端连接 /events 后，服务端在收到 POST /changes 变更时广播到所有客户端。
//
// 帧格式：文本帧，payload 为 JSON。
// Ping/pong：每 30s 服务端发送 ping，客户端应回复 pong。
// 连接管理：客户端集合 + 断开自动清理。

const WS_GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';
const WS_CLIENTS = new Set();
let wsPingTimer = null;

function wsAcceptKey(key) {
  return crypto.createHash('sha1').update(key + WS_GUID).digest('base64');
}

function wsEncodeFrame(payload) {
  const buf = Buffer.from(payload, 'utf8');
  const len = buf.length;
  let header;
  if (len < 126) {
    header = Buffer.alloc(2);
    header[0] = 0x81; // FIN + text opcode
    header[1] = len;
  } else if (len < 65536) {
    header = Buffer.alloc(4);
    header[0] = 0x81;
    header[1] = 126;
    header.writeUInt16BE(len, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = 0x81;
    header[1] = 127;
    header.writeBigUInt64BE(BigInt(len), 2);
  }
  return Buffer.concat([header, buf]);
}

function wsDecodeFrame(data) {
  if (data.length < 2) return null;
  const opcode = data[0] & 0x0f;
  const masked = (data[1] & 0x80) !== 0;
  let len = data[1] & 0x7f;
  let offset = 2;
  if (len === 126) { len = data.readUInt16BE(2); offset = 4; }
  else if (len === 127) { len = Number(data.readBigUInt64BE(2)); offset = 10; }
  if (data.length < offset + len) return null;
  let payload;
  if (masked) {
    const mask = data.slice(offset, offset + 4);
    payload = Buffer.alloc(len);
    for (let i = 0; i < len; i++) payload[i] = data[offset + 4 + i] ^ mask[i % 4];
  } else {
    payload = data.slice(offset, offset + len);
  }
  return { opcode, payload: payload.toString('utf8'), totalLen: offset + (masked ? 4 : 0) + len };
}

function wsBroadcast(msg) {
  const payload = JSON.stringify(msg);
  const frame = wsEncodeFrame(payload);
  for (const sock of WS_CLIENTS) {
    try { sock.write(frame); } catch (e) { WS_CLIENTS.delete(sock); }
  }
}

function wsHandleUpgrade(req, socket, head) {
  const parsed = url.parse(req.url, true);
  if (parsed.pathname !== '/events') {
    socket.destroy();
    return;
  }
  const key = req.headers['sec-websocket-key'];
  if (!key) { socket.destroy(); return; }

  const accept = wsAcceptKey(key);
  socket.write(
    'HTTP/1.1 101 Switching Protocols\r\n' +
    'Upgrade: websocket\r\n' +
    'Connection: Upgrade\r\n' +
    'Sec-WebSocket-Accept: ' + accept + '\r\n' +
    '\r\n'
  );

  WS_CLIENTS.add(socket);
  console.log(`[WSS] 客户端已连接（共 ${WS_CLIENTS.size} 个）`);

  let buf = Buffer.alloc(0);
  socket.on('data', (chunk) => {
    buf = Buffer.concat([buf, chunk]);
    while (buf.length > 0) {
      const frame = wsDecodeFrame(buf);
      if (!frame) break;
      buf = buf.slice(frame.totalLen);
      if (frame.opcode === 0x8) { // close
        socket.destroy();
        return;
      }
      if (frame.opcode === 0x9) { // ping → pong
        const pong = Buffer.alloc(2);
        pong[0] = 0x8A; pong[1] = 0;
        try { socket.write(pong); } catch (e) {}
        continue;
      }
      if (frame.opcode === 0xA) continue; // pong → ignore
      // text frame: ignore (客户端不主动发消息)
    }
  });

  socket.on('close', () => {
    WS_CLIENTS.delete(socket);
    console.log(`[WSS] 客户端已断开（共 ${WS_CLIENTS.size} 个）`);
  });
  socket.on('error', () => {
    WS_CLIENTS.delete(socket);
    socket.destroy();
  });
}

function wsStartPing() {
  if (wsPingTimer) return;
  wsPingTimer = setInterval(() => {
    if (WS_CLIENTS.size === 0) return;
    const ping = Buffer.alloc(2);
    ping[0] = 0x89; ping[1] = 0;
    for (const sock of WS_CLIENTS) {
      try { sock.write(ping); } catch (e) { WS_CLIENTS.delete(sock); }
    }
  }, 30000);
}

// ======== HTTP 处理 ========

function createRequestHandler(meta) {
  return (req, res) => {
    const t0 = Date.now();
    route(req, res, meta).catch(err => {
      console.error('[ERROR]', req.method, req.url, err);
      if (!res.headersSent) json(res, 500, { error: String(err) });
    }).finally(() => {
      console.log(`${req.method} ${req.url} → ${res.statusCode} ${Date.now() - t0}ms`);
    });
  };
}

function startServer(server, port, label) {
  server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.error(`[${label}] 端口 ${port} 已被占用。`);
    } else {
      console.error(`[${label}]`, err);
    }
  });
  // v2.12.0：监听 upgrade 事件以处理 WebSocket 连接
  server.on('upgrade', (req, socket, head) => {
    wsHandleUpgrade(req, socket, head);
  });
  server.listen(port, '0.0.0.0', () => {
    console.log(` [${label}] 监听 0.0.0.0:${port}`);
  });
}

const handler = createRequestHandler(meta);

console.log('================================================');
console.log(' 时间管理助手 · 同步服务（v2.13.0）');
console.log(` 主机: ${os.hostname()}  HostID: ${meta.hostId}`);
console.log(` 协议: v${PROTOCOL_VERSION}  数据目录: ${DATA_DIR}`);
console.log('');

// === HTTP 6372（开发/局域网兼容） ===
startServer(http.createServer(handler), PORT, 'HTTP ');
console.log(`   本机访问:      http://127.0.0.1:${PORT}/`);
for (const x of getLanIPs()) {
  console.log(`   LAN 访问:      http://${x.ip}:${PORT}/  (${x.iface})`);
}
console.log('');

// === HTTPS 6444（iPhone 通过同源 HTTPS 拉同步数据，避开 mixed content） ===
if (fs.existsSync(CERT_PATH) && fs.existsSync(KEY_PATH)) {
  const httpsOptions = {
    cert: fs.readFileSync(CERT_PATH),
    key: fs.readFileSync(KEY_PATH)
  };
  startServer(https.createServer(httpsOptions, handler), HTTPS_PORT, 'HTTPS');
  console.log(`   本机访问:      https://127.0.0.1:${HTTPS_PORT}/`);
  for (const x of getLanIPs()) {
    console.log(`   LAN 访问:      https://${x.ip}:${HTTPS_PORT}/  (${x.iface})`);
  }
} else {
  console.log(' [HTTPS] 未找到证书，跳过。');
  console.log('         若需 iPhone HTTPS：cd tools/gen-cert && npm install && node gen-cert.js');
}
console.log('');

// v2.12.0：启动 WebSocket ping 定时器
wsStartPing();

console.log(' 端点:');
console.log('   GET  /info');
console.log('   GET  /weeks');
console.log('   GET  /weeks/:year/:week');
console.log('   POST /weeks/:year/:week/changes');
console.log('   WSS  /events（实时推送变更）');
console.log('   POST /pair/start /pair/confirm（扫码绑定）');
console.log('   GET  /devices');
console.log('   DELETE /devices/:id');
console.log('');
console.log(' 按 Ctrl+C 停止');
console.log('================================================');
