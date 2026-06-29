import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175,
    host: '0.0.0.0',  // 允许局域网访问（手机测试）
    proxy: {
      "/api": "http://127.0.0.1:8001",
    },
  },
});
