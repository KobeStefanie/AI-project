// v2.11.1 合并逻辑验证
// 模拟 _applyServerWeekToLocal 在旧版（全量替换）vs 新版（逐条合并）下的行为

// 模拟数据：
// - 服务端有一个旧 cell（timestamp 1000）+ 一个较新 cell（timestamp 3000）
// - 本地有两个 cell：一个被服务端更新的（timestamp 500）+ 一个是离线新写的（timestamp 2000，服务器上没有）
// - 验证：新版保留离线编辑，旧版丢失

var serverCells = {
  "2026-05-27|07:00-07:30": { title: "服务端旧数据", code: 1.3, updatedAt: 1000 },
  "2026-05-27|08:00-08:30": { title: "服务端新数据", code: 2.1, updatedAt: 3000 }
};

var localCells = {
  "2026-05-27|07:00-07:30": { title: "本地旧数据-应被覆盖", code: 0 },
  "2026-05-27|09:00-09:30": { title: "离线编辑-应保留", code: 1.5 }
};

var localMetaCells = {
  "2026-05-27|07:00-07:30": 500,
  "2026-05-27|09:00-09:30": 2000
};

// ---- 旧版行为（v2.11.0） ----
function oldApply(server) {
  var result = {};
  for (var k in server) {
    var c = server[k];
    if (!c) continue;
    var emptyTitle = (c.title === '' || c.title == null);
    var emptyCode = (c.code === '' || c.code == null);
    if (emptyTitle && emptyCode) continue;
    result[k] = { title: c.title || '', code: c.code };
  }
  return result;
}

// ---- 新版行为（v2.11.1） ----
function newApply(server, local, meta) {
  var result = {};
  // 先复制本地
  for (var k in local) { result[k] = { title: local[k].title, code: local[k].code }; }
  // 逐条合并服务端
  for (var k in server) {
    var c = server[k];
    if (!c) continue;
    var serverTs = c.updatedAt || 0;
    var localTs = meta[k] || 0;
    var emptyTitle = (c.title === '' || c.title == null);
    var emptyCode = (c.code === '' || c.code == null);
    if (emptyTitle && emptyCode) {
      if (serverTs >= localTs) { delete result[k]; }
    } else if (serverTs >= localTs) {
      result[k] = { title: c.title || '', code: c.code };
    }
  }
  return result;
}

console.log("=== 旧版结果（全量替换） ===");
var oldResult = oldApply(serverCells);
for (var k in oldResult) console.log("  " + k + " -> " + JSON.stringify(oldResult[k]));
console.log("  键数: " + Object.keys(oldResult).length);

console.log("\n=== 新版结果（逐条合并） ===");
var newResult = newApply(serverCells, localCells, localMetaCells);
for (var k in newResult) console.log("  " + k + " -> " + JSON.stringify(newResult[k]));
console.log("  键数: " + Object.keys(newResult).length);

// 验证断言
var tests = [];
// 1. 旧版丢失了离线编辑
tests.push({
  name: "旧版丢失离线编辑 09:00-09:30",
  pass: !oldResult["2026-05-27|09:00-09:30"],
  expect: true
});
// 2. 新版保留了离线编辑
tests.push({
  name: "新版保留离线编辑 09:00-09:30",
  pass: newResult["2026-05-27|09:00-09:30"] && newResult["2026-05-27|09:00-09:30"].title === "离线编辑-应保留",
  expect: true
});
// 3. 新版用服务端数据覆盖了本地旧数据（serverTs=1000 >= localTs=500）
tests.push({
  name: "新版用服务端数据覆盖本地旧数据 07:00-07:30",
  pass: newResult["2026-05-27|07:00-07:30"] && newResult["2026-05-27|07:00-07:30"].title === "服务端旧数据",
  expect: true
});
// 4. 新版添加了服务端独有的数据
tests.push({
  name: "新版包含服务端独有 08:00-08:30",
  pass: newResult["2026-05-27|08:00-08:30"] && newResult["2026-05-27|08:00-08:30"].title === "服务端新数据",
  expect: true
});
// 5. 旧版只有 2 个键（丢失了离线编辑）
tests.push({
  name: "旧版键数=2（丢失离线编辑）",
  pass: Object.keys(oldResult).length === 2,
  expect: true
});
// 6. 新版有 3 个键（保留了离线编辑）
tests.push({
  name: "新版键数=3（保留离线编辑）",
  pass: Object.keys(newResult).length === 3,
  expect: true
});

var pass = 0, fail = 0;
for (var i = 0; i < tests.length; i++) {
  var t = tests[i];
  if (t.pass === t.expect) { pass++; console.log("  PASS: " + t.name); }
  else { fail++; console.log("  FAIL: " + t.name); }
}
console.log("\n" + pass + "/" + tests.length + " 通过" + (fail > 0 ? "  " + fail + " 失败" : ""));
process.exit(fail > 0 ? 1 : 0);
