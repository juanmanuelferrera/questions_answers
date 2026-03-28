const CACHE_NAME = 'rightq-v1';
const STATIC_ASSETS = ['/', '/manifest.json'];
const API_CACHE_NAME = 'rightq-api-v1';
const MAX_API_CACHE = 10;

// Install: cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME && k !== API_CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: network-first for API, cache-first for static
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // API calls: network-first
  if (url.pathname.startsWith('/api/')) {
    // Only cache GET requests or JSON responses
    if (event.request.method !== 'GET') return;
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const clone = response.clone();
          caches.open(API_CACHE_NAME).then(async cache => {
            cache.put(event.request, clone);
            // Limit API cache to MAX_API_CACHE entries
            const keys = await cache.keys();
            if (keys.length > MAX_API_CACHE) {
              for (let i = 0; i < keys.length - MAX_API_CACHE; i++) {
                cache.delete(keys[i]);
              }
            }
          });
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Static assets: cache-first
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        // Cache successful responses for same-origin
        if (response.ok && url.origin === self.location.origin) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      });
    })
  );
});
