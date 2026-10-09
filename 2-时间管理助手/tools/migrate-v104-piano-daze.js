// v104 编码调整迁移：GFP 新增 2.7 钢琴、休息新增 0.9 发呆 / 0.0 其他
//
// 用法：
//   node tools/migrate-v104-piano-daze.js            # 预演（dry-run），只打印结果，不写文件
//   node tools/migrate-v104-piano-daze.js --apply    # 正式写入 sync-data
//
// 规则（按顺序执行，先挪 2.7 再填 2.7，避免撞车）：
//   1. 2.7 其他 → 2.8 其他
//   2. 2.6 小资 中事件名含「琴」→ 2.7 钢琴
//   3. 0.9 其他 中事件名不是「发呆」→ 0（显示 0.0 其他）；「发呆」保留 0.9
//   4. config：gfpNames 7 项 → 8 项（插入「钢琴」，2.3「约会」改名「社交」），
//      restNames 9 项 → 10 项（0.9 发呆/放空 + 0.0 其他）
//
// 幂等：迁移过的周文件写入 codeSchema = 104，再次运行直接跳过
// 写入时刷新 cell.updatedAt / config.updatedAt / weekUpdatedAt，客户端「拉取全部周」即可同步
'use strict';
const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'sync-data');
const APPLY = process.argv.includes('--apply');
const SCHEMA = 104;
const PIANO_RE = /琴/;
const DAZE_TITLES = new Set(['发呆']);

function codeStr(code) { return code === null || code === undefined ? '' : String(code).trim(); }

function upgradeNames(cfg) {
  let changed = false;
  if (Array.isArray(cfg.gfpNames) && cfg.gfpNames.length === 7) {
    cfg.gfpNames = cfg.gfpNames.slice(0, 6).concat(['钢琴', cfg.gfpNames[6] || '其他']);
    if (cfg.gfpNames[2] === '约会') cfg.gfpNames[2] = '社交';
    changed = true;
  }
  if (!Array.isArray(cfg.restNames) || cfg.restNames.length === 9) {
    const old = Array.isArray(cfg.restNames) ? cfg.restNames
      : ['睡觉', '吃喝', '散步', '出行', '刷手机', '卫生', '游戏', '社交', '其他'];
    cfg.restNames = old.slice(0, 8).concat(['发呆/放空', old[8] || '其他']);
    changed = true;
  }
  return changed;
}

const summary = {};   // '旧→新' → { hours, titles }
let totalCells = 0, totalWeeks = 0, skipped = 0;
const now = Date.now();

function record(key, title) {
  const b = summary[key] || (summary[key] = { hours: 0, titles: {} });
  const t = (title || '').trim() || '(空)';
  b.hours += 0.5;
  b.titles[t] = (b.titles[t] || 0) + 0.5;
}

for (const y of fs.readdirSync(DATA_DIR).filter(n => /^\d{4}$/.test(n))) {
  const dir = path.join(DATA_DIR, y);
  for (const fn of fs.readdirSync(dir).filter(f => /^w\d+\.json$/.test(f)).sort()) {
    const fp = path.join(dir, fn);
    const data = JSON.parse(fs.readFileSync(fp, 'utf8'));
    if (data.codeSchema >= SCHEMA) { skipped++; continue; }

    let n = 0;
    for (const cell of Object.values(data.cells || {})) {
      if (!cell) continue;
      const c = codeStr(cell.code);
      let to = null;
      if (c === '2.7') to = 2.8;
      else if (c === '2.6' && PIANO_RE.test(cell.title || '')) to = 2.7;
      else if (c === '0.9' && !DAZE_TITLES.has((cell.title || '').trim())) to = 0;
      if (to === null) continue;
      record(`${c} → ${to === 0 ? '0.0' : to}`, cell.title);
      if (APPLY) {
        cell.code = to;
        cell.updatedAt = now;
        cell.updatedBy = 'migration-v104';
      }
      n++;
    }

    let cfgChanged = false;
    if (data.config && typeof data.config === 'object') {
      cfgChanged = upgradeNames(data.config);
      if (cfgChanged && APPLY) { data.config.updatedAt = now; data.config.updatedBy = 'migration-v104'; }
    }

    totalCells += n;
    totalWeeks++;
    if (n > 0 || cfgChanged) console.log(`${y}/${fn}: ${n} 格${cfgChanged ? ' + 配置' : ''}`);
    if (APPLY) {
      data.codeSchema = SCHEMA;
      data.weekUpdatedAt = now;
      // 原子写入：先写 .tmp 再 rename（与 sync-server 一致）
      const tmp = fp + '.tmp';
      fs.writeFileSync(tmp, JSON.stringify(data, null, 2));
      fs.renameSync(tmp, fp);
    }
  }
}

console.log(`\n${APPLY ? '【已写入】' : '【预演，未写入】'} 处理 ${totalWeeks} 周（跳过已迁移 ${skipped} 周），共 ${totalCells} 格 = ${totalCells * 0.5}h\n`);
for (const [k, b] of Object.entries(summary)) {
  const list = Object.entries(b.titles).sort((a, c) => c[1] - a[1]).map(([t, h]) => `${t} ${h}h`).join('、');
  console.log(`${k}  ${b.hours}h\n    ${list}`);
}
