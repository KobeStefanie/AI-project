// v2.16.0 休息细分迁移：把历史 code=0 的格子按事件名重分类为 0.1~0.9
//
// 用法：
//   node tools/migrate-rest-subcat.js            # 预演（dry-run），只打印结果，不写文件
//   node tools/migrate-rest-subcat.js --apply    # 正式写入 sync-data
//
// 特点：
//   - 只处理 code 恰好为 0 的格子（幂等，重复运行不会改动已是 0.x 的格子）
//   - 写入时刷新 cell.updatedAt 和 weekUpdatedAt，客户端「拉取全部周」即可同步
//   - 回退：backups/pre-rest-subcat-*/sync-data 为迁移前完整备份
'use strict';
const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'sync-data');
const APPLY = process.argv.includes('--apply');
const NAMES = ['睡觉', '吃喝', '散步', '出行', '刷手机', '卫生', '游戏', '社交', '其他'];

// 精确匹配优先（处理关键词会误判的标题）
const EXACT = {
  '洗澡+找手机': 0.6,
  '散步吃饭': 0.3,
  '出门干饭': 0.2,
  '买早点': 0.2,
  '休息0': 0.1,
  '吃饭0': 0.2,
  '整理资料': 0.9,
  '看书': 0.9,
  '抄字': 0.9,
  '等待': 0.9,
  '等待面试': 0.9,
  '放弃': 0.9,
  '低效': 0.9,
  '工资': 0.9,
  '领月饼': 0.9,
  '享受音乐': 0.9,
  '讨论钢琴和卡农': 0.8,
  '拼凑钢琴': 0.9,
  '回家休息': 0.9   // w31 回家那周整周记录，用户指定归「其他」（2026-09-29）
};

// 关键词规则：按顺序匹配，先命中先生效
const RULES = [
  [0.7, /原神|王者|游戏|kpl|ttg|黑客帝国/i],
  [0.5, /手机/],
  [0.8, /聊天|闲聊|交流|沟通|写信|电话|吵架|改天姐|🆚/],
  [0.9, /电影|摸鱼|超市|逛零食|快递|包裹|取钱|办卡|礼物|买东西|买日常|取书|投诉|打卡|发呆|凝神|选/],
  [0.3, /散步|出门|逛街|闲逛|运动|游玩|出来/],
  [0.6, /洗|打扫|理发|收拾|整理/],
  [0.2, /吃|饭|餐|夜宵|酸汤|蛋|面|米线|米皮|包子|蒸饺|烧烤|雪糕|羊肉粉|药/],
  [0.4, /回家|归家|在家|回来|昆明|贵阳|回宿舍|换家|退房|飞机|机场|高铁|车|出发|上班|下班|公司|办公室|过来|到这来|来这里|去|来/],
  [0.1, /睡|休息|躺|困|起床|身体不适/]
];

function classify(title) {
  const t = (title || '').trim();
  if (Object.prototype.hasOwnProperty.call(EXACT, t)) return EXACT[t];
  for (const [code, re] of RULES) if (re.test(t)) return code;
  return 0.9; // 兜底：其他
}

function isPlainZero(code) {
  return code === 0 || code === '0';
}

const yearDirs = fs.readdirSync(DATA_DIR).filter(n => /^\d{4}$/.test(n));
const byCode = {};         // code → { hours, titles: {title: hours} }
let changedCells = 0;
const now = Date.now();

for (const y of yearDirs) {
  const dir = path.join(DATA_DIR, y);
  for (const fn of fs.readdirSync(dir).filter(f => /^w\d+\.json$/.test(f)).sort()) {
    const fp = path.join(dir, fn);
    const data = JSON.parse(fs.readFileSync(fp, 'utf8'));
    let weekChanged = 0;
    for (const cell of Object.values(data.cells || {})) {
      if (!cell || !isPlainZero(cell.code)) continue;
      const newCode = classify(cell.title);
      const bucket = byCode[newCode] || (byCode[newCode] = { hours: 0, titles: {} });
      const t = (cell.title || '').trim() || '(空)';
      bucket.hours += 0.5;
      bucket.titles[t] = (bucket.titles[t] || 0) + 0.5;
      if (APPLY) {
        cell.code = newCode;
        cell.updatedAt = now;
        cell.updatedBy = 'migration-v2.16.0';
      }
      weekChanged++;
    }
    changedCells += weekChanged;
    if (APPLY && weekChanged > 0) {
      data.weekUpdatedAt = now;
      // 原子写入：先写 .tmp 再 rename（与 sync-server 一致）
      const tmp = fp + '.tmp';
      fs.writeFileSync(tmp, JSON.stringify(data, null, 2));
      fs.renameSync(tmp, fp);
    }
    if (weekChanged > 0) console.log(`${y}/${fn}: ${weekChanged} 格`);
  }
}

const total = changedCells * 0.5;
console.log(`\n${APPLY ? '【已写入】' : '【预演，未写入】'} 共 ${changedCells} 格 = ${total}h\n`);
Object.keys(byCode).map(Number).sort((a, b) => a - b).forEach(code => {
  const b = byCode[code];
  const pct = total ? (b.hours / total * 100).toFixed(1) : '0.0';
  const top = Object.entries(b.titles).sort((a, c) => c[1] - a[1])
    .map(([t, h]) => `${t}${h}`).join('、');
  console.log(`${code.toFixed(1)} ${NAMES[Math.round(code * 10) - 1]}  ${b.hours}h  ${pct}%`);
  console.log(`    ${top}`);
});
