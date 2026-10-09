// v108 编码调整迁移：GFP 2.1「演出」改名「影片」，新增 2.8「演出」；顺带修正几处归类
//
// 用法：
//   node tools/migrate-v108-film-show.js            # 预演（dry-run），只打印结果，不写文件
//   node tools/migrate-v108-film-show.js --apply    # 正式写入 sync-data
//
// 规则（用户 2026-10-09 确认）：
//   1. config：gfpNames[0] 演出 → 影片；gfpNames[7] 空 → 演出，gfpOn[7] = true
//   2. 格子：2.6「爱在黄昏日落时」「电影【康斯坦丁】」→ 2.1 影片
//            w28 2.1「吃饭」→ 2.3 社交
//            0.0「去看电影」→ 0.4 出行
//   历史 2.1 记录全是看电影，只改名称不改编码；2.8 演出暂无历史数据
//
// 幂等：迁移过的周文件写入 codeSchema = 108，再次运行直接跳过
// 写入时刷新 cell.updatedAt / config.updatedAt / weekUpdatedAt，客户端「拉取全部周」即可同步
'use strict';
const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'sync-data');
const APPLY = process.argv.includes('--apply');
const SCHEMA = 108;
const CELL_RULES = [
  { from: '2.6', titles: ['爱在黄昏日落时', '电影【康斯坦丁】'], to: 2.1, label: '2.6 → 2.1 影片' },
  { from: '2.1', titles: ['吃饭'], weeks: [28], to: 2.3, label: '2.1 → 2.3 社交' },
  { from: '0', titles: ['去看电影'], to: 0.4, label: '0.0 → 0.4 出行' }
];

const summary = {};
let totalCells = 0, totalWeeks = 0, skipped = 0;
const now = Date.now();

for (const y of fs.readdirSync(DATA_DIR).filter(n => /^\d{4}$/.test(n))) {
  const dir = path.join(DATA_DIR, y);
  for (const fn of fs.readdirSync(dir).filter(f => /^w\d+\.json$/.test(f)).sort()) {
    const fp = path.join(dir, fn);
    const week = parseInt(fn.slice(1), 10);
    const data = JSON.parse(fs.readFileSync(fp, 'utf8'));
    if (data.codeSchema >= SCHEMA) { skipped++; continue; }

    let n = 0;
    for (const [key, cell] of Object.entries(data.cells || {})) {
      if (!cell) continue;
      const c = cell.code === null || cell.code === undefined ? '' : String(cell.code).trim();
      const t = (cell.title || '').trim();
      const rule = CELL_RULES.find(r => r.from === c && r.titles.includes(t) && (!r.weeks || r.weeks.includes(week)));
      if (!rule) continue;
      const b = summary[rule.label] || (summary[rule.label] = { hours: 0, items: {} });
      const item = `w${week} ${key.split('|')[0]} ${t}`;
      b.hours += 0.5;
      b.items[item] = (b.items[item] || 0) + 0.5;
      if (APPLY) {
        cell.code = rule.to;
        cell.updatedAt = now;
        cell.updatedBy = 'migration-v108';
      }
      n++;
    }

    let cfgNote = '';
    const cfg = data.config;
    if (cfg && Array.isArray(cfg.gfpNames) && cfg.gfpNames.length === 10) {
      const changes = [];
      if (cfg.gfpNames[0] === '演出') changes.push('2.1 演出→影片');
      if (!cfg.gfpNames[7]) changes.push('2.8 新增演出');
      if (changes.length) {
        cfgNote = ' + 配置（' + changes.join('，') + '）';
        if (APPLY) {
          if (cfg.gfpNames[0] === '演出') cfg.gfpNames[0] = '影片';
          if (!cfg.gfpNames[7]) cfg.gfpNames[7] = '演出';
          if (Array.isArray(cfg.gfpOn)) cfg.gfpOn[7] = true;
          cfg.updatedAt = now;
          cfg.updatedBy = 'migration-v108';
        }
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
  const list = Object.entries(b.items).map(([t, h]) => `${t} ${h}h`).join('、');
  console.log(`${k}  ${b.hours}h\n    ${list}`);
}
