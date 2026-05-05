/** @type {import('next').NextConfig} */
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
  fallbacks: {
    document: '/offline.html',
  },
  runtimeCaching: [
    {
      // Same-origin API calls go through Caddy at /api/* — never cache POST/PUT,
      // serve the latest GET when online and fall back to cache offline.
      urlPattern: /^\/api\/.*$/i,
      handler: 'NetworkFirst',
      method: 'GET',
      options: {
        cacheName: 'kirobi-api',
        networkTimeoutSeconds: 5,
        expiration: { maxEntries: 64, maxAgeSeconds: 60 * 60 * 24 },
        cacheableResponse: { statuses: [0, 200] },
      },
    },
    {
      urlPattern: /^https?:.*\.(?:png|jpg|jpeg|svg|webp|gif|ico)$/i,
      handler: 'StaleWhileRevalidate',
      options: {
        cacheName: 'kirobi-images',
        expiration: { maxEntries: 64, maxAgeSeconds: 60 * 60 * 24 * 30 },
      },
    },
    {
      urlPattern: /^https?:.*\.(?:js|css|woff2?)$/i,
      handler: 'StaleWhileRevalidate',
      options: { cacheName: 'kirobi-static' },
    },
  ],
});

// Build the rewrite list dynamically so it stays empty when no upstream is
// configured (production deploys put Caddy in front and reach the services
// directly). Without this guard `next build` blows up when AUTH_SERVICE_URL
// is undefined.
function isValidUpstream(value) {
  if (!value || typeof value !== 'string') return false;
  try {
    const url = new URL(value);
    // Only http(s) to internal upstreams; reject anything weird like
    // file:, javascript:, ftp:, or URLs with embedded credentials.
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return false;
    if (url.username || url.password) return false;
    if (!url.hostname) return false;
    return true;
  } catch {
    return false;
  }
}

function buildRewrites() {
  const rewrites = [];
  const auth = process.env.AUTH_SERVICE_URL;
  const api = process.env.API_SERVICE_URL;
  if (isValidUpstream(auth)) {
    rewrites.push({
      source: '/api/auth/:path*',
      destination: auth.replace(/\/+$/, '') + '/:path*',
    });
  }
  if (isValidUpstream(api)) {
    rewrites.push({
      source: '/api/:path*',
      destination: api.replace(/\/+$/, '') + '/:path*',
    });
  }
  return rewrites;
}

const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  poweredByHeader: false,
  // The PWA is consumed under multiple origins (kirobi.local, LAN IP,
  // localhost). Letting Next inject CSP-unfriendly absolute URLs would
  // break the Service Worker on those origins, so we keep paths relative.
  async rewrites() {
    return buildRewrites();
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(self), geolocation=()' },
        ],
      },
      {
        // Service Worker must always be served fresh, otherwise PWAs end
        // up trapped on a stale build.
        source: '/sw.js',
        headers: [{ key: 'Cache-Control', value: 'no-cache, no-store, must-revalidate' }],
      },
      {
        source: '/manifest.json',
        headers: [{ key: 'Cache-Control', value: 'public, max-age=3600' }],
      },
    ];
  },
};

module.exports = withPWA(nextConfig);
