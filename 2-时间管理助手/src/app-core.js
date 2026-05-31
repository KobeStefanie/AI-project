// 时间管理助手 - 共享核心层
// 抽出自 app.js（v2.7.0）。包含常量、ISO 周计算、LocalStorage 存取、统计计算。
// 通过 window.AppCore 对外暴露，由 app.js 与未来的同步层共用。
(function (global) {
'use strict';

var STORAGE_PREFIX = 'tm_';
var WEEKDAYS = ['周一','周二','周三','周四','周五','周六','周天'];
var KEY_ROWS = ['第一件事','第二件事','第三件事','小确幸','关键词'];
// v2.13.1：前三件事的评价状态（白框=未评, 绿✓=已完成, 蓝O=持续, 红=未完成）
var KEY_ITEM_STATUS_ROWS = ['第一件事','第二件事','第三件事'];
// 循环顺序：无状态(白框) → done(绿✓已完成) → ongoing(蓝O持续) → todo(红未完成) → 无状态
var KEY_ITEM_STATUS_VALUES = ['done','ongoing','todo'];
// 给定起始时间（HH:MM 字符串），生成 34 个连续 30 分钟时段的字符串数组。
// 示例：buildTimeSlots('7:00') → ['7:00-7:30', '7:30-8:00', ..., '23:30-0:00']
// 输出与历史一致：小时不补零，分钟两位（'7:00-7:30' 而非 '07:00-07:30'）。
function buildTimeSlots(startTime) {
  var parts = String(startTime || '7:00').split(':');
  var sm = parseInt(parts[0], 10) * 60 + parseInt(parts[1] || '0', 10);
  if (isNaN(sm)) sm = 7 * 60;
  sm = ((sm % 1440) + 1440) % 1440;
  function fmt(min) {
    var m = ((min % 1440) + 1440) % 1440;
    var hh = Math.floor(m / 60);
    var mm = m % 60;
    return hh + ':' + (mm < 10 ? '0' + mm : '' + mm);
  }
  var slots = [];
  for (var i = 0; i < 34; i++) {
    var s = sm + i * 30;
    slots.push(fmt(s) + '-' + fmt(s + 30));
  }
  return slots;
}

// 默认时间表（起始 7:00；对应 7:00-0:00 共 17 小时 = 34 半小时格）
var TIME_SLOTS = buildTimeSlots('7:00');

var DEFAULT_CONFIG = {
  qwNames: ['新媒体运营','心理咨询','注会变现','读书','投资','造音师','其他'],
  gfpNames: ['演出','运动','约会','旅行','游戏','小资','其他'],
  procNames: ['睡懒觉','刷手机','拖延','无效/低效社交','其他'],
  standard: 12,
  startTime: '7:00'
};

function getISOWeek(date) {
  var d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  var yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  var weekNo = Math.ceil(((d - yearStart) / 86400000 + 1) / 7);
  return { year: d.getUTCFullYear(), week: weekNo };
}

function getWeekDates(year, week) {
  var jan4 = new Date(Date.UTC(year, 0, 4));
  var dow = jan4.getUTCDay() || 7;
  var monday = new Date(jan4);
  monday.setUTCDate(jan4.getUTCDate() - dow + 1 + (week - 1) * 7);
  var dates = [];
  for (var i = 0; i < 7; i++) {
    var d = new Date(monday);
    d.setUTCDate(monday.getUTCDate() + i);
    dates.push(d);
  }
  return dates;
}

function formatDate(d) {
  return d.getUTCFullYear() + '/' + (d.getUTCMonth() + 1) + '/' + d.getUTCDate();
}

function dateKey(d) { return d.toISOString().slice(0, 10); }

function getPrevWeek(year, week) {
  if (week > 1) return { year: year, week: week - 1 };
  var dec28 = new Date(Date.UTC(year - 1, 11, 28));
  return getISOWeek(dec28);
}

function getNextWeek(year, week) {
  var dec28 = new Date(Date.UTC(year, 11, 28));
  var last = getISOWeek(dec28).week;
  if (week < last) return { year: year, week: week + 1 };
  return { year: year + 1, week: 1 };
}

function sKey(year, week, suffix) { return STORAGE_PREFIX + year + '_w' + week + '_' + suffix; }

// =====【保存事件机制】=====
// save 函数在写入后 emit (year, week, part, prev, next)，syncClient 等模块可订阅
// part 取值：'cells' | 'keyitems' | 'review' | 'config' | 'archived'
var _saveListeners = [];
function onSaveChange(fn) { if (typeof fn === 'function') _saveListeners.push(fn); }
function _emitSaveChange(year, week, part, prev, next) {
  for (var i = 0; i < _saveListeners.length; i++) {
    try { _saveListeners[i](year, week, part, prev, next); }
    catch (e) { if (typeof console !== 'undefined') console.error('[onSaveChange listener]', e); }
  }
}

function getConfig(year, week) {
  var raw = localStorage.getItem(sKey(year, week, 'config'));
  var config = null;
  if (raw) {
    try { config = JSON.parse(raw); } catch (e) {}
  }
  if (!config) {
    var prev = getPrevWeek(year, week);
    var prevRaw = localStorage.getItem(sKey(prev.year, prev.week, 'config'));
    if (prevRaw) { try { config = JSON.parse(prevRaw); } catch (e) {} }
  }
  if (!config) {
    config = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
  }
  // v2.11.2：防御性修复——确保数组长度正确（GFP=7, QW=7, Proc=5）
  if (!Array.isArray(config.qwNames) || config.qwNames.length !== 7) {
    config.qwNames = DEFAULT_CONFIG.qwNames.slice();
  }
  if (!Array.isArray(config.gfpNames) || config.gfpNames.length !== 7) {
    config.gfpNames = DEFAULT_CONFIG.gfpNames.slice();
  }
  if (!Array.isArray(config.procNames) || config.procNames.length !== 5) {
    config.procNames = DEFAULT_CONFIG.procNames.slice();
  }
  if (typeof config.standard !== 'number' || config.standard < 0) {
    config.standard = DEFAULT_CONFIG.standard;
  }
  if (typeof config.startTime !== 'string' || !config.startTime) {
    config.startTime = DEFAULT_CONFIG.startTime;
  }
  return config;
}
function saveConfig(year, week, config) {
  // v2.11.2：防御性修复——确保数组长度正确（GFP=7, QW=7, Proc=5）
  if (config.qwNames && (!Array.isArray(config.qwNames) || config.qwNames.length !== 7)) {
    config.qwNames = DEFAULT_CONFIG.qwNames.slice();
  }
  if (config.gfpNames && (!Array.isArray(config.gfpNames) || config.gfpNames.length !== 7)) {
    config.gfpNames = DEFAULT_CONFIG.gfpNames.slice();
  }
  if (config.procNames && (!Array.isArray(config.procNames) || config.procNames.length !== 5)) {
    config.procNames = DEFAULT_CONFIG.procNames.slice();
  }
  var prev = null;
  var raw = localStorage.getItem(sKey(year, week, 'config'));
  if (raw) { try { prev = JSON.parse(raw); } catch (e) {} }
  localStorage.setItem(sKey(year, week, 'config'), JSON.stringify(config));
  _emitSaveChange(year, week, 'config', prev, config);
}

function getCells(year, week) {
  var raw = localStorage.getItem(sKey(year, week, 'cells'));
  return raw ? JSON.parse(raw) : {};
}
function saveCells(year, week, cells) {
  var prev = getCells(year, week);
  localStorage.setItem(sKey(year, week, 'cells'), JSON.stringify(cells));
  _emitSaveChange(year, week, 'cells', prev, cells);
}

function getKeyItems(year, week) {
  var raw = localStorage.getItem(sKey(year, week, 'keyitems'));
  return raw ? JSON.parse(raw) : {};
}
function saveKeyItems(year, week, items) {
  var prev = getKeyItems(year, week);
  localStorage.setItem(sKey(year, week, 'keyitems'), JSON.stringify(items));
  _emitSaveChange(year, week, 'keyitems', prev, items);
}

// v2.13.1：前三件事三态状态（按周存储，key 同 keyitems：'日期|第一件事' 等）
function getKeyItemStatus(year, week) {
  var raw = localStorage.getItem(sKey(year, week, 'keyitemStatus'));
  return raw ? JSON.parse(raw) : {};
}
function saveKeyItemStatus(year, week, status) {
  var prev = getKeyItemStatus(year, week);
  localStorage.setItem(sKey(year, week, 'keyitemStatus'), JSON.stringify(status));
  _emitSaveChange(year, week, 'keyitemStatus', prev, status);
}

function getReview(year, week) {
  var raw = localStorage.getItem(sKey(year, week, 'review'));
  return raw ? JSON.parse(raw) : {};
}
function saveReview(year, week, review) {
  var prev = getReview(year, week);
  localStorage.setItem(sKey(year, week, 'review'), JSON.stringify(review));
  _emitSaveChange(year, week, 'review', prev, review);
}

function isArchived(year, week) { return localStorage.getItem(sKey(year, week, 'archived')) === '1'; }
function setArchived(year, week) {
  var prev = isArchived(year, week);
  localStorage.setItem(sKey(year, week, 'archived'), '1');
  _emitSaveChange(year, week, 'archived', prev, true);
}

function getCatClass(code) {
  if (code === null || code === undefined || code === '') return '';
  var n = parseFloat(code);
  if (isNaN(n)) return '';
  var f = Math.floor(n);
  if (f === 0) return 'cat-rest';
  if (f === 1) return 'cat-qw';
  if (f === 2) return 'cat-gfp';
  if (f === 3) return 'cat-proc';
  if (f === 4) return 'cat-mw';
  return '';
}

function calcDailyStats(dayCells, standard) {
  var s = { gfp:0, rest:0, mw:0, qw:0, proc:0, filled:0,
    qwDetail:[0,0,0,0,0,0,0], gfpDetail:[0,0,0,0,0,0,0], procDetail:[0,0,0,0,0] };

  for (var slot in dayCells) {
    var cell = dayCells[slot];
    if (!cell || cell.code === null || cell.code === undefined || cell.code === '') continue;
    var code = parseFloat(cell.code);
    if (isNaN(code)) continue;
    s.filled++;
    var f = Math.floor(code);
    var dec = Math.round((code - f) * 10);
    if (f === 0) s.rest++;
    else if (f === 1) { s.qw++; if (dec >= 1 && dec <= 7) s.qwDetail[dec-1]++; }
    else if (f === 2) { s.gfp++; if (dec >= 1 && dec <= 7) s.gfpDetail[dec-1]++; }
    else if (f === 3) { s.proc++; if (dec >= 1 && dec <= 5) s.procDetail[dec-1]++; }
    else if (f === 4) s.mw++;
  }

  s.earned = s.qw + s.gfp;
  s.lost = s.proc;
  s.balance = s.earned - 2 * s.lost;
  s.validInvest = s.qw + s.gfp;
  s.invalidWaste = s.proc;
  s.potential = s.rest + s.mw;
  s.standard = standard;
  s.available = Math.max(0, s.potential - standard);
  s.checkTotal = s.filled - 34;
  s.checkLoss = s.proc - s.procDetail.reduce(function(a,b){return a+b;}, 0);
  s.checkInvest = (s.qw + s.gfp) - (s.qwDetail.reduce(function(a,b){return a+b;},0) + s.gfpDetail.reduce(function(a,b){return a+b;},0));
  return s;
}

function calcWeeklyStats(cellsByDate, dateKeys, standard) {
  var daily = [];
  for (var i = 0; i < dateKeys.length; i++) {
    daily.push(calcDailyStats(cellsByDate[dateKeys[i]] || {}, standard));
  }
  var t = { gfp:0, rest:0, mw:0, qw:0, proc:0, earned:0, lost:0, balance:0,
    validInvest:0, invalidWaste:0, potential:0, available:0, standard:0,
    qwDetail:[0,0,0,0,0,0,0], gfpDetail:[0,0,0,0,0,0,0], procDetail:[0,0,0,0,0],
    checkTotal:0, checkLoss:0, checkInvest:0 };
  for (var j = 0; j < daily.length; j++) {
    var d = daily[j];
    t.gfp += d.gfp; t.rest += d.rest; t.mw += d.mw; t.qw += d.qw; t.proc += d.proc;
    t.earned += d.earned; t.lost += d.lost; t.balance += d.balance;
    t.validInvest += d.validInvest; t.invalidWaste += d.invalidWaste;
    t.potential += d.potential; t.available += d.available; t.standard += d.standard;
    for (var k = 0; k < 7; k++) t.qwDetail[k] += d.qwDetail[k];
    for (var k2 = 0; k2 < 7; k2++) t.gfpDetail[k2] += d.gfpDetail[k2];
    for (var k3 = 0; k3 < 5; k3++) t.procDetail[k3] += d.procDetail[k3];
    t.checkTotal += d.checkTotal; t.checkLoss += d.checkLoss; t.checkInvest += d.checkInvest;
  }
  return { daily: daily, totals: t };
}

// =====【数据导出 / 导入】=====
// 仅导出周相关数据：tm_YYYY_wNN_(config|cells|keyitems|review|archived)
// 不导出 tm_viewMode 等设备级偏好
var EXPORT_KEY_RE = /^tm_\d{4}_w\d{1,2}_(config|cells|keyitems|keyitemStatus|review|archived)$/;

function exportAllData() {
  var data = {};
  for (var i = 0; i < localStorage.length; i++) {
    var k = localStorage.key(i);
    if (k && EXPORT_KEY_RE.test(k)) {
      data[k] = localStorage.getItem(k);
    }
  }
  return {
    schema: 'time-planner-v1',
    exportedAt: new Date().toISOString(),
    keyCount: Object.keys(data).length,
    data: data
  };
}

// 解析 + 校验 payload，返回摘要：{ ok, weeks: [{year, week, parts:[]}], totalKeys, errors:[] }
function summarizeImport(payload) {
  var result = { ok: false, weeks: [], totalKeys: 0, errors: [] };
  if (!payload || typeof payload !== 'object') {
    result.errors.push('文件内容不是有效 JSON 对象');
    return result;
  }
  if (payload.schema !== 'time-planner-v1') {
    result.errors.push('文件 schema 不是 time-planner-v1，可能是其他工具的导出');
    return result;
  }
  var data = payload.data || {};
  var weekMap = {};
  Object.keys(data).forEach(function(k) {
    var m = /^tm_(\d{4})_w(\d{1,2})_(config|cells|keyitems|keyitemStatus|review|archived)$/.exec(k);
    if (!m) {
      result.errors.push('忽略未识别 key：' + k);
      return;
    }
    var year = parseInt(m[1], 10);
    var week = parseInt(m[2], 10);
    var part = m[3];
    var wkey = year + '-W' + week;
    if (!weekMap[wkey]) weekMap[wkey] = { year: year, week: week, parts: [] };
    weekMap[wkey].parts.push(part);
    result.totalKeys++;
  });
  result.weeks = Object.keys(weekMap).sort().map(function(k) { return weekMap[k]; });
  result.ok = result.totalKeys > 0;
  return result;
}

// 模式：'merge' = 仅按 key 覆盖（不删除本地多余 key）；'replace' = 先删本地全部 tm_YYYY_wNN_*，再写入
function importAllData(payload, mode) {
  if (mode !== 'replace') mode = 'merge';
  var summary = summarizeImport(payload);
  if (!summary.ok) throw new Error(summary.errors.join('; ') || '导入数据为空');

  if (mode === 'replace') {
    // 收集要删的 key（避免边遍历边删）
    var toDel = [];
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i);
      if (k && EXPORT_KEY_RE.test(k)) toDel.push(k);
    }
    toDel.forEach(function(k) { localStorage.removeItem(k); });
  }

  var data = payload.data || {};
  var ok = 0;
  Object.keys(data).forEach(function(k) {
    if (!EXPORT_KEY_RE.test(k)) return;
    localStorage.setItem(k, data[k]);
    ok++;
  });
  return { mode: mode, written: ok, weekCount: summary.weeks.length };
}

