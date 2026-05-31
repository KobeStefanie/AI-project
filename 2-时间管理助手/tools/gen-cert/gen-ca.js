// 生成 CA 根证书 + 私钥（10 年有效）
//
// **幂等**：如果 certs/ca-cert.pem 已存在则跳过，不会覆盖。
// 这是为了避免一旦 CA 被覆盖，iPhone 上已装的旧 CA 信任会因指纹变化失效。
// 若确实需要重做 CA（例如私钥泄漏），先手动删 certs/ca-cert.pem 与 certs/ca-key.pem 再跑此脚本。
//
// 用法：
//   node gen-ca.js                  生成 CA（若已存在则跳过）
//   node gen-ca.js --force          强制重新生成（覆盖，iPhone 已装信任作废）

const lib = require('./lib-forge');
const { forge } = lib;

const FORCE = process.argv.includes('--force');

if (lib.exists('ca-cert.pem') && lib.exists('ca-key.pem') && !FORCE) {
  console.log('==== gen-ca.js ====');
  console.log('✓ certs/ca-cert.pem 与 ca-key.pem 已存在，跳过（幂等）');
  console.log('  若确实需要重做 CA，先手动删两个文件再运行，或加 --force 强制覆盖。');
  console.log('  注意：覆盖后 iPhone 上已装的旧 CA 信任会因指纹变化失效，需要重新安装信任。');
  process.exit(0);
}

console.log('==== gen-ca.js ====');
console.log('生成 CA 根证书（耗时 1-3 秒）...');

const caKeys = lib.genKeyPair();
const caCert = forge.pki.createCertificate();
caCert.publicKey = caKeys.publicKey;
// 序列号：固定为时间戳的十六进制（首位必须非 8 以上以避免被解释为负数）
caCert.serialNumber = '01' + Date.now().toString(16);
caCert.validity.notBefore = new Date();
caCert.validity.notAfter = new Date();
caCert.validity.notAfter.setFullYear(caCert.validity.notBefore.getFullYear() + 10);

// CA 主体属性：所有值必须 ASCII（避免 ASN.1 编码问题）
const caAttrs = [
  { name: 'commonName', value: 'Time Planner Personal CA' },
  { name: 'organizationName', value: 'Time Planner Personal' },
  { name: 'organizationalUnitName', value: 'Self-signed Root CA' }
];
caCert.setSubject(caAttrs);
caCert.setIssuer(caAttrs); // self-signed

caCert.setExtensions([
  {
    name: 'basicConstraints',
    cA: true,
    pathLenConstraint: 0,           // 只能签 1 层 leaf
    critical: true
  },
  {
    name: 'keyUsage',
    keyCertSign: true,              // 必须，能签发其他证书
    cRLSign: true,                  // 撤销列表（备用）
    digitalSignature: true,
    critical: true
  },
  { name: 'subjectKeyIdentifier' }
]);

caCert.sign(caKeys.privateKey, forge.md.sha256.create());

lib.writePem('ca-cert.pem', lib.certToPem(caCert));
lib.writePem('ca-cert.crt', lib.certToPem(caCert));  // .crt 扩展名供 iPhone Safari 识别
lib.writePem('ca-key.pem', lib.privateKeyToPem(caKeys.privateKey));

console.log('✓ 写入', lib.pathOf('ca-cert.pem'));
console.log('✓ 写入', lib.pathOf('ca-cert.crt'), '（iPhone 安装用）');
console.log('✓ 写入', lib.pathOf('ca-key.pem'), '（CA 私钥，必须保密）');
console.log();

// 打印 CA 指纹（SHA-256），方便后续核对
const der = forge.asn1.toDer(forge.pki.certificateToAsn1(caCert)).getBytes();
const sha256 = forge.md.sha256.create();
sha256.update(der);
const fp = sha256.digest().toHex().match(/.{2}/g).join(':');
console.log('CA SHA-256 指纹：', fp);
console.log();
console.log('CA 有效期：', caCert.validity.notBefore.toISOString(), '~', caCert.validity.notAfter.toISOString());
console.log();
console.log('下一步：');
console.log('  node gen-leaf.js                生成由 CA 签发的服务器证书');
