import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // sem isso, acessar por 127.0.0.1 bloqueia os assets dev e a página não hidrata
  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;
