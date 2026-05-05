/** @type {import('next').NextConfig} */
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development'
});

const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/auth/:path*',
        destination: process.env.AUTH_SERVICE_URL + '/:path*'
      },
      {
        source: '/api/:path*',
        destination: process.env.API_SERVICE_URL + '/:path*'
      }
    ];
  }
};

module.exports = withPWA(nextConfig);
