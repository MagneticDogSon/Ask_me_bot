import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  // Standard 'out' directory inside the web folder, to avoid Turbopack restriction.
  // We will move it manually after build.
  distDir: "out",
  images: {
    unoptimized: true,
  },
  // Set this if you are deploying to a subdirectory on GitHub Pages
  basePath: "/Ask_me_bot",
};

export default nextConfig;
