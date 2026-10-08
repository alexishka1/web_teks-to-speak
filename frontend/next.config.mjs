/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
  async rewrites() {
    const backendUrl = process.env.BACKEND_API_URL || "http://127.0.0.1:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: "/tts",
        destination: `${backendUrl}/tts`,
      },
      {
        source: "/voices",
        destination: `${backendUrl}/voices`,
      },
      {
        source: "/jobs/:path*",
        destination: `${backendUrl}/jobs/:path*`,
      },
      {
        source: "/health",
        destination: `${backendUrl}/health`,
      },
      {
        source: "/emotions",
        destination: `${backendUrl}/emotions`,
      },
      {
        source: "/emotions/:path*",
        destination: `${backendUrl}/emotions/:path*`,
      },
      {
        source: "/voice-clone/:path*",
        destination: `${backendUrl}/voice-clone/:path*`,
      },
      {
        source: "/projects/:path*",
        destination: `${backendUrl}/projects/:path*`,
      },
      {
        source: "/history/:path*",
        destination: `${backendUrl}/history/:path*`,
      },
    ];
  },
};

export default nextConfig;