// =====【同步客户端】(v2.10.0 / 阶段 3.2)=====
// 与 sync-server.js (端口 6372/6444) 配合，实现：
//   - 保存即推送（debounce 1.5s）
//   - 启动自动拉取
//   - hostname-first 连接（<电脑名>.local → <电脑名> → 缓存 IP）
//   - 服务器 wrap/unwrap：cells/keyitems 在传输层带 updatedAt + updatedBy
//   - v2.11.0：离线变更队列 + online 事件自动 flush（pushWeek 失败保留入队）
//   - v2.12.0：WebSocket 实时推送（WSS /events + 自动重连）
//   - v2.13.0：扫码绑定 + 设备令牌（配对码 + X-Device-Token + 设备管理）
var syncClient = (function() {
  var SYNC_CONFIG_KEY = 'tm_sync_config';
  var DEVICE_ID_KEY = 'tm_device_id';
  var DEVICE_TOKEN_KEY = 'tm_device_token';  // v2.13.0：设备令牌（X-Device-Token）
  // v2.11.0：离线变更队列（仅记录"待推送的 (year,week)"，去重）
  // 设计：失败的 pushWeek 保留入队，online 事件 / 启动时自动 flush。
  var PENDING_QUEUE_KEY = 'tm_sync_pending_queue';
  var DEBOUNCE_MS = 1500;
  var FETCH_TIMEOUT_MS = 4000;

  // v2.11.0：HTTP 走 6372，HTTPS 走 6444（与 sync-server.js 双听端口一致）
  var DEFAULT_HTTP_PORT  = 6372;
  var DEFAULT_HTTPS_PORT = 6444;

  var DEFAULT_SYNC_CONFIG = {
    enabled: false,
    autoHost: true,   // v2.10.1：默认从 window.location 自动推导主机名/端口/协议
    hostname: '',     // 手动覆盖（autoHost=false 时使用），例 'DESKTOP-QRG0JNN'
    port: 0,          // 手动覆盖（autoHost=false 时使用，0 表示按 protocol 自动选）
    protocol: '',     // 手动覆盖（autoHost=false 时使用），'http:' 或 'https:'，空串=自动
    lastIP: '',       // 上次成功连接的 LAN IP（自动从 /info 更新）
    autoSync: true,   // 保存后自动推送
    autoPull: true    // 启动时自动拉取当前周
  };

  var _state = {
    status: 'disabled',   // 'disabled' | 'disconnected' | 'connecting' | 'connected' | 'error'
    lastError: null,
    lastInfo: null,
    lastPushAt: 0,
    lastPullAt: 0,
    pendingPushTimer: null,
    pendingPushWeek: null,
    pendingQueueSize: 0,      // v2.11.0：离线变更队列大小（待推送的周数）
    applyingPullForWeek: null,
    currentWeek: null,      // app.js 通过 setCurrentWeek 通知
    healthCheckTimer: null,      // v2.11.1：周期性心跳检测定时器
    healthCheckInitTimer: null,  // v2.11.2：首次心跳 setTimeout
    ws: null,                    // v2.12.0：WebSocket 连接
    wsReconnectTimer: null,      // v2.12.0：WebSocket 重连定时器
    wsReconnectDelay: 1000       // v2.12.0：当前重连延迟（指数退避）
  };

  var _stateListeners = [];

  // ----- 设备 ID -----

  function getDeviceId() {
    var id = localStorage.getItem(DEVICE_ID_KEY);
    if (id) return id;
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      id = crypto.randomUUID();
    } else {
      id = 'dev-' + Math.random().toString(36).slice(2, 10) + '-' + Date.now().toString(36);
    }
    localStorage.setItem(DEVICE_ID_KEY, id);
    return id;
  }

  // v2.13.0：设备令牌（X-Device-Token）
  function getDeviceToken() {
    return localStorage.getItem(DEVICE_TOKEN_KEY) || '';
  }
  function saveDeviceToken(token) {
    if (token) localStorage.setItem(DEVICE_TOKEN_KEY, token);
    else localStorage.removeItem(DEVICE_TOKEN_KEY);
  }

  // ----- 配置 -----

  function getSyncConfig() {
    try {
      var raw = localStorage.getItem(SYNC_CONFIG_KEY);
      if (!raw) return _assign({}, DEFAULT_SYNC_CONFIG);
      var c = JSON.parse(raw);
      return _assign({}, DEFAULT_SYNC_CONFIG, c);
    } catch (e) {
      return _assign({}, DEFAULT_SYNC_CONFIG);
    }
  }

  function saveSyncConfig(updates) {
    var merged = _assign({}, getSyncConfig(), updates || {});
    localStorage.setItem(SYNC_CONFIG_KEY, JSON.stringify(merged));
    _setState({ status: merged.enabled ? (_state.status === 'disabled' ? 'disconnected' : _state.status) : 'disabled' });
    // v2.11.1：同步关闭时停止心跳；启用时确保心跳在跑
    if (merged.enabled) _startHealthCheck(); else _stopHealthCheck();
    // v2.12.0：同步启用时连接 WebSocket；关闭时断开
    if (merged.enabled) _wsConnect(); else _wsDisconnect();
    return merged;
  }

  function _assign(target) {
    for (var i = 1; i < arguments.length; i++) {
      var src = arguments[i];
      if (!src) continue;
      for (var k in src) if (Object.prototype.hasOwnProperty.call(src, k)) target[k] = src[k];
    }
    return target;
  }

  // ----- 状态 -----

  function getState() {
    return _assign({}, _state, { config: getSyncConfig() });
  }

  function _setState(updates) {
    _assign(_state, updates);
    for (var i = 0; i < _stateListeners.length; i++) {
      try { _stateListeners[i](getState()); } catch (e) {}
    }
  }

  function onStateChange(fn) {
    if (typeof fn !== 'function') return function() {};
    _stateListeners.push(fn);
    return function unsub() {
      var idx = _stateListeners.indexOf(fn);
      if (idx >= 0) _stateListeners.splice(idx, 1);
    };
  }

  // ----- URL 构建（hostname-first 三级 fallback） -----
  //
  // v2.10.1：autoHost=true 时优先用 window.location.hostname + 6372；
  //          autoHost=false 时用用户手动填写的 hostname/port。
  //          缓存 IP 仍作为最后一档 fallback。

  function getEffectiveHost(cfg) {
    cfg = cfg || getSyncConfig();
    if (cfg.autoHost !== false) {
      var auto = detectHostname();
      if (auto) return auto;
    }
    return (cfg.hostname || '').trim();
  }

  // v2.11.0：协议自适应。autoHost=true 时 protocol 跟随 window.location.protocol；
  // 否则用手动 protocol（默认 'http:'）。端口默认值按协议挑选。
  function getEffectiveProtocol(cfg) {
    cfg = cfg || getSyncConfig();
    if (cfg.autoHost !== false) {
      if (typeof window !== 'undefined' && window.location && window.location.protocol) {
        return window.location.protocol; // 'http:' 或 'https:'
      }
      return 'http:';
    }
    return (cfg.protocol === 'https:' || cfg.protocol === 'http:') ? cfg.protocol : 'http:';
  }

  function getEffectivePort(cfg) {
    cfg = cfg || getSyncConfig();
    var proto = getEffectiveProtocol(cfg);
    var defaultPort = (proto === 'https:') ? DEFAULT_HTTPS_PORT : DEFAULT_HTTP_PORT;
    if (cfg.autoHost !== false) return defaultPort;
    var p = parseInt(cfg.port, 10);
    if (p > 0 && p < 65536) return p;
    return defaultPort;
  }

  function buildUrls(cfg) {
    cfg = cfg || getSyncConfig();
    var proto = getEffectiveProtocol(cfg);
    var port = getEffectivePort(cfg);
    var host = getEffectiveHost(cfg);
    // 容错：用户可能粘贴了 http(s)://xxx:port/ 形式
    var hostMatch = host.match(/^(https?):\/\//i);
    if (hostMatch) {
      proto = hostMatch[1].toLowerCase() + ':';
      host = host.replace(/^https?:\/\//i, '');
    }
    host = host.replace(/[\/\?#].*$/, '');
    var pm = host.match(/:(\d+)$/);
    if (pm) { port = parseInt(pm[1], 10) || port; host = host.replace(/:\d+$/, ''); }
    var urls = [];

    function add(h) {
      var u = proto + '//' + h + ':' + port;
      if (urls.indexOf(u) < 0) urls.push(u);
    }

    if (host) {
      if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) {
        // IPv4 字面量
        add(host);
      } else if (/\.local$/i.test(host)) {
        add(host);
      } else {
        // 普通主机名 → 优先 .local（mDNS），再裸主机名（NetBIOS）
        add(host + '.local');
        add(host);
      }
    }
    // lastIP fallback（注意 HTTPS 场景下证书需包含该 IP 才能使用；自签证书已覆盖当前 IP）
    if (cfg.lastIP) add(cfg.lastIP);
    return urls;
  }

  // ----- 带超时的 fetch + 多 URL fallback -----

  function _fetchWithTimeout(url, options, ms) {
    options = options || {};
    options.cache = 'no-store';
    // v2.13.0：附加设备令牌
    var token = getDeviceToken();
    if (token) {
      options.headers = options.headers || {};
      if (typeof options.headers === 'object' && !options.headers['X-Device-Token']) {
        options.headers['X-Device-Token'] = token;
      }
    }
    return new Promise(function(resolve, reject) {
      var controller = (typeof AbortController !== 'undefined') ? new AbortController() : null;
      if (controller) options.signal = controller.signal;
      var timer = setTimeout(function() {
        if (controller) controller.abort();
        reject(new Error('timeout'));
      }, ms || FETCH_TIMEOUT_MS);
      fetch(url, options).then(function(res) {
        clearTimeout(timer);
        resolve(res);
      }).catch(function(err) {
        clearTimeout(timer);
        reject(err);
      });
    });
  }

  function _tryFetch(path, options) {
    var cfg = getSyncConfig();
    var urls = buildUrls(cfg);
    if (urls.length === 0) return Promise.reject(new Error('未配置同步主机；请到同步面板填写电脑名'));

    var i = 0, lastErr = null;
    function attempt() {
      if (i >= urls.length) return Promise.reject(lastErr || new Error('全部地址连接失败'));
      var base = urls[i++];
      return _fetchWithTimeout(base + path, options).then(function(res) {
        if (!res.ok) {
          // 4xx 当作业务错误抛出（不再尝试下一个 URL，避免误重试）
          if (res.status >= 400 && res.status < 500) {
            return res.text().then(function(t) { throw new Error('HTTP ' + res.status + (t ? ': ' + t.slice(0, 200) : '')); });
          }
          throw new Error('HTTP ' + res.status);
        }
        return { res: res, base: base };
      }).catch(function(err) {
        lastErr = err;
        // 4xx 直接抛，不再 fallback
        if (/^HTTP 4/.test(err.message)) throw err;
        return attempt();
      });
    }
    return attempt();
  }

  function _fetchJson(path, options) {
    return _tryFetch(path, options).then(function(r) {
      return r.res.json().then(function(j) { return { json: j, base: r.base }; });
    });
  }

  // ----- 操作：测试连接 / 拉取 / 推送 -----

  function testConnection() {
    _setState({ status: 'connecting', lastError: null });
    return _fetchJson('/info').then(function(r) {
      var info = r.json || {};
      // 缓存第一条 LAN IP，下次优先尝试
      if (info.lanIPs && info.lanIPs.length > 0) {
        saveSyncConfig({ lastIP: info.lanIPs[0].ip });
      }
      _setState({ status: 'connected', lastInfo: info, lastError: null });
      return { ok: true, info: info, base: r.base };
    }).catch(function(err) {
      _setState({ status: 'error', lastError: err.message || String(err) });
      throw err;
    });
  }

  function pullWeek(year, week) {
    _setState({ status: 'connecting', lastError: null });
    return _fetchJson('/weeks/' + year + '/' + week).then(function(r) {
      _applyServerWeekToLocal(year, week, r.json);
      _setState({ status: 'connected', lastPullAt: Date.now(), lastError: null });
      return { ok: true, applied: true };
    }).catch(function(err) {
      // 404 = 服务器还没该周的数据，不算错误
      if (/^HTTP 404/.test(err.message)) {
        _setState({ status: 'connected', lastPullAt: Date.now() });
        return { ok: true, applied: false, reason: 'week not on server' };
      }
      _setState({ status: 'error', lastError: err.message || String(err) });
      throw err;
    });
  }

  function pushWeek(year, week) {
    var deviceId = getDeviceId();
    var meta = _getMeta(year, week);
    var localCells = getCells(year, week);
    var localItems = getKeyItems(year, week);
    var localReview = getReview(year, week);
    var localConfigRaw = localStorage.getItem(sKey(year, week, 'config'));
    var localConfig = localConfigRaw ? JSON.parse(localConfigRaw) : null;
    var localArchived = isArchived(year, week);

    var payload = { year: year, week: week };
    var now = Date.now();

    // cells
    var hasCells = false, cellsPayload = {};
    for (var k in localCells) {
      var c = localCells[k];
      if (!c) continue;
      cellsPayload[k] = {
        title: c.title || '',
        code: c.code,
        updatedAt: meta.cells[k] || now,
        updatedBy: deviceId
      };
      hasCells = true;
    }
    if (hasCells) payload.cells = cellsPayload;

    // keyitems：本地存的是字符串，发送时包装为 {value, updatedAt, updatedBy}
    var hasItems = false, itemsPayload = {};
    for (var ki in localItems) {
      itemsPayload[ki] = {
        value: localItems[ki] == null ? '' : String(localItems[ki]),
        updatedAt: meta.keyitems[ki] || now,
        updatedBy: deviceId
      };
      hasItems = true;
    }
    if (hasItems) payload.keyitems = itemsPayload;

    // v2.13.1：前三件事状态（key 同 keyitems 格式，值与 localStorage 一致）
    var localKiStatus = getKeyItemStatus(year, week);
    var hasKiStatus = false, kiStatusPayload = {};
    for (var ks in localKiStatus) {
      kiStatusPayload[ks] = {
        value: localKiStatus[ks] || 'todo',
        updatedAt: meta.keyitemStatus[ks] || now,
        updatedBy: deviceId
      };
      hasKiStatus = true;
    }
    if (hasKiStatus) payload.keyitemStatus = kiStatusPayload;

    // review
    if (localReview && Object.keys(localReview).length > 0) {
      payload.review = _assign({}, localReview, { updatedAt: meta.review || now, updatedBy: deviceId });
    }

    // config
    if (localConfig) {
      payload.config = _assign({}, localConfig, { updatedAt: meta.config || now, updatedBy: deviceId });
    }

    // archived
    if (localArchived) payload.archived = true;

    // v2.11.0：进入即入队（去重）。push 成功 → 出队；失败 → 保留等下次 flush。
    _enqueuePending(year, week);

    _setState({ status: 'connecting' });
    return _fetchJson('/weeks/' + year + '/' + week + '/changes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }, 8000).then(function(r) {
      var resp = r.json || {};
      var m = _getMeta(year, week);
      m.serverWeekUpdatedAt = resp.weekUpdatedAt || 0;
      m.lastPushAt = Date.now();
      _saveMeta(year, week, m);
      _dequeuePending(year, week); // v2.11.0：成功才出队
      _setState({ status: 'connected', lastPushAt: Date.now(), lastError: null });
      return { ok: true, response: resp };
    }).catch(function(err) {
      _setState({ status: 'error', lastError: err.message || String(err) });
      throw err;
    });
  }

  // ----- 应用服务器整周到本地（pull） -----

  function _applyServerWeekToLocal(year, week, serverData) {
    if (!serverData) return;
    _state.applyingPullForWeek = { year: year, week: week };
    try {
      var meta = _getMeta(year, week);

      // cells（v2.11.1：逐 cell 按 updatedAt 合并，不再全量替换）
      if (serverData.cells && typeof serverData.cells === 'object') {
        var localCells = getCells(year, week);
        for (var k in serverData.cells) {
          var c = serverData.cells[k];
          if (!c) continue;
          var serverTs = c.updatedAt || 0;
          var localTs = meta.cells[k] || 0;
          var emptyTitle = (c.title === '' || c.title == null);
          var emptyCode = (c.code === '' || c.code == null);
          if (emptyTitle && emptyCode) {
            // 服务端该格已清空：仅当服务端版本更新时才删除本地
            if (serverTs >= localTs) { delete localCells[k]; meta.cells[k] = serverTs; }
          } else if (serverTs >= localTs) {
            // 服务端版本更新或同等：以服务端为准
            localCells[k] = { title: c.title || '', code: c.code };
            meta.cells[k] = serverTs;
          }
          // 本地版本更新 → 保留本地，不写 meta（等 push 时更新服务端）
        }
        saveCells(year, week, localCells);
      }

      // keyitems（v2.11.1：逐项按 updatedAt 合并）
      if (serverData.keyitems && typeof serverData.keyitems === 'object') {
        var localItems = getKeyItems(year, week);
        for (var ki in serverData.keyitems) {
          var it = serverData.keyitems[ki];
          if (!it) continue;
          var serverTsI = it.updatedAt || 0;
          var localTsI = meta.keyitems[ki] || 0;
          if (serverTsI >= localTsI) {
            if (it.value && it.value !== '') { localItems[ki] = it.value; }
            else { delete localItems[ki]; }
            meta.keyitems[ki] = serverTsI;
          }
        }
        saveKeyItems(year, week, localItems);
      }

      // v2.13.1：keyitemStatus 逐项按 updatedAt 合并（同 keyitems 策略）
      if (serverData.keyitemStatus && typeof serverData.keyitemStatus === 'object') {
        var localSt = getKeyItemStatus(year, week);
        for (var stk in serverData.keyitemStatus) {
          var st = serverData.keyitemStatus[stk];
          if (!st) continue;
          var serverStTs = st.updatedAt || 0;
          var localStTs = meta.keyitemStatus[stk] || 0;
          if (serverStTs >= localStTs) {
            if (st.value && st.value !== '') { localSt[stk] = st.value; }
            else { delete localSt[stk]; }
            meta.keyitemStatus[stk] = serverStTs;
          }
        }
        saveKeyItemStatus(year, week, localSt);
      }

      // review（v2.11.1：按 updatedAt 比较，本地较新则保留）
      if (serverData.review && typeof serverData.review === 'object') {
        var rev = _assign({}, serverData.review);
        var revAt = rev.updatedAt || 0;
        delete rev.updatedAt; delete rev.updatedBy;
        if (revAt >= (meta.review || 0)) {
          saveReview(year, week, rev);
          meta.review = revAt;
        }
      }

      // config
      if (serverData.config && typeof serverData.config === 'object') {
        var cfg = _assign({}, serverData.config);
        var cfgAt = cfg.updatedAt || 0;
        delete cfg.updatedAt; delete cfg.updatedBy;
        saveConfig(year, week, cfg);
        meta.config = cfgAt;
      }

      // archived
      if (serverData.archived === true) setArchived(year, week);

      meta.serverWeekUpdatedAt = serverData.weekUpdatedAt || 0;
      meta.lastPullAt = Date.now();
      _saveMeta(year, week, meta);
    } finally {
      _state.applyingPullForWeek = null;
    }
  }

  // ----- meta 跟踪（per-key updatedAt） -----

  function _metaKey(year, week) { return STORAGE_PREFIX + year + '_w' + week + '_syncmeta'; }

  function _getMeta(year, week) {
    try {
      var raw = localStorage.getItem(_metaKey(year, week));
      if (raw) {
        var m = JSON.parse(raw);
        m.cells = m.cells || {};
        m.keyitems = m.keyitems || {};
        m.keyitemStatus = m.keyitemStatus || {};
        return m;
      }
    } catch (e) {}
    return { cells: {}, keyitems: {}, keyitemStatus: {}, review: 0, config: 0, archived: 0, serverWeekUpdatedAt: 0, lastPullAt: 0, lastPushAt: 0 };
  }

  function _saveMeta(year, week, meta) {
    localStorage.setItem(_metaKey(year, week), JSON.stringify(meta));
  }

  // ----- 保存事件订阅：diff 出变化 → 更新 meta → 调度推送 -----

  function _handleSaveChange(year, week, part, prev, next) {
    // pull 中的写不再回推
    if (_state.applyingPullForWeek &&
        _state.applyingPullForWeek.year === year &&
        _state.applyingPullForWeek.week === week) return;

    var cfg = getSyncConfig();
    if (!cfg.enabled) return;

    var now = Date.now();
    var meta = _getMeta(year, week);

    if (part === 'cells') {
      var pc = prev || {}, nc = next || {}, all = {};
      for (var k1 in pc) all[k1] = 1;
      for (var k2 in nc) all[k2] = 1;
      for (var k in all) {
        if (JSON.stringify(pc[k] || null) !== JSON.stringify(nc[k] || null)) {
          meta.cells[k] = now;
        }
      }
    } else if (part === 'keyitems') {
      var pi = prev || {}, ni = next || {}, allI = {};
      for (var ki1 in pi) allI[ki1] = 1;
      for (var ki2 in ni) allI[ki2] = 1;
      for (var ki in allI) {
        if ((pi[ki] || '') !== (ni[ki] || '')) {
          meta.keyitems[ki] = now;
        }
      }
    } else if (part === 'keyitemStatus') {
      var ps = prev || {}, ns = next || {}, allS = {};
      for (var ks1 in ps) allS[ks1] = 1;
      for (var ks2 in ns) allS[ks2] = 1;
      for (var ks in allS) {
        if ((ps[ks] || '') !== (ns[ks] || '')) {
          meta.keyitemStatus[ks] = now;
        }
      }
    } else if (part === 'review') {
      if (JSON.stringify(prev || {}) !== JSON.stringify(next || {})) meta.review = now;
    } else if (part === 'config') {
      if (JSON.stringify(prev || {}) !== JSON.stringify(next || {})) meta.config = now;
    } else if (part === 'archived') {
      if (next === true && prev !== true) meta.archived = now;
    }

    _saveMeta(year, week, meta);

    if (cfg.autoSync) _schedulePush(year, week);
  }

  // ----- 离线变更队列（v2.11.0） -----
  //
  // 失败的 pushWeek 自动保留在 localStorage 中的队列里，online 事件 / 启动时自动 flush。
  // 队列只记录 (year, week) 不存重复项 —— pushWeek 整周策略下，重复入队没意义。

  function _loadPendingQueue() {
    try {
      var raw = localStorage.getItem(PENDING_QUEUE_KEY);
      if (!raw) return [];
      var arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr : [];
    } catch (e) { return []; }
  }

  function _savePendingQueue(q) {
    try { localStorage.setItem(PENDING_QUEUE_KEY, JSON.stringify(q)); } catch (e) {}
    _setState({ pendingQueueSize: q.length });
  }

  function _enqueuePending(year, week) {
    var q = _loadPendingQueue();
    for (var i = 0; i < q.length; i++) {
      if (q[i].year === year && q[i].week === week) {
        q[i].queuedAt = Date.now(); // 刷新时间戳
        _savePendingQueue(q);
        return;
      }
    }
    q.push({ year: year, week: week, queuedAt: Date.now() });
    _savePendingQueue(q);
  }

  function _dequeuePending(year, week) {
    var q = _loadPendingQueue();
    var changed = false;
    for (var i = q.length - 1; i >= 0; i--) {
      if (q[i].year === year && q[i].week === week) {
        q.splice(i, 1);
        changed = true;
      }
    }
    if (changed) _savePendingQueue(q);
  }

  function getPendingQueue() {
    return _loadPendingQueue();
  }

  // 串行 flush 队列：每个待推送周顺序 pushWeek，避免并发把服务器搞乱。
  // 同步开关关闭 / 已在 flush 中 → 直接跳过。
  var _flushing = false;
  function flushOfflineQueue() {
    if (_flushing) return Promise.resolve({ skipped: true, reason: 'flushing' });
    var cfg = getSyncConfig();
    if (!cfg.enabled) return Promise.resolve({ skipped: true, reason: 'disabled' });
    var q = _loadPendingQueue();
    if (q.length === 0) return Promise.resolve({ ok: true, count: 0 });
    _flushing = true;
    var pushed = 0, failed = 0;
    return q.reduce(function(p, item) {
      return p.then(function() {
        return pushWeek(item.year, item.week)
          .then(function() { pushed++; })
          .catch(function() { failed++; }); // 失败保留队列
      });
    }, Promise.resolve()).then(function() {
      _flushing = false;
      if (typeof console !== 'undefined') {
        console.log('[sync] flushOfflineQueue done: pushed=' + pushed + ' failed=' + failed);
      }
      return { ok: failed === 0, pushed: pushed, failed: failed };
    });
  }

  // ----- debounced push -----

  function _schedulePush(year, week) {
    if (_state.pendingPushTimer) {
      clearTimeout(_state.pendingPushTimer);
      _state.pendingPushTimer = null;
    }
    _state.pendingPushWeek = { year: year, week: week };
    _setState({}); // 通知 UI: pendingPush 待处理
    _state.pendingPushTimer = setTimeout(function() {
      _state.pendingPushTimer = null;
      var w = _state.pendingPushWeek;
      _state.pendingPushWeek = null;
      if (!w) return;
      pushWeek(w.year, w.week).catch(function(err) {
        if (typeof console !== 'undefined') console.warn('[sync] auto-push failed:', err.message);
      });
    }, DEBOUNCE_MS);
  }

  function flushPendingPush() {
    if (_state.pendingPushTimer) {
      clearTimeout(_state.pendingPushTimer);
      _state.pendingPushTimer = null;
      var w = _state.pendingPushWeek;
      _state.pendingPushWeek = null;
      if (w) return pushWeek(w.year, w.week);
    }
    return Promise.resolve({ ok: true, skipped: true });
  }

  // ----- 周期性心跳检测（v2.11.2 增强） -----
  //
  // v2.11.1：轻量 ping /info 每 30s，解决重启后状态假阳性。
  // v2.11.2：首次心跳 1s 后立即执行（不等 30s），并覆盖 disconnected 状态，
  //          确保服务器后启动也能自动恢复。

  var HEALTH_CHECK_MS = 30000;

  function _startHealthCheck() {
    if (_state.healthCheckTimer) return;
    // v2.11.2：首次心跳立即执行（1s 延迟让 UI 就位），之后每 30s。
    // 覆盖 disconnected / connected / error 三种状态，确保重启后自动恢复。
    _state.healthCheckInitTimer = setTimeout(function() {
      _state.healthCheckInitTimer = null;
      _healthCheckPing();
    }, 1000);
    _state.healthCheckTimer = setInterval(function() {
      _healthCheckPing();
    }, HEALTH_CHECK_MS);
    if (typeof console !== 'undefined') console.log('[sync] 心跳检测已启动（间隔 ' + (HEALTH_CHECK_MS / 1000) + 's，首次 1s 后）');
  }

  function _healthCheckPing() {
    var st = _state.status;
    // 仅在禁用或连接中时跳过；disconnected / connected / error 均尝试
    if (st === 'disabled' || st === 'connecting') return;
    _fetchJson('/info').then(function(r) {
      var info = r.json || {};
      if (info.lanIPs && info.lanIPs.length > 0) {
        saveSyncConfig({ lastIP: info.lanIPs[0].ip });
      }
      _setState({ status: 'connected', lastInfo: info, lastError: null });
    }).catch(function(err) {
      _setState({ status: 'error', lastError: '心跳失败: ' + (err.message || String(err)) });
    });
  }

  function _stopHealthCheck() {
    if (_state.healthCheckTimer) {
      clearInterval(_state.healthCheckTimer);
      _state.healthCheckTimer = null;
    }
    if (_state.healthCheckInitTimer) {
      clearTimeout(_state.healthCheckInitTimer);
      _state.healthCheckInitTimer = null;
    }
    if (typeof console !== 'undefined') console.log('[sync] 心跳检测已停止');
  }

  // ----- WebSocket 实时推送（v2.12.0 / 阶段 3.3） -----
  //
  // 与服务端 WSS /events 建立持久连接，收到 week-changed 广播时
  // 自动 pullWeek 对应周数据，实现"另一端保存 → 本端实时收到"。

  var WS_RECONNECT_MAX = 30000;   // 最大重连间隔 30s
  var WS_RECONNECT_FACTOR = 2;     // 指数退避因子

  function _wsBuildUrl() {
    var cfg = getSyncConfig();
    var proto = getEffectiveProtocol(cfg);
    var wsProto = (proto === 'https:') ? 'wss:' : 'ws:';
    var host = getEffectiveHost(cfg);
    var port = getEffectivePort(cfg);
    if (!host) return '';
    host = host.replace(/^https?:\/\//i, '').replace(/[\/\?#].*$/, '').replace(/:\d+$/, '');
    // IPv4 字面量直接用
    if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) {
      return wsProto + '//' + host + ':' + port + '/events';
    }
    // 已带 .local 后缀直接用
    if (/\.local$/i.test(host)) {
      return wsProto + '//' + host + ':' + port + '/events';
    }
    // 普通主机名 → 优先 .local（mDNS）
    return wsProto + '//' + host + '.local:' + port + '/events';
  }

  function _wsConnect() {
    if (_state.ws && (_state.ws.readyState === WebSocket.OPEN || _state.ws.readyState === WebSocket.CONNECTING)) return;
    _wsDisconnect(); // 清理旧连接

    var url = _wsBuildUrl();
    if (!url) {
      if (typeof console !== 'undefined') console.log('[sync] WebSocket：未配置主机，跳过');
      return;
    }

    try {
      if (typeof console !== 'undefined') console.log('[sync] WebSocket 连接中: ' + url);
      var ws = new WebSocket(url);
      _state.ws = ws;
      _state.wsReconnectDelay = 1000;

      ws.onopen = function() {
        if (typeof console !== 'undefined') console.log('[sync] WebSocket 已连接');
        _state.wsReconnectDelay = 1000; // 重置退避
      };

      ws.onmessage = function(ev) {
        try {
          var msg = JSON.parse(ev.data);
          if (msg && msg.type === 'week-changed' && msg.year && msg.week) {
            if (typeof console !== 'undefined') console.log('[sync] WebSocket 收到变更广播: ' + msg.year + '-W' + msg.week);
            // 自动拉取变更的周（当前周立即刷新，其他周静默拉取）
            var cur = _state.currentWeek;
            pullWeek(msg.year, msg.week).then(function(r) {
              if (r && r.applied && cur && cur.year === msg.year && cur.week === msg.week) {
                // 当前正在查看的周 → 触发 UI 刷新
                if (typeof window !== 'undefined' && window.dispatchEvent) {
                  window.dispatchEvent(new CustomEvent('sync-remote-change', { detail: msg }));
                }
              }
            }).catch(function(err) {
              if (typeof console !== 'undefined') console.warn('[sync] WebSocket 触发的拉取失败:', err.message);
            });
          }
        } catch (e) {}
      };

      ws.onclose = function(ev) {
        if (typeof console !== 'undefined') console.log('[sync] WebSocket 已断开 (code=' + ev.code + ')');
        _state.ws = null;
        _wsScheduleReconnect();
      };

      ws.onerror = function() {
        // onclose 会紧随其后，在 onclose 里统一处理重连
      };
    } catch (e) {
      _state.ws = null;
      _wsScheduleReconnect();
    }
  }

  function _wsDisconnect() {
    if (_state.wsReconnectTimer) {
      clearTimeout(_state.wsReconnectTimer);
      _state.wsReconnectTimer = null;
    }
    if (_state.ws) {
      try { _state.ws.close(1000); } catch (e) {}
      _state.ws = null;
    }
  }

  function _wsScheduleReconnect() {
    if (_state.wsReconnectTimer) return; // 已有待重连
    var cfg = getSyncConfig();
    if (!cfg.enabled) return;
    var delay = _state.wsReconnectDelay || 1000;
    if (typeof console !== 'undefined') console.log('[sync] WebSocket ' + (delay / 1000) + 's 后重连');
    _state.wsReconnectTimer = setTimeout(function() {
      _state.wsReconnectTimer = null;
      _state.wsReconnectDelay = Math.min(_state.wsReconnectDelay * WS_RECONNECT_FACTOR, WS_RECONNECT_MAX);
      _wsConnect();
    }, delay);
  }

  // ----- 启动 -----

  function init() {
    onSaveChange(_handleSaveChange);
    var cfg = getSyncConfig();
    _setState({
      status: cfg.enabled ? 'disconnected' : 'disabled',
      pendingQueueSize: _loadPendingQueue().length
    });

    // v2.11.1：启用同步时启动周期性心跳检测（§22.10 修复）
    if (cfg.enabled) _startHealthCheck();

    // v2.12.0：启用同步时连接 WebSocket 实时推送
    if (cfg.enabled) _wsConnect();

    // v2.13.0：若无设备令牌，桌面自动注册（首次部署 + 过渡期兼容）
    if (cfg.enabled && !getDeviceToken()) {
      setTimeout(function() {
        registerDesktop().then(function(r) {
          if (r && r.token && typeof console !== 'undefined') {
            console.log('[sync] 桌面设备已注册');
          }
        }).catch(function(err) {
          if (typeof console !== 'undefined') console.warn('[sync] 桌面自注册失败（可能已有设备）:', err.message);
        });
      }, 1000);
    }

    // v2.11.0：监听 online 事件 → 自动 flush 离线变更队列
    if (typeof window !== 'undefined' && window.addEventListener) {
      window.addEventListener('online', function() {
        if (typeof console !== 'undefined') console.log('[sync] online 事件触发，flush 离线队列');
        flushOfflineQueue();
      });
      // v2.12.0：visibilitychange 补充 iOS Safari online 事件不可靠问题（§22.2）
      document.addEventListener('visibilitychange', function() {
        if (!document.hidden && navigator.onLine !== false) {
          if (typeof console !== 'undefined') console.log('[sync] 页面回到前台，flush 离线队列');
          flushOfflineQueue();
        }
      });
    }

    // v2.11.0：启动时若已在线且队列非空，延迟 flush（让 UI 先就位）
    if (typeof navigator !== 'undefined' && navigator.onLine !== false) {
      if (_loadPendingQueue().length > 0) {
        setTimeout(function() { flushOfflineQueue(); }, 1500);
      }
    }
  }

  function setCurrentWeek(year, week) {
    _state.currentWeek = { year: year, week: week };
  }

  // ----- 配对与设备管理（v2.13.0） -----

  function pairStart() {
    return _fetchJson('/pair/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
      .then(function(r) { return r.json; });
  }

  function pairConfirm(code, deviceName, platform) {
    return _fetchJson('/pair/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code, deviceName: deviceName, platform: platform })
    }).then(function(r) { return r.json; });
  }

  function registerDesktop() {
    return _fetchJson('/pair/register-desktop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ deviceName: detectHostname() || 'Windows' })
    }).then(function(r) {
      var token = r.json && r.json.token;
      if (token) saveDeviceToken(token);
      return r.json;
    });
  }

  function getDevices() {
    return _fetchJson('/devices').then(function(r) { return r.json || []; });
  }

  function deleteDevice(deviceId) {
    return _fetchJson('/devices/' + deviceId, { method: 'DELETE' }).then(function(r) { return r.json; });
  }

  // ----- 自动检测 hostname（基于 window.location） -----
  //
  // v2.10.1：放开 IPv4 与 localhost。设计前提是 PWA 静态资源（6371）
  // 与同步服务（6372）在同一台机器，因此 window.location.hostname 即同步服务地址。

  function detectHostname() {
    if (typeof window === 'undefined' || !window.location) return '';
    var h = window.location.hostname || '';
    if (!h) return '';
    // localhost 等价于 127.0.0.1
    if (h === 'localhost') return '127.0.0.1';
    // IPv4 字面量直接用（手机端常见，如 192.168.31.153）
    if (/^\d{1,3}(\.\d{1,3}){3}$/.test(h)) return h;
    // <name>.local（mDNS）→ 抽出 <name>，让 buildUrls 走 .local + 裸名 fallback
    if (/\.local$/i.test(h)) return h.replace(/\.local$/i, '');
    return h;
  }

  return {
    DEFAULT_PORT: DEFAULT_HTTP_PORT,           // 向后兼容老 UI 文案
    DEFAULT_HTTP_PORT: DEFAULT_HTTP_PORT,
    DEFAULT_HTTPS_PORT: DEFAULT_HTTPS_PORT,
    getDeviceId: getDeviceId,
    getSyncConfig: getSyncConfig,
    saveSyncConfig: saveSyncConfig,
    getState: getState,
    onStateChange: onStateChange,
    buildUrls: buildUrls,
    testConnection: testConnection,
    pullWeek: pullWeek,
    pushWeek: pushWeek,
    flushPendingPush: flushPendingPush,
    flushOfflineQueue: flushOfflineQueue, // v2.11.0：手动触发离线队列 flush
    getPendingQueue: getPendingQueue,     // v2.11.0：读取当前队列（UI/调试用）
    setCurrentWeek: setCurrentWeek,
    detectHostname: detectHostname,
    getEffectiveHost: getEffectiveHost,
    getEffectivePort: getEffectivePort,
    getEffectiveProtocol: getEffectiveProtocol,
    startHealthCheck: _startHealthCheck,   // v2.11.1：启动周期性心跳检测
    stopHealthCheck: _stopHealthCheck,     // v2.11.1：停止心跳检测
    // v2.13.0：配对与设备管理
    getDeviceToken: getDeviceToken,
    saveDeviceToken: saveDeviceToken,
    pairStart: pairStart,
    pairConfirm: pairConfirm,
    registerDesktop: registerDesktop,
    getDevices: getDevices,
    deleteDevice: deleteDevice,
    init: init
  };
})();

