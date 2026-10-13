// 离线缓存：页面外壳 cache-first + 后台刷新；同步接口 /m/api/* 一律不经过缓存
// 参考 2-时间管理助手 踩过的坑：cache.match 要 ignoreSearch；cache.put 前要 clone()
const CACHE = 'tj-mobile-v1';
const SHELL = ['/', '/m.js', '/manifest.json', '/icon.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin || url.pathname.startsWith('/m/api/')) return;
  const key = e.request.mode === 'navigate' ? '/' : e.request;
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(key, { ignoreSearch: true });
    const net = fetch(e.request).then(r => {
      if (r.ok) c.put(key, r.clone());
      return r;
    }).catch(() => null);
    if (hit) { e.waitUntil(net); return hit; }
    return (await net) || new Response('离线，且还没有缓存过页面。先在和电脑同一 Wi-Fi 下打开一次。',
      { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
  }));
});
