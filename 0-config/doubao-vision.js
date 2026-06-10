/**
 * 豆包视觉识别工具
 * 用法: node doubao-vision.js <图片路径> [提示词]
 * 示例: node doubao-vision.js photo.jpg "这张图片里有什么？"
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// 读取配置
const envPath = path.resolve(__dirname, '.doubao-env');
if (!fs.existsSync(envPath)) {
  console.error('❌ 未找到 .doubao-env 配置文件');
  process.exit(1);
}
const env = {};
fs.readFileSync(envPath, 'utf-8').split('\n').forEach(line => {
  const trimmed = line.trim();
  if (trimmed && !trimmed.startsWith('#')) {
    const [k, ...v] = trimmed.split('=');
    env[k.trim()] = v.join('=').trim();
  }
});

const API_KEY = env.DOUBAO_API_KEY;
const MODEL = env.DOUBAO_MODEL || 'Doubao-Seed-2.0-lite';
const BASE_URL = env.DOUBAO_BASE_URL || 'https://ark.cn-beijing.volces.com/api/v3';

// 解析参数
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('用法: node doubao-vision.js <图片路径> [提示词]');
  console.error('示例: node doubao-vision.js photo.jpg "描述这张图片"');
  process.exit(1);
}

const imagePath = args[0];
const prompt = args.slice(1).join(' ') || '请详细描述这张图片的内容，包括场景、物体、人物、文字、颜色、构图等。';

if (!fs.existsSync(imagePath)) {
  console.error(`❌ 图片不存在: ${imagePath}`);
  process.exit(1);
}

// 读取图片并转 base64
const imageBuffer = fs.readFileSync(imagePath);
const ext = path.extname(imagePath).toLowerCase();
const mimeMap = {
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.bmp': 'image/bmp',
};
const mimeType = mimeMap[ext] || 'image/jpeg';
const base64Image = imageBuffer.toString('base64');
const dataUrl = `data:${mimeType};base64,${base64Image}`;

// 构建请求
const requestBody = JSON.stringify({
  model: MODEL,
  messages: [
    {
      role: 'user',
      content: [
        { type: 'image_url', image_url: { url: dataUrl } },
        { type: 'text', text: prompt },
      ],
    },
  ],
  max_tokens: 2000,
});

const url = new URL(BASE_URL + '/chat/completions');
const options = {
  hostname: url.hostname,
  port: url.port || 443,
  path: url.pathname,
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Length': Buffer.byteLength(requestBody),
  },
};

// 发送请求
const transport = url.protocol === 'https:' ? https : http;
const req = transport.request(options, (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    if (res.statusCode !== 200) {
      console.error(`❌ API 错误 (${res.statusCode}):`, data);
      process.exit(1);
    }
    try {
      const result = JSON.parse(data);
      const content = result.choices?.[0]?.message?.content || data;
      console.log(content);
    } catch {
      console.log(data);
    }
  });
});

req.on('error', (err) => {
  console.error('❌ 请求失败:', err.message);
  process.exit(1);
});

req.write(requestBody);
req.end();
