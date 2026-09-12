const APP_CACHE = "sococo-app-v15";
const TILE_CACHE = "sococo-tiles-v15";

const APP_SHELL = [
  "./index.html",
  "./manifest.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./data/moju/sococo_geral.geojson",
  "./data/moju/parcelas_adm.geojson",
  "./data/moju/parcelas_boa_fama.geojson",
  "./data/moju/parcelas_industrial.geojson",
  "./data/moju/parcelas_piaueira.geojson",
  "./data/moju/parcelas_lm.geojson",
  "./data/moju/parcelas_burraria.geojson",
  "./data/moju/estradas_internas.geojson",
  "./data/moju/estradas_estaduais.geojson",
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css",
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css",
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js",
  "https://unpkg.com/shpjs@4.0.4/dist/shp.min.js"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(APP_CACHE).then((cache) =>
      Promise.all(
        APP_SHELL.map((url) =>
          cache.add(url).catch(() => null) // não falhar a instalação se um CDN estiver fora do ar
        )
      )
    )
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== APP_CACHE && k !== TILE_CACHE)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

function isTileRequest(url) {
  return /tile\.openstreetmap\.org/.test(url) || /arcgisonline\.com\/ArcGIS\/rest\/services/.test(url);
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = req.url;

  // Tiles de mapa: network-first, guarda no cache para uso offline depois
  if (isTileRequest(url)) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(TILE_CACHE).then((cache) => cache.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // App shell e libs: cache-first, atualiza em segundo plano
  event.respondWith(
    caches.match(req).then((cached) => {
      const fetchPromise = fetch(req)
        .then((res) => {
          if (res && res.status === 200) {
            const copy = res.clone();
            caches.open(APP_CACHE).then((cache) => cache.put(req, copy));
          }
          return res;
        })
        .catch(() => cached);
      return cached || fetchPromise;
    })
  );
});
