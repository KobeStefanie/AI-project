// ⚠️  Deprecated（自 v2.11.0 起）
//
// 旧的单层自签流程已废弃。请改用新的 CA + leaf 两层架构：
//
//   - 首次：  node gen-all.js     （生成 CA 永久 + leaf 当前 SAN）
//   - 重生成：node gen-leaf.js    （CA 不变，iPhone 信任继续有效）
//
// 此文件保留只是为了避免错误调用旧脚本仍然产单层证书覆盖新文件。
// 直接调用此脚本会打印提示并退出。

console.error('⚠️  gen-cert.js 已废弃 (v2.11.0 起)');
console.error();
console.error('请改用：');
console.error('  node gen-all.js      首次：生成 CA + leaf');
console.error('  node gen-leaf.js     之后：只重新生成 leaf');
console.error();
console.error('详细背景：项目根 plans/v2.11.0-https-and-offline-queue.md 与');
console.error('         需求文档.md §21.17。');
process.exit(2);
