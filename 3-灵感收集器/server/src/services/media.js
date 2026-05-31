import path from 'path';
import fs from 'fs';
import multer from 'multer';
import { nanoid } from 'nanoid';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DEFAULT_UPLOAD_ROOT = path.resolve(__dirname, '../../../uploads');

const TYPE_DIR = {
  audio: 'audio',
  image: 'images',
  video: 'videos'
};

const ALLOWED_TYPES = {
  audio: /^audio\//,
  image: /^image\//,
  video: /^video\//
};

export const MAX_VIDEO_BYTES = Number(process.env.MAX_VIDEO_BYTES || 1024 * 1024 * 1024);
export const MAX_VIDEO_DURATION_SECONDS = Number(process.env.MAX_VIDEO_DURATION_SECONDS || 600);

export function uploadRoot() {
  return path.resolve(process.cwd(), process.env.UPLOAD_DIR || DEFAULT_UPLOAD_ROOT);
}

export function getMediaType(mimeType = '') {
  if (ALLOWED_TYPES.audio.test(mimeType)) return 'audio';
  if (ALLOWED_TYPES.image.test(mimeType)) return 'image';
  if (ALLOWED_TYPES.video.test(mimeType)) return 'video';
  return null;
}

function monthPath(date = new Date()) {
  const year = String(date.getFullYear());
  const month = String(date.getMonth() + 1).padStart(2, '0');
  return { year, month };
}

const storage = multer.diskStorage({
  destination(req, file, cb) {
    const type = getMediaType(file.mimetype);
    if (!type) return cb(new Error('不支持的媒体类型'));
    const { year, month } = monthPath();
    const dir = path.join(uploadRoot(), TYPE_DIR[type], year, month);
    fs.mkdirSync(dir, { recursive: true });
    cb(null, dir);
  },
  filename(req, file, cb) {
    const ext = path.extname(file.originalname || '') || mimeToExt(file.mimetype);
    cb(null, `${nanoid()}${ext}`);
  }
});

export const upload = multer({
  storage,
  limits: {
    fileSize: MAX_VIDEO_BYTES
  },
  fileFilter(req, file, cb) {
    const type = getMediaType(file.mimetype);
    if (!type) return cb(new Error('仅支持音频、图片和视频文件'));
    cb(null, true);
  }
});

export function toPublicUrl(filePath, type) {
  const relative = path.relative(uploadRoot(), filePath).split(path.sep).join('/');
  return `/uploads/${relative}`;
}

export function removeFileByUrl(url) {
  if (!url || !url.startsWith('/uploads/')) return;
  const relative = url.replace('/uploads/', '');
  const fullPath = path.join(uploadRoot(), relative);
  if (fs.existsSync(fullPath)) fs.unlinkSync(fullPath);
}

export function validateUploadedMedia(file, existingCounts = {}) {
  const type = getMediaType(file.mimetype);
  if (!type) {
    const error = new Error('不支持的媒体类型');
    error.status = 400;
    throw error;
  }

  if (type === 'video' && file.size > MAX_VIDEO_BYTES) {
    const error = new Error('视频大小必须小于 1GB');
    error.status = 400;
    throw error;
  }

  if (type === 'audio' && existingCounts.audio >= 1) {
    const error = new Error('每条灵感最多只能包含 1 个主音频');
    error.status = 400;
    throw error;
  }

  if (type === 'video' && existingCounts.video >= 1) {
    const error = new Error('每条灵感最多只能包含 1 个视频');
    error.status = 400;
    throw error;
  }

  return type;
}

function mimeToExt(mimeType) {
  if (mimeType === 'image/jpeg') return '.jpg';
  if (mimeType === 'image/png') return '.png';
  if (mimeType === 'image/webp') return '.webp';
  if (mimeType === 'audio/webm') return '.webm';
  if (mimeType === 'audio/mpeg') return '.mp3';
  if (mimeType === 'video/mp4') return '.mp4';
  if (mimeType === 'video/quicktime') return '.mov';
  return '';
}
