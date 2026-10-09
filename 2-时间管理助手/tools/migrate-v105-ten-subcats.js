// v105 编码调整迁移：四大类统一 10 个子类，「其他」固定为 x.0
//
// 用法：
//   node tools/migrate-v105-ten-subcats.js            # 预演（dry-run），只打印结果，不写文件
//   node tools/migrate-v105-ten-subcats.js --apply    # 正式写入 sync-data
//
// 规则：
//   1. 格子：1.7 → 1（1.0 其他）、2.8 → 2（2.0 其他）、3.5 → 3（3.0 其他）；0.x 不变
//   2. config：调用 src/app-core.js 的 normalizeConfigNames（与前端同一份逻辑），
//      名称数组展开为 10 项、「其他」移到下标 9，补齐 qwOn/gfpOn/procOn/restOn
//
// 幂等：迁移过的周文件写入 codeSchema = 105，再次运行直接跳过
// 写入时刷新 cell.updatedAt / config.updatedAt / weekUpdatedAt，客户端「拉取全部周」即可同步
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..');
const DATA_DIR = path.join(ROOT, 'sync-data');
const APPLY = process.argv.includes('--apply');
const SCHEMA = 105;
const CELL_MAP = { '1.7': 1, '2.8': 2, '3.5': 3 };

// 加载前端的 AppCore（只用纯函数 normalizeConfigNames）
const sandbox = { console: { log() {}, warn() {}, error() {} }, setTimeout, clearTimeout, setInterval: () => 0, clearInterval() {},
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} }, navigator: { userAgent: 'node' }, location: { protocol: 'http:', hostname: '127.0.0.1' } };
sandbox.window = sandbox;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(ROOT, 'src', 'app-core.js'), 'utf8'), sandbox);
const { normalizeConfigNames } = sandbox.AppCore;

const summary = {};
let totalCells = 0, totalWeeks = 0, skipped = 0;
const now = Date.now();

for (const y of fs.readdirSync(DATA_DIR).filter(n => /^\d{4}$/.test(n))) {
  const dir = path.join(DATA_DIR, y);
  for (const fn of fs.readdirSync(dir).filter(f => /^w\d+\.json$/.test(f)).sort()) {
    const fp = path.join(dir, fn);
    const data = JSON.parse(fs.readFileSync(fp, 'utf8'));
    if (data.codeSchema >= SCHEMA) { skipped++; continue; }

    let n = 0;
    for (const cell of Object.values(data.cells || {})) {
      if (!cell) continue;
      const c = cell.code === null || cell.code === undefined ? '' : String(cell.code).trim();
      if (!(c in CELL_MAP)) continue;
      const key = `${c} → ${CELL_MAP[c]}.0`;
      const b = summary[key] || (summary[key] = { hours: 0, titles: {} });
      const t = (cell.title || '').trim() || '(空)';
      b.hours += 0.5;
      b.titles[t] = (b.titles[t] || 0) + 0.5;
      if (APPLY) {
        cell.code = CELL_MAP[c];
        cell.updatedAt = now;
        cell.updatedBy = 'migration-v105';
      }
      n++;
    }

    let cfgNote = '';
    if (data.config && typeof data.config === 'object') {
      const meta = { updatedAt: data.config.updatedAt, updatedBy: data.config.updatedBy };
      const before = JSON.stringify(data.config);
      const cfg = normalizeConfigNames(JSON.parse(before));
      cfg.updatedAt = meta.updatedAt; cfg.updatedBy = meta.updatedBy;
      if (JSON.stringify(cfg) !== before) {
        cfgNote = ` + 配置（QW 1.0=${cfg.qwNames[9]} / GFP 2.0=${cfg.gfpNames[9]} / Proc 3.0=${cfg.procNames[9]}）`;
        if (APPLY) { cfg.updatedAt = now; cfg.updatedBy = 'migration-v105'; data.config = cfg; }
      }
    }

    totalCells += n;
    totalWeeks++;
    if (n > 0 || cfgNote) console.log(`${y}/${fn}: ${n} 格${cfgNote}`);
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
