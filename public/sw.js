// Vedabase RAG Service Worker
// Provides offline capability and caching

const CACHE_NAME = 'vedabase-v1.1';
const RUNTIME_CACHE = 'vedabase-runtime-v1';

// Assets to cache on install
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/apple-touch-icon.png'
];

// Install event - cache core assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Precaching core assets');
        return cache.addAll(PRECACHE_URLS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME && name !== RUNTIME_CACHE)
            .map((name) => {
              console.log('Service Worker: Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // For API requests, try network first, fallback to cache
  if (url.pathname.includes('workers.dev')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone response to cache it
          const responseClone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // Network failed, try cache
          return caches.match(request);
        })
    );
    return;
  }

  // For static assets, cache first, fallback to network
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }

        return fetch(request).then((response) => {
          // Don't cache non-successful responses
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone response to cache it
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });

          return response;
        });
      })
  );
});

// Background sync for failed searches (future enhancement)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-searches') {
    event.waitUntil(syncSearches());
  }
});

async function syncSearches() {
  // Sync any pending searches when back online
  console.log('Service Worker: Syncing pending searches');
}

// Push notifications (future enhancement)
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'Daily wisdom awaits',
    icon: '/apple-touch-icon.png',
    badge: '/apple-touch-icon.png',
    vibrate: [200, 100, 200],
    tag: 'vedabase-notification',
    requireInteraction: false
  };

  event.waitUntil(
    self.registration.showNotification('Vedabase Wisdom', options)
  );
});
