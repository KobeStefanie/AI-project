import 'dotenv/config';
import express from 'express';
import https from 'https';
import http from 'http';
import fs from 'fs';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { notFound, errorHandler } from './middleware/error.js';
import { notesRouter } from './routes/notes.js';
import { themesRouter } from './routes/themes.js';
import { mediaRouter } from './routes/media.js';
import { calendarRouter } from './routes/calendar.js';
import { timelineRouter } from './routes/timeline.js';
import { dashboardRouter } from './routes/dashboard.js';
import { reviewRouter } from './routes/review.js';
import { analyzeRouter } from './routes/analyze.js';
import { uploadRoot } from './services/media.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const HTTP_PORT = parseInt(process.env.HTTP_PORT || '3000', 10);
const HTTPS_PORT = parseInt(process.env.HTTPS_PORT || '3443', 10);
const HOST = process.env.HOST || '0.0.0.0';

app.use(cors());
app.use(express.json());

const frontendRoot = path.resolve(__dirname, '../../');
app.use(express.static(frontendRoot));
app.use('/uploads', express.static(uploadRoot()));

app.get('/api/health', (_req, res) => res.json({ status: 'ok' }));

app.use('/api/notes', notesRouter);
app.use('/api/themes', themesRouter);
app.use('/api', mediaRouter);
app.use('/api/calendar', calendarRouter);
app.use('/api/timeline', timelineRouter);
app.use('/api/dashboard', dashboardRouter);
app.use('/api/review', reviewRouter);
app.use('/api', analyzeRouter);

app.use(notFound);
app.use(errorHandler);

// HTTP
http.createServer(app).listen(HTTP_PORT, HOST, () => {
  console.log(`HTTP 已启动：http://${HOST}:${HTTP_PORT}`);
});

// HTTPS（iPhone 必须使用 HTTPS，否则 localStorage 不持久化）
const CERT_DIR = path.resolve(__dirname, '../certs');
const certFile = path.join(CERT_DIR, 'leaf-cert.pem');
const keyFile = path.join(CERT_DIR, 'leaf-key.pem');

if (fs.existsSync(certFile) && fs.existsSync(keyFile)) {
  const httpsOpts = {
    cert: fs.readFileSync(certFile),
    key: fs.readFileSync(keyFile)
  };
  https.createServer(httpsOpts, app).listen(HTTPS_PORT, HOST, () => {
    console.log(`HTTPS 已启动：https://${HOST}:${HTTPS_PORT}`);
  });
} else {
  console.log('未找到 SSL 证书，跳过 HTTPS。iPhone 端数据将不会持久化。');
}
