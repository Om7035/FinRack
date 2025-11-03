const withPWA = require('next-pwa')({ dest: 'public', disable: process.env.NODE_ENV === 'development' })

/** @type {import('next').NextConfig} */
module.exports = withPWA({
  reactStrictMode: true,
  swcMinify: true,
  images: { domains: ['localhost'] },
  async rewrites() {
    return [
      { source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' },
    ]
  },
})
