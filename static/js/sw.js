/**
 * sw.js — Service Worker para Sports-Max SENA
 * CP-12: Notificaciones Push
 */
const CACHE_NAME = 'sportsmax-v1';
const URLS_CACHE = [
  '/',
  '/habitos/',
  '/habitos/mis-rutinas/',
  '/habitos/sueno/',
  '/habitos/mi-progreso/',
];

// ── Instalación ────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(URLS_CACHE)).catch(() => {})
  );
  self.skipWaiting();
});

// ── Activación ──────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Push recibido ───────────────────────────────────────────
self.addEventListener('push', event => {
  let data = {
    title: '¡Sports-Max SENA! 🏋️',
    body:  'Tienes un recordatorio de salud pendiente.',
    icon:  '/static/img/logo.png',
    badge: '/static/img/badge.png',
    url:   '/habitos/mi-progreso/',
  };

  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (e) {
      data.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body:  data.body,
      icon:  data.icon,
      badge: data.badge,
      data:  { url: data.url },
      vibrate: [100, 50, 100],
      actions: [
        { action: 'ver',   title: '👀 Ver ahora' },
        { action: 'luego', title: '⏰ Recordar más tarde' },
      ],
    })
  );
});

// ── Clic en notificación ────────────────────────────────────
self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'luego') {
    // Programar otro push local en 30 min (aproximado)
    return;
  }

  const url = event.notification.data?.url || '/habitos/mi-progreso/';
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(clientList => {
      for (const client of clientList) {
        if (client.url === url && 'focus' in client) return client.focus();
      }
      return clients.openWindow ? clients.openWindow(url) : null;
    })
  );
});

// ── Fetch (cache-first para recursos estáticos) ─────────────
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/api/')) return; // No cachear APIs

  event.respondWith(
    caches.match(event.request).then(
      cached => cached || fetch(event.request).catch(() => cached)
    )
  );
});
