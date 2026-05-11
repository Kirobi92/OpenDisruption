/** @type {import('next').NextConfig} */

function isValidUpstream(value: string | undefined): boolean {
  if (!value || typeof value !== 'string') return false;
  try {
    const url = new URL(value);
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return false;
    if (url.username || url.password) return false;
    if (!url.hostname) return false;
    return true;
  } catch {
    return false;
  }
}

function buildRewrites(): { source: string; destination: string }[] {
  const rewrites: { source: string; destination: string }[] = [];
  const auth = process.env.AUTH_SERVICE_URL;
  const api = process.env.API_SERVICE_URL;
  if (isValidUpstream(auth)) {
    rewrites.push({
      source: '/api/auth/:path*',
      destination: auth!.replace(/\/+$/, '') + '/:path*',
    });
  }
  if (isValidUpstream(api)) {
    rewrites.push({
      source: '/api/:path*',
      destination: api!.replace(/\/+$/, '') + '/:path*',
    });
  }
  return rewrites;
}

const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  distDir: '.next-build',
  poweredByHeader: false,
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
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
        ],
      },
    ];
  },
};

export default nextConfig;
