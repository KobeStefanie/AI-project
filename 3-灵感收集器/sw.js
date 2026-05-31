const CACHE_NAME = 'inspiration-cache-v1';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/src/app-core.js',
  '/src/app.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // 跳过非 GET 请求和 API 请求
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/api/')) {
    // API: 网络优先，失败时尝试缓存
    event.respondWith(
      fetch(event.request)
        .then((res) => {
          const cloned = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, cloned));
          return res;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // 静态资源: 缓存优先
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
