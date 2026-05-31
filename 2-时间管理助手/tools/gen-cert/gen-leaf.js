// 生成由 CA 签发的服务器证书（leaf）—— 每次运行均覆盖
//
// SAN 自动覆盖：localhost / 127.0.0.1 / <hostname> / <hostname>.local / <所有 LAN IPv4>
// LAN IP 或主机名变化后只需重跑此脚本，iPhone 不需要任何操作（CA 不变）。
//
// 用法：
//   node gen-leaf.js               生成 leaf 证书并写入 certs/leaf-* 三件套

const lib = require('./lib-forge');
const { forge } = lib;

// 前置：CA 必须已经存在
if (!lib.exists('ca-cert.pem') || !lib.exists('ca-key.pem')) {
  console.error('✗ 未找到 CA。请先运行：node gen-ca.js');
  process.exit(1);
}

const hostname = lib.getHostname();
const lanIPs = lib.getLanIPv4();

// 构造 SAN
const altNames = [
  { type: 2, value: 'localhost' },                  // DNS
  { type: 7, ip: '127.0.0.1' },                     // IP
  { type: 2, value: hostname + '.local' },          // mDNS
  { type: 2, value: hostname },                     // NetBIOS
  ...lanIPs.map(ip => ({ type: 7, ip }))
];

console.log('==== gen-leaf.js ====');
console.log('主机名：', hostname);
console.log('SAN 列表：');
for (const s of altNames) {
  if (s.type === 2) console.log('  DNS:', s.value);
  if (s.type === 7) console.log('  IP :', s.ip);
}
console.log();

// 加载 CA
const caCert = lib.pemToCert(lib.readPem('ca-cert.pem'));
const caKey  = lib.pemToPrivateKey(lib.readPem('ca-key.pem'));

console.log('生成 leaf 私钥（耗时 1-3 秒）...');
const leafKeys = lib.genKeyPair();
const leafCert = forge.pki.createCertificate();
leafCert.publicKey = leafKeys.publicKey;
leafCert.serialNumber = '02' + Date.now().toString(16);
leafCert.validity.notBefore = new Date();
leafCert.validity.notAfter = new Date();
leafCert.validity.notAfter.setFullYear(leafCert.validity.notBefore.getFullYear() + 2);

const leafAttrs = [
  { name: 'commonName', value: hostname },
  { name: 'organizationName', value: 'Time Planner Local' },
  { name: 'organizationalUnitName', value: 'LAN Server' }
];
leafCert.setSubject(leafAttrs);
// issuer = CA 的 subject
leafCert.setIssuer(caCert.subject.attributes);

leafCert.setExtensions([
  { name: 'basicConstraints', cA: false, critical: true },
  {
    name: 'keyUsage',
    digitalSignature: true,
    keyEncipherment: true,
    critical: true
  },
  { name: 'extKeyUsage', serverAuth: true, clientAuth: true },
  { name: 'subjectAltName', altNames },
  { name: 'subjectKeyIdentifier' },
  // 关联 CA 的 subjectKeyIdentifier，让 RFC 5280 风格的链校验能通过
  {
    name: 'authorityKeyIdentifier',
    keyIdentifier: caCert.generateSubjectKeyIdentifier().getBytes()
  }
]);

// 用 CA 私钥签发
leafCert.sign(caKey, forge.md.sha256.create());

const leafCertPem = lib.certToPem(leafCert);
const caCertPem   = lib.readPem('ca-cert.pem');
const leafKeyPem  = lib.privateKeyToPem(leafKeys.privateKey);
const chainPem    = leafCertPem + caCertPem;   // chain：leaf 在前，CA 在后

lib.writePem('leaf-cert.pem', leafCertPem);
lib.writePem('leaf-cert-chain.pem', chainPem);
lib.writePem('leaf-key.pem', leafKeyPem);

console.log('✓ 写入', lib.pathOf('leaf-cert.pem'));
console.log('✓ 写入', lib.pathOf('leaf-cert-chain.pem'), '（chain：leaf + CA，server 用）');
console.log('✓ 写入', lib.pathOf('leaf-key.pem'));
console.log();

// 自校验（用 Node 原生 X509，比 forge 的 verifyCertificateChain 更宽容）
try {
  const { X509Certificate } = require('crypto');
  const leafX = new X509Certificate(leafCertPem);
  const caX = new X509Certificate(caCertPem);
  const issued = leafX.checkIssued(caX);
  const verified = leafX.verify(caX.publicKey);
  if (!issued || !verified) {
    console.error('✗ Node 自校验失败：checkIssued=' + issued + ' verify=' + verified);
    process.exit(2);
  }
  console.log('✓ 自校验通过：leaf 由 CA 签发，Node TLS 可加载');
} catch (e) {
  console.error('✗ 自校验异常：', e.message);
  process.exit(2);
}

// leaf SHA-256 指纹
const der = forge.asn1.toDer(forge.pki.certificateToAsn1(leafCert)).getBytes();
const sha256 = forge.md.sha256.create();
sha256.update(der);
const fp = sha256.digest().toHex().match(/.{2}/g).join(':');
console.log('Leaf SHA-256 指纹：', fp);
console.log();
console.log('Leaf 有效期：', leafCert.validity.notBefore.toISOString(), '~', leafCert.validity.notAfter.toISOString());
console.log();
console.log('下一步：');
console.log('  重启 src/server.js 与 sync-server.js 以加载新证书');
