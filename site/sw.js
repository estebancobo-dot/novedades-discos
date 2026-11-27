// Funciona sin conexión: todo se pide primero a la red (así se ven siempre las
// novedades y los cambios de la web) y, si no hay red, se usa lo último guardado.
const VERSION = "v2";
const CARCASA = ["./", "index.html", "app.js", "styles.css", "manifest.webmanifest", "icono-192.png", "icono-512.png"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(CARCASA)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith(fetch(e.request).then(r => {
    if (r.ok) { const copia = r.clone(); caches.open(VERSION).then(c => c.put(e.request, copia)); }
    return r;
  }).catch(() => caches.match(e.request)));
});
