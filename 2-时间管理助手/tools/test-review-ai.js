// 测试脚本：用真实 sync-data 验证 buildDataContext 与 prompt 生成
// 不改动任何生产文件，只在 node 中模拟浏览器环境跑一遍引擎
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

// ---- 模拟 localStorage ----
const store = {};
global.localStorage = {
  getItem: k => (k in store ? store[k] : null),
  setItem: (k, v) => { store[k] = String(v); },
  key: i => Object.keys(store)[i],
  get length() { return Object.keys(store).length; }
};

// ---- 把 sync-data 灌进模拟的 localStorage（格式与浏览器一致：拆包 {value}）----
function unwrap(obj) {
  const out = {};
  Object.keys(obj || {}).forEach(k => {
    const v = obj[k];
    out[k] = (v && typeof v === 'object' && 'value' in v) ? v.value : v;
  });
  return out;
}

const YEAR = 2026;
const WEEKS = [33, 34, 35, 36];
WEEKS.forEach(w => {
  const f = path.join(ROOT, 'sync-data', String(YEAR), `w${w}.json`);
  if (!fs.existsSync(f)) { console.log(`跳过 w${w}（无文件）`); return; }
  const d = JSON.parse(fs.readFileSync(f, 'utf8'));
  const pad = String(w).padStart(2, '0');
  // cells 的值本身就是 {title, code, updatedAt}，不需要 unwrap
  localStorage.setItem(`tm_${YEAR}_w${pad}_cells`, JSON.stringify(d.cells || {}));
  localStorage.setItem(`tm_${YEAR}_w${pad}_keyitems`, JSON.stringify(unwrap(d.keyitems)));
  localStorage.setItem(`tm_${YEAR}_w${pad}_review`, JSON.stringify(unwrap(d.review)));
  localStorage.setItem(`tm_${YEAR}_w${pad}_config`, JSON.stringify(unwrap(d.config)));
});

// ---- 最小化的 AppCore（只提供引擎用到的几个方法）----
function getWeekDates(year, week) {
  // ISO 周一为首日
  const jan4 = new Date(Date.UTC(year, 0, 4));
  const dow = (jan4.getUTCDay() + 6) % 7;
  const week1Mon = new Date(jan4);
  week1Mon.setUTCDate(jan4.getUTCDate() - dow);
  const mon = new Date(week1Mon);
  mon.setUTCDate(week1Mon.getUTCDate() + (week - 1) * 7);
  const out = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(mon);
    d.setUTCDate(mon.getUTCDate() + i);
    out.push(`${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`);
  }
  return out;
}
function readJSON(key, fallback) {
  const raw = localStorage.getItem(key);
  if (!raw) return fallback;
  try { return JSON.parse(raw); } catch (e) { return fallback; }
}
global.window = {
  AppCore: {
    getWeekDates,
    getCells: (y, w) => readJSON(`tm_${y}_w${String(w).padStart(2, '0')}_cells`, {}),
    getKeyItems: (y, w) => readJSON(`tm_${y}_w${String(w).padStart(2, '0')}_keyitems`, {}),
    getReview: (y, w) => readJSON(`tm_${y}_w${String(w).padStart(2, '0')}_review`, {}),
    getConfig: (y, w) => readJSON(`tm_${y}_w${String(w).padStart(2, '0')}_config`, {})
  }
};

// ---- 加载引擎 ----
const src = fs.readFileSync(path.join(ROOT, 'src', 'review-engine.js'), 'utf8');
eval(src);
const engine = global.window.ReviewEngine;

// ---- 跑起来 ----
console.log('='.repeat(70));
const ctx = engine.buildDataContext(YEAR, 33, 36);
console.log('统计结果:');
console.log('  QW =', ctx.stats.totalQW, 'h');
console.log('  GFP =', ctx.stats.totalGFP, 'h');
console.log('  Proc =', ctx.stats.totalProc, 'h');
console.log('  Rest =', ctx.stats.totalRest, 'h');
console.log('  MW =', ctx.stats.totalMW, 'h');
console.log('  凌晨工作 =', ctx.stats.midnightWorkCount);
console.log('  日期范围 =', ctx.dateRange);
console.log('  上次复盘 =', ctx.previousReview ? '有' : '无');
console.log('='.repeat(70));

const factText = engine.formatContextForPrompt(ctx);
fs.writeFileSync(path.join(__dirname, 'out-facts.txt'), factText, 'utf8');
fs.writeFileSync(path.join(__dirname, 'out-chat-prompt.txt'), engine.buildChatSystemPrompt(ctx), 'utf8');
fs.writeFileSync(path.join(__dirname, 'out-report-prompt.txt'), engine.buildReportSystemPrompt(ctx), 'utf8');
console.log('事实清单长度:', factText.length, '字');
console.log('已写出 out-facts.txt / out-chat-prompt.txt / out-report-prompt.txt');
