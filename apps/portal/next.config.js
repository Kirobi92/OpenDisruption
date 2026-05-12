/** @type {import('next').NextConfig} */
const path = require('path')
const nextConfig = {
  output: 'standalone',
  eslint: { ignoreDuringBuilds: true },
  outputFileTracingRoot: path.join(__dirname, '../../'),
};
module.exports = nextConfig;
