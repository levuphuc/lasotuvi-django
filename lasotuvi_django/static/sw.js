const CACHE_NAME = 'lasotuvi-v1.0.0';
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/jquery.min.js',
  '/static/jsrender.min.js',
  '/static/html2canvas.js',
  '/static/lstv.min.js',
  '/static/zebra_tooltips.js',
  '/static/texture.jpg',
  '/static/texture1.jpg',
  '/static/texture2.jpg',
  '/static/favicon.ico'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
      .catch((error) => {
        console.error('Cache installation failed:', error);
      })
  );
});

// Fetch event - serve cached content when possible
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }
        
        // Clone the request for fetching
        const fetchRequest = event.request.clone();
        
        return fetch(fetchRequest).then((response) => {
          // Check if we received a valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }
          
          // Clone the response for caching
          const responseToCache = response.clone();
          
          // Cache new resources (only for static assets)
          if (event.request.url.includes('/static/') || event.request.url.includes('/api')) {
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });
          }
          
          return response;
        }).catch(() => {
          // Return offline fallback for navigation requests
          if (event.request.mode === 'navigate') {
            return caches.match('/');
          }
        });
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  const cacheWhitelist = [CACHE_NAME];
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background sync for API requests (if supported)
self.addEventListener('sync', (event) => {
  if (event.tag === 'api-sync') {
    event.waitUntil(syncApiRequests());
  }
});

async function syncApiRequests() {
  // Handle background sync for failed API requests
  try {
    const requests = await getStoredRequests();
    for (const request of requests) {
      await fetch(request.url, request.options);
    }
    await clearStoredRequests();
  } catch (error) {
    console.error('Sync failed:', error);
  }
}

async function getStoredRequests() {
  // Retrieve stored requests from IndexedDB
  return [];
}

async function clearStoredRequests() {
  // Clear stored requests from IndexedDB
}