global.AppCore = {
  STORAGE_PREFIX: STORAGE_PREFIX,
  WEEKDAYS: WEEKDAYS,
  KEY_ROWS: KEY_ROWS,
  TIME_SLOTS: TIME_SLOTS,
  buildTimeSlots: buildTimeSlots,
  DEFAULT_CONFIG: DEFAULT_CONFIG,
  getISOWeek: getISOWeek,
  getWeekDates: getWeekDates,
  formatDate: formatDate,
  dateKey: dateKey,
  getPrevWeek: getPrevWeek,
  getNextWeek: getNextWeek,
  sKey: sKey,
  getConfig: getConfig,
  saveConfig: saveConfig,
  getCells: getCells,
  saveCells: saveCells,
  getKeyItems: getKeyItems,
  saveKeyItems: saveKeyItems,
  getKeyItemStatus: getKeyItemStatus,
  saveKeyItemStatus: saveKeyItemStatus,
  KEY_ITEM_STATUS_ROWS: KEY_ITEM_STATUS_ROWS,
  KEY_ITEM_STATUS_VALUES: KEY_ITEM_STATUS_VALUES,
  getReview: getReview,
  saveReview: saveReview,
  isArchived: isArchived,
  setArchived: setArchived,
  getCatClass: getCatClass,
  calcDailyStats: calcDailyStats,
  calcWeeklyStats: calcWeeklyStats,
  exportAllData: exportAllData,
  summarizeImport: summarizeImport,
  importAllData: importAllData,
  onSaveChange: onSaveChange,
  syncClient: syncClient
};

})(typeof window !== 'undefined' ? window : this);
