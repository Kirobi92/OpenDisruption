/** @type {import('next').NextConfig} */
const path = require('path')
const nextConfig = {
  output: 'standalone',
  basePath: '/portal',
  env: {
    NEXT_PUBLIC_BASE_PATH: '/portal',
  },
  eslint: { ignoreDuringBuilds: true },
  outputFileTracingRoot: path.join(__dirname, '../../'),
};
module.exports = nextConfig;
