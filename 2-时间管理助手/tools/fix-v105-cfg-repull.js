// v105 补丁：刷新服务端各周 config.updatedAt + weekUpdatedAt，让客户端重新拉取正确配置
//   背景：v104 客户端拉取 10 项配置时，normalizeConfigNames 因长度不符把 qwNames 重置为旧默认值
//         （1.3 注会变现 / 1.4 读书，与实际相反），且 meta.config 已记为服务端时间戳，v105 不会再拉
//   用法：node tools/fix-v105-cfg-repull.js          （dry-run）
//         node tools/fix-v105-cfg-repull.js --apply  （写入）
'use strict';
const fs = require('fs');
const path = require('path');

const DIR = path.join(__dirname, '..', 'sync-data', '2026');
const APPLY = process.argv.includes('--apply');
const EXPECT = ['AI', '心理咨询', '读书', '注会变现', '投资', '自我管理'];
const now = Date.now();

let n = 0;
for (const f of fs.readdirSync(DIR).filter(f => /^w\d+\.json$/.test(f)).sort()) {
  const file = path.join(DIR, f);
  const d = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (!d.config) continue;
  const head = (d.config.qwNames || []).slice(0, 6);
  if (JSON.stringify(head) !== JSON.stringify(EXPECT)) {
    console.log(`${f}: qwNames 与预期不符，跳过 → ${head.join('/')}`);
    continue;
  }
  console.log(`${f}: config.updatedAt ${d.config.updatedAt} → ${now}`);
  if (APPLY) {
    d.config.updatedAt = now;
    d.config.updatedBy = 'fix-v105-cfg';
    d.weekUpdatedAt = now;
    const tmp = file + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(d, null, 2));
    fs.renameSync(tmp, file);
  }
  n++;
}
console.log(`${APPLY ? '已写入' : 'dry-run'}：${n} 周`);
