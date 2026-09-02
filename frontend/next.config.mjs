const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`,
      },
      {
        source: '/catalog',
        destination: `${BACKEND_URL}/catalog`,
      },
      {
        source: '/agent-spec',
        destination: `${BACKEND_URL}/agent-spec`,
      },
      {
        source: '/merchant-b/:path*',
        destination: `${BACKEND_URL}/merchant-b/:path*`,
      },
      {
        source: '/simulate-stockout',
        destination: `${BACKEND_URL}/simulate-stockout`,
      },
      {
        source: '/reset-catalog',
        destination: `${BACKEND_URL}/reset-catalog`,
      },
    ];
  },
};

export default nextConfig;
