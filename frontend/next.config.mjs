/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
      {
        source: '/catalog',
        destination: 'http://127.0.0.1:8000/catalog',
      },
      {
        source: '/agent-spec',
        destination: 'http://127.0.0.1:8000/agent-spec',
      },
      {
        source: '/merchant-b/:path*',
        destination: 'http://127.0.0.1:8000/merchant-b/:path*',
      },
      {
        source: '/simulate-stockout',
        destination: 'http://127.0.0.1:8000/simulate-stockout',
      },
      {
        source: '/reset-catalog',
        destination: 'http://127.0.0.1:8000/reset-catalog',
      },
    ];
  },
};

export default nextConfig;
