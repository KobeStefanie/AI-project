// 公共 forge 封装 —— 给 gen-ca.js / gen-leaf.js 复用
//
// 设计要点：
//   - 输入输出统一用 PEM 字符串
//   - 文件 IO 集中在这里，使用方只关心证书逻辑
//   - 所有 attrs 用 ASCII（node-forge ASN.1 编码遇 UTF-8 多字节会出 "asn1 too long"）

const fs = require('fs');
const path = require('path');
const os = require('os');
const forge = require('node-forge');

const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const CERTS_DIR = path.join(PROJECT_ROOT, 'certs');

function ensureCertsDir() {
  if (!fs.existsSync(CERTS_DIR)) fs.mkdirSync(CERTS_DIR, { recursive: true });
}

function pathOf(name) {
  return path.join(CERTS_DIR, name);
}

function readPem(file) {
  return fs.readFileSync(pathOf(file), 'utf8');
}

function writePem(file, content) {
  ensureCertsDir();
  fs.writeFileSync(pathOf(file), content, 'utf8');
}

function exists(file) {
  return fs.existsSync(pathOf(file));
}

// 生成 2048 位 RSA 密钥对（同步，约 1-3 秒）
function genKeyPair() {
  return forge.pki.rsa.generateKeyPair({ bits: 2048, e: 0x10001 });
}

// 获取当前所有 LAN IPv4（用于 leaf SAN）
function getLanIPv4() {
  const ifaces = os.networkInterfaces();
  const ips = new Set();
  for (const name of Object.keys(ifaces)) {
    for (const ifc of ifaces[name]) {
      if (ifc.family === 'IPv4' && !ifc.internal) ips.add(ifc.address);
    }
  }
  return Array.from(ips);
}

// 当前主机名（用于 leaf CN / SAN）
function getHostname() {
  return os.hostname();
}

// 解析 PEM 格式 cert / key 回 forge 对象
function pemToCert(pem) {
  return forge.pki.certificateFromPem(pem);
}

function pemToPrivateKey(pem) {
  return forge.pki.privateKeyFromPem(pem);
}

// forge cert/key → PEM 字符串
function certToPem(cert) {
  return forge.pki.certificateToPem(cert);
}

function privateKeyToPem(key) {
  return forge.pki.privateKeyToPem(key);
}

module.exports = {
  forge,
  PROJECT_ROOT,
  CERTS_DIR,
  ensureCertsDir,
  pathOf,
  readPem,
  writePem,
  exists,
  genKeyPair,
  getLanIPv4,
  getHostname,
  pemToCert,
  pemToPrivateKey,
  certToPem,
  privateKeyToPem
};
