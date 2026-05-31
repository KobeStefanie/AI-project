// 灵感收集器 - API 客户端

const API_BASE = '/api';

const api = {
  async get(url) {
    const res = await fetch(API_BASE + url);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async post(url, body) {
    const res = await fetch(API_BASE + url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async put(url, body) {
    const res = await fetch(API_BASE + url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async del(url) {
    const res = await fetch(API_BASE + url, { method: 'DELETE' });
    if (!res.ok && res.status !== 204) throw new Error(await res.text());
    return res.status === 204 ? null : res.json();
  },
  async upload(url, formData, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', API_BASE + url);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      };
      xhr.onload = () => {
        try { resolve(JSON.parse(xhr.responseText)); }
        catch { resolve(xhr.responseText); }
      };
      xhr.onerror = () => reject(new Error('上传失败'));
      xhr.send(formData);
    });
  }
};

// 状态
const state = {
  notes: [],
  themes: [],
  dashboard: null,
  currentView: 'capture',
  isMobile: window.innerWidth < 768,
  mediaRecorder: null,
  audioChunks: [],
  isRecording: false,
  selectedNotes: new Set(),
  filters: { status: '', mood: '', source: '', media: '', q: '', from: '', to: '' },
  listOffset: 0,
  hasMore: true
};

// 心情映射
const MOOD_MAP = {
  excited: { label: '兴奋', icon: 'fa-smile-o', color: 'text-yellow-500' },
  calm: { label: '平和', icon: 'fa-meh-o', color: 'text-gray-400' },
  low: { label: '低落', icon: 'fa-frown-o', color: 'text-blue-500' },
  confused: { label: '困惑', icon: 'fa-question-circle-o', color: 'text-purple-500' },
  anxious: { label: '焦虑', icon: 'fa-meh-o', color: 'text-red-400' },
  inspired: { label: '受启发', icon: 'fa-lightbulb-o', color: 'text-amber-400' },
  determined: { label: '坚定', icon: 'fa-hand-rock-o', color: 'text-green-500' }
};

const STATUS_MAP = {
  raw: { label: '原始', icon: 'fa-circle-o', color: 'text-gray-400' },
  expanded: { label: '已扩展', icon: 'fa-dot-circle-o', color: 'text-blue-500' },
  realized: { label: '已实现', icon: 'fa-check-circle-o', color: 'text-green-500' },
  archived: { label: '已归档', icon: 'fa-archive', color: 'text-yellow-600' },
  abandoned: { label: '已放弃', icon: 'fa-times-circle-o', color: 'text-red-400' }
};

const CONTEXT_OPTIONS = ['', '播客', '聊天', '读书', '做梦', '开会', '路上', '项目中', '其他'];

// 工具函数
function formatTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) {
    return `今天 ${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`;
  }
  const month = (d.getMonth() + 1).toString().padStart(2, '0');
  const day = d.getDate().toString().padStart(2, '0');
  const time = `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`;
  return `${month}-${day} ${time}`;
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
