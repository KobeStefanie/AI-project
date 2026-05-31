import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let db;

const DEFAULT_DB_PATH = path.resolve(__dirname, '../../../data/inspirations.db');

export function getDb() {
  if (!db) {
    const dbPath = path.resolve(process.cwd(), process.env.DATABASE_PATH || DEFAULT_DB_PATH);
    fs.mkdirSync(path.dirname(dbPath), { recursive: true });
    db = new Database(dbPath);
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
    runMigrations(db);
  }
  return db;
}

function runMigrations(database) {
  database.exec(`
    CREATE TABLE IF NOT EXISTS inspirations (
      id TEXT PRIMARY KEY,
      content TEXT DEFAULT '',
      summary TEXT DEFAULT '',
      transcript TEXT DEFAULT '',
      transcript_quality TEXT,
      tags TEXT NOT NULL DEFAULT '[]',
      keywords TEXT NOT NULL DEFAULT '[]',
      mood TEXT,
      status TEXT NOT NULL DEFAULT 'raw',
      context TEXT DEFAULT '',
      expanded TEXT DEFAULT '',
      linked_ids TEXT NOT NULL DEFAULT '[]',
      source_types TEXT NOT NULL DEFAULT '[]',
      source_detail TEXT,
      sync_status TEXT NOT NULL DEFAULT 'synced',
      media_status TEXT NOT NULL DEFAULT 'none',
      ai_status TEXT NOT NULL DEFAULT 'pending',
      ai_error TEXT,
      processed_at TEXT,
      device TEXT NOT NULL DEFAULT 'windows',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      CHECK (status IN ('raw', 'expanded', 'realized', 'archived', 'abandoned')),
      CHECK (sync_status IN ('synced', 'pending', 'failed')),
      CHECK (media_status IN ('none', 'pending', 'uploading', 'uploaded', 'failed')),
      CHECK (ai_status IN ('pending', 'processing', 'done', 'failed'))
    );

    CREATE TABLE IF NOT EXISTS media_assets (
      id TEXT PRIMARY KEY,
      inspiration_id TEXT NOT NULL,
      type TEXT NOT NULL,
      original_name TEXT NOT NULL,
      filename TEXT NOT NULL,
      mime_type TEXT NOT NULL,
      size INTEGER NOT NULL,
      duration REAL,
      width INTEGER,
      height INTEGER,
      url TEXT NOT NULL,
      upload_status TEXT NOT NULL DEFAULT 'uploaded',
      created_at TEXT NOT NULL,
      FOREIGN KEY (inspiration_id) REFERENCES inspirations(id) ON DELETE CASCADE,
      CHECK (type IN ('audio', 'image', 'video')),
      CHECK (upload_status IN ('pending', 'uploading', 'uploaded', 'failed'))
    );

    CREATE TABLE IF NOT EXISTS themes (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      description TEXT DEFAULT '',
      color TEXT NOT NULL DEFAULT '#f97316',
      notes TEXT DEFAULT '',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS theme_inspirations (
      theme_id TEXT NOT NULL,
      inspiration_id TEXT NOT NULL,
      created_at TEXT NOT NULL,
      PRIMARY KEY (theme_id, inspiration_id),
      FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE,
      FOREIGN KEY (inspiration_id) REFERENCES inspirations(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_inspirations_status ON inspirations(status);
    CREATE INDEX IF NOT EXISTS idx_inspirations_created_at ON inspirations(created_at);
    CREATE INDEX IF NOT EXISTS idx_media_assets_inspiration ON media_assets(inspiration_id);
    CREATE INDEX IF NOT EXISTS idx_theme_inspirations_note ON theme_inspirations(inspiration_id);
  `);
}

export function closeDb() {
  if (db) {
    db.close();
    db = null;
  }
}
