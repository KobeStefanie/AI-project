// Minimal PNG generator - 192x192 solid blue (#2563eb) with white "TM" text
// No external dependencies - pure Node.js
const fs = require('fs');
const zlib = require('zlib');
const path = require('path');

const W = 192, H = 192;
const R = 37, G2 = 99, B = 235; // #2563eb

// Build raw pixel data: each row = filter byte (0) + RGBA pixels
const rows = [];
for (let y = 0; y < H; y++) {
  const row = Buffer.alloc(1 + W * 4);
  row[0] = 0; // filter type: None
  for (let x = 0; x < W; x++) {
    row[1 + x * 4 + 0] = R;
    row[1 + x * 4 + 1] = G2;
    row[1 + x * 4 + 2] = B;
    row[1 + x * 4 + 3] = 255;
  }
  rows.push(row);
}
const rawData = Buffer.concat(rows);
const compressed = zlib.deflateSync(rawData);

function crc32(buf) {
  let c = 0xFFFFFFFF;
  const table = [];
  for (let i = 0; i < 256; i++) {
    let v = i;
    for (let j = 0; j < 8; j++) v = (v & 1) ? 0xEDB88320 ^ (v >>> 1) : (v >>> 1);
    table[i] = v;
  }
  for (let i = 0; i < buf.length; i++) c = table[(c ^ buf[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

function chunk(type, data) {
  const typeBuf = Buffer.from(type, 'ascii');
  const lenBuf = Buffer.alloc(4); lenBuf.writeUInt32BE(data.length, 0);
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([lenBuf, typeBuf, data, crcBuf]);
}

const ihdr = Buffer.alloc(13);
ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(H, 4);
ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;

const sig = Buffer.from([137,80,78,71,13,10,26,10]);
const png = Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', compressed), chunk('IEND', Buffer.alloc(0))]);

const dest = path.join('D:\\AI-项目\\2-时间管理助手\\src', 'icon-192.png');
fs.writeFileSync(dest, png);
console.log('icon-192.png created:', dest, png.length, 'bytes');
