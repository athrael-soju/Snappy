import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: '200mb',
    },
    // Turbopack filesystem caching for faster dev server restarts (beta in Next.js 16)
    turbopackFileSystemCacheForDev: true,
  },
  // Cache Components - opt-in caching model (new in Next.js 16)
  cacheComponents: true,
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/files/**",
      },
      {
        protocol: "http",
        hostname: "backend",
        port: "8000",
        pathname: "/files/**",
      },
    ],
  },
};

export default nextConfig;
